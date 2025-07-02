# Dynamodb module variables

variable "weather_prefix" {
  description = "The name of dynamodb table for weather agent"
  type        = string
  default     = "weather-agent"
}

variable "cluster_name" {
  description = "EKS cluster name"
  type        = string
  default     = "agentic-ai-on-eks"
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

variable "tags" {
  description = "Tags to apply to resources"
  type        = map(string)
  default     = {}
}
