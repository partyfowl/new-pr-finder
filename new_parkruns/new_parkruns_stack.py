from aws_cdk import BundlingOptions, DockerImage, Stack
from aws_cdk.aws_cloudwatch_actions import SnsAction
from aws_cdk.aws_events import Rule, Schedule
from aws_cdk.aws_events_targets import LambdaFunction
from aws_cdk.aws_iam import PolicyStatement
from aws_cdk.aws_lambda import Code, Function, Runtime
from aws_cdk.aws_s3 import Bucket
from aws_cdk.aws_sns import Subscription, SubscriptionProtocol, Topic
from constructs import Construct
import yaml


class NewParkrunsStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        alarm_topic = Topic(
            self, "DeadLetter", display_name="New Parkrun Notification - ERROR"
        )

        function = Function(
            self,
            "NewParkrunNotifier",
            handler="main.handler",
            runtime=Runtime.PYTHON_3_10,
            code=Code.from_asset(
                "./app",
                bundling=BundlingOptions(
                    image=DockerImage(
                        "public.ecr.aws/lambda/python:3.10.2023.05.07.17"
                    ),
                    command=[
                        "pip install -r requirements.txt -t /asset-output/ && cp main.py /asset-output/"
                    ],
                    entrypoint=["/bin/bash", "-c"],
                ),
            ),
        )

        function.metric_errors(statistic="sum").create_alarm(
            self,
            "ErrorAlarm",
            threshold=1,
            evaluation_periods=1,
        ).add_alarm_action(SnsAction(alarm_topic))

        Rule(self, "CronJob", schedule=Schedule.cron(minute="0", hour="19")).add_target(
            LambdaFunction(function)
        )

        topic = Topic(self, "Topic", display_name="New Parkrun Notification")

        with open("subscriptions.yaml") as f:
            config = yaml.safe_load(f)

        for key, email_address in config["new-parkruns"].items():
            Subscription(
                self,
                key,
                topic=topic,
                endpoint=email_address,
                protocol=SubscriptionProtocol.EMAIL,
            )

        for key, email_address in config["errors"].items():
            Subscription(
                self,
                key,
                topic=alarm_topic,
                endpoint=email_address,
                protocol=SubscriptionProtocol.EMAIL,
            )

        bucket = Bucket(self, "bucket")

        function.add_environment(key="TOPIC", value=topic.topic_arn)

        function.add_environment(key="S3_BUCKET", value=bucket.bucket_name)

        function.add_environment(key="S3_KEY", value="events.json")

        function.add_to_role_policy(
            PolicyStatement(actions=["SNS:Publish"], resources=[topic.topic_arn])
        )

        function.add_to_role_policy(
            PolicyStatement(
                actions=["S3:GetObject", "S3:PutObject", "s3:ListBucket"],
                resources=[bucket.bucket_arn, f"{bucket.bucket_arn}/events.json"],
            )
        )
