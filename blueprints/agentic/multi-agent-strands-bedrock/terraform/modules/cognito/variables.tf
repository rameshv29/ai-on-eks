# Cognito module variables

variable "additional_redirect_uri" {
  description = "Additional allowed redirect URI after authorization"
  type        = list(string)
  default     = []
}

variable "additional_logout_uri" {
  description = "Additional allowed logout URIs"
  type        = list(string)
  default     = []
}

variable "prefix_user_pool" {
  description = "Prefix for user pool"
  type        = string
  default     = "agents-on-eks"
}

variable "agent_endpoint" {
  description = "Agent endpoint"
  type        = string
  default     = "http://localhost:3001/prompt"
}
