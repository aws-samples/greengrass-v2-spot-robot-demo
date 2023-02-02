import aws_cdk as cdk
import aws_cdk.aws_cloudtrail as cloudtrail
from constructs import Construct


class MonitoringStack(cdk.Stack):
    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        trail = cloudtrail.Trail(
            self, "AccountCloudTrail", send_to_cloud_watch_logs=True
        )
