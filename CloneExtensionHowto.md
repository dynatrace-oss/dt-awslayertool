# Clone Dynatrace OneAgent AWS Lambda extension

This document describes how to clone Dynatrace OneAgent extension to private AWS accounts.

Dynatrace OneAgent AWS Lambda extension is a AWS Lambda layer shared from a Dynatrace AWS account. The
layer must be attached to AWS Lambda functions to enable deep monitoring. Specific security policies might
apply that disallow the usage of such shared AWS Lambda layers.

To mitigate those security concerns, Dynatrace OneAgent AWS Lambda extension can be cloned to an private AWS account.

`dtlayertool` can be used to clone a layer.

```bash
$ dtlayertool --profile default clone arn:aws:lambda:us-east-1:725887861453:layer:Dynatrace_OneAgent_1_207_6_20201127-103507_nodejs:1 --target-region eu-central-1
querying layer version meta information for arn:aws:lambda:us-east-1:725887861453:layer:Dynatrace_OneAgent_1_207_6_20201127-103507_nodejs:1
downloading arn:aws:lambda:us-east-1:725887861453:layer:Dynatrace_OneAgent_1_207_6_20201127-103507_nodejs:1 content [1833343 bytes] to Dynatrace_OneAgent_1_207_6_20201127-103507_nodejs-v1.zip ...
Connected... 10% 20% 29% 39% 49% 59% 69% 79% 88% 98% Done.
downloaded layer content to Dynatrace_OneAgent_1_207_6_20201127-103507_nodejs-v1.zip
cloning layer to eu-central-1
created arn:aws:lambda:eu-central-1:123456789012:layer:Dynatrace_OneAgent_1_207_6_20201127-103507_nodejs:1
```

The command cloned AWS Lambda layer
`arn:aws:lambda:us-east-1:725887861453:layer:Dynatrace_OneAgent_1_207_6_20201127-103507_nodejs:1` to the
account defined by `default` AWS profile and AWS region `eu-central-1`.

`dtlayertool` can be used to query the properties of the cloned or original layer in a readable format:

```bash
$ dtlayertool info arn:aws:lambda:us-east-1:725887861453:layer:Dynatrace_OneAgent_1_207_6_20201127-103507_nodejs:1
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

Once the layer is cloned to the specific account or region, it can be attached to Lambda functions to enable
monitoring.
