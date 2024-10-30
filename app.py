from aws_cdk import (
    Stack,
    aws_s3 as s3,
    aws_cloudfront as cloudfront,
    aws_cloudfront_origins as origins,
    aws_cloudtrail as cloudtrail,
    aws_kms as kms,
    RemovalPolicy,
    Duration,
)
from constructs import Construct

class StaticWebsiteStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # Create S3 bucket for website content
        website_bucket = s3.Bucket(
            self, 
            "WebsiteBucket",
            block_public_access=s3.BlockPublicAccess.BLOCK_ALL,
            removal_policy=RemovalPolicy.DESTROY,  # For development - change for production
            auto_delete_objects=True,  # For development - change for production
            enforce_ssl=True,
        )

        # Create S3 bucket for CloudTrail logs
        cloudtrail_bucket = s3.Bucket(
            self,
            "CloudTrailLogsBucket",
            block_public_access=s3.BlockPublicAccess.BLOCK_ALL,
            encryption=s3.BucketEncryption.S3_MANAGED,
            enforce_ssl=True,
            removal_policy=RemovalPolicy.RETAIN,
            lifecycle_rules=[
                s3.LifecycleRule(
                    expiration=Duration.days(365),  # Retain logs for 1 year
                    transitions=[
                        s3.Transition(
                            storage_class=s3.StorageClass.INTELLIGENT_TIERING,
                            transition_after=Duration.days(90)
                        )
                    ]
                )
            ],
        )

        # Create KMS key for CloudTrail
        cloudtrail_key = kms.Key(
            self,
            "CloudTrailKey",
            enable_key_rotation=True,
            description="KMS key for CloudTrail log encryption",
            pending_window=Duration.days(7),
            removal_policy=RemovalPolicy.RETAIN,
        )

        # Allow CloudTrail to use the KMS key
        cloudtrail_key.add_to_resource_policy(
            kms.PolicyStatement(
                actions=[
                    "kms:GenerateDataKey*",
                    "kms:Decrypt"
                ],
                principals=[cloudtrail.ServicePrincipal],
                resources=["*"]
            )
        )

        # Create CloudTrail
        trail = cloudtrail.Trail(
            self,
            "WebsiteBucketTrail",
            bucket=cloudtrail_bucket,
            encryption_key=cloudtrail_key,
            enable_file_validation=True,
            include_global_service_events=True,
            is_multi_region_trail=True,
            trail_name="website-bucket-trail",
        )

        # Add S3 data events for the website bucket
        trail.add_s3_event_selector(
            [s3.EventSelector(
                bucket=website_bucket,
                include_management_events=True,
            )]
        )

        # Create Origin Access Control
        oac = cloudfront.CfnOriginAccessControl(
            self,
            "MyOAC",
            origin_access_control_config=cloudfront.CfnOriginAccessControl.OriginAccessControlConfigProperty(
                name="MyOAC",
                origin_access_control_origin_type="s3",
                signing_behavior="always",
                signing_protocol="sigv4"
            )
        )

        # Create CloudFront distribution
        distribution = cloudfront.Distribution(
            self,
            "Distribution",
            default_behavior=cloudfront.BehaviorOptions(
                origin=origins.S3Origin(
                    bucket=website_bucket,
                    origin_access_control_id=oac.attr_id
                ),
                viewer_protocol_policy=cloudfront.ViewerProtocolPolicy.REDIRECT_TO_HTTPS,
                cache_policy=cloudfront.CachePolicy.CACHING_OPTIMIZED,
            ),
            default_root_object="index.html",
        )

        # Grant CloudFront access to the website buc
