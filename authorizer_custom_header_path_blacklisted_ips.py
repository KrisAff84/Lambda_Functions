"""
Lambda authorizer that performs various checks to determine if a request is authorized.
1.) Checks for custom header - required
2.) Checks for an allowed path - specifies '/' as default
3.) Checks for any blacklisted IPs - specifies '[]' as default

Additionally, this function publishes a custom metric to CloudWatch based on the result of the authorizerion
check. The metric will count the number of times the LambdaAuthorizer either approves or denies a request.
"""

import json
from datetime import datetime, timezone
import os
import boto3

cloudwatch = boto3.client('cloudwatch')

def lambda_handler(event, context):
    # Log the full event for debugging
    print("Full event received:", json.dumps(event))

    headers = event.get('headers', {})
    path = event.get('rawPath', '')
    sourceIp = event.get("requestContext", {}).get("http", {}).get("sourceIp")
    current_utc_time = datetime.now(tz=timezone.utc)

    # Define the allowed path and custom header
    allowed_paths = json.loads(os.environ.get('ALLOWED_PATHS', '["/"]'))
    custom_header = os.environ.get('CUSTOM_HEADER')

    # Define a list of blacklisted IPs
    blacklisted_ips = json.loads(os.environ.get('BLACKLISTED_IPS', '[]'))

    # CloudWatch metric variables
    metric_namespace = os.environ.get('CW_METRIC_NAMESPACE')
    dimension_name = os.environ.get('CW_DIMENSION_NAME')
    dimension_value = os.environ.get('CW_DIMENSION_VALUE') 

    # Check for the custom header, allowed path, and if source IP is not blacklisted
    if headers.get('x-custom-header') == custom_header and path in allowed_paths and sourceIp not in blacklisted_ips:
        isAuthorized = {
            "isAuthorized": True,
        }
        metric_authorization = "Approvals"
    else:
        isAuthorized = {
            "isAuthorized": False,
        }
        metric_authorization = "Denials"
        
    cloudwatch.put_metric_data(
        Namespace= metric_namespace,
        MetricData=[
            {
                'MetricName': metric_authorization,
                'Dimensions': [
                    {
                        'Name': dimension_name,
                        'Value': dimension_value
                    }
                ],
                'Timestamp': current_utc_time,
                'Value': 1,
                'Unit': 'Count'
            }
        ]
    )
    
    return isAuthorized