"""CDK stack for handling frontend resources."""

import os
from aws_cdk import (
    Stack,
    aws_iam as iam,
    aws_ssm as ssm,
    SecretValue,
)
from aws_cdk.aws_amplify_alpha import (
    App as AmplifyApp,
    GitHubSourceCodeProvider,
)

from constructs import Construct
from shared_resource_config import SharedValues, SSMParameterPaths


class FrontendStack(Stack):
    """CDK stack for handling frontend resources."""

    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        shared_values: SharedValues,
        ssm_paths: SSMParameterPaths,
        **kwargs,
    ) -> None:
        super().__init__(scope, construct_id, **kwargs)

        amplify_role = iam.Role(
            self,
            shared_values.iam_amplify_service_role_name,
            assumed_by=iam.ServicePrincipal("amplify.amazonaws.com"),  # trust policy
        )

        allowed_params = [
            ssm_paths.cognito_user_pool_id,
            ssm_paths.cognito_user_pool_client_id,
            ssm_paths.apigw_messaging_service_url,
        ]
        amplify_ssm_policy = iam.Policy(
            self,
            "AmplifySSMReadPolicy",
            statements=[
                iam.PolicyStatement(
                    actions=["ssm:GetParameter"],
                    resources=[
                        ssm.StringParameter.from_string_parameter_name(
                            self, f"SSMParam{param.replace('/', '_')}", param
                        ).parameter_arn
                        for param in allowed_params
                    ]
                    + [
                        f"arn:aws:ssm:{self.region}:{self.account}:parameter/cdk-bootstrap/*"
                    ],
                )
            ],
        )
        amplify_role.attach_inline_policy(amplify_ssm_policy)

        amplify_role.add_managed_policy(
            iam.ManagedPolicy.from_aws_managed_policy_name(
                "AdministratorAccess-Amplify"
            )
        )
        amplify_role.add_managed_policy(
            iam.ManagedPolicy.from_aws_managed_policy_name(
                "service-role/AmplifyBackendDeployFullAccess"
            )
        )

        github_token = os.getenv("GITHUB_TOKEN")
        if not github_token:
            raise ValueError("GITHUB_TOKEN environment variable not set!")
        app = AmplifyApp(
            self,
            shared_values.amplify_sanora_frontend_app_name,
            role=amplify_role,
            source_code_provider=GitHubSourceCodeProvider(
                owner=shared_values.amplify_github_repo_owner,
                repository=shared_values.amplify_github_repo_name,
                oauth_token=SecretValue.unsafe_plain_text(github_token),
            ),
        )
        prod = app.add_branch("main")
        prod.add_environment("STAGE", "prod")
