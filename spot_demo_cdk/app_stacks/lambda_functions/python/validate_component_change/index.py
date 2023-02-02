from __future__ import print_function

import json
import os
import traceback
import logging

import boto3
from boto3.session import Session
from botocore.exceptions import ClientError

code_commit = boto3.client("codecommit")
code_pipeline = boto3.client("codepipeline")

logger = logging.getLogger(__name__)


def put_job_success(job, message):
    """Notify CodePipeline of a successful job

    Args:
        job: The CodePipeline job ID
        message: A message to be logged relating to the job status

    Raises:
        Exception: Any exception thrown by .put_job_success_result()

    """
    print("Putting job success")
    print(message)
    code_pipeline.put_job_success_result(jobId=job)


def put_job_failure(job, message):
    """Notify CodePipeline of a failed job

    Args:
        job: The CodePipeline job ID
        message: A message to be logged relating to the job status

    Raises:
        Exception: Any exception thrown by .put_job_failure_result()

    """
    print("Putting job failure")
    print(message)
    code_pipeline.put_job_failure_result(
        jobId=job, failureDetails={"message": message, "type": "JobFailed"}
    )


def stop_pipeline_execution(pipeline_name, pipeline_execution_id):
    print("Stopping pipeline execution")

    response = code_pipeline.stop_pipeline_execution(
        pipelineName=pipeline_name,
        pipelineExecutionId=pipeline_execution_id,
        abandon=True,
        reason="NoChanges",
    )


def get_last_commit_log(repository, commitId):
    response = code_commit.get_commit(repositoryName=repository, commitId=commitId)
    return response["commit"]


def get_file_differences(repository_name, lastCommitID, previousCommitID):
    response = None

    if previousCommitID != None:
        response = code_commit.get_differences(
            repositoryName=repository_name,
            beforeCommitSpecifier=previousCommitID,
            afterCommitSpecifier=lastCommitID,
        )
    else:
        # The case of getting initial commit (Without beforeCommitSpecifier)
        response = code_commit.get_differences(
            repositoryName=repository_name, afterCommitSpecifier=lastCommitID
        )

    differences = []

    if response == None:
        return differences

    while "nextToken" in response:
        response = code_commit.get_differences(
            repositoryName=repository_name,
            beforeCommitSpecifier=previousCommitID,
            afterCommitSpecifier=lastCommitID,
            nextToken=response["nextToken"],
        )
        differences += response.get("differences", [])
    else:
        differences += response["differences"]

    return differences


def get_last_commit_id(repository, branch="main"):
    response = code_commit.get_branch(repositoryName=repository, branchName=branch)
    commitId = response["branch"]["commitId"]
    return commitId


def get_user_params(job_data):
    """Decodes the JSON user parameters and validates the required properties.

    Args:
        job_data: The job data structure containing the UserParameters string which should be a valid JSON structure

    Returns:
        The JSON parameters decoded as a dictionary.

    Raises:
        Exception: The JSON can't be decoded or a property is missing.

    """
    try:
        # Get the user parameters which contain the stack, artifact and file settings
        user_parameters = job_data["actionConfiguration"]["configuration"][
            "UserParameters"
        ]
        decoded_parameters = json.loads(user_parameters)

    except Exception as e:
        # We're expecting the user parameters to be encoded as JSON
        # so we can pass multiple values. If the JSON can't be decoded
        # then fail the job with a helpful message.
        raise Exception("UserParameters could not be decoded as JSON")

    return decoded_parameters


def handler(event, context):

    try:
        # Initialize needed variables
        file_extension_allowed = [".yml", ".yaml", ".gitignore", ".txt", ".py"]
        filenames_allowed = [
            "app.py",
            "requirements.txt",
            "buildspec.yml",
            "recipe-template.yml",
        ]

        # Extract the Job ID
        job_id = event["CodePipeline.job"]["id"]

        # Extract the Job Data
        job_data = event["CodePipeline.job"]["data"]

        # Extract the params
        params = get_user_params(job_data)

        component_name = params["component_name"]
        commit_id = params["commit_id"]
        repository_name = params["repository_name"]
        branch_name = params["branch_name"]
        pipeline_name = params["pipeline_name"]
        pipeline_execution_id = params["pipeline_execution_id"]

        # Get commit ID for fetching the commit log
        if (commit_id == None) or (
            commit_id == "0000000000000000000000000000000000000000"
        ):
            commit_id = get_last_commit_id(repository_name, branch_name)

        lastCommit = get_last_commit_log(repository_name, commit_id)

        previous_commit_id = None
        if len(lastCommit["parents"]) > 0:
            previous_commit_id = lastCommit["parents"][0]

        print(
            "lastCommitID: {0} previousCommitID: {1}".format(
                commit_id, previous_commit_id
            )
        )

        differences = get_file_differences(
            repository_name, commit_id, previous_commit_id
        )

        print(differences)

        # Check whether specific file or specific extension file is added/modified
        # and set flag for build triggering
        change_detected = False
        for diff in differences:

            if "afterBlob" in diff and diff["afterBlob"]["path"].startswith(
                f"components/{component_name}"
            ):

                change_detected = True
                break

        if change_detected:
            put_job_success(job_id, "Changes detected for this component!")
        else:
            stop_pipeline_execution(pipeline_name, pipeline_execution_id)

    except Exception as e:
        # If any other exceptions which we didn't expect are raised
        # then fail the job and log the exception message.
        print("Function failed due to exception.")
        print(e)
        traceback.print_exc()
        put_job_failure(job_id, "Function exception: " + str(e))

    print("Function complete.")
    return "Complete."
