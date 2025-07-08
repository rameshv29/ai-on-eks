#!/bin/sh

if ! [ -x "$(command -v jq)" ]; then
  echo 'jq not found, you must install it first. https://jqlang.org/download/' >&2
  exit 1
fi

if ! [ -x "$(command -v aws)" ]; then
  echo 'AWS CLI not found, you must install it first. https://docs.aws.amazon.com/cli' >&2
  exit 1
fi

WEATHER_DST_FILE_NAME=${WEATHER_DST_FILE_NAME:-../weather/.env}
echo "> Injecting values into $WEATHER_DST_FILE_NAME"
echo "" > $WEATHER_DST_FILE_NAME

echo "> Parsing Terraform outputs"
TERRAFORM_OUTPUTS_MAP=$(terraform output --json outputs_map)
#echo $TERRAFORM_OUTPUTS_MAP
COGNITO_JWKS_URL=$(echo "$TERRAFORM_OUTPUTS_MAP" | jq -r ".cognito_jwks_url")
BEDROCK_MODEL_ID=$(terraform output -json bedrock_model_id)
DYNAMODB_AGENT_STATE_TABLE_NAME=$(terraform output -json weather_agent_table_name)
echo "COGNITO_JWKS_URL=$COGNITO_JWKS_URL"
echo "BEDROCK_MODEL_ID=$BEDROCK_MODEL_ID"
echo "DYNAMODB_AGENT_STATE_TABLE_NAME=$DYNAMODB_AGENT_STATE_TABLE_NAME"

echo "COGNITO_JWKS_URL=\"$COGNITO_JWKS_URL\"" >> $WEATHER_DST_FILE_NAME
echo "BEDROCK_MODEL_ID=$BEDROCK_MODEL_ID" >> $WEATHER_DST_FILE_NAME
echo "DYNAMODB_AGENT_STATE_TABLE_NAME=$DYNAMODB_AGENT_STATE_TABLE_NAME" >> $WEATHER_DST_FILE_NAME

echo "> Done"
