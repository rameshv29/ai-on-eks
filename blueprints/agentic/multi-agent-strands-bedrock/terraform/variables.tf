variable "name" {
  description = "EKS Cluster name"
  type        = string
  default     = "agentic-ai-on-eks"
}

variable "region" {
  description = "Region for the EKS cluster"
  type        = string
  default     = "us-west-2"
}

variable "tags" {
  description = "Tags to apply to resources"
  type        = map(string)
  default     = {}
}

variable "weather_prefix" {
  description = "The name of dynamodb table for weather agent"
  type        = string
  default     = "weather-agent"
}

variable "weather_namespace" {
  description = "Kubernetes namespace"
  type        = string
  default     = "weather-agent"
}

variable "weather_service_account" {
  description = "Kubernetes service account name"
  type        = string
  default     = "weather-agent"
}

variable "bedrock_model_id" {
  description = "Model ID for the agents"
  type        = string
  default     = "us.anthropic.claude-3-7-sonnet-20250219-v1:0"
}

# Cognito module variables

variable "cognito_additional_redirect_uri" {
  description = "Additional allowed redirect URI after authorization"
  type        = list(string)
  default     = []
}

variable "cognito_additional_logout_uri" {
  description = "Additional allowed logout URIs"
  type        = list(string)
  default     = []
}

variable "cognito_prefix_user_pool" {
  description = "Prefix for user pool"
  type        = string
  default     = "agents-on-eks"
}

variable "weather_web_agent_endpoint" {
  description = "Agent endpoint"
  type        = string
  default     = "http://localhost:3000/prompt"
}
