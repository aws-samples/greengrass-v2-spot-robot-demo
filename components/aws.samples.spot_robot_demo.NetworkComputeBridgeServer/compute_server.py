# Copyright (c) 2021 Boston Dynamics, Inc.  All rights reserved.
#
# Downloading, reproducing, distributing or otherwise using the SDK Software
# is subject to the terms and conditions of the Boston Dynamics Software
# Development Kit License (20191101-BDSDK-SL).
#
# This sample code from Boston Dynamics has been modified for demonstration purposes.

"""
Tutorial to show how to use the Boston Dynamics Network Compute API

This example server handles requests to run an AutoGluon model with image
services registered on Spot.
"""
import multiprocessing
import argparse
import io
from multiprocessing import Process, Queue
import os
import sys
import time
import logging
import numpy
import json
import requests
import backoff

import cv2
import numpy as np
from PIL import Image
from scipy import ndimage

from bosdyn.api.image_pb2 import ImageSource
from bosdyn.api import network_compute_bridge_service_pb2_grpc
from bosdyn.api import network_compute_bridge_service_pb2
from bosdyn.api import network_compute_bridge_pb2
from bosdyn.api import world_object_pb2
from bosdyn.api import header_pb2
from bosdyn.api import image_pb2
import bosdyn.client
import bosdyn.client.util
from bosdyn.client.image import ImageClient
import grpc
from concurrent import futures
import math

# import the necessary packages for ML
import numpy as np
import argparse
import cv2
from timeit import default_timer as timer
import os

import queue
import threading
from google.protobuf import any_pb2
from google.protobuf import wrappers_pb2
import socket

from edge_manager_client import EdgeManagerClient

IMAGE_WIDTH = 1920  # 640
IMAGE_HEIGHT = 1080  # 480
MODEL_INPUT_SIZE = 512
MODEL_NAME = "valve-classification"
MODEL_CLASSES = ["closed", "open"]

logger = logging.getLogger(__name__)

# This is a multiprocessing.Queue for communication between the main process and the
# Tensorflow processes.
REQUEST_QUEUE = Queue()

# This is a multiprocessing.Queue for communication between the Tensorflow processes and
# the display process.
RESPONSE_QUEUE = Queue()


def start_processes(options):
    """Starts Tensorflow processes in parallel.

    It does not keep track of the processes once they are started because they run indefinitely
    and are never joined back to the main process.
    """

    process = Process(target=process_images, args=([options]))
    process.start()


