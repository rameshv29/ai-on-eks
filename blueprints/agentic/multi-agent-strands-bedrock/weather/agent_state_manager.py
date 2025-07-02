import boto3
import logging
import os
import json
from strands import Agent

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


ddb = boto3.resource('dynamodb')
agent_state_table = ddb.Table(os.environ['DYNAMODB_AGENT_STATE_TABLE_NAME'])

def save(user_id: str, agent: Agent):
    logger.info(f"saving agent state for user.id={user_id}")
    messages = agent.messages
    agent_state_table.put_item(Item={
        'user_id': user_id,
        'state': json.dumps(messages)
    })


def restore(user_id: str):
    logger.info(f"restoring agent state for user.id={user_id}")
    ddb_response = agent_state_table.get_item(Key={'user_id': user_id})
    item = ddb_response.get('Item')
    if item:
        messages=json.loads(item['state'])
    else:
        messages = []

    print(f"messages={messages}")
    return messages
