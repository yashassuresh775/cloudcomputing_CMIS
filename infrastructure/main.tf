# CMIS Engagement Platform - Shared Infrastructure
# Team Gig 'Em: External Core - Cognito, DynamoDB, Lambda, API Gateway

terraform {
  required_version = ">= 1.0"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
    archive = {
      source  = "hashicorp/archive"
      version = "~> 2.4"
    }
  }
}

provider "aws" {
  region = var.aws_region
}

# -----------------------------------------------------------------------------
# Cognito User Pool - Email/Password for External (Partner/Former Student/Friend)
# -----------------------------------------------------------------------------
resource "aws_cognito_user_pool" "external" {
  name = "${var.project_name}-external-pool"

  username_attributes      = ["email"]
  auto_verified_attributes = ["email"]

  password_policy {
    minimum_length    = 10
    require_lowercase = true
    require_uppercase = true
    require_numbers   = true
    require_symbols   = true
  }

  schema {
    name                = "email"
    attribute_data_type = "String"
    required            = true
    mutable             = true
    string_attribute_constraints {
      min_length = 1
      max_length = 256
    }
  }

  schema {
    name                = "custom:role"
    attribute_data_type = "String"
    required            = false
    mutable             = true
    developer_only_attribute = false
    string_attribute_constraints {
      min_length = 1
      max_length = 64
    }
  }

  schema {
    name                = "custom:class_year"
    attribute_data_type = "String"
    required            = false
    mutable             = true
    developer_only_attribute = false
    string_attribute_constraints {
      min_length = 1
      max_length = 16
    }
  }

  schema {
    name                = "custom:linked_uin"
    attribute_data_type = "String"
    required            = false
    mutable             = true
    developer_only_attribute = false
    string_attribute_constraints {
      min_length = 1
      max_length = 32
    }
  }

  admin_create_user_config {
    allow_admin_create_user_only = false
  }

  account_recovery_setting {
    recovery_mechanism {
      name     = "verified_email"
      priority = 1
    }
  }

  tags = var.tags
}

resource "aws_cognito_user_pool_client" "external" {
  name         = "${var.project_name}-external-client"
  user_pool_id = aws_cognito_user_pool.external.id

  explicit_auth_flows = [
    "ALLOW_USER_PASSWORD_AUTH",
    "ALLOW_REFRESH_TOKEN_AUTH",
    "ALLOW_USER_SRP_AUTH"
  ]

  prevent_user_existence_errors = "ENABLED"
  generate_secret               = false
  refresh_token_validity        = 30
  access_token_validity        = 60
  id_token_validity            = 60
  token_validity_units {
    access_token  = "minutes"
    id_token      = "minutes"
    refresh_token = "days"
  }
}

# -----------------------------------------------------------------------------
# DynamoDB - External users and graduation handover link
# -----------------------------------------------------------------------------
resource "aws_dynamodb_table" "external_users" {
  name         = "${var.project_name}-external-users"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "user_id"

  attribute {
    name = "user_id"
    type = "S"
  }
  attribute {
    name = "email"
    type = "S"
  }
  attribute {
    name = "linked_uin"
    type = "S"
  }

  global_secondary_index {
    name            = "email-index"
    hash_key        = "email"
    projection_type = "ALL"
  }
  global_secondary_index {
    name            = "linked-uin-index"
    hash_key        = "linked_uin"
    projection_type = "ALL"
  }

  tags = var.tags
}

# -----------------------------------------------------------------------------
# IAM role for External Service Lambda
# -----------------------------------------------------------------------------
resource "aws_iam_role" "external_lambda" {
  name = "${var.project_name}-external-lambda-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "lambda.amazonaws.com"
        }
      }
    ]
  })
}

