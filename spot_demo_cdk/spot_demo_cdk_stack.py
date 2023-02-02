# Copyright 2022 Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: LicenseRef-.amazon.com.-AmznSL-1.0
# Licensed under the Amazon Software License  http://aws.amazon.com/asl/

import aws_cdk as cdk
from aws_cdk import Stack
from aws_cdk.aws_codecommit import Repository
from aws_cdk.pipelines import CodePipeline, CodePipelineSource, ShellStep
from constructs import Construct

from spot_demo_cdk.spot_demo_cdk_app_stage import (
    SpotDemoCdkAppStage,
)


class SpotDemoCdkStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        repository = Repository.from_repository_arn(
            self,
            "SpotCdkDemoRepository",
            repository_arn=self.node.try_get_context("codecommit_repository_arn"),
        )

        pipeline = CodePipeline(
            self,
            "Pipeline",
            pipeline_name="SpotCdkDemoPipeline",
            docker_enabled_for_synth=True,
            synth=ShellStep(
                "Synth",
                input=CodePipelineSource.code_commit(
                    branch="main", repository=repository
                ),
                commands=[
                    "npm install -g aws-cdk",
                    "python -m pip install -r requirements.txt",
                    "cdk synth",
                ],
            ),
        )

        pipeline.add_stage(
            SpotDemoCdkAppStage(
                self,
                "SpotCdkDemoAppStage",
                env=cdk.Environment(
                    account=self.node.try_get_context("account"),
                    region=self.node.try_get_context("region"),
                ),
            )
        )

# SpotDemoCdkStack
