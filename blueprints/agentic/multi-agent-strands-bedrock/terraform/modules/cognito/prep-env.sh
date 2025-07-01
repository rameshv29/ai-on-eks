#!/bin/sh

if ! [ -x "$(command -v jq)" ]; then
  echo 'jq not found, you must install it first. https://jqlang.org/download/' >&2
  exit 1
fi

if ! [ -x "$(command -v aws)" ]; then
  echo 'AWS CLI not found, you must install it first. https://docs.aws.amazon.com/cli' >&2
  exit 1
fi

echo "> Parsing Terraform outputs"
TERRAFORM_OUTPUTS_MAP=$(terraform output --json outputs_map)
#echo $TERRAFORM_OUTPUTS_MAP
COGNITO_USER_POOL_ID=$(echo "$TERRAFORM_OUTPUTS_MAP" | jq -r ".cognito_userpool_id")
COGNITO_CLIENT_ID=$(echo "$TERRAFORM_OUTPUTS_MAP" | jq -r ".cognito_client_id")
COGNITO_CLIENT_SECRET=$(echo "$TERRAFORM_OUTPUTS_MAP" | jq -r ".cognito_client_secret")
COGNITO_SIGN_IN_URL=$(echo "$TERRAFORM_OUTPUTS_MAP" | jq -r ".cognito_sign_in_url")
COGNITO_LOGOUT_URL=$(echo "$TERRAFORM_OUTPUTS_MAP" | jq -r ".cognito_logout_url")
COGNITO_WELL_KNOWN_URL=$(echo "$TERRAFORM_OUTPUTS_MAP" | jq -r ".cognito_well_known_url")
COGNITO_JWKS_URL=$(echo "$TERRAFORM_OUTPUTS_MAP" | jq -r ".cognito_jwks_url")
AGENT_ENDPOINT_URL=$(echo "$TERRAFORM_OUTPUTS_MAP" | jq -r ".agent_endpoint")

echo "COGNITO_USER_POOL_ID=$COGNITO_USER_POOL_ID"
echo "COGNITO_CLIENT_ID=$COGNITO_CLIENT_ID"
echo "COGNITO_CLIENT_SECRET=${COGNITO_CLIENT_SECRET:0:3}....redacted..."
echo "COGNITO_SIGN_IN_URL=$COGNITO_SIGN_IN_URL"
echo "COGNITO_LOGOUT_URL=$COGNITO_LOGOUT_URL"
echo "COGNITO_WELL_KNOWN_URL=$COGNITO_WELL_KNOWN_URL"
echo "COGNITO_JWKS_URL=$COGNITO_JWKS_URL"
echo "AGENT_ENDPOINT_URL=$AGENT_ENDPOINT_URL"

echo "> Setting user passwords for Alice and Bob"
aws cognito-idp admin-set-user-password --user-pool-id $COGNITO_USER_POOL_ID --username Alice --password "Passw0rd@" --permanent
aws cognito-idp admin-set-user-password --user-pool-id $COGNITO_USER_POOL_ID --username Bob --password "Passw0rd@" --permanent


WEB_DST_FILE_NAME=${WEB_DST_FILE_NAME:-../../../weather/web/.env}
echo "> Injecting values into $WEB_DST_FILE_NAME"
echo "" > $WEB_DST_FILE_NAME
echo "COGNITO_CLIENT_ID=\"$COGNITO_CLIENT_ID\"" >> $WEB_DST_FILE_NAME
echo "COGNITO_CLIENT_SECRET=\"$COGNITO_CLIENT_SECRET\"" >> $WEB_DST_FILE_NAME
echo "COGNITO_SIGNIN_URL=\"$COGNITO_SIGN_IN_URL\"" >> $WEB_DST_FILE_NAME
echo "COGNITO_LOGOUT_URL=\"$COGNITO_LOGOUT_URL\"" >> $WEB_DST_FILE_NAME
echo "COGNITO_WELL_KNOWN_URL=\"$COGNITO_WELL_KNOWN_URL\"" >> $WEB_DST_FILE_NAME
echo "COGNITO_JWKS_URL=\"$COGNITO_JWKS_URL\"" >> $WEB_DST_FILE_NAME
echo "AGENT_ENDPOINT_URL=\"$AGENT_ENDPOINT_URL\"" >> $WEB_DST_FILE_NAME

WEATHER_DST_FILE_NAME=${WEATHER_DST_FILE_NAME:-../../../weather/.env}
echo "> Injecting values into $WEATHER_DST_FILE_NAME"
echo "" >> $WEATHER_DST_FILE_NAME
echo "COGNITO_JWKS_URL=\"$COGNITO_JWKS_URL\"" >> $WEATHER_DST_FILE_NAME

echo "> Done"