def process_images(options):
    """Starts Edge Manager client and detects objects in the incoming images."""

    # TODO: load + initialize model!
    edge_manager_client = EdgeManagerClient()

    while True:
        request = REQUEST_QUEUE.get()

        if isinstance(request, network_compute_bridge_pb2.ListAvailableModelsRequest):
            out_proto = network_compute_bridge_pb2.ListAvailableModelsResponse()
            # TODO: list models!
            response = edge_manager_client.list_models()
            for f in response.models:
                out_proto.available_models.append(f.name)
            RESPONSE_QUEUE.put(out_proto)
            continue
        else:
            out_proto = network_compute_bridge_pb2.NetworkComputeResponse()

        # TODO: list models!
        response = edge_manager_client.list_models()

        models = []
        for m in response.models:
            models.append(m.name)

        # Find the model
        if request.input_data.model_name not in models:
            err_str = (
                'Cannot find model "'
                + request.input_data.model_name
                + '" in loaded models.'
            )
            print(err_str)

            # Set the error in the header.
            out_proto.header.error.code = header_pb2.CommonError.CODE_INVALID_REQUEST
            out_proto.header.error.message = err_str
            RESPONSE_QUEUE.put(out_proto)
            continue

        if request.input_data.image.format == image_pb2.Image.FORMAT_RAW:
            logger.info("RAW!!!!!!")
            pil_image = Image.open(io.BytesIO(request.input_data.image.data))
            pil_image = ndimage.rotate(pil_image, 0)
            if (
                request.input_data.image.pixel_format
                == image_pb2.Image.PIXEL_FORMAT_GREYSCALE_U8
            ):
                image = cv2.cvtColor(
                    pil_image, cv2.COLOR_GRAY2RGB
                )  # Converted to RGB for Tensorflow
            elif (
                request.input_data.image.pixel_format
                == image_pb2.Image.PIXEL_FORMAT_RGB_U8
            ):
                # Already in the correct format
                # image = pil_image
                image = cv2.cvtColor(pil_image, cv2.COLOR_RGB2RGB)
            else:
                err_str = (
                    "Error: image input in unsupported pixel format: ",
                    request.input_data.image.pixel_format,
                )
                print(err_str)

                # Set the error in the header.
                out_proto.header.error.code = (
                    header_pb2.CommonError.CODE_INVALID_REQUEST
                )
                out_proto.header.error.message = err_str
                RESPONSE_QUEUE.put(out_proto)
                continue
        elif request.input_data.image.format == image_pb2.Image.FORMAT_JPEG:
            dtype = np.uint8
            jpg = np.frombuffer(request.input_data.image.data, dtype=dtype)
            image = cv2.imdecode(jpg, -1)

            if len(image.shape) < 3:
                # Single channel image, convert to RGB.
                image = cv2.cvtColor(image, cv2.COLOR_GRAY2RGB)

        logger.info("SHAPE: {}".format(image.shape))

        boxes, scores, classes = edge_manager_client.get_prediction(
            request.input_data.model_name, image
        )

        logger.info("BOXES")
        logger.info(boxes)

        logger.info("SCORES")
        logger.info(scores)

        logger.info("CLASSES")
        logger.info(classes)

        num_objects = 0

        for i in range(len(boxes)):

            try:
                logger.info("attempting to use classifier")
                cv2.imwrite("/images/local.jpg", image)
                r = requests.get("http://127.0.0.1:5000/")
                valve_class = r.json()["result"]
            except Exception as ex:
                logger.info(ex)
                logger.info("using 0 instead")
                valve_class = 0

            label = MODEL_CLASSES[valve_class]
            print("Label: {}".format(label))
            box = boxes[i]
            score = scores[i]

            if score < 0.17:
                # scores are sorted so we can break
                break

            logger.info("min_confidence: {}".format(request.input_data.min_confidence))
            logger.info("box: {}".format(box))
            logger.info("score: {}".format(score))
            logger.info("width: {}".format(IMAGE_WIDTH))
            logger.info("height: {}".format(IMAGE_HEIGHT))
            logger.info("input size: {}".format(MODEL_INPUT_SIZE))

            try:

                x1 = int(box[0] * IMAGE_WIDTH / MODEL_INPUT_SIZE)
                y1 = int(box[1] * IMAGE_HEIGHT / MODEL_INPUT_SIZE)
                x2 = int(box[2] * IMAGE_WIDTH / MODEL_INPUT_SIZE)
                y2 = int(box[3] * IMAGE_HEIGHT / MODEL_INPUT_SIZE)

                box = [x1, y1, x2, y2]

                # draw_box(draw, b, color=color)
                print(
                    'Found object with label: "' + label + '" and score: ' + str(score)
                )

                num_objects += 1

                point1 = np.array([box[0], box[1]])
                point2 = np.array([box[2], box[1]])
                point3 = np.array([box[2], box[3]])
                point4 = np.array([box[0], box[3]])

                # Add data to the output proto.
                out_obj = out_proto.object_in_image.add()
                out_obj.name = "obj" + str(num_objects) + "_label_" + label

                vertex1 = out_obj.image_properties.coordinates.vertexes.add()
                vertex1.x = point1[0]
                vertex1.y = point1[1]

                vertex2 = out_obj.image_properties.coordinates.vertexes.add()
                vertex2.x = point2[0]
                vertex2.y = point2[1]

                vertex3 = out_obj.image_properties.coordinates.vertexes.add()
                vertex3.x = point3[0]
                vertex3.y = point3[1]

                vertex4 = out_obj.image_properties.coordinates.vertexes.add()
                vertex4.x = point4[0]
                vertex4.y = point4[1]

                # Pack the confidence value.
                confidence = wrappers_pb2.FloatValue(value=score)
                out_obj.additional_properties.Pack(confidence)

                # Pack the status value.
                status = wrappers_pb2.StringValue(value=label)
                out_obj.additional_properties.Pack(status)

                if not options.no_debug:

                    polygon = np.array([point1, point2, point3, point4], np.int32)
                    polygon = polygon.reshape((-1, 1, 2))
                    cv2.polylines(image, [polygon], True, (0, 255, 0), 2)

                    caption = "{}: {:.3f}".format(label, score)
                    left_x = min(point1[0], min(point2[0], min(point3[0], point4[0])))
                    top_y = min(point1[1], min(point2[1], min(point3[1], point4[1])))
                    cv2.putText(
                        image,
                        caption,
                        (int(left_x), int(top_y)),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        0.5,
                        (0, 255, 0),
                        2,
                    )

            except:
                logger.info("could not process object")

            # only use one detection
            break

        if not options.no_debug:
            debug_image_filename = "ncb_server_output.jpg"
            cv2.imwrite(debug_image_filename, image)
            print('Wrote debug image output to: "' + debug_image_filename + '"')

        RESPONSE_QUEUE.put(out_proto)


