#!/bin/bash
# filepath: launch_agent_runtime.sh

set -e

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color


# Required environment variables
REQUIRED_VARS=("AWS_REGION" "AGENT_NAME")


echo -e "${GREEN}=== AWS Bedrock Agentcore Runtime Configuration ===${NC}"

# Validate required environment variables
echo "Validating environment variables..."
for var in "${REQUIRED_VARS[@]}"; do
    if [ -z "${!var}" ]; then
        echo -e "${RED}Error: $var is not set${NC}"
        exit 1
    fi
done
echo -e "${GREEN}✓ All required environment variables are set${NC}"

# SSM parameter paths
TUTOR_AGENT_RUNTIME_PARAM="/sanora/agentcore/tutor_agent_runtime_arn"
AGENT_ARTIFACTS_BUCKET_NAME_PARAM="/sanora/s3/agent_artifacts_bucket_name"

AGENTS_DIR="${GITHUB_WORKSPACE:-$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)}/agents"

if [ ! -d "$AGENTS_DIR" ]; then
    echo -e "${RED}Error: Agents directory not found at ${AGENTS_DIR}${NC}"
    exit 1
fi

cd "$AGENTS_DIR"
mkdir -p ".bedrock_agentcore/${AGENT_NAME}"

# Lauch the agent runtime
echo -e "${GREEN}Launching agent runtime...${NC}"
echo "Agent: ${AGENT_NAME}"
echo "Region: ${AWS_REGION}"

echo "Retrieving S3 bucket name from SSM..."
S3_BUCKET_NAME=$(aws ssm get-parameter \
    --name "$AGENT_ARTIFACTS_BUCKET_NAME_PARAM" \
    --region "$AWS_REGION" \
    --query 'Parameter.Value' \
    --output text 2>/dev/null || echo "")

if [ -z "$S3_BUCKET_NAME" ]; then
    echo -e "${RED}Error: Could not retrieve S3 bucket name from SSM parameter /sanora/s3/agent_artifacts_bucket_name${NC}"
    exit 1
fi

# Define S3 paths
S3_PREFIX="agents/${AGENT_NAME}"
S3_CONFIG_KEY="${S3_PREFIX}/.bedrock_agentcore.yaml"

AGENTCORE_CONFIG_FILE="${AGENTS_DIR}/.bedrock_agentcore.yaml"
AGENT_DOCKERFILE="${AGENTS_DIR}/.bedrock_agentcore/${AGENT_NAME}/Dockerfile"

# Download the configuration file from S3
echo "Downloading configuration file from s3://${S3_BUCKET_NAME}/${S3_CONFIG_KEY} ..."
if aws s3 cp "s3://${S3_BUCKET_NAME}/${S3_CONFIG_KEY}" "${AGENTCORE_CONFIG_FILE}" --region "$AWS_REGION"; then
    echo -e "${GREEN}✓ Configuration file downloaded successfully.${NC}"
else
    echo -e "${RED}Error: Failed to download configuration file from S3.${NC}"
    exit 1
fi

# Download the Dockerfile from S3
S3_DOCKERFILE_KEY="${S3_PREFIX}/Dockerfile"
echo "Downloading Dockerfile from s3://${S3_BUCKET_NAME}/${S3_DOCKERFILE_KEY} ..."
if aws s3 cp "s3://${S3_BUCKET_NAME}/${S3_DOCKERFILE_KEY}" "${AGENT_DOCKERFILE}" --region "$AWS_REGION"; then
    echo -e "${GREEN}✓ Dockerfile downloaded successfully.${NC}"
else
    echo -e "${RED}Error: Failed to download Dockerfile from S3.${NC}"
    exit 1
fi  

# Launch the agent runtime using the configuration file
echo "Launching agent runtime with configuration file..."
if agentcore launch; then
    echo -e "${GREEN}✓ Agent runtime launched successfully.${NC}"
else
    echo -e "${RED}Error: Failed to launch agent runtime.${NC}"
    exit 1
fi

# Upload the configuration file to S3
if aws s3 cp "${AGENTCORE_CONFIG_FILE}" "s3://${S3_BUCKET_NAME}/${S3_CONFIG_KEY}" --region "$AWS_REGION"; then
    echo -e "${GREEN}✓ Configuration file uploaded to S3 successfully.${NC}"
else
    echo -e "${RED}Error: Failed to upload configuration file to S3.${NC}"
    exit 1
fi

# Get the agent runtime ARN
echo "Retrieving agent runtime ARN..."
agentcore status -v | tr -d '\000-\037'
AGENT_ARN=$(agentcore status -v | tr -d '\000-\037' | jq -r '.config.agent_arn')
if [ -z "$AGENT_ARN" ]; then
    echo -e "${RED}Error: Could not retrieve agent ARN from agentcore status command.${NC}"
    exit 1
fi

# Add the agent runtime ARN to SSM Parameter Store
echo "Storing agent runtime ARN in SSM Parameter Store..."
if aws ssm put-parameter \
    --name "$TUTOR_AGENT_RUNTIME_PARAM" \
    --region "$AWS_REGION" \
    --value "$AGENT_ARN" \
    --type String \
    --overwrite; then
    echo -e "${GREEN}✓ Agent runtime ARN stored in SSM successfully.${NC}"
else
    echo -e "${RED}Error: Failed to store agent runtime ARN in SSM.${NC}"
    exit 1
fi
