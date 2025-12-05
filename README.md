# Sanora - AI-Powered Finnish Language Tutor

**Sanora** is a conversational Finnish language tutor built with Amazon Bedrock AgentCore. It provides immersive, scenario-based learning experiences for A1-level Finnish learners through natural conversation practice.

## Architecture

### Deployment Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                         AWS Infrastructure                       │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌──────────────┐      ┌──────────────────┐   ┌─────────────┐ │
│  │   Amplify    │      │   API Gateway    │   │   Cognito   │ │
│  │  (Frontend)  │─────▶│  + Authorizer    │──▶│ User Pool   │ │
│  └──────────────┘      └────────┬─────────┘   └─────────────┘ │
│         │                        │                               │
│         │                        ▼                               │
│         │               ┌─────────────────┐                     │
│         │               │ Lambda Function │                     │
│         │               │  (Container)    │                     │
│         │               └────────┬────────┘                     │
│         │                        │                               │
│         │                        ▼                               │
│         │          ┌──────────────────────────┐                 │
│         │          │  Bedrock AgentCore       │                 │
│         │          │  (Tutor Agent Runtime)   │                 │
│         │          └────────┬─────────────────┘                 │
│         │                   │                                    │
│         │                   ▼                                    │
│         │          ┌──────────────────────┐                     │
│         │          │  Secrets Manager     │                     │
│         │          │  (API Keys)          │                     │
│         │          └──────────────────────┘                     │
│         │                                                        │
│         └──────────▶ SSM Parameters (Config Sharing)            │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│                       CI/CD Pipeline                             │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  GitHub Actions ─▶ Build Container ─▶ ECR ─▶ Deploy to         │
│                                                AgentCore         │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### AWS Infrastructure Components

Sanora is deployed across three AWS CDK stacks:

1. **AgentsStack** - Core agent infrastructure
   - ECR repository for agent containers
   - IAM execution roles for Bedrock AgentCore
   - S3 bucket for agent artifacts
   - AWS Secrets Manager for API keys
   - SSM parameters for resource sharing

2. **AgentMessagingStack** - API and authentication
   - Amazon Cognito for user authentication
   - Lambda function (containerized) for message handling
   - API Gateway with Cognito authorizer
   - Integration with Bedrock AgentCore runtime

3. **FrontendStack** - Web application hosting
   - AWS Amplify for frontend deployment
   - Automatic deployment from GitHub repository
   - Environment variable injection from SSM parameters

### Application Architecture

```
sanora/
├── agents/                      # AI Agent implementations
│   ├── models/                 # Agent base classes and configuration
│   ├── prompts/                # System prompts for different AI roles
│   └── tutor_agent.py          # Main AgentCore entrypoint
├── deployment-stacks/          # AWS CDK infrastructure code
│   ├── app.py                  # CDK app entry point
│   ├── stack_agents/           # AgentsStack definition
│   ├── stack_agent_messaging/  # AgentMessagingStack definition
│   ├── stack_frontend/         # FrontendStack definition
│   └── lambdas/server/         # Lambda function code
│       ├── main.py             # FastAPI application
│       ├── config/             # Middleware and logging
│       └── v1/                 # API version 1
│           ├── api/            # REST endpoints
│           ├── models/         # Pydantic data models
│           └── service/        # Business logic layer
└── .github/workflows/          # CI/CD for agent deployment
```

### AI Agent Pipeline

1. **Teacher Agent** (Gemini 2.5 Flash)
   - Generates conversational responses in Finnish
   - Provides grammar corrections and explanations
   - Creates contextual vocabulary suggestions

2. **Extractor Agent** (GPT-4o)
   - Parses teacher responses into structured JSON
   - Categorizes message types (initiation, feedback, conclusion)
   - Extracts error details and learning metadata

## AWS Deployment Guide

### Prerequisites

- AWS Account with:
  - Bedrock AgentCore access enabled
  - Permissions to create IAM roles, Lambda functions, API Gateway, Cognito, and Amplify resources
