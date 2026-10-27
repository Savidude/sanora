"""CDK stack for managing agent resources for agrent runtimes"""

from pathlib import Path

from aws_cdk import (
    Stack,
    aws_bedrockagentcore as agentcore,
    aws_ecr_assets as ecr_assets,
    aws_iam as iam,
    aws_secretsmanager as secretsmanager,
    aws_ssm as ssm,
    RemovalPolicy,
)
from constructs import Construct
from shared_resource_config import SharedValues, SSMParameterPaths


class AgentsStack(Stack):
    """CDK stack for managing agent resources for agent runtimes"""

    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        shared_values: SharedValues,
        ssm_paths: SSMParameterPaths,
        **kwargs,
    ) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # CDK builds and publishes the image before creating the runtime.
        repository_root = Path(__file__).parents[2]
        agent_image = ecr_assets.DockerImageAsset(
            self,
            "StoryDesignerImage",
            directory=str(repository_root),
            file="agents/Dockerfile",
            exclude=[
                ".git",
                ".github",
                "deployment-stacks",
                "**/.venv",
                "**/__pycache__",
                "**/.pytest_cache",
                "**/.cdk.staging",
                "**/cdk.out",
            ],
            platform=ecr_assets.Platform.LINUX_ARM64,
        )

        ssm.StringParameter(
            self,
            "AgentECRRepository",
            parameter_name=ssm_paths.ecr_tutor_agent_repository_uri,
            string_value=agent_image.repository.repository_uri,
        )

        # Secrets Manager secrets for agent API keys
        gemini_agent_key_secret = secretsmanager.Secret(
            self,
            shared_values.secret_manager_gemini_api_key_name,
            secret_name=shared_values.secret_manager_gemini_api_key_name,
            description="API key for the Gemini agent",
            removal_policy=RemovalPolicy.DESTROY,
        )

        # IAM role for agent execution
        agent_execution_role = iam.Role(
            self,
            shared_values.iam_tutor_agent_execution_role_name,
            assumed_by=iam.ServicePrincipal("bedrock-agentcore.amazonaws.com"),
            role_name=shared_values.iam_tutor_agent_execution_role_name,
        )
        custom_policy_statements = [
            iam.PolicyStatement(
                actions=[
                    "bedrock:InvokeModel",
                    "bedrock:InvokeModelWithResponseStream",
                ],
                resources=[
                    "arn:aws:bedrock:*::foundation-model/*",
                    (f"arn:aws:bedrock:*:{self.account}:inference-profile/*"),
                ],
            ),
            iam.PolicyStatement(
                actions=[
                    "logs:DescribeLogStreams",
                    "logs:CreateLogGroup",
                    "logs:CreateLogStream",
                    "logs:PutLogEvents",
                ],
                resources=[
                    f"arn:aws:logs:{self.region}:{self.account}:log-group:/aws/bedrock-agentcore/runtimes/*",
                ],
            ),
        ]
        for statement in custom_policy_statements:
            agent_execution_role.add_to_policy(statement)
        gemini_agent_key_secret.grant_read(agent_execution_role)

        ecr_pull_policy = iam.Policy(
            self,
            "AgentCoreEcrPullPolicy",
            roles=[agent_execution_role],
            statements=[
                iam.PolicyStatement(
                    actions=["ecr:GetAuthorizationToken"],
                    resources=["*"],
                ),
                iam.PolicyStatement(
                    actions=[
                        "ecr:BatchGetImage",
                        "ecr:GetDownloadUrlForLayer",
                    ],
                    resources=[agent_image.repository.repository_arn],
                ),
            ],
        )

        runtime = agentcore.CfnRuntime(
            self,
            "StoryDesignerRuntime",
            agent_runtime_name="StoryDesigner",
            agent_runtime_artifact=agentcore.CfnRuntime.AgentRuntimeArtifactProperty(
                container_configuration=agentcore.CfnRuntime.ContainerConfigurationProperty(
                    container_uri=agent_image.image_uri,
                )
            ),
            network_configuration=agentcore.CfnRuntime.NetworkConfigurationProperty(
                network_mode="PUBLIC",
            ),
            role_arn=agent_execution_role.role_arn,
            environment_variables={
                "GEMINI_API_KEY_SECRET_ARN": gemini_agent_key_secret.secret_arn,
                "WIND_DOWN_GRAMMAR_CONCEPT_THRESHOLD": "3",
                "WIND_DOWN_TURN_LIMIT": "5",
            },
            description="Sanora Finnish story designer AgentCore runtime",
        )
        ssm.StringParameter(
            self,
            "StoryDesignerRuntimeArnParameter",
            parameter_name=ssm_paths.story_designer_agent_runtime_arn,
            string_value=runtime.attr_agent_runtime_arn,
        )
        runtime.node.add_dependency(ecr_pull_policy)
