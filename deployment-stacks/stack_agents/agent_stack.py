"""CDK stack for managing agent resources for agrent runtimes"""

from aws_cdk import (
    Stack,
    aws_iam as iam,
    aws_ecr as ecr,
    aws_ssm as ssm,
    aws_s3 as s3,
    aws_secretsmanager as secretsmanager,
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

        # S3 bucket for agent artifacts
        agent_artifacts_bucket = s3.Bucket(
            self,
            shared_values.s3_agent_artifacts_bucket_name,
            bucket_name=shared_values.s3_agent_artifacts_bucket_name,
            removal_policy=RemovalPolicy.RETAIN,
            auto_delete_objects=False,
        )
        ssm.StringParameter(
            self,
            "AgentArtifactsBucketName",
            parameter_name=ssm_paths.s3_agent_artifacts_bucket_name,
            string_value=agent_artifacts_bucket.bucket_name,
        )

        self._create_agentcore_starter_toolkit_user_role(
            shared_values, agent_artifacts_bucket.bucket_arn
        )

        # ECR repository for agent containers
        agent_repository = ecr.Repository(
            self,
            shared_values.ecr_agent_repository_name,
            repository_name=shared_values.ecr_agent_repository_name,
            removal_policy=RemovalPolicy.RETAIN,
            lifecycle_rules=[
                ecr.LifecycleRule(
                    description="Keep last 10 images",
                    max_image_count=10,
                )
            ],
        )

        ssm.StringParameter(
            self,
            "AgentECRRepository",
            parameter_name=ssm_paths.ecr_tutor_agent_repository_uri,
            string_value=agent_repository.repository_uri,
        )

        # Secrets Manager secrets for agent API keys
        gemini_agent_key_secret = secretsmanager.Secret(
            self,
            shared_values.secret_manager_gemini_api_key_name,
            secret_name=shared_values.secret_manager_gemini_api_key_name,
            description="API key for the Gemini agent",
            removal_policy=RemovalPolicy.DESTROY,
        )
        openai_agent_key_secret = secretsmanager.Secret(
            self,
            shared_values.secret_manager_openai_api_key_name,
            secret_name=shared_values.secret_manager_openai_api_key_name,
            description="API key for the OpenAI agent",
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
                    "ecr:BatchGetImage",
                    "ecr:GetDownloadUrlForLayer",
                    "ecr:GetAuthorizationToken",
                    "ecr:InitiateLayerUpload",
                    "ecr:BatchGetImage",
                    "ecr:GetDownloadUrlForLayer",
                ],
                resources=[agent_repository.repository_arn],
            ),
            iam.PolicyStatement(
                actions=["ecr:GetAuthorizationToken"],
                resources=["*"],
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
            iam.PolicyStatement(
                actions=[
                    "secretsmanager:GetSecretValue",
                ],
                resources=[
                    gemini_agent_key_secret.secret_arn,
                    openai_agent_key_secret.secret_arn,
                ],
            ),
        ]
        for statement in custom_policy_statements:
            agent_execution_role.add_to_policy(statement)

        ssm.StringParameter(
            self,
            "AgentExecutionRoleArn",
            parameter_name=ssm_paths.iam_tutor_agent_execution_role_arn,
            string_value=agent_execution_role.role_arn,
        )

        # Placeholder for agent runtime ARN (updated by CI/CD)
        ssm.StringParameter(
            self,
            "AgentRuntimeArn",
            parameter_name=ssm_paths.agentcore_tutor_agent_runtime_arn,
            string_value="PENDING_DEPLOYMENT",
            description="ARN of the deployed agent runtime (updated by CI/CD)",
        )

    def _create_agentcore_starter_toolkit_user_role(
        self, shared_values: SharedValues, agent_artifacts_bucket_arn: str
    ) -> None:
        """Create IAM custom policy for Agentcore Starter Toolkit users.
        This policy is to be set to the IAM user performing the Agentcore CI/CD tasks.
        """

        # Create custom managed policy
        iam.ManagedPolicy(
            self,
            shared_values.iam_agentcore_cicd_user_policy_name,
            managed_policy_name=shared_values.iam_agentcore_cicd_user_policy_name,
            description="Managed policy for Agentcore CI/CD operations",
            statements=[
                iam.PolicyStatement(
                    sid="IAMRoleManagement",
                    effect=iam.Effect.ALLOW,
                    actions=[
                        "iam:CreateRole",
                        "iam:DeleteRole",
                        "iam:GetRole",
                        "iam:PutRolePolicy",
                        "iam:DeleteRolePolicy",
                        "iam:AttachRolePolicy",
                        "iam:DetachRolePolicy",
                        "iam:TagRole",
                        "iam:ListRolePolicies",
                        "iam:ListAttachedRolePolicies",
                    ],
                    resources=[
                        "arn:aws:iam::*:role/*BedrockAgentCore*",
                        "arn:aws:iam::*:role/service-role/*BedrockAgentCore*",
                    ],
                ),
                iam.PolicyStatement(
                    sid="CodeBuildProjectAccess",
                    effect=iam.Effect.ALLOW,
                    actions=[
                        "codebuild:StartBuild",
                        "codebuild:BatchGetBuilds",
                        "codebuild:ListBuildsForProject",
                        "codebuild:CreateProject",
                        "codebuild:UpdateProject",
                        "codebuild:BatchGetProjects",
                    ],
                    resources=[
                        "arn:aws:codebuild:*:*:project/bedrock-agentcore-*",
                        "arn:aws:codebuild:*:*:build/bedrock-agentcore-*",
                    ],
                ),
                iam.PolicyStatement(
                    sid="CodeBuildListAccess",
                    effect=iam.Effect.ALLOW,
                    actions=[
                        "codebuild:ListProjects",
                    ],
                    resources=["*"],
                ),
                iam.PolicyStatement(
                    sid="IAMPassRoleAccess",
                    effect=iam.Effect.ALLOW,
                    actions=[
                        "iam:PassRole",
                    ],
                    resources=[
                        "arn:aws:iam::*:role/AmazonBedrockAgentCore*",
                        f"arn:aws:iam::*:role/{shared_values.iam_tutor_agent_execution_role_name}",
                        "arn:aws:iam::*:role/service-role/AmazonBedrockAgentCore*",
                    ],
                ),
                iam.PolicyStatement(
                    sid="CloudWatchLogsAccess",
                    effect=iam.Effect.ALLOW,
                    actions=[
                        "logs:GetLogEvents",
                        "logs:DescribeLogGroups",
                        "logs:DescribeLogStreams",
                    ],
                    resources=[
                        "arn:aws:logs:*:*:log-group:/aws/bedrock-agentcore/*",
                        "arn:aws:logs:*:*:log-group:/aws/codebuild/*",
                    ],
                ),
                iam.PolicyStatement(
                    sid="S3Access",
                    effect=iam.Effect.ALLOW,
                    actions=[
                        "s3:GetObject",
                        "s3:PutObject",
                        "s3:ListBucket",
                        "s3:CreateBucket",
                        "s3:PutLifecycleConfiguration",
                    ],
                    resources=[
                        "arn:aws:s3:::bedrock-agentcore-*",
                        "arn:aws:s3:::bedrock-agentcore-*/*",
                    ],
                ),
                iam.PolicyStatement(
                    sid="ECRRepositoryAccess",
                    effect=iam.Effect.ALLOW,
                    actions=[
                        "ecr:CreateRepository",
                        "ecr:DescribeRepositories",
                        "ecr:GetRepositoryPolicy",
                        "ecr:InitiateLayerUpload",
                        "ecr:CompleteLayerUpload",
                        "ecr:PutImage",
                        "ecr:UploadLayerPart",
                        "ecr:BatchCheckLayerAvailability",
                        "ecr:GetDownloadUrlForLayer",
                        "ecr:BatchGetImage",
                        "ecr:ListImages",
                        "ecr:TagResource",
                    ],
                    resources=[
                        "arn:aws:ecr:*:*:repository/bedrock-agentcore-*",
                    ],
                ),
                iam.PolicyStatement(
                    sid="ECRAuthorizationAccess",
                    effect=iam.Effect.ALLOW,
                    actions=[
                        "ecr:GetAuthorizationToken",
                    ],
                    resources=["*"],
                ),
                iam.PolicyStatement(
                    sid="SSMParameterStoreAccess",
                    effect=iam.Effect.ALLOW,
                    actions=[
                        "ssm:PutParameter",
                        "ssm:GetParameter",
                        "ssm:DeleteParameter",
                    ],
                    resources=[
                        "arn:aws:ssm:*:*:parameter/sanora/*",
                    ],
                ),
                iam.PolicyStatement(
                    sid="S3ConfigUpload",
                    effect=iam.Effect.ALLOW,
                    actions=[
                        "s3:PutObject",
                        "s3:GetObject",
                    ],
                    resources=[f"{agent_artifacts_bucket_arn}*"],
                ),
                iam.PolicyStatement(
                    sid="AgentcoreCreateRuntimeAccess",
                    effect=iam.Effect.ALLOW,
                    actions=[
                        "bedrock-agentcore:CreateAgentRuntime",
                        "bedrock-agentcore:UpdateAgentRuntime",
                        "bedrock-agentcore:GetAgentRuntime",
                        "bedrock-agentcore:ListAgentRuntimes",
                        "bedrock-agentcore:CreateAgentRuntimeEndpoint",
                        "bedrock-agentcore:GetAgentRuntimeEndpoint",
                        "bedrock-agentcore:CreateWorkloadIdentity",
                    ],
                    resources=["*"],
                ),
            ],
        )
