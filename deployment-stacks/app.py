#!/usr/bin/env python3
import os

import aws_cdk as cdk

from shared_resource_config import SharedValues as shared_values
from shared_resource_config import SSMParameterPaths as ssm_parameter_paths

from stack_agent_messaging import AgentMessagingStack
from stack_agents import AgentsStack


app = cdk.App()
env = cdk.Environment(
    account=os.getenv("ACCOUNT_ID"), region=os.getenv("CDK_DEFAULT_REGION")
)

agent_messaging_stack = AgentMessagingStack(
    app, "AgentMessagingStack", shared_values, ssm_parameter_paths, env=env
)
agents_stack = AgentsStack(app, "AgentsStack", shared_values, ssm_parameter_paths)

agent_messaging_stack.add_dependency(agents_stack)

app.synth()
