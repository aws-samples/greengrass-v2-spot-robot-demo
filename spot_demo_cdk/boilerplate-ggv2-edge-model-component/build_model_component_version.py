import argparse
import json
import os
import string
import time
import uuid

import boto3

greengrass_client = boto3.client("greengrassv2")
s3_client = boto3.client("s3")
sts_client = boto3.client("sts")


class ParseKwargs(argparse.Action):
    def __call__(self, parser, namespace, values, option_string=None):
        setattr(namespace, self.dest, dict())
        for value in values:
            key, value = value.split("=")
            getattr(namespace, self.dest)[key] = value


parser = argparse.ArgumentParser()

parser.add_argument("-d", "--components-directory", type=str, required=True)
parser.add_argument("-m", "--model-uri", type=str, required=True)
parser.add_argument("-r", "--role-arn", type=str, required=True)
parser.add_argument("-g", "--use-gpu", type=str, required=True)
parser.add_argument("-b", "--bucket", type=str, required=True)
parser.add_argument("-c", "--components", nargs="+", required=True)
parser.add_argument("-v", "--variables", nargs="*", action=ParseKwargs)


def compile_and_package_model(next_version, role_arn, bucket_name, model_uri, use_gpu):
    client = boto3.client("sagemaker")

    compilation_job_name = str(uuid.uuid4())
    packaging_job_name = str(uuid.uuid4())

    output_config = {
        "S3OutputLocation": "s3://{}/compiled/".format(bucket_name),
        "TargetPlatform": {"Os": "LINUX", "Arch": "X86_64"},
    }

    model_name = "gluoncv-model"

    if int(use_gpu):
        model_name = "gluoncv-gpu-model"

        output_config = {
            "S3OutputLocation": "s3://{}/compiled/".format(bucket_name),
            "TargetPlatform": {
                "Os": "LINUX",
                "Arch": "X86_64",
                "Accelerator": "NVIDIA",
            },
            "CompilerOptions": json.dumps(
                {"cuda-ver": "10.2", "trt-ver": "7.2.1", "gpu-code": "sm_61"}
            ),
        }

    response = client.create_compilation_job(
        CompilationJobName=compilation_job_name,
        RoleArn=role_arn,
        InputConfig={
            "S3Uri": model_uri,
            "DataInputConfig": json.dumps({"data": [1, 3, 512, 512]}),
            "Framework": "MXNET",
        },
        OutputConfig=output_config,
        StoppingCondition={"MaxRuntimeInSeconds": 900, "MaxWaitTimeInSeconds": 900},
    )

    finished = False

    while not finished:

        response = client.describe_compilation_job(
            CompilationJobName=compilation_job_name
        )

        finished = response["CompilationJobStatus"] in [
            "COMPLETED",
            "FAILED",
            "STOPPED",
        ]

        if finished:
            break

        time.sleep(10)

    client.create_edge_packaging_job(
        EdgePackagingJobName=packaging_job_name,
        CompilationJobName=compilation_job_name,
        ModelName=model_name,
        ModelVersion=next_version,
        RoleArn=role_arn,
        OutputConfig={"S3OutputLocation": "s3://{}/packaged/".format(bucket_name)},
    )

    finished = False

    while not finished:

        response = client.describe_edge_packaging_job(
            EdgePackagingJobName=packaging_job_name
        )

        finished = response["EdgePackagingJobStatus"] in [
            "COMPLETED",
            "FAILED",
            "STOPPED",
        ]

        if finished:
            return "{}{}-{}.tar.gz".format(
                response["OutputConfig"]["S3OutputLocation"],
                response["ModelName"],
                response["ModelVersion"],
            )
            break

        time.sleep(10)


def generate_recipe(component_name, version, model_uri):
    component_variables = args.variables.copy()
    component_variables["component_version_number"] = version
    component_variables["component_name"] = component_name
    component_variables["packaged_model_uri"] = model_uri
    component_variables["packaged_model_filename"] = model_uri.split("/")[-1]

    # substitute variables, and generate new recipe file
    with open(
        "{}/recipe-template.yml".format(args.components_directory), "r"
    ) as input_recipe:
        src = string.Template(input_recipe.read())
        result = src.substitute(component_variables)
        with open(
            "{}/{}.yml".format(args.components_directory, component_name), "w"
        ) as output_recipe:
            output_recipe.write(result)


def create_component_version(component_name):
    with open(
        "{}/{}.yml".format(args.components_directory, component_name), "r"
    ) as recipe_file:
        recipe = recipe_file.read().encode()
        greengrass_client.create_component_version(inlineRecipe=recipe)


def get_next_component_version(component_name):
    versions = greengrass_client.list_component_versions(
        arn="arn:aws:greengrass:{}:{}:components:{}".format(
            os.environ["AWS_REGION"],
            sts_client.get_caller_identity()["Account"],
            component_name,
        )
    )["componentVersions"]

    print(versions)

    if len(versions) > 0:
        current_version = versions[0]["componentVersion"]
    else:
        return "1.0.0"

    current_versions = current_version.split(".")

    major = int(current_versions[0])
    minor = int(current_versions[1])
    micro = int(current_versions[2])

    return "{}.{}.{}".format(major, minor, micro + 1)


if __name__ == "__main__":

    args = parser.parse_args()

    print(args)

    for component in args.components:
        next_component_version = get_next_component_version(component)
        packaged_model_uri = compile_and_package_model(
            next_component_version,
            args.role_arn,
            args.bucket,
            args.model_uri,
            args.use_gpu,
        )
        generate_recipe(component, next_component_version, packaged_model_uri)
        create_component_version(component)
