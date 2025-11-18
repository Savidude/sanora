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

    lambda_messaging_function_name: str = "messaging-server-function"

    apigw_messaging_name: str = "SanoraMessagingAPI"
    apigw_messaging__throttle_rate_limit: int = 1000
    apigw_messaging_throttle_burst_limit: int = 2000
    apigw_messaging_authorizer_name: str = "MessagingAuthorizer"

    ecr_agent_repository_name: str = "bedrock-agentcore-tutor-agent"

    s3_agent_artifacts_bucket_name: str = "sanora-agent-artifacts-bucket"


@dataclass
class SSMParameterPaths:
    """
    SSM Parameter Store paths for shared resources.
    """

    iam_tutor_agent_execution_role_arn: str = (
        "/sanora/iam/tutor_agent_execution_role_arn"
    )

    ecr_tutor_agent_repository_uri: str = "/sanora/ecr/tutor_agent_repository_uri"

    agentcore_tutor_agent_runtime_arn: str = "/sanora/agentcore/tutor_agent_runtime_arn"

    s3_agent_artifacts_bucket_name: str = "/sanora/s3/agent_artifacts_bucket_name"
