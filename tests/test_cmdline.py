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

import argparse
import shlex
from argparse import ArgumentError, Namespace

import pytest

from dtlayertool.app import make_arg_parser

# Note that the tests here use vars(namespace) == dict(...) instead of the
# shorter and in theory equivalent namespace == Namespace(...) because
# the error output of pytest is better for dicts.


def argdict(args, **kwargs):
    assert isinstance(args.parser, argparse.ArgumentParser)
    result = dict(
        parser=args.parser,
        profile=None,
        debug=None,
    )
    result.update(kwargs)
    return result


def parse_cmdline(cmdline: str) -> Namespace:
    try:
        return make_arg_parser().parse_args(shlex.split(cmdline))
    except SystemExit as exc:
        cause = exc.__cause__ or exc.__context__
        # Raise the inner ArgumentError
        if cause:
            raise cause from None
        raise


def test_howto_clone_not_working():
    # This is from the original howto, but does not work anymore
    # because the subparser's arguments need to be after the command.
    with pytest.raises(ArgumentError) as excinfo:
        parse_cmdline(
            "--target-region eu-central-1 --profile default clone "
            "arn:aws:lambda:us-east-1:123456789012:layer:foo:1"
        )
    assert "argument command: invalid choice" in str(excinfo.value)


def test_howto_clone():
    args = parse_cmdline(
        "--profile default clone "
        "arn:aws:lambda:us-east-1:123456789012:layer:foo:1 "
        "--target-region eu-central-1"
    )
    args2 = parse_cmdline(
        "--profile default clone --target-region eu-central-1 "
        "arn:aws:lambda:us-east-1:123456789012:layer:foo:1"
    )
    args2.parser = args.parser
    assert args == args2

    assert vars(args) == argdict(
        args,
        command="clone",
        profile="default",
        layer_arn="arn:aws:lambda:us-east-1:123456789012:layer:foo:1",
        target_region="eu-central-1",
        overwrite=False,
    )


def test_clone_overwrite():
    args = parse_cmdline(
        "clone --overwrite arn:aws:lambda:us-east-1:123456789012:layer:foo:1"
    )
    assert vars(args) == argdict(
        args,
        command="clone",
        layer_arn="arn:aws:lambda:us-east-1:123456789012:layer:foo:1",
        target_region=None,
        overwrite=True,
    )


def test_howto_pull():
    args = parse_cmdline(
        "pull arn:aws:lambda:us-east-1:123456789012:layer:foo:1 "
        "--extract DynatraceOneAgentExtension"
    )
    assert vars(args) == argdict(
        args,
        command="pull",
        layer_arn="arn:aws:lambda:us-east-1:123456789012:layer:foo:1",
        overwrite=False,
        extract="DynatraceOneAgentExtension",
    )


def test_pull_positional_in_middle():
    args = parse_cmdline(
        "--profile=x --debug --debug pull --overwrite "
        "arn:aws:lambda:us-east-1:123456789012:layer:foo:1 "
        "--extract DynatraceOneAgentExtension"
    )
    assert vars(args) == argdict(
        args,
        profile="x",
        debug=2,
        command="pull",
        layer_arn="arn:aws:lambda:us-east-1:123456789012:layer:foo:1",
        overwrite=True,
        extract="DynatraceOneAgentExtension",
    )


def test_pull_overwrite_noextract():
    args = parse_cmdline(
        "pull --overwrite arn:aws:lambda:us-east-1:123456789012:layer:foo:1"
    )
    assert vars(args) == argdict(
        args,
        command="pull",
        layer_arn="arn:aws:lambda:us-east-1:123456789012:layer:foo:1",
        overwrite=True,
        extract=None,
    )


def test_howto_info():
    args = parse_cmdline("info arn:aws:lambda:us-east-1:123456789012:layer:foo:1")
    assert vars(args) == argdict(
        args,
        command="info",
        layer_arn="arn:aws:lambda:us-east-1:123456789012:layer:foo:1",
    )
