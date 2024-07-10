"""
This Lambda function generates a credential report, determines which access keys are older than 
a specified number of days, and deletes those keys. It then sends an SNS message to a specified
topic with the keys that were deleted. If no keys were determined to be older than the specified
number of days, the SNS message will indicate that the function was successful but no keys were
deleted.

The following environment variables are required:
1.) MAX_NUMBER_OF_DAYS - The maximum number of days before an access key should be rotated
2.) SNS_TOPIC_ARN - The ARN of the SNS topic to publish the message to

Additionally, the function needs the following permissions:

iam:GenerateCredentialReport
iam:GetCredentialReport
iam:ListAccessKeys
iam:DeleteAccessKey
sns:Publish
logs:CreateLogGroup
logs:CreateLogStream
logs:PutLogEvents

This function is intended to be triggered by a CloudWatch Event Rule on a schedule.

"""

import json
import os
import time
import datetime
import csv
import io
import boto3


iam = boto3.client('iam')
sns = boto3.client('sns')


def get_credential_report():
    report_ready = False

    # Get credential report if ready, otherwise generate a new report and then get
    while not report_ready:
        try:
            response = iam.get_credential_report()
            content = response['Content'].decode('utf-8')
            report_ready = True

        except iam.exceptions.CredentialReportNotReadyException: 
            print("Waiting for credential report to generate...")
            time.sleep(2)

        except (iam.exceptions.CredentialReportNotPresentException, iam.exceptions.CredentialReportExpiredException):
            print("Generating credential report...")
            response = iam.generate_credential_report()
            time.sleep(2)

    # Separate the keys from the user credentials
    keys, *user_credentials = csv.reader(io.StringIO(content))

    # Create a dictionary of each user's credentials
    credentials = {}
    full_credential_report = []
    for user in user_credentials:
        key_index = 0
        for key in keys:
            credentials[key] = user[key_index]
            key_index += 1

        full_credential_report.append(credentials.copy())
    
    return full_credential_report


def determine_keys_to_delete(full_credential_report, max_number_of_days):
    current_date = datetime.datetime.now(datetime.timezone.utc)
    all_keys_to_delete = []
    for credential in full_credential_report:
        
        try:
            access_key_1_last_rotated = datetime.datetime.fromisoformat(credential['access_key_1_last_rotated'])
            number_of_days_string = (str(access_key_1_last_rotated - current_date).split(',')[0])
            number_of_days_int = int(number_of_days_string.strip('-').split(' ')[0])

            if number_of_days_int > max_number_of_days:
                access_key_id_1 = iam.list_access_keys(UserName=credential['user'])['AccessKeyMetadata'][0]['AccessKeyId']
                key_to_delete = {"KeyID" : access_key_id_1,
                                "User" : credential['user'],
                                "KeyAge" : number_of_days_int}
                
                all_keys_to_delete.append(key_to_delete)
                
            else:
                pass

        except ValueError:
            pass

        try:
            access_key_2_last_rotated = datetime.datetime.fromisoformat(credential['access_key_2_last_rotated'])
            number_of_days_string = (str(access_key_2_last_rotated - current_date).split(',')[0])
            number_of_days_int = int(number_of_days_string.strip('-').split(' ')[0])

            if number_of_days_int > max_number_of_days:
                access_key_id_2 = iam.list_access_keys(UserName=credential['user'])['AccessKeyMetadata'][1]['AccessKeyId']
                key_to_delete = {"KeyID" : access_key_id_2,
                                "User" : credential['user'],
                                "KeyAge" : number_of_days_int}
                all_keys_to_delete.append(key_to_delete)
            else:
                pass

        except ValueError:
            pass

    return all_keys_to_delete


def delete_access_keys(all_keys_to_delete, max_number_of_days):
    if all_keys_to_delete:
        try:
        # This actually deletes the keys. Do not uncomment until code is implemented in Lambda function
            # for key in all_keys_to_delete:
            #     iam.delete_access_key(UserName=key['User'], AccessKeyId=key['KeyID'])

            sns_message = (f"The following access keys were older than {max_number_of_days} days and have been deleted:\n" 
                        f"{json.dumps(all_keys_to_delete, indent=2)}")
                
        except iam.exceptions.ServiceFailureException:
            sns_message = (f"You have keys that are older than {max_number_of_days} days, but there was an error deleting them. Please check the logs.")
    else:
        sns_message = (f"The Delete_Old_Access_Keys Lambda function ran successfully, but no keys were detected that were older than {max_number_of_days} days.\n"
                        f"\nNo Access Keys were deleted.")

    return sns_message

def send_sns_message(sns_topic_arn, sns_message):
    print(sns_message)
    sns.publish(TopicArn=sns_topic_arn,
                Message= sns_message,
                )
    
   
def lambda_handler(event, context):
    max_number_of_days_str = os.environ.get('MAX_NUMBER_OF_DAYS', 180)
    max_number_of_days = int(max_number_of_days_str)
    sns_topic_arn = os.environ.get('SNS_TOPIC_ARN')

    full_credential_report = get_credential_report()
    all_keys_to_delete = determine_keys_to_delete(full_credential_report, max_number_of_days)
    sns_message = delete_access_keys(all_keys_to_delete, max_number_of_days)
    send_sns_message(sns_topic_arn, sns_message)
    response = {
        'statusCode': 200,
        'snsTopic' : sns_topic_arn,
        'snsMessage': sns_message
    }
    print(response)