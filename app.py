#!/usr/bin/env python3
import os

import aws_cdk as cdk

from spot_demo_cdk.spot_demo_cdk_stack import SpotDemoCdkStack


app = cdk.App()
SpotDemoCdkStack(
    app,
    "SpotDemoCdkStack",
    env=cdk.Environment(
        account=app.node.try_get_context("account"),
        region=app.node.try_get_context("region"),
    ),
)

app.synth()
