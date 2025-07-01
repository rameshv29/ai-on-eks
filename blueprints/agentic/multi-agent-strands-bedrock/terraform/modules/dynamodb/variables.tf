# Dynamodb module variables

variable "weather_prefix" {
  description = "The name of dynamodb table for weather agent"
  type        = string
  default     = "agents-on-eks-weather"
}
