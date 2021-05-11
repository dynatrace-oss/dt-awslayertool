# Copyright 2021 Dynatrace LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import contextlib
import hashlib
import os
import re
import shutil
import typing
import urllib.request
from base64 import b64encode
from email import message_from_string
from http.client import HTTPMessage
from pathlib import Path
from typing import Callable, ContextManager, NamedTuple, Optional, Tuple, Union
from unittest import mock
from zipfile import ZipFile

import boto3
import pytest
from botocore.stub import Stubber

from dtawslayertool import app


@pytest.fixture
def tmp_cwd(
    tmp_path: Path,
) -> typing.Iterable[Path]:
    prev_cwd = Path.cwd()
    os.chdir(tmp_path)
    yield tmp_path
    os.chdir(prev_cwd)


MOCK_LOCATION = "https://example.invalid/layer/foo"
MOCK_ZIPFILESOURCE_FNAME = "serverside-layer.zip"
MOCK_INNERFILENAME = "dynatrace"
MOCK_INNERFILECONTENT = b"#!/bin/sh\ntrue\n"


def write_mock_zip(tmp_path: Path) -> Tuple[Path, str]:
    """Writes the mock zip and returns its path and base64-sha256"""
    ofpath = tmp_path / MOCK_ZIPFILESOURCE_FNAME
    with ZipFile(ofpath, "w") as zipf:
        zipf.writestr(MOCK_INNERFILENAME, MOCK_INNERFILECONTENT)
    return (
        ofpath,
        b64encode(hashlib.sha256(ofpath.read_bytes()).digest()).decode("ascii"),
    )


class MockInfo(NamedTuple):
    srczippath: Path


