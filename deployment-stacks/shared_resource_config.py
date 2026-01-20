"""
Contains values shared across multiple deployment stacks and SSM parameter resouece paths.
"""

from dataclasses import dataclass


@dataclass
class SharedValues:
    """
    Shared values across multiple deployment stacks.
    """

    cognito_user_pool_name: str = "sanora-user-pool"
    congnito_user_pool_client_name: str = "sanora-user-pool-web-client"

    iam_messaging_function_role_name: str = "SanoraMessagingFunctionRole"
    iam_tutor_agent_execution_role_name: str = "SanoraTutorAgentExecutionRole"
    iam_agentcore_cicd_user_policy_name: str = "SanoraAgentcoreCICDUserPolicy"
    iam_amplify_service_role_name: str = "SanoraAmplifyServiceRole"

    lambda_messaging_function_name: str = "messaging-service"

    apigw_messaging_name: str = "SanoraMessagingAPI"
    apigw_messaging__throttle_rate_limit: int = 1000
    apigw_messaging_throttle_burst_limit: int = 2000
    apigw_messaging_authorizer_name: str = "MessagingAuthorizer"

    ecr_agent_repository_name: str = "bedrock-agentcore-tutor-agent"

    s3_agent_artifacts_bucket_name: str = "sanora-agent-artifacts-bucket"

    amplify_sanora_frontend_app_name: str = "SanoraFrontendApp"
    amplify_github_repo_owner: str = "Savidude"
    amplify_github_repo_name: str = "sanora-frontend"
    amplify_app_name: str = "SanoraFrontendApp"

    secret_manager_gemini_api_key_name: str = "GeminiApiKey"
    secret_manager_openai_api_key_name: str = "OpenAIApiKey"


@dataclass
class SSMParameterPaths:
    """
    SSM Parameter Store paths for shared resources.
    """

    env: str = "/sanora/env" # added manually, possible values: "dev"/"stg"/"prd"

    iam_tutor_agent_execution_role_arn: str = (
        "/sanora/iam/tutor_agent_execution_role_arn"
    )

    ecr_tutor_agent_repository_uri: str = "/sanora/ecr/tutor_agent_repository_uri"

    agentcore_tutor_agent_runtime_arn: str = "/sanora/agentcore/tutor_agent_runtime_arn"

    s3_agent_artifacts_bucket_name: str = "/sanora/s3/agent_artifacts_bucket_name"

    cognito_user_pool_id: str = "/sanora/cognito/user_pool_id"
    cognito_user_pool_client_id: str = "/sanora/cognito/user_pool_client_id"

    apigw_messaging_service_url: str = "/sanora/apigw/messaging_service_url"
