import shlex
from argparse import ArgumentError, Namespace

import pytest

from dtlayertool.app import make_arg_parser

# Note that the tests here use vars(namespace) == dict(...) instead of the
# shorter and in theory equivalent namespace == Namespace(...) because
# the error output of pytest is better for dicts.


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

    assert vars(args) == dict(
        command="clone",
        profile="default",
        layer_arn="arn:aws:lambda:us-east-1:123456789012:layer:foo:1",
        target_region="eu-central-1",
        parser=args.parser,
        overwrite=False,
    )


def test_clone_overwrite():
    args = parse_cmdline(
        "clone --overwrite arn:aws:lambda:us-east-1:123456789012:layer:foo:1"
    )
    assert vars(args) == dict(
        command="clone",
        profile=None,
        layer_arn="arn:aws:lambda:us-east-1:123456789012:layer:foo:1",
        target_region=None,
        parser=args.parser,
        overwrite=True,
    )


def test_howto_pull():
    args = parse_cmdline(
        "pull arn:aws:lambda:us-east-1:123456789012:layer:foo:1 "
        "--extract DynatraceOneAgentExtension"
    )
    assert vars(args) == dict(
        command="pull",
        profile=None,
        layer_arn="arn:aws:lambda:us-east-1:123456789012:layer:foo:1",
        parser=args.parser,
        overwrite=False,
        extract="DynatraceOneAgentExtension",
    )


def test_pull_overwrite_noextract():
    args = parse_cmdline(
        "pull --overwrite arn:aws:lambda:us-east-1:123456789012:layer:foo:1"
    )
    assert vars(args) == dict(
        command="pull",
        profile=None,
        layer_arn="arn:aws:lambda:us-east-1:123456789012:layer:foo:1",
        parser=args.parser,
        overwrite=True,
        extract=None,
    )


def test_howto_info():
    args = parse_cmdline("info arn:aws:lambda:us-east-1:123456789012:layer:foo:1")
    assert vars(args) == dict(
        command="info",
        profile=None,
        layer_arn="arn:aws:lambda:us-east-1:123456789012:layer:foo:1",
        parser=args.parser,
    )
