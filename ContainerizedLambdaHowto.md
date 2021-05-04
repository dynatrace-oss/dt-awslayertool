# Enable Dynatrace monitoring for containerized AWS Lambda functions

As an addition to function deployment as a ZIP file, AWS Lambda features deployment
of [Lambda function as container images](https://aws.amazon.com/de/blogs/aws/new-for-aws-lambda-container-image-support/).

The container image must include files and configuration required to run the function code. The same applies
to files and configuration of Dynatrace OneAgent, once monitoring should be enabled for the containerized
Lambda function.

In ZIP file style function deployment, Dynatrace OneAgent code modules will be attached to the function with a
[AWS Lambda Extension](https://docs.aws.amazon.com/lambda/latest/dg/using-extensions.html)
(which is a Lambda layer with an extension specific folder layout).

A Lambda layer is, similar to the function bundle a ZIP file, extracted at function
cold start time to the `/opt` folder of the AWS Lambda function instance.

Thus, the process to enable Dynatrace monitoring for a containerized Lambda function requires to

1. provision Dynatrace OneAgent configuration and to
2. add contents of OneAgent Extension to the Lambda container image.

## Provision Dynatrace OneAgent configuration

Retrieve OneAgent configuration as described in [Dynatrace documentation](https://www.dynatrace.com/support/help/technology-support/cloud-platforms/amazon-web-services/integrations/deploy-oneagent-as-lambda-extension/).

Select configuration type `Configure with environment variables` and complete remaining configuration items.

Open the projects `Dockerfile` in an editor and copy the environment variables from the deployment screen. Each
line must be prefixed with `ENV` and spaces around the equal signs must be removed.

```Dockerfile
ENV AWS_LAMBDA_EXEC_WRAPPER=/opt/dynatrace
ENV DT_TENANT=abcd1234
ENV DT_CLUSTER_ID=1234567890
ENV DT_CONNECTION_BASE_URL=https://abcd1234.live.dynatrace.com
ENV DT_CONNECTION_AUTH_TOKEN=dt0a01...
```

## Add OneAgent extension to container image

First, the contents of Dynatrace OneAgent extension must be downloaded.
`dtlayertool` is a Python 3.6+ application to download given Lambda extension or
layers by their ARN. The ARN of Dynatrace OneAgent extension can be copied from the deployment screen.

Example invocation:

```bash
$ dtlayertool pull arn:aws:lambda:us-east-1:725887861453:layer:Dynatrace_OneAgent_1_207_6_20201127-103507_nodejs:1 --extract DynatraceOneAgentExtension
querying layer version meta information for arn:aws:lambda:us-east-1:725887861453:layer:Dynatrace_OneAgent_1_207_6_20201127-103507_nodejs:1
downloading arn:aws:lambda:us-east-1:725887861453:layer:Dynatrace_OneAgent_1_207_6_20201127-103507_nodejs:1 content [1833343 bytes] to Dynatrace_OneAgent_1_207_6_20201127-103507_nodejs-v1.zip ...
Connected... 10% 20% 29% 39% 49% 59% 69% 79% 88% 98% Done.
downloaded layer content to Dynatrace_OneAgent_1_207_6_20201127-103507_nodejs-v1.zip
extracting layer contents to "DynatraceOneAgentExtension"
```

This will download and extract
`arn:aws:lambda:us-east-1:725887861453:layer:Dynatrace_OneAgent_1_207_6_20201127-103507_nodejs:1` contents
to local folder `DynatraceOneAgentExtension`.

The following `Dockerfile` commands copy the downloaded extension content into the container image and
assure, that the shell script file `/opt/dynatrace` is executable.

```Dockerfile
COPY DynatraceOneAgentExtension/ /opt/
RUN chmod +x /opt/dynatrace
```

## Sample `Dockerfile` with Dynatrace OneAgent monitoring enabled

This sample project creates a containerized Node.js Lambda function. The project folder has following
files and folders:

```text
containerized-lambda-sample
├── Dockerfile
├── DynatraceOneAgentExtension
└── index.js
```

The contents of the Dynatrace OneAgent extension is assumed to be downloaded and
extracted (as outlined above) to the folder `DynatraceOneAgentExtension`.

The handler function is a exported by the `index.js` file:

```javascript
exports.handler = async () => {
    return "hello world";
}
```

The `Dockerfile` with the modifications applied to deploy Dynatrace OneAgent to the containerized
function:

```Dockerfile
FROM public.ecr.aws/lambda/nodejs:12

COPY index.js ${LAMBDA_TASK_ROOT}

# --- Begin of enable Dynatrace OneAgent monitoring section

# environment variables copied from Dynatrace AWS Lambda deployment screen
# (prefix with ENV and remove spaces around equal signs)
ENV AWS_LAMBDA_EXEC_WRAPPER=/opt/dynatrace
ENV DT_TENANT=abcd1234
ENV DT_CLUSTER_ID=1234567890
ENV DT_CONNECTION_BASE_URL=https://abcd1234.live.dynatrace.com
ENV DT_CONNECTION_AUTH_TOKEN=dt0a01...

# copy Dynatrace OneAgent extension download and extracted to local disk into container image
COPY DynatraceOneAgentExtension/ /opt/

# make /opt/dynatrace shell script executable
RUN chmod +x /opt/dynatrace

# --- End of enable Dynatrace OneAgent monitoring section

CMD [ "index.handler" ]
```

## Limitations

OneAgent monitoring is only supported for container images
[created from an AWS base image for Lambda](https://docs.aws.amazon.com/lambda/latest/dg/images-create.html#images-create-1).

## Additional resources

* [AWS - Creating Lambda container images](https://docs.aws.amazon.com/lambda/latest/dg/images-create.html)
