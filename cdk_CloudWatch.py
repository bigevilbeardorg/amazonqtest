from aws_cdk import (
    Stack,
    aws_events as events,
    aws_events_targets as targets,
    aws_iam as iam,
    aws_logs as logs,
    Duration,
    CfnOutput,
)
from constructs import Construct

class EC2SchedulerStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, instance_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # Create CloudWatch Log Group
        log_group = logs.LogGroup(
            self,
            "SchedulerLogGroup",
            retention=logs.RetentionDays.ONE_MONTH,
            removal_policy=RemovalPolicy.DESTROY
        )

        # Create IAM role for EventBridge
        eventbridge_role = iam.Role(
            self,
            "EventBridgeRole",
            assumed_by=iam.ServicePrincipal("events.amazonaws.com"),
            description="Role for EventBridge to stop EC2 instances",
        )

        # Add policy to allow stopping EC2 instances
        eventbridge_role.add_to_policy(
            iam.PolicyStatement(
                effect=iam.Effect.ALLOW,
                actions=[
                    "ec2:StopInstances",
                    "ec2:DescribeInstances"
                ],
                resources=[f"arn:aws:ec2:{self.region}:{self.account}:instance/{instance_id}"]
            )
        )

        # Add policy to allow CloudWatch Logs
        eventbridge_role.add_to_policy(
            iam.PolicyStatement(
                effect=iam.Effect.ALLOW,
                actions=[
                    "logs:CreateLogStream",
                    "logs:PutLogEvents"
                ],
                resources=[log_group.log_group_arn]
            )
        )

        # Create EventBridge rule
        stop_instance_rule = events.Rule(
            self,
            "StopInstanceRule",
            description="Rule to stop web instance at 15:00 UTC daily",
            schedule=events.Schedule.cron(
                minute="0",
                hour="15",
                month="*",
                week_day="*",
                year="*"
            ),
            enabled=True
        )

        # Add target to the rule
        stop_instance_rule.add_target(
            targets.AwsApi(
                action="stopInstances",
                service="EC2",
                parameters={
                    "InstanceIds": [
                        instance_id
                    ]
                },
                role=eventbridge_role,
                log_group=log_group
            )
        )

        # Output the rule ARN and log group name
        CfnOutput(
            self,
            "RuleArn",
            value=stop_instance_rule.rule_arn,
            description="EventBridge Rule ARN"
        )

        CfnOutput(
            self,
            "LogGroupName",
            value=log_group.log_group_name,
            description="CloudWatch Log Group Name"
        )
