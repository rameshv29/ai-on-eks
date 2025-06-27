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
