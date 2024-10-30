import json
import logging

logger = logging.getLogger()
logger.setLevel(logging.INFO)

def main(event, context):
    logger.info('Event: %s', event)
    
    try:
        http_method = event['httpMethod']
        
        if http_method == 'GET':
            return handle_get(event)
        elif http_method == 'POST':
            return handle_post(event)
        else:
            return create_response(400, {'error': 'Unsupported HTTP method'})
            
    except Exception as e:
        logger.error('Error: %s', e)
        return create_response(500, {'error': 'Internal server error'})

def handle_get(event):
    # Handle GET request
    query_parameters = event.get('queryStringParameters', {})
    
    return create_response(200, {
        'message': 'GET request successful',
        'parameters': query_parameters
    })

def handle_post(event):
    # Handle POST request
    try:
        body = json.loads(event.get('body', '{}'))
    except json.JSONDecodeError:
        return create_response(400, {'error': 'Invalid JSON body'})
    
    return create_response(200, {
        'message': 'POST request successful',
        'body': body
    })

def create_response(status_code, body):


Create an `app.py` file:

```python
#!/usr/bin/env python3
from aws_cdk import App
from lambda_api_stack import LambdaApiStack

app = App()
LambdaApiStack(app, "LambdaApiStack")
app.synth()
