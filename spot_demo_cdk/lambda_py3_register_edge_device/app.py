import boto3
import json
import logging
import os

logger = logging.getLogger()
logger.setLevel(logging.INFO)

client = boto3.client('sagemaker')
DEVICE_FLEET_NAME = os.environ['DEVICE_FLEET_NAME']
THING_GROUP_NAME = os.environ['THING_GROUP_NAME']

def handler(event, context):

    logger.info('Received event: {}'.format(json.dumps(event)))
    logger.info('DEVICE_FLEET_NAME: {}'.format(DEVICE_FLEET_NAME))
    logger.info('THING_GROUP_NAME: {}'.format(THING_GROUP_NAME))

    if event['eventType'] == 'THING_GROUP_MEMBERSHIP_EVENT':

        iot_thing_name = event['thingArn'].split('/')[1]

        if event['operation'] == 'ADDED':

            response = register_device(iot_thing_name)
            logger.info('Register device response: {}'.format(response))

        elif event['operation'] == 'REMOVED':

            response = deregister_device(iot_thing_name)
            logger.info('Deregister device response: {}'.format(response))


def register_device(thing_name):

    return client.register_devices(
        DeviceFleetName=DEVICE_FLEET_NAME,
        Devices=[
            {
                'DeviceName': thing_name,
                'IotThingName': thing_name
            }
        ]
    )


def deregister_device(thing_name):

    return client.deregister_devices(
        DeviceFleetName=DEVICE_FLEET_NAME,
        DeviceNames=[
            thing_name,
        ]
    )