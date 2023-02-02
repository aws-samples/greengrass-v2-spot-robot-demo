# Copyright 2021 Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: LicenseRef-.amazon.com.-AmznSL-1.0
# Licensed under the Amazon Software License  http://aws.amazon.com/asl/

import json
import logging
import os
import sys
from threading import Timer

import awsiot.greengrasscoreipc
import bosdyn.client
import bosdyn.client.util
import backoff
from awsiot.greengrasscoreipc.model import (
    PublishToIoTCoreRequest,
)
from bosdyn.client.robot_state import RobotStateClient
from google.protobuf.json_format import MessageToDict

TIMEOUT = 10

# Setup logging to stdout
logger = logging.getLogger(__name__)
logging.basicConfig(stream=sys.stdout, level=logging.INFO)


def get_guid_and_secret():
    # Returns the GUID and secret on the Spot CORE
    kGuidAndSecretPath = "/payload_credentials/payload_guid_and_secret"
    try:
        payload_file = open(kGuidAndSecretPath)
        guid = payload_file.readline().strip("\n")
        secret = payload_file.readline().strip("\n")
    except IOError as io_error:
        print(
            "Unable to get the GUID/Secret for Spot Core: IOError when reading the file at: "
            + kGuidAndSecretPath
        )
        raise io_error
    return guid, secret


@backoff.on_exception(backoff.expo, Exception, max_time=900)
def create_robot_safe():
    # Create robot object with an image client.
    sdk = bosdyn.client.create_standard_sdk("RobotStateClient")
    robot = sdk.create_robot("192.168.50.3")
    guid, secret = get_guid_and_secret()
    robot.authenticate_from_payload_credentials(guid, secret)
    robot_state_client = robot.ensure_client(RobotStateClient.default_service_name)
    return robot_state_client


robot_state_client = create_robot_safe()
ipc_client = awsiot.greengrasscoreipc.connect()


def get_robot_state_loop():
    try:

        ## STATE

        # Make a robot state request
        request_fn = getattr(robot_state_client, "get_robot_state")
        response = request_fn()

        json_output = MessageToDict(response)

        # include selected payload attributes
        payload = {
            "kinematicState": json_output["kinematicState"],
            "powerState": json_output["powerState"],
            "batteryStates": json_output["batteryStates"],
            "commsStates": json_output["commsStates"],
        }

        ipc_client.new_publish_to_iot_core().activate(
            request=PublishToIoTCoreRequest(
                topic_name="robots/{}/state".format(os.environ["AWS_IOT_THING_NAME"]),
                qos="0",
                payload=json.dumps(payload).encode(),
            )
        )

        ## METRICS

        # Make a robot state request
        request_fn = getattr(robot_state_client, "get_robot_metrics")
        response = request_fn()

        json_output = MessageToDict(response)

        ipc_client.new_publish_to_iot_core().activate(
            request=PublishToIoTCoreRequest(
                topic_name="robots/{}/metrics".format(os.environ["AWS_IOT_THING_NAME"]),
                qos="0",
                payload=json.dumps(json_output).encode(),
            )
        )

    except Exception as e:
        logger.error("Failed to publish message: " + repr(e))

    # Asynchronously schedule this function to be run again in 5 seconds
    Timer(5, get_robot_state_loop).start()


# Start executing the function above
get_robot_state_loop()
