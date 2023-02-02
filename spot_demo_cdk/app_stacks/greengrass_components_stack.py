import os
from unicodedata import name

import aws_cdk as cdk
import aws_cdk.aws_codepipeline as codepipeline
import aws_cdk.aws_s3 as s3
from aws_cdk import aws_codebuild as codebuild
from aws_cdk import aws_codepipeline_actions as pipeline_actions
from aws_cdk import aws_iam as iam
from aws_cdk import aws_lambda as lambda_
import aws_cdk.aws_stepfunctions_tasks as tasks
from aws_cdk import aws_s3 as s3
import aws_cdk.aws_stepfunctions as stepfunctions
from aws_cdk.aws_codecommit import Repository
from constructs import Construct


class GreengrassComponentsStack(cdk.Stack):
    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        repo = Repository.from_repository_arn(
            self,
            "CodeCommitRepository",
            repository_arn=self.node.try_get_context("codecommit_repository_arn"),
        )

        self.add_component_gitops(repo)

    def add_component_gitops(self, repository):

        validate_source_artifact_lambda = lambda_.Function(
            self,
            "ValidateSourceArtifactLambda",
            code=lambda_.Code.from_asset(os.path.join(os.path.dirname(__file__), "lambda_functions/python/validate_component_change")),
            handler="index.handler",
            runtime=lambda_.Runtime.PYTHON_3_7,
        )

        validate_source_artifact_lambda.add_to_role_policy(
            iam.PolicyStatement(
                effect=iam.Effect.ALLOW,
                resources=["*"],
                actions=[
                    "codepipeline:PutJobSuccessResult",
                    "codepipeline:PutJobFailureResult",
                    "codepipeline:StopPipelineExecution",
                    "codecommit:GetTree",
                    "codecommit:BatchGetCommits",
                    "codecommit:GetCommit",
                    "codecommit:GetCommitHistory",
                    "codecommit:GetDifferences",
                    "codecommit:GetReferences",
                    "codecommit:GetObjectIdentifier",
                    "codecommit:BatchGetCommits",
                ],
            )
        )

        components_bucket = s3.Bucket(
            self, "GGv2ComponentsBucket", server_access_logs_prefix="access-logs"
        )

        component_list = []
        rootdir = "./components/"
        for path, dirs, files in os.walk(rootdir):

            for d in dirs:
                component_list.append(d)

            del dirs[:]  # go only one level deep

        for component in component_list:

            component_pipeline = codepipeline.Pipeline(
                self,
                "{}-{}-component".format(component, self.artifact_id[-8:]),
                pipeline_name="{}-{}-component".format(
                    component, self.artifact_id[-8:]
                ),
            )

            # add a stage
            source_stage = component_pipeline.add_stage(stage_name="Source")

            source_action = pipeline_actions.CodeCommitSourceAction(
                action_name="Source",
                output=codepipeline.Artifact(artifact_name="SourceArtifact"),
                repository=repository,
                branch="main",
            )

            # add a source action to the stage
            source_stage.add_action(source_action)

            ggv2_component_build_project = self.generate_codebuild_project_generic(
                component,
                repository,
                components_bucket,
            )

            ggv2_component_build_project.role.add_to_policy(
                iam.PolicyStatement(
                    effect=iam.Effect.ALLOW,
                    resources=["*"],
                    actions=[
                        "greengrass:CreateComponentVersion",
                        "greengrass:ListComponentVersions",
                    ],
                )
            )

            ggv2_component_build_project.role.add_to_policy(
                iam.PolicyStatement(
                    effect=iam.Effect.ALLOW,
                    resources=[f"arn:aws:s3:::{components_bucket.bucket_name}"],
                    actions=["s3:CreateBucket", "s3:GetBucketLocation"],
                )
            )

            ggv2_component_build_project.role.add_to_policy(
                iam.PolicyStatement(
                    effect=iam.Effect.ALLOW,
                    resources=[f"arn:aws:s3:::{components_bucket.bucket_name}/*"],
                    actions=["s3:PutObject", "s3:GetObject"],
                )
            )

            # add a stage
            build_stage = component_pipeline.add_stage(stage_name="Build")

            # add a validation action to the build stage
            build_stage.add_action(
                pipeline_actions.LambdaInvokeAction(
                    lambda_=validate_source_artifact_lambda,
                    action_name="Validate",
                    user_parameters={
                        "pipeline_name": "{}-{}-component".format(
                            component, self.artifact_id[-8:]
                        ),
                        "pipeline_execution_id": codepipeline.GlobalVariables.EXECUTION_ID,
                        "component_name": component,
                        "commit_id": source_action.variables.commit_id,
                        "repository_name": source_action.variables.repository_name,
                        "branch_name": source_action.variables.branch_name,
                    },
                    inputs=[codepipeline.Artifact(artifact_name="SourceArtifact")],
                    run_order=1,
                )
            )

            # add a build action to the build stage
            build_stage.add_action(
                pipeline_actions.CodeBuildAction(
                    action_name="Build",
                    input=codepipeline.Artifact(artifact_name="SourceArtifact"),
                    project=ggv2_component_build_project,
                    run_order=2,
                )
            )

    def generate_codebuild_project_generic(
        self,
        component,
        repo_object,
        components_bucket,
    ):
        return codebuild.Project(
            self,
            "build-{}".format(component),
            project_name="{}-{}-build".format(
                component.replace(".", ""), self.artifact_id[-8:]
            ),
            build_spec=codebuild.BuildSpec.from_source_filename(
                f"components/{component}/buildspec.yml"
            ),
            source=codebuild.Source.code_commit(repository=repo_object),
            environment=codebuild.BuildEnvironment(
                build_image=codebuild.LinuxBuildImage.STANDARD_4_0
            ),
            environment_variables={
                "COMPONENT_NAME": codebuild.BuildEnvironmentVariable(value=component),
                "S3_BUCKET_NAME": codebuild.BuildEnvironmentVariable(
                    value=components_bucket.bucket_name
                ),
            },
        )