def setup_urlretrieve(
    srcpath: Path, sha256: str, fsize: int, monkeypatch: pytest.MonkeyPatch
):
    def mocked_urlretrieve(
        url: str,
        filename: Optional[Union[str, os.PathLike]] = None,
        reporthook: Optional[Callable[[int, int, int], None]] = None,
        data: Optional[bytes] = None,
    ) -> Tuple[str, HTTPMessage]:
        assert url == MOCK_LOCATION
        assert isinstance(data, bytes) or data is None
        filename = filename or "retrieved.dat"
        reporthook(0, fsize // 2, fsize)
        dstpath = (shutil.copyfile(srcpath, filename),)
        reporthook(1, fsize // 2, fsize)
        reporthook(2, fsize // 2, fsize)
        return (
            dstpath,
            message_from_string(
                f"""x-amz-id-2: o7+2hkEMcor15Ja=
x-amz-request-id: 7YTCM76R6WJDQVP7
Date: Thu, 06 May 2021 11:04:40 GMT
Last-Modified: Fri, 27 Nov 2020 09:40:42 GMT
ETag: "{sha256}-bla"
x-amz-server-side-encryption: AES256
x-amz-version-id: inaUofwd8k5ejWZg2uvNbB4FK.6XLm9F
Accept-Ranges: bytes
Content-Type: application/zip
Content-Length: {fsize}
Server: AmazonS3
Connection: close""",
                HTTPMessage,
            ),
        )

    urlretrieve_mock = mock.Mock(side_effect=mocked_urlretrieve)
    monkeypatch.setattr(urllib.request, "urlretrieve", urlretrieve_mock)
    monkeypatch.setattr(app, "urlretrieve", urlretrieve_mock)


# Pytest fixtures work by matching names, so this pylint warning is annoying:
# pylint:disable=redefined-outer-name


@contextlib.contextmanager
def setup_mocks(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    configure_stubber: Callable[[Stubber, dict], None],
    allow_retrieve: bool,
) -> ContextManager[MockInfo]:
    srcpath, sha256 = write_mock_zip(tmp_path)
    fsize = srcpath.stat().st_size
    if allow_retrieve:
        setup_urlretrieve(srcpath, sha256, fsize, monkeypatch)

    original_client = boto3.Session.client

    layerinfo = {
        "ResponseMetadata": {
            "RequestId": "7a3a5c85-9608-45e4-8783-b81f09a2f176",
            "HTTPStatusCode": 200,
            "HTTPHeaders": {
                "date": "Thu, 06 May 2021 11:04:40 GMT",
                "content-type": "application/json",
                "content-length": "2298",
                "connection": "keep-alive",
                "x-amzn-requestid": "7a3a5c85-9608-45e4-8783-b81f09a2f176",
            },
            "RetryAttempts": 0,
        },
        "Content": {
            "Location": MOCK_LOCATION,
            "CodeSha256": sha256,
            "CodeSize": fsize,
        },
        "LayerArn": "arn:aws:lambda:us-east-1:123456789012:layer:foo",
        "LayerVersionArn": "arn:aws:lambda:us-east-1:123456789012:layer:foo:1",
        "Description": "Dynatrace OneAgent for Node.js runtime.",
        "CreatedDate": "2020-11-27T09:40:44.607+0000",
        "Version": 1,
        "CompatibleRuntimes": ["nodejs10.x", "nodejs12.x"],
        "LicenseInfo": "Copyright (c) 2012-2020 Dynatrace LLC. All rights reserved.",
    }

    stubbers = []  # type: typing.List[Stubber]

    def wrap_client(self: boto3.Session, service_name: str, *args, **kwargs):
        assert service_name == "lambda"
        client = original_client(self, service_name, *args, **kwargs)
        stubber = Stubber(client)
        configure_stubber(stubber, layerinfo)
        stubber.activate()
        stubbers.append(stubber)
        return client

    monkeypatch.setattr(boto3.Session, "client", wrap_client)
    yield MockInfo(srcpath)
    for stubber in stubbers:
        stubber.assert_no_pending_responses()


def setup_info_stubber(stubber: Stubber, layerinfo: dict):
    stubber.add_response("get_layer_version_by_arn", layerinfo)


def test_pull(tmp_cwd: Path, monkeypatch: pytest.MonkeyPatch):
    with setup_mocks(
        tmp_cwd, monkeypatch, setup_info_stubber, allow_retrieve=True
    ) as mockinfo:
        app.main(
            (
                "pull",
                "arn:aws:lambda:us-east-1:123456789012:layer:foo:1",
                "--extract=extracted",
            )
        )
        dlpath = tmp_cwd / "foo-v1.zip"

        assert dlpath.is_file()
        assert mockinfo.srczippath.read_bytes() == dlpath.read_bytes()

        extractpath = tmp_cwd / "extracted"
        assert extractpath.is_dir()
        assert tuple(p.name for p in extractpath.iterdir()) == (MOCK_INNERFILENAME,)
        innerfilepath = extractpath / MOCK_INNERFILENAME
        assert innerfilepath.read_bytes() == MOCK_INNERFILECONTENT


def test_info(
    tmp_cwd: Path, capsys: pytest.CaptureFixture, monkeypatch: pytest.MonkeyPatch
):
    with setup_mocks(tmp_cwd, monkeypatch, setup_info_stubber, allow_retrieve=False):
        app.main(
            (
                "info",
                "arn:aws:lambda:us-east-1:123456789012:layer:foo:1",
            )
        )
        out = capsys.readouterr().out
        assert re.search(
            r"Description: +Dynatrace OneAgent for Node.js runtime.",
            out,
        )


def test_clone(tmp_cwd: Path, monkeypatch: pytest.MonkeyPatch):
    def setup_pub_stubber(stubber: Stubber, layerinfo: dict):
        layerinfo["ResponseMetadata"]["HTTPStatusCode"] = 201
        layerinfo["LayerArn"] = layerinfo["LayerArn"].replace("123456", "012345")
        layerinfo["LayerVersionArn"] = layerinfo["LayerVersionArn"].replace(
            "123456", "012345"
        )
        stubber.add_response("publish_layer_version", layerinfo)

    stubbers = iter((setup_info_stubber, setup_pub_stubber))

    def setup_stubbers(stubber: Stubber, layerinfo: dict):
        return next(stubbers)(stubber, layerinfo)

    with setup_mocks(
        tmp_cwd, monkeypatch, setup_stubbers, allow_retrieve=True
    ) as mockinfo:
        app.main(
            (
                "clone",
                "arn:aws:lambda:us-east-1:123456789012:layer:foo:1",
                "--overwrite",
            )
        )
        dlpath = tmp_cwd / "foo-v1.zip"

        assert dlpath.is_file()
        assert mockinfo.srczippath.read_bytes() == dlpath.read_bytes()
