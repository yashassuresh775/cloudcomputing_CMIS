output "cognito_user_pool_id" {
  description = "Cognito User Pool ID for external auth"
  value       = aws_cognito_user_pool.external.id
}

output "cognito_client_id" {
  description = "Cognito App Client ID"
  value       = aws_cognito_user_pool_client.external.id
  sensitive   = false
}

output "external_users_table_name" {
  description = "DynamoDB table name for external users"
  value       = aws_dynamodb_table.external_users.name
}

output "api_gateway_url" {
  description = "External API base URL"
  value       = "${aws_apigatewayv2_api.external.api_endpoint}"
}

output "api_invoke_url" {
  description = "Full API invoke URL (with stage)"
  value       = "${aws_apigatewayv2_api.external.api_endpoint}"
}

output "students_table_name" {
  description = "DynamoDB table name for students (graduation scan)"
  value       = aws_dynamodb_table.students.name
}
