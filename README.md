# dt-awslayertool

`dt-awslayertool` is an utility to download or clone
[AWS Lambda Layers](https://docs.aws.amazon.com/lambda/latest/dg/configuration-layers.html),
including extensions distributed as layers.

## Installation

> TODO: Upload to PyPI.

It is recommended that you install to a Python virtual environment (venv)
and update the `pip`, `setuptools` and `wheel` packages before installation.

```bash
$ python3 -m venv .venv # On Windows use "py -3" instead of "python3"
$ . .venv/bin/activate  # On Windows use .venv\Scripts\activate
(.venv) $ python -m pip install -U pip
(.venv) $ pip install -U setuptools wheel
```

To install the latest development version, use

```bash
pip install 'git+https://github.com/dynatrace-oss/dt-awslayertool.git#egg=dt-awslayertool'
```

See the [`pip install` documentation](https://pip.pypa.io/en/stable/cli/pip_install/#git)
for more information, e.g. how to install a particular version.

## Usage

This sections is extracted from `dt-awslayertool --help` output.

    usage: dt-awslayertool [-h] [-p <aws profile>] {info,pull,clone} ...

    Download or clone an AWS Lambda layer.

    optional arguments:
    -h, --help            show this help message and exit
    -p <aws profile>, --profile <aws profile>
                          use the specified AWS profile (~/.aws/credentials)

    Commands:
    {info,pull,clone}
        info              print layer meta information
        pull              download given layer to <layer name>-<layer
                          version>.zip file
        clone             clone layer to AWS account defined by current profile

    Example:
    Downloads the layer content to file my_layer-v1.zip.
        dt-awslayertool --profile default pull arn:aws:lambda:us-east-1:1234861453:layer:my_layer:1

    Clone layer to default account
        dt-awslayertool --profile default clone arn:aws:lambda:us-east-1:1234861453:layer:my_layer:1

### info

Print layer meta information.

    usage: dt-awslayertool info [-h] layer_arn

    positional arguments:
    layer_arn             ARN of the layer to operate on

Example output:

```bash
$ dt-awslayertool info arn:aws:lambda:us-east-1:725887861453:layer:Dynatrace_OneAgent_1_207_6_20201127-103507_nodejs:1
querying layer version meta information for arn:aws:lambda:us-east-1:725887861453:layer:Dynatrace_OneAgent_1_207_6_20201127-103507_nodejs:1
Description:         Dynatrace OneAgent 1.207.6.20201127-103507 for Node.js runtime.
LicenseInfo:         Copyright (c) 2012-2020 Dynatrace LLC. All rights reserved.
CompatibleRuntimes:  nodejs10.x nodejs12.x
Version:             1
CreatedDate:         2020-11-27T09:40:44.607+0000
CodeSize:            1833343
CodeSha256:          PHsE+LnCmzo9aP2+HC7BDNXKwNxKITtRU9+2TnxPmNQ=
Location:            https://prod-04-2014-layers.s3.us-east-1.amazonaws.com/snapshots/725887861453/Dynatrace_OneAgent_1_207_6_20201127-103507_nodejs-75cf9f3f-85f9-4134-a48c-d11acc158daf?versionId=...
```

Using the `aws` command line tool (`aws lambda get-layer-version-by-arn --arn arn:aws:lambda:us-east-1:725887861453:layer:Dynatrace_OneAgent_1_207_6_20201127-103507_nodejs:1`)
displays more complete information.

### pull

Download given layer to `<layer name>-<layer version>.zip` file.
See also [Clone Dynatrace OneAgent AWS Lambda extension](docs/CloneExtensionHowto.md).

    usage: dt-awslayertool pull [-h] [-o] [-x <folder>] layer_arn

    positional arguments:
    layer_arn             ARN of the layer to operate on

    optional arguments:
    -o, --overwrite       overwrite existing layer contents or extracted folders
    -x <folder>, --extract <folder>
                          extract the downloaded layer content to given folder

### clone

Clone layer to AWS account defined by current profile.
See also [Enable Dynatrace monitoring for containerized AWS Lambda functions](docs/ContainerizedLambdaHowto.md).

    usage: dt-awslayertool clone [-h] [-o] [-t <aws region>] layer_arn

    positional arguments:
    layer_arn             ARN of the layer to operate on

    optional arguments:
    -o, --overwrite       overwrite existing layer contents or extracted folders
    -t <aws region>, --target-region <aws region>
                          clone the layer to the specified AWS region. By
                          default, the region of the source ARN is used
