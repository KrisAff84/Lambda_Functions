

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