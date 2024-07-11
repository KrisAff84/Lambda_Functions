"""
This is a simple example of an API Gateway custom authorizer Lambda function.
The function demonstrates how to parse the headers of an incoming request and
check for a specific custom header value.
"""

def lambda_handler(event, context):

    headers = event.get('headers', {})
    
    if headers.get('x-custom-header') == '<custom_header_value':
        return {
            "isAuthorized": True,
        }
    else:
        return {
            "isAuthorized": False,
        }