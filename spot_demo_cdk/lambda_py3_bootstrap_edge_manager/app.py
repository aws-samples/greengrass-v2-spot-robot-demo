from __future__ import print_function

import json
import logging
import os
import time
import uuid

import boto3
from crhelper import CfnResource

logger = logging.getLogger(__name__)
# Initialise the helper, all inputs are optional, this example shows the defaults
helper = CfnResource(json_logging=False, log_level="DEBUG", boto_level="CRITICAL")

try:
    ## Init code goes here
    ROLE_ARN = os.environ["ROLE_ARN"]
    OUTPUT_BUCKET_NAME = os.environ["OUTPUT_BUCKET_NAME"]
    DEVICE_FLEET_NAME = os.environ["DEVICE_FLEET_NAME"]

    pass

except Exception as e:
    helper.init_failure(e)


def update_event_based_messaging():
    client = boto3.client("iot")

    response = client.update_event_configurations(
        eventConfigurations={
            "THING_GROUP_MEMBERSHIP": {"Enabled": True},
            "THING": {"Enabled": True},
        }
    )


def create_device_fleet():
    client = boto3.client("sagemaker")

    response = client.create_device_fleet(
        DeviceFleetName=DEVICE_FLEET_NAME,
        RoleArn=ROLE_ARN,
        OutputConfig={
            "S3OutputLocation": "s3://{}/collected_sample_data/".format(
                OUTPUT_BUCKET_NAME
            )
        },
    )


def update_device_fleet():
    client = boto3.client("sagemaker")

    response = client.update_device_fleet(
        DeviceFleetName=DEVICE_FLEET_NAME,
        RoleArn=ROLE_ARN,
        OutputConfig={
            "S3OutputLocation": "s3://{}/collected_sample_data/".format(
                OUTPUT_BUCKET_NAME
            )
        },
    )


def delete_device_fleet():
    client = boto3.client("sagemaker")

    response = client.delete_device_fleet(DeviceFleetName=DEVICE_FLEET_NAME)

    client = boto3.client("iot")

    response = client.delete_role_alias(
        roleAlias="SageMakerEdge-{}".format(DEVICE_FLEET_NAME)
    )


@helper.create
def create(event, context):
    logger.info("Got Create")
    # Optionally return an ID that will be used for the resource PhysicalResourceId,
    # if None is returned an ID will be generated. If a poll_create function is defined
    # return value is placed into the poll event as event['CrHelperData']['PhysicalResourceId']
    #
    # To add response data update the helper.Data dict
    # If poll is enabled data is placed into poll event as event['CrHelperData']

    update_event_based_messaging()
    create_device_fleet()

    return


@helper.update
def update(event, context):
    logger.info("Got Update")
    # If the update resulted in a new resource being created, return an id for the new resource.
    # CloudFormation will send a delete event with the old id when stack update completes

    update_event_based_messaging()
    update_device_fleet()


@helper.delete
def delete(event, context):
    logger.info("Got Delete")
    # Delete never returns anything. Should not fail if the underlying bootstrap_lambda are already deleted.
    # Desired state.

    delete_device_fleet()


def handler(event, context):
    logger.info("Received event: {}".format(json.dumps(event)))
    helper(event, context)