- AWS CLI configured with appropriate credentials
- Python 3.12+
- Node.js 18+ and AWS CDK CLI (`npm install -g aws-cdk`)
- OpenAI API key (for Extractor Agent)
- Google Gemini API key (for Teacher Agent)
- GitHub account with repository access

### Step 1: Deploy the AgentsStack

The AgentsStack creates the foundational infrastructure for your AI agents.

```bash
# Clone the repository
git clone https://github.com/Savidude/sanora.git
cd sanora/deployment-stacks

# Set up AWS credentials
export AWS_ACCOUNT_ID="your-account-id"
export CDK_DEFAULT_REGION="eu-central-1"  # or your preferred region
export ACCOUNT_ID=$AWS_ACCOUNT_ID

# Install CDK dependencies
pip install -r requirements.txt

# Bootstrap CDK (first time only)
cdk bootstrap aws://$AWS_ACCOUNT_ID/$CDK_DEFAULT_REGION

# Deploy the AgentsStack
cdk deploy AgentsStack
```

This creates:
- ECR repository for agent containers
- IAM roles for agent execution and CI/CD
- S3 bucket for agent artifacts
- Secrets Manager secrets (empty, to be filled in Step 3)
- SSM parameters for cross-stack resource sharing

### Step 2: Configure and Launch AgentCore Runtime

Use GitHub Actions workflows to build and deploy your AI agent to Bedrock AgentCore.

#### 2.1 Configure GitHub Repository Secrets and Variables

In your GitHub repository, navigate to **Settings > Secrets and variables > Actions** and add:

**Secrets:**
- `AWS_ACCESS_KEY_ID` - AWS access key with AgentCore permissions
- `AWS_SECRET_ACCESS_KEY` - AWS secret access key

**Variables:**
- `AWS_REGION` - Your AWS region (e.g., `eu-central-1`)
- `AGENT_NAME` - Name for your agent runtime (e.g., `tutor-agent`)

The IAM user must have the `SanoraAgentcoreCICDUserPolicy` managed policy attached (created by AgentsStack).

#### 2.2 Run the Configuration Workflow

1. Go to **Actions** tab in your GitHub repository
2. Select the **Configure Agent Runtime** workflow
3. Click **Run workflow**
4. Wait for completion (configures the agent runtime settings)

#### 2.3 Run the Launch Workflow

1. Select the **Launch Agent Runtime** workflow
2. Click **Run workflow**
3. Wait for completion (builds container, pushes to ECR, deploys to Bedrock AgentCore)

The workflow will:
- Build the agent Docker container
- Push it to the ECR repository
- Create/update the Bedrock AgentCore runtime
- Update the SSM parameter `/sanora/agentcore/tutor_agent_runtime_arn` with the runtime ARN

**Note:** The launch workflow also runs automatically on pushes to `main` branch when files in the `agents/` directory change.

### Step 3: Configure API Keys in Secrets Manager

Store your AI model API keys in AWS Secrets Manager:

```bash
# Set Gemini API key
aws secretsmanager put-secret-value \
  --secret-id GeminiApiKey \
  --secret-string "your-gemini-api-key-here" \
  --region $CDK_DEFAULT_REGION

# Set OpenAI API key
aws secretsmanager put-secret-value \
  --secret-id OpenAIApiKey \
  --secret-string "your-openai-api-key-here" \
  --region $CDK_DEFAULT_REGION
```

Alternatively, use the AWS Console:
1. Go to **AWS Secrets Manager**
2. Find `GeminiApiKey` and `OpenAIApiKey`
3. Click **Retrieve secret value** > **Edit**
4. Paste your API keys and save

### Step 4: Deploy the AgentMessagingStack

Deploy the API Gateway, Lambda function, and Cognito authentication:

```bash
# From the deployment-stacks directory
cdk deploy AgentMessagingStack
```

This creates:
- Cognito User Pool for authentication
- Lambda function (containerized) that invokes the AgentCore runtime
- API Gateway with Cognito authorizer
- SSM parameters with API endpoint URL

### Step 5: Set Up Frontend Repository

#### 5.1 Fork the Frontend Repository

