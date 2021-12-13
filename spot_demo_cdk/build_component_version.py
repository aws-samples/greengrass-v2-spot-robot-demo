import argparse
import os
import shutil
import string

import boto3

greengrass_client = boto3.client("greengrassv2")
s3_client = boto3.client("s3")
sts_client = boto3.client("sts")

parser = argparse.ArgumentParser()

parser.add_argument("-c", "--component", type=str, required=True)
parser.add_argument("-p", "--path", type=str, required=True)


def generate_recipe(component_name, version, s3_path):

    component_variables = {
        "component_version_number": version,
        "component_name": component_name,
        "artifacts_zip_file_name": component_name,
        "s3_path": s3_path,
    }

    # substitute variables, and generate new recipe file
    with open("./recipe-template.yml", "r") as input_recipe:
        src = string.Template(input_recipe.read())
        result = src.substitute(component_variables)
        with open("./{}.yml".format(component_name), "w") as output_recipe:
            output_recipe.write(result)


def create_component_version(component_name):
    with open("./{}.yml".format(component_name), "r") as recipe_file:
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


def archive_upload_artifacts(component_name, next_version):
    shutil.make_archive(
        base_name="{}".format(component_name),
        format="zip",
        root_dir=".",
        base_dir="artifacts",
    )

    bucket_name = args.path.split("s3://")[1].split("/")[0]
    key_prefix = args.path.split("s3://")[1].split("/")[1]

    s3_client.upload_file(
        "{}.zip".format(component_name),
        bucket_name,
        "{}/{}/{}/{}.zip".format(
            key_prefix, component_name, next_version, component_name
        ),
    )


if __name__ == "__main__":

    args = parser.parse_args()

    print(args)

    next_component_version = get_next_component_version(args.component)
    generate_recipe(args.component, next_component_version, args.path)
    archive_upload_artifacts(args.component, next_component_version)
    create_component_version(args.component)
