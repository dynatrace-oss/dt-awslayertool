# dtlayertool

`dtlayertool` is an utility to download or clone AWS Lambda Layers or extensions.

## Installation

> TODO: Upload to PyPI.

It is recommended that you install to a Python virtual environment (venv)
and update the `pip`, `setuptools` and `wheel` packages before installation.

To install the latest development version, use

```bash
pip install 'git+https://github.com/dynatrace-oss/dtlayertool.git#egg=dtlayertool'
```

See the [`pip install` documentation](https://pip.pypa.io/en/stable/cli/pip_install/#git)
for more information.

## Usage

    usage: dtlayertool [-h] [-p <aws profile>] {info,pull,clone} ...

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
        dtlayertool --profile default pull arn:aws:lambda:us-east-1:1234861453:layer:my_layer:1

    Clone layer to default account
        dtlayertool --profile default clone arn:aws:lambda:us-east-1:1234861453:layer:my_layer:1

## info

    usage: dtlayertool info [-h] layer_arn

    positional arguments:
    layer_arn             ARN of the layer to operate on

## pull

    usage: dtlayertool pull [-h] [-o] [-x <folder>] layer_arn

    positional arguments:
    layer_arn             ARN of the layer to operate on

    optional arguments:
    -o, --overwrite       overwrite existing layer contents or extracted folders
    -x <folder>, --extract <folder>
                          extract the downloaded layer content to given folder

## clone

    usage: dtlayertool clone [-h] [-o] [-t <aws region>] layer_arn

    positional arguments:
    layer_arn             ARN of the layer to operate on

    optional arguments:
    -o, --overwrite       overwrite existing layer contents or extracted folders
    -t <aws region>, --target-region <aws region>
                          clone the layer to the specified AWS region. By
                          default, the region of the source ARN is used
