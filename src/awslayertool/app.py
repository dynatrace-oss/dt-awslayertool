import argparse
import os
import shutil
import sys
from collections import namedtuple
from collections.abc import Iterable
from os import path
from urllib.request import urlretrieve
from zipfile import ZipFile

import boto3

# extract_all_with_permission from
# https://stackoverflow.com/a/46837272/2128694
# by de1 <https://stackoverflow.com/users/8676953/de1>

ZIP_UNIX_SYSTEM = 3


def extract_all_with_permission(zipfile: ZipFile, target_dir: str):
    for info in zipfile.infolist():
        extracted_path = zipfile.extract(info, target_dir)

        if info.create_system == ZIP_UNIX_SYSTEM:
            unix_attributes = info.external_attr >> 16
            if unix_attributes:
                os.chmod(extracted_path, unix_attributes)


def eprint(*args, **kwargs):
    return print(*args, **kwargs, file=sys.stderr, flush=True)


class Arn(
    namedtuple("Arn", "partition service region account_id resource_type resource_id")
):
    @classmethod
    def parse(cls, raw: str) -> "Arn":
        arn_prefix = "arn:"
        if not raw.startswith(arn_prefix):
            raise ValueError("Not an ARN (prefix missing): " + raw)
        parts = raw[len(arn_prefix) :].split(":", 5)
        if len(parts) == 5:
            parts.insert(-2, None)  # resource-type is optional
        if len(parts) != 6:
            raise ValueError("ARN has too few parts: " + raw)
        return cls._make(parts)

    def __str__(self):
        return "arn:" + ":".join(self)


class LayerResourceName(namedtuple("LayerResourceName", "layer_name version")):
    @classmethod
    def parse(cls, raw: str) -> "LayerResourceName":
        parts = raw.split(":", 2)
        if len(parts) == 1:
            return LayerResourceName(layer_name=parts[0], version=None)
        if len(parts) > 2:
            raise ValueError("Too many colons: " + raw)
        return LayerResourceName._make(parts)

    @classmethod
    def from_arn(cls, arn: Arn) -> "LayerResourceName":
        if arn.resource_type != "layer":
            raise ValueError("Bad ARN type: " + arn.resource_type)
        return cls.parse(arn.resource_id)

    def __str__(self):
        return ":".join(self)


def add_download_args(parser: argparse.ArgumentParser):
    parser.add_argument(
        "-o",
        "--overwrite",
        action="store_true",
        help="overwrite existing layer contents or extracted folders",
    )


def make_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description="Download or clone a AWS Lambda layer.",
        epilog="""
Example:
 Downloads the layer content to file my_layer-v1.zip.
  %(prog)s--profile default pull arn:aws:lambda:us-east-1:1234861453:layer:my_layer:1

 Clone layer to default account
  %(prog)s --profile default clone arn:aws:lambda:us-east-1:1234861453:layer:my_layer:1
  """,
    )
    parser.set_defaults(parser=parser)
    parser.add_argument(
        "-p",
        "--profile",
        help="use the specified AWS profile (~/.aws/credentials)",
        metavar="<aws profile>",
    )

    subparsers = parser.add_subparsers(title="Commands", dest="command")
    subparsers.required = True

    parser.add_argument("layer_arn", help="ARN of the layer to operate on")

    subparsers.add_parser("info", help="print layer meta information")

    pull_parser = subparsers.add_parser(
        "pull", help="download given layer to <layer name>-<layer version>.zip file"
    )
    add_download_args(pull_parser)
    pull_parser.add_argument(
        "-x",
        "--extract",
        help="extract the downloaded layer content to given folder",
        metavar="<folder>",
    )

    clone_parser = subparsers.add_parser(
        "clone", help="clone layer to AWS account defined by current profile"
    )
    add_download_args(clone_parser)
    clone_parser.add_argument(
        "-t",
        "--target-region",
        help="clone the layer to the specified AWS region",
        metavar="<aws region>",
    )

    return parser


def print_values(mapping, keys):
    for key in keys:
        value = mapping[key]
        if isinstance(value, Iterable) and not isinstance(value, str):
            value = " ".join(value)
        print("{:20} {}".format(str(key) + ":", value))


