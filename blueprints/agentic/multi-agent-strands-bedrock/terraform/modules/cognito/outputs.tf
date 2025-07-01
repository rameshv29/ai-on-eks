output "cognito_user_pool_id" {
  description = "The ID of the Cognito User Pool"
  value       = aws_cognito_user_pool.user_pool.id
}

output "cognito_well_known_url" {
  description = "The well-known OpenID configuration URL for the Cognito User Pool"
  value       = local.cognito_well_known_url
}

output "cognito_sign_in_url" {
  description = "The sign-in URL for the Cognito User Pool"
  value       = local.cognito_sign_in_url
}

output "cognito_logout_url" {
  description = "The logout URL for the Cognito User Pool"
  value       = local.cognito_logout_url
}

output "cognito_client_id" {
  description = "The ID of the Cognito User Pool Client"
  value       = aws_cognito_user_pool_client.user_pool_client.id
}

output "cognito_client_secret" {
  description = "The client secret of the Cognito User Pool Client"
  value       = aws_cognito_user_pool_client.user_pool_client.client_secret
  sensitive   = true
}

output "cognito_jwks_url" {
  description = "The JWKS URL for the Cognito User Pool"
  value       = local.cognito_jwks_url
}

output "outputs_map" {
  description = "Map of all Cognito and agent configuration outputs"
  value = tomap({
    cognito_userpool_id : aws_cognito_user_pool.user_pool.id,
    cognito_client_id : aws_cognito_user_pool_client.user_pool_client.id,
    cognito_client_secret : aws_cognito_user_pool_client.user_pool_client.client_secret,
    cognito_jwks_url : local.cognito_jwks_url,
    cognito_sign_in_url : local.cognito_sign_in_url,
    cognito_logout_url : local.cognito_logout_url,
    cognito_well_known_url : local.cognito_well_known_url,
    agent_endpoint : var.agent_endpoint
  })
  sensitive = true
}
