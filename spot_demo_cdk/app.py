#!/usr/bin/env python3
from aws_cdk import core as cdk
from spot_demo_cdk.spot_demo_cdk_stack import SpotDemoCdkStack

app = cdk.App()
SpotDemoCdkStack(app, "SpotDemoCdkStack")

app.synth()
