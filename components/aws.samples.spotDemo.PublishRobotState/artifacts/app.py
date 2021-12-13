import json
import logging
import os
import sys
from threading import Timer

import awsiot.greengrasscoreipc
import bosdyn.client
import bosdyn.client.util
from awsiot.greengrasscoreipc.model import (
    PublishToIoTCoreRequest,
    GetSecretValueRequest,
)
from bosdyn.client.robot_state import RobotStateClient
from google.protobuf.json_format import MessageToDict

TIMEOUT = 10

# Setup logging to stdout
logger = logging.getLogger(__name__)
logging.basicConfig(stream=sys.stdout, level=logging.INFO)

ipc_client = awsiot.greengrasscoreipc.connect()

get_secret_value = ipc_client.new_get_secret_value()
get_secret_value.activate(request=GetSecretValueRequest(secret_id="spot_secrets"))
secret_response = get_secret_value.get_response().result()
json_secret_string = json.loads(secret_response.secret_value.secret_string)
get_secret_value.close()

# Create robot object with an image client.
sdk = bosdyn.client.create_standard_sdk("RobotStateClient")
robot = sdk.create_robot("192.168.50.3")
robot.authenticate(json_secret_string["spot_user"], json_secret_string["spot_password"])
robot_state_client = robot.ensure_client(RobotStateClient.default_service_name)


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
