from aws_cdk import (
    Stack,
    aws_codecommit as codecommit,
    aws_codepipeline as codepipeline,
    aws_codepipeline_actions as pipeline_actions,
    aws_codebuild as codebuild,
    pipelines as pipelines,
    Stage,
    aws_lambda as lambda_,
    aws_apigateway as apigw,
    aws_dynamodb as dynamodb,
    aws_s3 as s3,
    aws_iam as iam,
    RemovalPolicy,
)
from constructs import Construct

class ServerlessAppStage(Stage):
    def __init__(self, scope: Construct, construct_id: str, **kwargs):
        super().__init__(scope, construct_id, **kwargs)

        # Create the serverless application stack in this stage
        ServerlessAppStack(self, "ServerlessApp")

class ServerlessAppStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, **kwargs):
        super().__init__(scope, construct_id, **kwargs)

        # Frontend - S3 bucket for web assets
        website_bucket = s3.Bucket(
            self,
            "WebsiteBucket",
            removal_policy=RemovalPolicy.DESTROY,
            auto_delete_objects=True,
            cors=[
                s3.CorsRule(
                    allowed_methods=[s3.HttpMethods.GET],
                    allowed_origins=["*"],
                    allowed_headers=["*"],
                )
            ],
        )

        # Backend - DynamoDB table
        table = dynamodb.Table(
            self,
            "Database",
            partition_key=dynamodb.Attribute(
                name="id",
                type=dynamodb.AttributeType.STRING
            ),
            billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST,
            removal_policy=RemovalPolicy.DESTROY,
        )

        # Backend - Lambda function
        backend_function = lambda_.Function(
            self,
            "BackendFunction",
            runtime=lambda_.Runtime.PYTHON_3_9,
            handler="index.handler",
            code=lambda_.Code.from_asset("lambda"),
            environment={
                "TABLE_NAME": table.table_name,
            }
        )

        # Grant Lambda function permissions to access DynamoDB
        table.grant_read_write_data(backend_function)

        # API Gateway
        api = apigw.RestApi(
            self,
            "ServerlessApi",
            default_cors_preflight_options=apigw.CorsOptions(
                allow_origins=["*"],
                allow_methods=["GET", "POST", "PUT", "DELETE"],
                allow_headers=["*"],
            )
        )

        # API Gateway integration
        api_integration = apigw.LambdaIntegration(backend_function)
        api.root.add_method("GET", api_integration)
        api.root.add_method("POST", api_integration)

class PipelineStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, **kwargs):
        super().__init__(scope, construct_id, **kwargs)

        # Create CodeCommit repository
        repo = codecommit.Repository(
            self,
            "ServerlessRepo",
            repository_name="serverless-app-repo",
            description="Repository for serverless application"
        )

        # Create pipeline
        pipeline = pipelines.CodePipeline(
            self,
            "Pipeline",
            synth=pipelines.ShellStep(
                "Synth",
                input=pipelines.CodePipelineSource.code_commit(repo, "main"),
                commands=[
                    "npm install -g aws-cdk",
                    "pip install -r requirements.txt",
                    "cdk synth",
                ]
            ),
            docker_enabled_for_synth=True,
        )

        # Add stages to pipeline
        pipeline.add_stage(
            ServerlessAppStage(
                self,
                "Dev",
                env={
                    "account": self.account,
                    "region": self.region
                }
            )
        )

        # Add production stage with manual approval
        prod_stage = pipeline.add_stage(
            ServerlessAppStage(
                self,
                "Prod",
                env={
                    "account": self.account,
                    "region": self.region
                }
            )
        )



Create an `app.py` file:

```python
#!/usr/bin/env python3
from aws_cdk import App, Environment [[2]](https://docs.aws.amazon.com/wellarchitected/latest/serverless-applications-lens/opex-deploying.html)
from pipeline_stack import PipelineStack

app = App()


app.synth()
