"""CDK stack for managing resources for agent messaging functionality."""

from pathlib import Path

from aws_cdk import (
    Stack,
    Duration,
    aws_cognito as cognito,
    aws_dynamodb as dynamodb,
    aws_ecr_assets as ecr_assets,
    aws_lambda as _lambda,
    aws_iam as iam,
    aws_apigateway as apigw,
    aws_ssm as ssm,
    aws_s3 as s3,
    RemovalPolicy,
)
from constructs import Construct
from shared_resource_config import SharedValues, SSMParameterPaths


class AgentMessagingStack(Stack):
    """CDK stack for agent messaging resources."""

    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        shared_values: SharedValues,
        ssm_paths: SSMParameterPaths,
        **kwargs,
    ) -> None:
        super().__init__(scope, construct_id, **kwargs)

        user_pool = self._create_cognito_resources(shared_values, ssm_paths)
        messaging_function = self._create_messaging_function_resources(
            shared_values, ssm_paths
        )
        story_bucket = self._create_story_bucket(shared_values)
        story_designer_table = self._create_story_designer_table(shared_values)
        self._create_story_designer_function_resources(
            shared_values, ssm_paths, story_designer_table, story_bucket
        )
        self._create_messaging_api_resources(
            user_pool, messaging_function, shared_values, ssm_paths
        )

    def _create_cognito_resources(
        self, shared_values: SharedValues, ssm_paths: SSMParameterPaths
    ) -> cognito.UserPool:
        """Create Cognito User Pool and User Pool Client for authentication."""

        user_pool = cognito.UserPool(
            self,
            shared_values.cognito_user_pool_name,
            self_sign_up_enabled=True,
            sign_in_aliases=cognito.SignInAliases(email=True, username=True),
            password_policy=cognito.PasswordPolicy(
                min_length=8,
                require_lowercase=True,
                require_uppercase=True,
                require_digits=True,
                require_symbols=False,
            ),
            account_recovery=cognito.AccountRecovery.EMAIL_ONLY,
        )
        # Store the User Pool ID in SSM Parameter Store
        ssm.StringParameter(
            self,
            "CognitoUserPoolIdParameter",
            parameter_name=ssm_paths.cognito_user_pool_id,
            string_value=user_pool.user_pool_id,
        )

        user_pool_client = user_pool.add_client(
            shared_values.congnito_user_pool_client_name,
            auth_flows=cognito.AuthFlow(user_password=True, user_srp=True),
            generate_secret=False,
            o_auth=cognito.OAuthSettings(
                flows=cognito.OAuthFlows(implicit_code_grant=True),
                callback_urls=[
                    # Add your Amplify/Frontend callback URLs here
                    "http://localhost:3000",
                ],
                logout_urls=[
                    "http://localhost:3000",
                ],
            ),
            supported_identity_providers=[
                cognito.UserPoolClientIdentityProvider.COGNITO
            ],
        )
        # Store the User Pool Client ID in SSM Parameter Store
        ssm.StringParameter(
            self,
            "CognitoUserPoolClientIdParameter",
            parameter_name=ssm_paths.cognito_user_pool_client_id,
            string_value=user_pool_client.user_pool_client_id,
        )

        return user_pool

    def _create_messaging_function_resources(
        self, shared_values: SharedValues, ssm_paths: SSMParameterPaths
    ) -> _lambda.DockerImageFunction:
        """Create Lambda function for handling messaging."""

        story_designer_agent_runtime_arn = (
            ssm.StringParameter.value_for_string_parameter(
                self, ssm_paths.story_designer_agent_runtime_arn
            )
        )

        role = iam.Role(
            self,
            shared_values.iam_messaging_function_role_name,
            assumed_by=iam.ServicePrincipal("lambda.amazonaws.com"),
            role_name=shared_values.iam_messaging_function_role_name,
        )
        custom_policy_statements = [
            iam.PolicyStatement(
                actions=[
                    "logs:CreateLogGroup",
                    "logs:CreateLogStream",
                    "logs:PutLogEvents",
                ],
                resources=["*"],
            ),
            iam.PolicyStatement(
                actions=["bedrock-agentcore:InvokeAgentRuntime"],
                resources=[f"{story_designer_agent_runtime_arn}*"],
            ),
        ]
        for statement in custom_policy_statements:
            role.add_to_policy(statement)

        messaging_function = _lambda.DockerImageFunction(
            self,
            shared_values.lambda_messaging_function_name,
            function_name=shared_values.lambda_messaging_function_name,
            code=_lambda.DockerImageCode.from_image_asset(directory="lambdas/server"),
            role=role,
            memory_size=256,
            timeout=Duration.minutes(1),
            architecture=_lambda.Architecture.X86_64,
            environment={
                "TUTOR_AGENT_RUNTIME_ARN": story_designer_agent_runtime_arn,
            },
        )

        return messaging_function

    def _create_story_bucket(self, shared_values: SharedValues) -> s3.Bucket:
        """Create the bucket used to store generated story states."""

        return s3.Bucket(
            self,
            shared_values.s3_stories_bucket_name,
            bucket_name=shared_values.s3_stories_bucket_name,
            removal_policy=RemovalPolicy.DESTROY,
        )

    def _create_story_designer_table(
        self, shared_values: SharedValues
    ) -> dynamodb.Table:
        """Create the table used to store generated story responses."""

        table = dynamodb.Table(
            self,
            shared_values.dynamodb_story_table_name,
            table_name=shared_values.dynamodb_story_table_name,
            partition_key=dynamodb.Attribute(
                name="PK", type=dynamodb.AttributeType.STRING
            ),
            sort_key=dynamodb.Attribute(name="SK", type=dynamodb.AttributeType.STRING),
            billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST,
            removal_policy=RemovalPolicy.RETAIN,
        )
        # Keep the existing GSI projections unchanged. DynamoDB does not allow
        # changing a GSI projection in place.
        table.add_global_secondary_index(
            index_name="DateIndex",
            partition_key=dynamodb.Attribute(
                name="date_index_pk", type=dynamodb.AttributeType.STRING
            ),
            sort_key=dynamodb.Attribute(
                name="date_index_sk", type=dynamodb.AttributeType.STRING
            ),
            projection_type=dynamodb.ProjectionType.INCLUDE,
            non_key_attributes=["id", "created_at", "s3_object_path"],
        )
        table.add_global_secondary_index(
            index_name="IdentifiedConceptIndex",
            partition_key=dynamodb.Attribute(
                name="concept_index_pk", type=dynamodb.AttributeType.STRING
            ),
            sort_key=dynamodb.Attribute(
                name="concept_index_sk", type=dynamodb.AttributeType.STRING
            ),
            projection_type=dynamodb.ProjectionType.INCLUDE,
            non_key_attributes=[
                "story_id",
                "grammar_concept_code",
                "identified",
                "total_findings",
                "created_at",
                "s3_object_path",
            ],
        )
        return table

    def _create_story_designer_function_resources(
        self,
        shared_values: SharedValues,
        ssm_paths: SSMParameterPaths,
        story_designer_table: dynamodb.Table,
        story_bucket: s3.Bucket,
    ) -> _lambda.DockerImageFunction:
        """Create a Lambda function for invoking the StoryDesigner runtime."""

        story_designer_runtime_arn = ssm.StringParameter.value_for_string_parameter(
            self, ssm_paths.story_designer_agent_runtime_arn
        )

        role = iam.Role(
            self,
            shared_values.iam_story_designer_function_role_name,
            assumed_by=iam.ServicePrincipal("lambda.amazonaws.com"),
            role_name=shared_values.iam_story_designer_function_role_name,
        )
        role.add_to_policy(
            iam.PolicyStatement(
                actions=[
                    "logs:CreateLogGroup",
                    "logs:CreateLogStream",
                    "logs:PutLogEvents",
                ],
                resources=["*"],
            )
        )
        role.add_to_policy(
            iam.PolicyStatement(
                actions=["bedrock-agentcore:InvokeAgentRuntime"],
                resources=[f"{story_designer_runtime_arn}*"],
            )
        )

        repository_root = Path(__file__).parents[2]
        story_designer_function = _lambda.DockerImageFunction(
            self,
            shared_values.lambda_story_designer_function_name,
            function_name=shared_values.lambda_story_designer_function_name,
            architecture=_lambda.Architecture.X86_64,
            code=_lambda.DockerImageCode.from_image_asset(
                str(repository_root),
                file="deployment-stacks/lambdas/story_designer/Dockerfile",
                exclude=[
                    "agents",
                    "deployment-stacks/stack_agents",
                    "deployment-stacks/stack_agent_messaging",
                    "deployment-stacks/stack_frontend",
                    "deployment-stacks/app.py",
                    "deployment-stacks/cdk.json",
                    "deployment-stacks/cdk.context.json",
                    "deployment-stacks/requirements*.txt",
                    "deployment-stacks/shared_resource_config.py",
                    "**/.cdk.staging",
                    "**/cdk.out",
                ],
                platform=ecr_assets.Platform.LINUX_AMD64,
            ),
            role=role,
            timeout=Duration.minutes(10),
            environment={
                "STORY_DESIGNER_RUNTIME_ARN": story_designer_runtime_arn,
                "STORY_DESIGNER_TABLE_NAME": story_designer_table.table_name,
                "STORY_DESIGNER_BUCKET_NAME": story_bucket.bucket_name,
            },
        )
        story_designer_table.grant_write_data(story_designer_function)
        story_bucket.grant_put(story_designer_function)
        return story_designer_function

    def _create_messaging_api_resources(
        self,
        user_pool: cognito.UserPool,
        messaging_function: _lambda.DockerImageFunction,
        shared_values: SharedValues,
        ssm_paths: SSMParameterPaths,
    ) -> None:
        """Create API Gateway resources for messaging API."""

        # Role that API Gateway uses to push execution logs to CloudWatch Logs
        apigw_cw_role = iam.Role(
            self,
            "ApiGwCloudWatchRole",
            assumed_by=iam.ServicePrincipal("apigateway.amazonaws.com"),
            managed_policies=[
                iam.ManagedPolicy.from_aws_managed_policy_name(
                    "service-role/AmazonAPIGatewayPushToCloudWatchLogs"
                )
            ],
            description="Role for API Gateway to push execution logs to CloudWatch Logs",
        )
        # Set the account-level CloudWatch Logs role ARN for API Gateway
        cfn_account = apigw.CfnAccount(
            self, "ApiGatewayAccount", cloud_watch_role_arn=apigw_cw_role.role_arn
        )

        messaging_api = apigw.RestApi(
            self,
            shared_values.apigw_messaging_name,
            rest_api_name=shared_values.apigw_messaging_name,
            description="API Gateway fronting the Messaging Lambda.",
            default_cors_preflight_options=apigw.CorsOptions(
                allow_origins=apigw.Cors.ALL_ORIGINS,
                allow_methods=["GET", "POST", "OPTIONS"],
                allow_headers=apigw.Cors.DEFAULT_HEADERS,
            ),
            deploy_options=apigw.StageOptions(
                throttling_rate_limit=10,
                throttling_burst_limit=100,
                metrics_enabled=True,
                logging_level=apigw.MethodLoggingLevel.INFO,
                data_trace_enabled=False,
            ),
        )

        # Ensure the stage is only created after the account role is set,
        # avoiding the "CloudWatch Logs role ARN must be set" race condition.
        cfn_stage = messaging_api.deployment_stage.node.default_child
        cfn_stage.add_dependency(cfn_account)

        authorizer = apigw.CognitoUserPoolsAuthorizer(
            self,
            shared_values.apigw_messaging_authorizer_name,
            cognito_user_pools=[user_pool],
        )

        api_res = messaging_api.root.add_resource("api")
        v1_res = api_res.add_resource("v1")
        chat_res = v1_res.add_resource("chat")
        message_res = chat_res.add_resource("message")

        message_res.add_method(
            "POST",
            apigw.LambdaIntegration(messaging_function, proxy=True),
            authorization_type=apigw.AuthorizationType.COGNITO,
            authorizer=authorizer,
        )

        # Store the API endpoint in SSM Parameter Store
        ssm.StringParameter(
            self,
            "MessagingApiEndpointParameter",
            parameter_name=ssm_paths.apigw_messaging_service_url,
            string_value=messaging_api.url,
        )
