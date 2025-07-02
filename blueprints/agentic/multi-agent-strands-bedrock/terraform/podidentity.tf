module "weather_agent_pod_identity" {
  source  = "terraform-aws-modules/eks-pod-identity/aws"
  version = "~> 1.0"

  ## IAM role / policy
  name                 = "${local.name}-bedrock-role"
  attach_custom_policy = true
  policy_statements = [
    {
      sid = "BedrockAccess"
      actions = [
        "bedrock:InvokeModel",
        "bedrock:InvokeModelWithResponseStream"
      ]
      resources = ["*"]
    },
    {
      sid = "DynamoDBAccess"
      actions = [
        "dynamodb:GetItem",
        "dynamodb:PutItem"
      ]
      resources = ["arn:aws:dynamodb:*:*:table/*weather*"]
    }
  ]

  ## Pod-identity association
  associations = {
    weather-agent = {
      cluster_name    = module.eks.cluster_name
      namespace       = "weather-agent"
      service_account = "weather-agent"
    }
  }

  tags = local.tags
}
