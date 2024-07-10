import json

def lambda_handler(event, context):
    
    # Log the full event for debugging
    print("Full event received:", json.dumps(event))

    headers = event.get('headers', {})
    
    if headers.get('x-custom-header') == '<custom_header_value':
        return {
            "isAuthorized": True,
        }
    else:
        return {
            "isAuthorized": False,
        }