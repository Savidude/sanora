"""CDK stack for managing resources for agent messaging functionality."""

from aws_cdk import (
    Stack,
    Duration,
    aws_cognito as cognito,
    aws_lambda as _lambda,
    aws_iam as iam,
    aws_apigateway as apigw,
    aws_ssm as ssm,
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

        tutor_agent_runtime_arn = ssm.StringParameter.value_for_string_parameter(
            self, ssm_paths.agentcore_tutor_agent_runtime_arn
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
                resources=[f"{tutor_agent_runtime_arn}*"],
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
                "TUTOR_AGENT_RUNTIME_ARN": tutor_agent_runtime_arn,
            },
        )

        return messaging_function

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
