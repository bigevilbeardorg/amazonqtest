from constructs import Construct

class LambdaApiStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # Create Lambda function
        handler = lambda_.Function(
            self, 
            "ApiHandler",
            runtime=lambda_.Runtime.PYTHON_3_9,
            code=lambda_.Code.from_asset("lambda"),
            handler="handler.main",
            timeout=Duration.seconds(30),
            memory_size=128,
            environment={
                "ENVIRONMENT": "prod"  # Example environment variable
            },
            tracing=lambda_.Tracing.ACTIVE,  # Enable X-Ray tracing
        )
        
        # Create API Gateway
        api = apigw.RestApi(
            self,
            "ApiGateway",
            rest_api_name="Sample API",
            description="API Gateway with Lambda integration",
            deploy_options=apigw.StageOptions(
                stage_name="prod",
                logging_level=apigw.MethodLoggingLevel.INFO,
                data_trace_enabled=True,
                metrics_enabled=True,
            ),
            default_cors_preflight_options=apigw.CorsOptions(
                allow_origins=apigw.Cors.ALL_ORIGINS,
                allow_methods=apigw.Cors.ALL_METHODS,
                allow_headers=["Content-Type", "Authorization"],
            )
        )

        # Create API Gateway integration with Lambda

        # Add resources and methods
        api_resource = api.root.add_resource("api")
        
        # Add GET method
        api_resource.add_method(
            "GET",
            lambda_integration,
            method_responses=[
                apigw.MethodResponse(
                    status_code="200",
                    response_parameters={
                        "method.response.header.Access-Control-Allow-Origin": True
                    }
                )
            ]
        )

        # Add POST method
        api_resource.add_method(
            "POST",
            lambda_integration,
            method_responses=[
                apigw.MethodResponse(
                    status_code="200",
                    response_parameters={
                        "method.response.header.Access-Control-Allow-Origin": True
                    }
                )
            ]
        )

        # Output the API URL
        CfnOutput(
            self,
            "ApiUrl",
            value=f"{api.url}api",
            description="API Gateway URL"
        )
