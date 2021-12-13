import json
import string
import sys

import boto3

cf_client = boto3.client("cloudformation")
ggv2_client = boto3.client("greengrassv2")
sm_client = boto3.client("secretsmanager")
sts_client = boto3.client("sts")

spot_components = [
    "aws.samples.spotDemo.SageMakerComputePlugin",
    "aws.samples.spotDemo.PublishRobotState",
    "aws.samples.spotDemo.SageMakerComputeBridge",
    "aws.samples.spotDemo.GluonCVObjectDetectionModelCPU",
]

stack_name = "SpotDemoCdkStack"
bucket_output_variable = "SageMakerBucketName"
spot_secret_id = "spot_secrets"


# Retrieve latest Greengrass component versions
def retrieve_latest_greengrass_component_versions(component_names):

    latest_component_versions = []

    response = ggv2_client.list_components(scope="PRIVATE")

    for component in component_names:

        result = next(
            (c for c in response["components"] if c["componentName"] == component),
            None,
        )

        if result is not None:

            latest_component_versions.append(
                {
                    result["componentName"]: {
                        "componentVersion": result["latestVersion"]["componentVersion"],
                        "configurationUpdate": {"reset": [""]},
                    },
                }
            )

        else:
            sys.exit("Greengrass component {} NOT FOUND!".format(component))

    return latest_component_versions


# Retrieve SageMaker Edge Manager S3 bucket name
def retrieve_sagemaker_edge_manager_bucket_name(stack, output_variable):

    try:
        response = cf_client.describe_stacks(StackName=stack_name)
    except:
        sys.exit("CloudFormation stack {} NOT FOUND!".format(stack_name))

    result = result = next(
        (
            o
            for o in response["Stacks"][0]["Outputs"]
            if o["OutputKey"] == output_variable
        ),
        None,
    )

    if result is not None:

        output_value = result["OutputValue"]
        return output_value

    else:
        sys.exit("Output variable {} NOT FOUND!".format(output_variable))


# Retrieve ARN of Spot credentials stored in AWS Secrets Manager
def retrieve_secret_arn(secret_id):

    try:
        response = sm_client.describe_secret(SecretId=secret_id)
        return response["ARN"]
    except:
        sys.exit("Secrets Manager secret with id {} NOT FOUND!".format(secret_id))


def generate_deployment_template(input_file):
    with open(input_file) as f:
        deployment_template = json.load(f)

    for c in spot_component_versions:
        deployment_template["components"].update(c)

    deployment_template["components"]["aws.greengrass.SageMakerEdgeManager"][
        "configurationUpdate"
    ]["merge"] = json.dumps(
        {"DeviceFleetName": "spot-fleet", "BucketName": edge_manager_bucket_name}
    )

    deployment_template["components"]["aws.greengrass.SecretManager"][
        "configurationUpdate"
    ]["merge"] = json.dumps({"cloudSecrets": [{"arn": spot_credentials_secret_arn}]})

    deployment_template["targetArn"] = "arn:aws:iot:{}:{}:thinggroup/spot_group".format(
        boto3.session.Session().region_name,
        sts_client.get_caller_identity().get("Account"),
    )

    return deployment_template


spot_component_versions = retrieve_latest_greengrass_component_versions(
    component_names=spot_components
)
edge_manager_bucket_name = retrieve_sagemaker_edge_manager_bucket_name(
    stack=stack_name, output_variable=bucket_output_variable
)

spot_credentials_secret_arn = retrieve_secret_arn(secret_id=spot_secret_id)

template = generate_deployment_template("spot-deployment.json")

print("--- Latest Greengrass component versions: {}".format(spot_component_versions))
print("--- SageMaker Edge Manager S3 bucket name: {}".format(edge_manager_bucket_name))
print("--- Spot credentials secret ARN: {}".format(spot_credentials_secret_arn))
print(json.dumps(template, indent=4, sort_keys=True))

ggv2_client.create_deployment(
    targetArn=template["targetArn"],
    deploymentName=template["deploymentName"],
    components=template["components"],
    deploymentPolicies=template["deploymentPolicies"],
    iotJobConfiguration=template["iotJobConfiguration"],
)
