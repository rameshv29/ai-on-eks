import boto3
import logging
import os
import json
from strands import Agent

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Explicitly set region and endpoint URL from environment variables
aws_region = os.environ.get('AWS_REGION', 'us-west-2')
endpoint_url = os.environ.get('AWS_ENDPOINT_URL')

logger.info(f"Connecting to DynamoDB with region={aws_region}, endpoint_url={endpoint_url}")

ddb = boto3.resource('dynamodb', 
                    region_name=aws_region,
                    endpoint_url=endpoint_url)
agent_state_table = ddb.Table(os.environ['DYNAMODB_AGENT_STATE_TABLE_NAME'])

def save(user_id: str, agent: Agent):
    logger.info(f"saving citymapper agent state for user.id={user_id}")
    messages = agent.messages
    agent_state_table.put_item(Item={
        'user_id': user_id,
        'state': json.dumps(messages)
    })


def restore(user_id: str):
    logger.info(f"restoring citymapper agent state for user.id={user_id}")
    ddb_response = agent_state_table.get_item(Key={'user_id': user_id})
    item = ddb_response.get('Item')
    if item:
        messages=json.loads(item['state'])
    else:
        messages = []

    print(f"messages={messages}")
    return messages