class NetworkComputeBridgeWorkerServicer(
    network_compute_bridge_service_pb2_grpc.NetworkComputeBridgeWorkerServicer
):
    def __init__(self, thread_input_queue, thread_output_queue):
        super(NetworkComputeBridgeWorkerServicer, self).__init__()

        self.thread_input_queue = thread_input_queue
        self.thread_output_queue = thread_output_queue

    def NetworkCompute(self, request, context):
        self.thread_input_queue.put(request)
        out_proto = self.thread_output_queue.get()
        return out_proto

    def ListAvailableModels(self, request, context):
        self.thread_input_queue.put(request)
        out_proto = self.thread_output_queue.get()
        return out_proto


def register_with_robot(options):
    """Registers this worker with the robot's Directory."""

    ip = bosdyn.client.common.get_self_ip(options.hostname)
    print("Detected IP address as: " + ip)
    kServiceName = "ncb-server"
    kServiceAuthority = "auth.spot.robot"

    sdk = bosdyn.client.create_standard_sdk("ncb_server")

    robot = sdk.create_robot(options.hostname)
    guid, secret = get_guid_and_secret()
    robot.authenticate_from_payload_credentials(guid, secret)

    directory_client = robot.ensure_client(
        bosdyn.client.directory.DirectoryClient.default_service_name
    )
    directory_registration_client = robot.ensure_client(
        bosdyn.client.directory_registration.DirectoryRegistrationClient.default_service_name
    )

    # Check to see if a service is already registered with our name
    services = directory_client.list()
    for s in services:
        if s.name == kServiceName:
            print(
                'WARNING: existing service with name, "'
                + kServiceName
                + '", removing it.'
            )
            directory_registration_client.unregister(kServiceName)
            break

    # Register service
    print(
        "Attempting to register "
        + ip
        + ":"
        + options.port
        + " onto "
        + options.hostname
        + " directory..."
    )
    directory_registration_client.register(
        kServiceName,
        "bosdyn.api.NetworkComputeBridgeWorker",
        kServiceAuthority,
        ip,
        int(options.port),
    )


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
def main(argv):
    """Command line interface.

    Args:
        argv: List of command-line arguments passed to the program.
    """

    default_port = "50097"
    model_extension = ".params"

    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-p",
        "--port",
        help="Server's port number, default: " + default_port,
        default=default_port,
    )
    parser.add_argument(
        "-n", "--no-debug", help="Disable writing debug images.", action="store_true"
    )
    parser.add_argument(
        "-r",
        "--no-registration",
        help="Don't register with the robot's directory. This is useful for cloud applications where we can't reach into every robot directly. Instead use another program to register this server.",
        action="store_true",
    )

    parser.add_argument(
        "--username", help="User name of account to get credentials for."
    )
    parser.add_argument("--password", help="Password to get credentials for.")
    parser.add_argument(
        "hostname",
        nargs="?",
        help="Hostname or address of robot," ' e.g. "beta25-p" or "192.168.80.3"',
    )

    options = parser.parse_args(argv)

    # Either we need a hostname to talk to the robot or the --no-registration argument.
    if not options.no_registration and (
        options.hostname is None or len(options.hostname) < 1
    ):
        print(
            "Error: must either provide a robot hostname or the --no-registration argument."
        )
        sys.exit(1)

    if options.no_registration and (
        options.hostname is not None and len(options.hostname) > 0
    ):
        print(
            "Error: cannot provide both a robot hostname and the --no-registration argument."
        )
        sys.exit(1)

    if not os.path.isdir(options.model_dir):
        print(
            "Error: model directory ("
            + options.model_dir
            + ") not found or is not a directory."
        )
        sys.exit(1)

    if not options.no_registration:
        register_with_robot(options)

    # Start compute server processes
    start_processes(options, model_extension)

    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    network_compute_bridge_service_pb2_grpc.add_NetworkComputeBridgeWorkerServicer_to_server(
        NetworkComputeBridgeWorkerServicer(REQUEST_QUEUE, RESPONSE_QUEUE), server
    )
    server.add_insecure_port("[::]:" + options.port)
    server.start()

    print("Running...")
    while True:
        print(".", end="")
        sys.stdout.flush()
        time.sleep(2)

    return True


if __name__ == "__main__":

    logging.basicConfig()

    if not main(sys.argv[1:]):
        sys.exit(1)