1. Go to https://github.com/Savidude/sanora-frontend
2. Click **Fork** to create your own copy
3. Clone your forked repository locally (optional, for development)

#### 5.2 Create GitHub Personal Access Token

1. Go to GitHub **Settings > Developer settings > Personal access tokens > Tokens (classic)**
2. Click **Generate new token (classic)**
3. Give it a descriptive name (e.g., "Sanora Amplify Deployment")
4. Select the following scopes:
   - `repo` (all sub-scopes)
   - `admin:repo_hook` (all sub-scopes)
5. Click **Generate token**
6. **Copy the token immediately** (you won't be able to see it again)

#### 5.3 Set the GitHub Token as Environment Variable

```bash
export GITHUB_TOKEN="your-github-personal-access-token"
```

**Important:** Keep this token secure. Do not commit it to version control.

### Step 6: Update Shared Resource Configuration

Update the frontend repository details in the configuration file:

```bash
# Edit deployment-stacks/shared_resource_config.py
```

Modify these values to point to your forked repository:

```python
amplify_github_repo_owner: str = "YourGitHubUsername"
amplify_github_repo_name: str = "sanora-frontend"  # or your fork name
```

### Step 7: Deploy the FrontendStack

Deploy the Amplify application:

```bash
# Ensure GITHUB_TOKEN is still set in your environment
echo $GITHUB_TOKEN  # Should display your token

# From the deployment-stacks directory
cdk deploy FrontendStack
```

This creates:
- AWS Amplify application
- Connects to your forked GitHub repository
- Configures automatic deployments from the `main` branch
- Sets up environment variables from SSM parameters

### Step 8: Access Your Application

#### 8.1 Get the Amplify App URL

Retrieve your application URL:

```bash
# Get the Amplify app ID from the stack output or AWS Console
aws amplify list-apps --region $CDK_DEFAULT_REGION

# Get the domain for your app
aws amplify get-app --app-id <your-app-id> --region $CDK_DEFAULT_REGION
```

Or via AWS Console:
1. Go to **AWS Amplify** service
2. Select your **SanoraFrontendApp**
3. Find the URL under the **main** branch deployment

#### 8.2 Update Cognito Callback URLs (Important!)

Once you have the Amplify URL, update the Cognito User Pool Client callback URLs:

```bash
# Get your Amplify URL (e.g., https://main.d3x4mpl3.amplifyapp.com)
AMPLIFY_URL="your-amplify-url-here"

# Get the User Pool Client ID
USER_POOL_CLIENT_ID=$(aws ssm get-parameter \
  --name /sanora/cognito/user_pool_client_id \
  --query Parameter.Value \
  --output text \
  --region $CDK_DEFAULT_REGION)

USER_POOL_ID=$(aws ssm get-parameter \
  --name /sanora/cognito/user_pool_id \
  --query Parameter.Value \
  --output text \
  --region $CDK_DEFAULT_REGION)

# Update the callback URLs
aws cognito-idp update-user-pool-client \
  --user-pool-id $USER_POOL_ID \
  --client-id $USER_POOL_CLIENT_ID \
  --callback-urls "http://localhost:3000" "$AMPLIFY_URL" \
  --logout-urls "http://localhost:3000" "$AMPLIFY_URL" \
  --region $CDK_DEFAULT_REGION
```

Your Sanora application is now live! Visit the Amplify URL to start learning Finnish.

## Local Development

### Running the Lambda Function Locally

For local development and testing of the API:

```bash
cd deployment-stacks/lambdas/server

# Install dependencies
pip install -r requirements.txt

# Set environment variables
export TUTOR_AGENT_RUNTIME_ARN="your-agent-runtime-arn"
export AWS_REGION="eu-central-1"

# Run with uvicorn
uvicorn main:app --reload --port 8000

# Server will start on http://localhost:8000
```

### API Endpoints

#### Send Chat Message
```http
POST /api/v1/chat/message
```

**Request Body:**
```json
{
  "message": "Hei! Mitä kuuluu?",
  "sessionId": "user-123"
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "message_type": "initiation",
    "has_error": "NO",
    "feedback_text": null,
    "error_details": null,
    "greeting": "Hei! Hauska tutustua!",
    "scenario": "You're meeting someone for the first time at a café.",
    "conversation_continuation": "Mitä sinä haluat juoda?",
    "word_tips": [
      {
        "finnish": "juoda",
        "english": "to drink"
      }
    ]
  },
  "session_id": "user-123",
  "timestamp": "2025-11-07T10:30:00.123456"
}
```

### Response Data Models

#### TutorResponseData

| Field | Type | Description |
|-------|------|-------------|
| `message_type` | `MessageType` | Type of message: `initiation`, `feedback`, or `conclusion` |
| `has_error` | `ErrorType` | Error status: `YES`, `NO`, or `MINOR` |
| `feedback_text` | `string \| null` | Feedback provided by the tutor agent |
| `error_details` | `ErrorDetail \| null` | Details about user mistakes and corrections |
| `greeting` | `string \| null` | Greeting message (for initiation messages) |
| `scenario` | `string \| null` | Scenario description (for initiation messages) |
| `conversation_continuation` | `string` | Text to continue the conversation |
| `word_tips` | `WordTip[]` | List of difficult words with translations |

#### ErrorDetail

| Field | Type | Description |
|-------|------|-------------|
| `user_mistake` | `string \| null` | The specific mistake made by the user |
| `corrections` | `string[]` | List of suggested corrections |
| `explanation` | `string \| null` | Explanation of the mistake and corrections |

#### WordTip

| Field | Type | Description |
|-------|------|-------------|
| `finnish` | `string` | The difficult word in Finnish |
| `english` | `string` | The English translation |

### Example cURL Request (Local Development)

```bash
curl -X POST http://localhost:8000/api/v1/chat/message \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Minä olen opiskelija",
    "sessionId": "user-123"
  }'
```

### Testing with Production API

To test the deployed API, you need a valid Cognito JWT token:

```bash
# Get your API Gateway URL
API_URL=$(aws ssm get-parameter \
  --name /sanora/apigw/messaging_service_url \
  --query Parameter.Value \
  --output text)

# Use a valid JWT token from Cognito authentication
curl -X POST ${API_URL}api/v1/chat/message \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer your-cognito-jwt-token" \
  -d '{
    "message": "Hei! Mitä kuuluu?",
    "sessionId": "user-123"
  }'
```

### Interactive API Documentation

Once the server is running, access the auto-generated API documentation:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

These provide interactive API exploration and testing capabilities.

## Configuration Reference

### Environment Variables

#### Deployment (CDK)

| Variable | Description | Required |
|----------|-------------|----------|
| `AWS_ACCOUNT_ID` | Your AWS account ID | Yes |
| `CDK_DEFAULT_REGION` | AWS region for deployment | Yes |
| `GITHUB_TOKEN` | GitHub personal access token (for FrontendStack) | Yes |

#### GitHub Actions (Agent Deployment)

**Secrets:**
- `AWS_ACCESS_KEY_ID` - AWS access key with AgentCore permissions
- `AWS_SECRET_ACCESS_KEY` - AWS secret access key

**Variables:**
- `AWS_REGION` - Your AWS region
- `AGENT_NAME` - Name for your agent runtime

#### AWS Secrets Manager

| Secret Name | Description |
|-------------|-------------|
| `GeminiApiKey` | Google Gemini API key for Teacher Agent |
| `OpenAIApiKey` | OpenAI API key for Extractor Agent |

#### Lambda Environment Variables (Auto-configured)

| Variable | Description | Source |
|----------|-------------|--------|
| `TUTOR_AGENT_RUNTIME_ARN` | ARN of the deployed agent runtime | SSM Parameter |

### Agent Configuration

Agent configuration is managed in `agents/agent_config.json`:

```json
{
  "teacher_agent": {
    "prompt_path": "prompts/prompt_tutor_finnish.txt",
    "model_type": "gemini",
    "model_id": "gemini-2.5-flash",
    "agent_type": "text"
  },
  "extractor_agent": {
    "prompt_path": "prompts/prompt_agent_extractor.txt",
    "model_type": "openai",
    "model_id": "gpt-4o",
    "agent_type": "text"
  }
}
```

### SSM Parameters (Auto-created by Stacks)

| Parameter Path | Description | Created By |
|----------------|-------------|------------|
| `/sanora/iam/tutor_agent_execution_role_arn` | IAM role ARN for agent execution | AgentsStack |
| `/sanora/ecr/tutor_agent_repository_uri` | ECR repository URI | AgentsStack |
| `/sanora/agentcore/tutor_agent_runtime_arn` | AgentCore runtime ARN | GitHub Actions |
| `/sanora/s3/agent_artifacts_bucket_name` | S3 bucket name for artifacts | AgentsStack |
| `/sanora/cognito/user_pool_id` | Cognito User Pool ID | AgentMessagingStack |
| `/sanora/cognito/user_pool_client_id` | Cognito User Pool Client ID | AgentMessagingStack |
| `/sanora/apigw/messaging_service_url` | API Gateway endpoint URL | AgentMessagingStack |

## Troubleshooting

### Common Issues

#### "CloudWatch Logs role ARN must be set"
This error occurs if API Gateway deployment happens before the CloudWatch Logs role is configured. The CDK stack handles this automatically with dependencies, but if you encounter this:

```bash
# Redeploy the AgentMessagingStack
cdk deploy AgentMessagingStack --require-approval never
```

#### Agent Runtime Not Found
If the Lambda function can't find the agent runtime:

1. Verify the agent was deployed successfully via GitHub Actions
2. Check the SSM parameter:
```bash
aws ssm get-parameter --name /sanora/agentcore/tutor_agent_runtime_arn
```
3. If it shows "PENDING_DEPLOYMENT", run the GitHub Actions workflows again

#### Cognito Authentication Failures
Ensure callback URLs are updated:

```bash
# Verify current callback URLs
aws cognito-idp describe-user-pool-client \
  --user-pool-id <your-pool-id> \
  --client-id <your-client-id>
```

#### API Keys Not Working
Verify secrets are set correctly:

```bash
aws secretsmanager get-secret-value --secret-id GeminiApiKey
aws secretsmanager get-secret-value --secret-id OpenAIApiKey
```

### Stack Deployment Order

The stacks must be deployed in this order due to dependencies:
1. **AgentsStack** (creates base resources)
2. **GitHub Actions workflows** (deploys agent runtime, updates SSM)
3. **AgentMessagingStack** (depends on agent runtime ARN)
4. **FrontendStack** (depends on Cognito and API Gateway URLs)

### Cleanup

To remove all resources:

```bash
# Delete stacks in reverse order
cdk destroy FrontendStack
cdk destroy AgentMessagingStack
cdk destroy AgentsStack

# Manually delete the ECR repository if needed (retained by default)
aws ecr delete-repository \
  --repository-name bedrock-agentcore-tutor-agent \
  --force
```

## Cost Considerations

Running Sanora on AWS incurs the following approximate costs (as of December 2025):

- **AWS Amplify**: Free tier includes 1,000 build minutes/month, then $0.01/build minute
- **API Gateway**: $3.50/million requests (first 333M requests)
- **Lambda**: Free tier includes 1M requests/month, then $0.20/1M requests
- **Cognito**: Free tier includes 50,000 MAUs, then $0.0055/MAU
- **Bedrock AgentCore**: Based on compute time and invocations
- **ECR**: $0.10/GB-month storage
- **S3**: $0.023/GB-month (Standard)
- **Secrets Manager**: $0.40/secret/month
- **SSM Parameters**: Free for standard parameters

**Estimated monthly cost for light usage (< 10,000 conversations):** $5-15 USD

## Contributing

Contributions are welcome! Please feel free to submit issues or pull requests.

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

For issues, questions, or suggestions:
- Open an issue on GitHub
- Check existing issues for solutions
- Review the troubleshooting section above

**Tervetuloa opiskelemaan suomea! (Welcome to learning Finnish!)** 🇫🇮