resource "aws_iam_role_policy_attachment" "lambda_basic" {
  role       = aws_iam_role.external_lambda.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

resource "aws_iam_role_policy" "external_lambda" {
  name = "external-lambda-policy"
  role = aws_iam_role.external_lambda.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "dynamodb:GetItem",
          "dynamodb:PutItem",
          "dynamodb:UpdateItem",
          "dynamodb:Query",
          "dynamodb:Scan",
          "dynamodb:BatchGetItem",
          "dynamodb:ConditionCheckItem"
        ]
        Resource = [
          aws_dynamodb_table.external_users.arn,
          "${aws_dynamodb_table.external_users.arn}/index/*"
        ]
      },
      {
        Effect = "Allow"
        Action = [
          "cognito-idp:AdminGetUser",
          "cognito-idp:AdminCreateUser",
          "cognito-idp:AdminSetUserPassword",
          "cognito-idp:AdminUpdateUserAttributes",
          "cognito-idp:SignUp",
          "cognito-idp:InitiateAuth",
          "cognito-idp:AdminInitiateAuth",
          "cognito-idp:GetUser",
          "cognito-idp:AdminConfirmSignUp",
          "cognito-idp:ListUsers"
        ]
        Resource = [aws_cognito_user_pool.external.arn]
      }
    ]
  })
}

# -----------------------------------------------------------------------------
# Lambda - External Service (single handler with path routing)
# -----------------------------------------------------------------------------
data "archive_file" "external_service" {
  type        = "zip"
  source_dir  = "${path.module}/../services/external-service"
  output_path = "${path.module}/build/external-service.zip"
  excludes    = ["__pycache__", "*.pyc", ".pytest_cache", "tests", "*.zip"]
}

resource "aws_lambda_function" "external_service" {
  filename         = data.archive_file.external_service.output_path
  function_name    = "${var.project_name}-external-service"
  role             = aws_iam_role.external_lambda.arn
  handler          = "handler.lambda_handler"
  source_code_hash = data.archive_file.external_service.output_base64sha256
  runtime          = "python3.12"
  timeout          = 30

  environment {
    variables = {
      USER_POOL_ID        = aws_cognito_user_pool.external.id
      CLIENT_ID           = aws_cognito_user_pool_client.external.id
      EXTERNAL_USERS_TABLE = aws_dynamodb_table.external_users.name
      COMPANY_LIST_API_URL = var.company_list_api_url
    }
  }

  tags = var.tags
}

# -----------------------------------------------------------------------------
# API Gateway HTTP API (or REST) for External Service
# -----------------------------------------------------------------------------
resource "aws_apigatewayv2_api" "external" {
  name          = "${var.project_name}-external-api"
  protocol_type = "HTTP"
  cors_configuration {
  allow_headers = ["content-type", "x-amz-date", "authorization", "x-api-key"]
  allow_methods = ["*"]
  allow_origins = ["*"] # This allows localhost:5173 to talk to AWS
}
  tags = var.tags
}

resource "aws_apigatewayv2_integration" "external" {
  api_id           = aws_apigatewayv2_api.external.id
  integration_type  = "AWS_PROXY"
  integration_uri   = aws_lambda_function.external_service.invoke_arn
  payload_format_version = "2.0"
}

resource "aws_apigatewayv2_route" "external_any" {
  api_id    = aws_apigatewayv2_api.external.id
  route_key = "ANY /{proxy+}"
  target    = "integrations/${aws_apigatewayv2_integration.external.id}"
}

resource "aws_apigatewayv2_route" "external_root" {
  api_id    = aws_apigatewayv2_api.external.id
  route_key = "ANY /"
  target    = "integrations/${aws_apigatewayv2_integration.external.id}"
}

resource "aws_apigatewayv2_stage" "default" {
  api_id      = aws_apigatewayv2_api.external.id
  name        = "$default"
  auto_deploy = true
}

resource "aws_lambda_permission" "api_gw" {
  statement_id  = "AllowAPIGatewayInvoke"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.external_service.function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_apigatewayv2_api.external.execution_arn}/*/*"
}
