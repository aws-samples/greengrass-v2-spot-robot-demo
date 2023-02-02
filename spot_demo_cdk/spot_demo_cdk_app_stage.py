# Copyright 2022 Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: LicenseRef-.amazon.com.-AmznSL-1.0
# Licensed under the Amazon Software License  http://aws.amazon.com/asl/

import aws_cdk as cdk
from constructs import Construct

from spot_demo_cdk.app_stacks.greengrass_components_stack import (
    GreengrassComponentsStack,
)
from spot_demo_cdk.app_stacks.monitoring_stack import MonitoringStack


class SpotDemoCdkAppStage(cdk.Stage):
    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        greengrassComponentsStack = GreengrassComponentsStack(
            self, "GreengrassComponentsStack"
        )

        monitoringStack = MonitoringStack(self, "MonitoringStack")

# SpotDemoCdkStack
