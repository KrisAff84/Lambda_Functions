"""
Sends a custom metric to CloudWatch when the authorizer function is invoked.
The value for metric_authorization can be set to any values you want. For this
example it could be either 'Approvals' or 'Denials', which would count the number
of times the LambdaAuthorizer function was invoked and either approved or denied
a request. A full implementation of this function within the context of the other
authorization logic can be found in authorizer_custom_header_path_blacklisted_ips.py. 
"""
import boto3
import datetime

session = boto3.Session(profile_name='kris84')
aws_s3_region_name = 'us-east-1'

def lambda_handler(event, context):
    cloudwatch = boto3.client('cloudwatch')
    metric_authorization = 'Approvals'
    timezone = datetime.timezone.utc
    current_utc_time = datetime.datetime.now(tz=timezone)

    cloudwatch.put_metric_data(
            Namespace='Custom/LambdaAuthorizer',
            MetricData=[
                {
                    'MetricName': metric_authorization,
                    'Dimensions': [
                        {
                            'Name': 'AuthorizerFunction',
                            'Value': 'lyria-authorizer'
                        }
                    ],
                    'Timestamp': current_utc_time,
                    'Value': 1,
                    'Unit': 'Count'
                }
            ]
        )