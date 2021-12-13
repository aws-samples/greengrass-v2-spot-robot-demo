import os
from enum import Enum

import aws_cdk.aws_codepipeline as codepipeline
from aws_cdk import (
    core as cdk,
    aws_codebuild as codebuild,
    aws_codecommit as codecommit,
    aws_codepipeline_actions as pipeline_actions,
    aws_s3 as s3,
    aws_iam as iam,
    aws_lambda as lambda_,
    aws_cloudformation as cfn,
)
from aws_cdk.aws_s3_assets import Asset
import aws_solutions_constructs.aws_iot_lambda as ail


class SourceType(Enum):
    CUSTOM = (0,)
    BOILERPLATE_PYTHON_COMPONENT = (1,)
    BOILERPLATE_EDGE_ML_MODEL = 2


class BuildProjectType(Enum):
    CODEBUILD_GENERIC_PYTHON = (1,)
    CODEBUILD_EDGE_ML_MODEL = 2


class SpotDemoCdkStack(cdk.Stack):
    def __init__(self, scope: cdk.Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # The code that defines your stack goes here

        (
            sagemaker_edge_manager_role,
            bucket,
            model_uri,
        ) = self.add_sagemaker_edge_manager_resources()

        components_to_build = [
            {
                "name": "aws.samples.spotDemo.SageMakerComputeBridge",
                "source_type": SourceType.CUSTOM,
                "build_project_type": BuildProjectType.CODEBUILD_GENERIC_PYTHON,
            },
            {
                "name": "aws.samples.spotDemo.SageMakerComputePlugin",
                "source_type": SourceType.CUSTOM,
                "build_project_type": BuildProjectType.CODEBUILD_GENERIC_PYTHON,
            },
            {
                "name": "aws.samples.spotDemo.PublishRobotState",
                "source_type": SourceType.CUSTOM,
                "build_project_type": BuildProjectType.CODEBUILD_GENERIC_PYTHON,
            },
            # {
            #     "name": "aws.samples.spotDemo.GluonCVObjectDetectionModel",
            #     "source_type": SourceType.BOILERPLATE_EDGE_ML_MODEL,
            #     "build_project_type": BuildProjectType.CODEBUILD_EDGE_ML_MODEL,
            #     "edge_manager_role_arn": sagemaker_edge_manager_role.role_arn,
            #     "edge_manager_bucket_name": bucket.bucket_name,
            #     "model_uri": model_uri,
            #     "use_gpu": 1,
            # },
            {
                "name": "aws.samples.spotDemo.GluonCVObjectDetectionModelCPU",
                "source_type": SourceType.BOILERPLATE_EDGE_ML_MODEL,
                "build_project_type": BuildProjectType.CODEBUILD_EDGE_ML_MODEL,
                "edge_manager_role_arn": sagemaker_edge_manager_role.role_arn,
                "edge_manager_bucket_name": bucket.bucket_name,
                "model_uri": model_uri,
                "use_gpu": 0,
            },
        ]

        self.add_component_gitops(components_to_build)

    def generate_codebuild_project_generic(
        self, component, repo_object, components_bucket, script_asset
    ):
        return codebuild.Project(
            self,
            "build-{}".format(component),
            build_spec=codebuild.BuildSpec.from_source_filename("buildspec.yml"),
            source=codebuild.Source.code_commit(repository=repo_object),
            environment=codebuild.BuildEnvironment(
                build_image=codebuild.LinuxBuildImage.STANDARD_4_0
            ),
            environment_variables={
                "COMPONENT_NAME": codebuild.BuildEnvironmentVariable(value=component),
                "S3_PATH": codebuild.BuildEnvironmentVariable(
                    value="s3://{}/components".format(components_bucket.bucket_name)
                ),
                "BUILD_SCRIPT_URL": codebuild.BuildEnvironmentVariable(
                    value=script_asset.s3_object_url
                ),
            },
        )

    def generate_codebuild_project_edge_manager_model(
        self,
        component,
        repo_object,
        components_bucket,
        role_arn,
        bucket_name,
        model_uri,
        use_gpu,
    ):

        project = codebuild.Project(
            self,
            "build-{}".format(component),
            build_spec=codebuild.BuildSpec.from_source_filename("buildspec.yml"),
            source=codebuild.Source.code_commit(repository=repo_object),
            environment=codebuild.BuildEnvironment(
                build_image=codebuild.LinuxBuildImage.STANDARD_4_0
            ),
            environment_variables={
                "COMPONENT_NAME": codebuild.BuildEnvironmentVariable(value=component),
                "COMPONENT_DIRECTORY": codebuild.BuildEnvironmentVariable(value="."),
                "S3_PATH": codebuild.BuildEnvironmentVariable(
                    value="s3://{}/components".format(components_bucket.bucket_name)
                ),
                "ROLE_ARN": codebuild.BuildEnvironmentVariable(value=role_arn),
                "BUCKET_NAME": codebuild.BuildEnvironmentVariable(value=bucket_name),
                "MODEL_URI": codebuild.BuildEnvironmentVariable(value=model_uri),
                "USE_GPU": codebuild.BuildEnvironmentVariable(value=use_gpu),
            },
        )

        project.role.add_to_policy(
            iam.PolicyStatement(
                effect=iam.Effect.ALLOW,
                resources=["*"],
                actions=[
                    "s3:putObject",
                    "sagemaker:createCompilationJob",
                    "sagemaker:describeCompilationJob",
                    "sagemaker:createEdgePackagingJob",
                    "sagemaker:describeEdgePackagingJob",
                    "iam:PassRole",
                ],
            )
        )

        project.role.add_to_policy(
            iam.PolicyStatement(
                effect=iam.Effect.ALLOW,
                resources=["arn:aws:s3:::{}/*".format(bucket_name)],
                actions=[
                    "s3:*",
                ],
            )
        )

        return project

    def add_component_gitops(self, component_list):

        build_script_asset = Asset(
            self,
            "BuildComponentVersionScript",
            path=os.path.join(
                os.path.dirname(__file__), "../build_component_version.py"
            ),
        )

        boilerplate_ggv2_component_asset = Asset(
            self,
            "BoilerplateGGv2ComponentAsset",
            path=os.path.join(".", "boilerplate-ggv2-component"),
        )

        boilerplate_ggv2_edge_model_component_asset = Asset(
            self,
            "BoilerplateGGv2EdgeModelComponentAsset",
            path=os.path.join(".", "boilerplate-ggv2-edge-model-component"),
        )

        components_bucket = s3.Bucket(self, "GGv2ComponentsBucket")

        for component in component_list:

            if "source_type" in component:

                if component["source_type"] == SourceType.BOILERPLATE_PYTHON_COMPONENT:
                    asset = boilerplate_ggv2_component_asset

                elif component["source_type"] == SourceType.BOILERPLATE_EDGE_ML_MODEL:
                    asset = boilerplate_ggv2_edge_model_component_asset

                elif component["source_type"] == SourceType.CUSTOM:

                    asset = Asset(
                        self,
                        "{}-CustomComponentAsset".format(component["name"]),
                        path=os.path.join("../components", component["name"]),
                    )

            else:

                asset = boilerplate_ggv2_component_asset

            repo = codecommit.CfnRepository(
                self,
                component["name"],
                repository_name=component["name"],
                code=codecommit.CfnRepository.CodeProperty(
                    s3={"bucket": asset.s3_bucket_name, "key": asset.s3_object_key}
                ),
            )

            repo_object = codecommit.Repository.from_repository_arn(
                self,
                "repo_arn-{}".format(component["name"]),
                repository_arn=repo.attr_arn,
            )

            component_pipeline = codepipeline.Pipeline(
                self, "{}-pipeline".format(component["name"])
            )

            # add a stage
            source_stage = component_pipeline.add_stage(stage_name="Source")

            # add a source action to the stage
            source_stage.add_action(
                pipeline_actions.CodeCommitSourceAction(
                    action_name="Source",
                    output=codepipeline.Artifact(artifact_name="SourceArtifact"),
                    repository=repo_object,
                    branch="main",
                )
            )

            if "build_project_type" in component:

                if (
                    component["build_project_type"]
                    == BuildProjectType.CODEBUILD_GENERIC_PYTHON
                ):
                    ggv2_component_build_project = (
                        self.generate_codebuild_project_generic(
                            component["name"],
                            repo_object,
                            components_bucket,
                            build_script_asset,
                        )
                    )

                elif (
                    component["build_project_type"]
                    == BuildProjectType.CODEBUILD_EDGE_ML_MODEL
                ):
                    ggv2_component_build_project = (
                        self.generate_codebuild_project_edge_manager_model(
                            component["name"],
                            repo_object,
                            components_bucket,
                            component["edge_manager_role_arn"],
                            component["edge_manager_bucket_name"],
                            component["model_uri"],
                            component["use_gpu"],
                        )
                    )

            else:

                ggv2_component_build_project = self.generate_codebuild_project_generic(
                    component["name"], repo_object, components_bucket
                )

            ggv2_component_build_project.role.add_to_policy(
                iam.PolicyStatement(
                    effect=iam.Effect.ALLOW,
                    resources=["*"],
                    actions=[
                        "greengrass:createComponentVersion",
                        "greengrass:listComponentVersions",
                    ],
                )
            )

            ggv2_component_build_project.role.add_to_policy(
                iam.PolicyStatement(
                    effect=iam.Effect.ALLOW,
                    resources=[
                        "arn:aws:s3:::{}/{}".format(
                            build_script_asset.s3_bucket_name,
                            build_script_asset.s3_object_key,
                        )
                    ],
                    actions=[
                        "s3:GetObject",
                    ],
                )
            )

            ggv2_component_build_project.role.add_to_policy(
                iam.PolicyStatement(
                    effect=iam.Effect.ALLOW,
                    resources=[
                        "{}/components/{}/*".format(
                            components_bucket.bucket_arn, component["name"]
                        )
                    ],
                    actions=[
                        "s3:*",
                    ],
                )
            )

            # add a stage
            build_stage = component_pipeline.add_stage(stage_name="Build")

            # add a source action to the stage
            build_stage.add_action(
                pipeline_actions.CodeBuildAction(
                    action_name="Build",
                    input=codepipeline.Artifact(artifact_name="SourceArtifact"),
                    project=ggv2_component_build_project,
                )
            )

    def add_sagemaker_edge_manager_resources(self):

        device_fleet_name = "spot-fleet"
        thing_group_name = "spot_group"

        model_asset = Asset(
            self,
            "SSD_512_MobileNet_Pretrained",
            path=os.path.join(".", "pretrained_models/ssd_512_mobilenet1.0_voc.tar.gz"),
        )

        sagemaker_role = iam.Role(
            self,
            "SageMakerDeviceFleetRole",
            assumed_by=iam.CompositePrincipal(
                iam.ServicePrincipal("credentials.iot.amazonaws.com"),
                iam.ServicePrincipal("sagemaker.amazonaws.com"),
            ),
        )

        sagemaker_role.add_managed_policy(
            iam.ManagedPolicy.from_aws_managed_policy_name("AmazonS3FullAccess")
        )

        sagemaker_role.add_managed_policy(
            iam.ManagedPolicy.from_aws_managed_policy_name("AmazonSageMakerFullAccess")
        )

        sagemaker_role.add_managed_policy(
            iam.ManagedPolicy.from_managed_policy_arn(
                self,
                id="EdgeFleetPolicy",
                managed_policy_arn="arn:aws:iam::aws:policy/service-role/AmazonSageMakerEdgeDeviceFleetPolicy",
            )
        )

        sagemaker_role.add_managed_policy(
            iam.ManagedPolicy.from_aws_managed_policy_name("AWSIoTFullAccess")
        )

        bucket = s3.Bucket(self, "CompiledModelsBucket")

        bootstrap_lambda = lambda_.SingletonFunction(
            self,
            "BootstrapLambda",
            uuid="8d886c5d-ee5b-4329-a9d4-e8247f8574c8",
            code=lambda_.Code.asset(
                "_lambda_py3_output/lambda_py3_bootstrap_edge_manager"
            ),
            handler="app.handler",
            timeout=cdk.Duration.seconds(900),
            runtime=lambda_.Runtime.PYTHON_3_7,
            environment=dict(
                ROLE_ARN=sagemaker_role.role_arn,
                OUTPUT_BUCKET_NAME=bucket.bucket_name,
                DEVICE_FLEET_NAME=device_fleet_name,
            ),
        )

        bootstrap_lambda.add_to_role_policy(
            iam.PolicyStatement(
                effect=iam.Effect.ALLOW,
                resources=["*"],
                actions=[
                    "sagemaker:createDeviceFleet",
                    "sagemaker:deleteDeviceFleet",
                    "iot:deleteRoleAlias",
                    "iot:updateEventConfigurations",
                    "iam:PassRole",
                ],
            )
        )

        bootstrap_edge_manager_custom_resource = cfn.CustomResource(
            self,
            "BootstrapEdgeManagerCustomResource",
            provider=cfn.CustomResourceProvider.lambda_(bootstrap_lambda),
        )

        register_device_trigger = ail.IotToLambda(
            self,
            "RegisterDeviceTrigger",
            lambda_function_props={
                "code": lambda_.Code.asset(
                    "_lambda_py3_output/lambda_py3_register_edge_device"
                ),
                "runtime": lambda_.Runtime.PYTHON_3_7,
                "handler": "app.handler",
                "environment": {
                    "DEVICE_FLEET_NAME": device_fleet_name,
                    "THING_GROUP_NAME": thing_group_name,
                },
            },
            iot_topic_rule_props={
                "topic_rule_payload": {
                    "ruleDisabled": False,
                    "sql": "SELECT * FROM '$aws/events/thingGroupMembership/thingGroup/{}/thing/#'".format(
                        thing_group_name
                    ),
                    "actions": [],
                }
            },
        )

        register_device_trigger.lambda_function.add_to_role_policy(
            iam.PolicyStatement(
                effect=iam.Effect.ALLOW,
                resources=["*"],
                actions=["sagemaker:registerDevices", "sagemaker:deregisterDevices"],
            )
        )

        sagemaker_bucket_name = cdk.CfnOutput(
            self,
            "SageMakerBucketName",
            value=bucket.bucket_name,
            export_name="sagemaker-bucket-name",
        )

        return sagemaker_role, bucket, model_asset.s3_object_url