def query_layerinfo(client, layer_arn):
    eprint("querying layer version meta information for", layer_arn)
    return client.get_layer_version_by_arn(Arn=layer_arn)


def cmd_info(args):
    print_layerinfo(query_layerinfo(lambda_client_for(args.layer_arn), args.layer_arn))


def error_exists(name):
    sys.exit(
        "{} already exists. Remove and re-run or specify --overwrite option".format(
            name,
        )
    )


def show_progress(block_count, block_size, total_size):
    if block_count == 0:
        eprint("Connected...", end=" ")
    else:
        blocks_per_mb = max(1, int(1024 * 1024 / block_size))
        if block_count % blocks_per_mb == 0:
            ratio = block_count * block_size / total_size
            eprint("{:%}".format(ratio), end=" ")


def download_layer(client, layer_arn: str, overwrite: bool):
    layername = LayerResourceName.from_arn(Arn.parse(layer_arn))
    outfilename = "{}-v{}.zip".format(*layername)

    if path.exists(outfilename) and not overwrite:
        error_exists(outfilename)

    layerinfo = query_layerinfo(client, layer_arn)
    codesize = layerinfo["Content"]["CodeSize"]  # type: int
    eprint(
        "downloading {} content [{} bytes] to {} ...".format(
            layer_arn, codesize, outfilename
        )
    )
    urlretrieve(layerinfo["Content"]["Location"], outfilename, reporthook=show_progress)
    eprint()  # Newline after progress report
    filesize = path.getsize(outfilename)
    if filesize != codesize:
        sys.exit(
            "Downloaded file corrupted -- expected {} bytes, but have {}", codesize
        )
    eprint("downloaded layer content to", outfilename)
    return layerinfo, outfilename


def lambda_client_for(layer_arn: str):
    return boto3.client("lambda", region_name=Arn.parse(layer_arn).region)


def cmd_pull(args):
    extractdir = args.extract  # type: str
    need_clean = False
    if extractdir:
        if path.exists(extractdir):
            if args.overwrite:
                need_clean = True
            else:
                error_exists(extractdir)
    _layerinfo, outfilename = download_layer(
        lambda_client_for(args.layer_arn), args.layer_arn, args.overwrite
    )
    if extractdir:
        if need_clean:
            shutil.rmtree(extractdir)
        eprint('extracting layer contents to "{}"'.format(args.extract))
        with ZipFile(outfilename, "r") as zipfile:
            extract_all_with_permission(zipfile, args.extract)


def cmd_clone(args):
    layerinfo, outfilename = download_layer(
        lambda_client_for(args.layer_arn), args.layer_arn, args.overwrite
    )
    arn = Arn.parse(args.layer_arn)
    target_region = args.target_region or arn.region
    eprint("cloning layer to", target_region)
    client = boto3.client("lambda", region_name=target_region)

    # We need to read the whole file into memory at once,
    # the API won't accept it any other way.
    with open(outfilename, "rb") as filehandle:
        layercontent = filehandle.read()

    newlayerinfo = client.publish_layer_version(
        LayerName=LayerResourceName.from_arn(arn).layer_name,
        Description=layerinfo["Description"],
        CompatibleRuntimes=layerinfo["CompatibleRuntimes"],
        LicenseInfo=layerinfo["LicenseInfo"],
        Content=dict(ZipFile=layercontent),
    )
    newlayerhash = newlayerinfo["Content"]["CodeSha256"]
    layerhash = layerinfo["Content"]["CodeSha256"]
    if newlayerhash != layerhash:
        sys.exit(
            "something went terribly wrong -"
            " SHA256 fingerprint of source and cloned layer do not match."
        )


def print_layerinfo(layerinfo):
    content = layerinfo["Content"]
    print_values(
        layerinfo,
        keys=(
            "Description",
            "LicenseInfo",
            "CompatibleRuntimes",
            "Version",
            "CreatedDate",
        ),
    )
    print_values(content, keys=("CodeSize", "CodeSha256", "Location"))


def main():
    parser = make_arg_parser()
    args = parser.parse_args()
    print(args)
    globals()["cmd_" + args.command](args)


if __name__ == "__main__":
    main()
