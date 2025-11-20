#!/bin/bash
# filepath: configure_agent_runtime.sh

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
AGENT_EXECUTION_ROLE_ARN_PARAM="/sanora/iam/tutor_agent_execution_role_arn"
AGENT_ECR_URI_PARAM="/sanora/ecr/tutor_agent_repository_uri"


# Function to check if runtime is already configured
check_runtime_configured() {
    echo "Checking if runtime is already configured..."
    
    RUNTIME_ARN=$(aws ssm get-parameter \
        --name "$TUTOR_AGENT_RUNTIME_PARAM" \
        --region "$AWS_REGION" \
        --query 'Parameter.Value' \
        --output text 2>/dev/null || echo "")
    
    if [ -z "$RUNTIME_ARN" ]; then
        echo "Runtime parameter does not exist. Configuration needed."
        return 1
    elif [ "$RUNTIME_ARN" = "PENDING_DEPLOYMENT" ]; then
        echo -e "${YELLOW}Runtime status: PENDING_DEPLOYMENT. Configuration needed.${NC}"
        return 1
    else
        echo -e "${GREEN}Runtime already configured.${NC}"
        return 0
    fi
}

# Check if already configured
if check_runtime_configured; then
    echo -e "${GREEN}=== Configuration check complete ===${NC}"
    exit 0
fi

# Navigate to agents directory
AGENTS_DIR="${GITHUB_WORKSPACE:-$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)}/agents"

if [ ! -d "$AGENTS_DIR" ]; then
    echo -e "${RED}Error: Agents directory not found at ${AGENTS_DIR}${NC}"
    exit 1
fi

cd "$AGENTS_DIR"

# Configure the agent runtime
echo -e "${GREEN}Configuring agent runtime...${NC}"
echo "Agent: ${AGENT_NAME}"
echo "Region: ${AWS_REGION}"

AGENT_EXECUTION_ROLE_ARN=$(aws ssm get-parameter \
        --name "$AGENT_EXECUTION_ROLE_ARN_PARAM" \
        --region "$AWS_REGION" \
        --query 'Parameter.Value' \
        --output text 2>/dev/null || echo "")
if [ -z "$AGENT_EXECUTION_ROLE_ARN" ]; then
    echo -e "${RED}Error: Could not retrieve agent execution role ARN from SSM parameter ${AGENT_EXECUTION_ROLE_ARN_PARAM}${NC}"
    exit 1
fi

AGENT_ECR_URI=$(aws ssm get-parameter \
        --name "$AGENT_ECR_URI_PARAM" \
        --region "$AWS_REGION" \
        --query 'Parameter.Value' \
        --output text 2>/dev/null || echo "")
if [ -z "$AGENT_ECR_URI" ]; then
    echo -e "${RED}Error: Could not retrieve agent ECR URI from SSM parameter ${AGENT_ECR_URI_PARAM}${NC}"
    exit 1
fi


# Run agentcore configure command
if agentcore configure \
    --entrypoint "tutor_agent.py" \
    --name "$AGENT_NAME" \
    --requirements-file "requirements.txt" \
    --execution-role "$AGENT_EXECUTION_ROLE_ARN" \
    --ecr "$AGENT_ECR_URI" \
    --authorizer-config null \
    --disable-memory; then
    echo -e "${GREEN}✓ agentcore configure command completed successfully${NC}"
else
    echo -e "${RED}Error: agentcore configure command failed${NC}"
    exit 1
fi

# Check if .bedrock_agentcore.yaml file was created
AGENTCORE_CONFIG_FILE="${AGENTS_DIR}/.bedrock_agentcore.yaml"
if [ ! -f "$AGENTCORE_CONFIG_FILE" ]; then
    echo -e "${RED}Error: Configuration file not found at ${AGENTCORE_CONFIG_FILE}${NC}"
    echo -e "${RED}agentcore configure may have failed to create the configuration${NC}"
    exit 1
fi

AGENT_DOCKERFILE="${AGENTS_DIR}/.bedrock_agentcore/${AGENT_NAME}/Dockerfile"
if [ ! -f "$AGENT_DOCKERFILE" ]; then
    echo -e "${RED}Error: Dockerfile not found at ${AGENT_DOCKERFILE}${NC}"
    echo -e "${RED}agentcore configure may have failed to create the Dockerfile${NC}"
    exit 1
fi

# Get agent artifacts S3 bucket name from SSM Parameter Store
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

echo -e "${GREEN}✓ S3 bucket name retrieved: ${S3_BUCKET_NAME}${NC}"

# Define S3 paths
S3_PREFIX="agents/${AGENT_NAME}"
S3_CONFIG_KEY="${S3_PREFIX}/.bedrock_agentcore.yaml"

# Upload configuration file to S3
echo "Uploading configuration file to S3..."
echo "Bucket: ${S3_BUCKET_NAME}"
echo "Key: ${S3_CONFIG_KEY}"

if aws s3 cp "$AGENTCORE_CONFIG_FILE" "s3://${S3_BUCKET_NAME}/${S3_CONFIG_KEY}" \
    --region "$AWS_REGION"; then
    echo -e "${GREEN}✓ Configuration file uploaded to S3 successfully${NC}"
else
    echo -e "${RED}Error: Failed to upload configuration file to S3${NC}"
    exit 1
fi

# Upload Dockerfile to S3
echo "Uploading Dockerfile to S3..."
S3_DOCKERFILE_KEY="${S3_PREFIX}/Dockerfile"
echo "Bucket: ${S3_BUCKET_NAME}"
echo "Key: ${S3_DOCKERFILE_KEY}"

if aws s3 cp "$AGENT_DOCKERFILE" "s3://${S3_BUCKET_NAME}/${S3_DOCKERFILE_KEY}" \
    --region "$AWS_REGION"; then
    echo -e "${GREEN}✓ Dockerfile uploaded to S3 successfully${NC}"
else
    echo -e "${RED}Error: Failed to upload Dockerfile to S3${NC}"
    exit 1
fi
