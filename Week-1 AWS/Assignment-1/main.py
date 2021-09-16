import boto3
import os
import platform
import sys
import cmd
# let's use Amazon Simple Service Storage
# Client VS Resource: https://www.learnaws.org/2021/02/24/boto3-resource-client/
# Quick Start Guide: https://boto3.amazonaws.com/v1/documentation/api/latest/guide/quickstart.html


# The location of the credentials stores:
# On Windows: C:\Users\username\.aws\credentials
# On Mac/Linux: ~/.aws/credentials
# To change the location of the shared config and credentials files:
# https://docs.aws.amazon.com/sdkref/latest/guide/file-location.html
# On Windows:
# C:\> setx AWS_CONFIG_FILE c:\some\file\path\on\the\system\config-file-name
# C:\> setx AWS_SHARED_CREDENTIALS_FILE c:\some\other\file\path\on\the\system\credentials-file-name
# setx AWS_SHARED_CREDENTIALS_FILE C:\Users\Zhuzhu\S5-S3config
# On Linux/Max:
# $ export AWS_CONFIG_FILE=/some/file/path/on/the/system/config-file-name
# $ export AWS_SHARED_CREDENTIALS_FILE=/some/other/file/path/on/the/system/credentials-file-name

# use a session to connect to AWS service
# https://stackoverflow.com/questions/45981950/how-to-specify-credentials-when-connecting-to-boto3-s3
# session = boto3.Session(aws_access_key_id="AKIA6OYXELHFFSCVWP5H",
#                         aws_secret_access_key="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")
# s3 = session.client('s3')
# response = s3.list_buckets()
# print(response)
# # Output the bucket names
# print("Existing buckets:")
# for bucket in response['Buckets']:
#     print(f'{bucket["Name"]}')

# s3 = session.resource('s3')
#
# bucket = s3.Bucket(name = "cis4010-ymei")
#
# for file in bucket.objects.all():
#     print(file.key)

ON_CONNECTION_SUCCESS_TEXT = "Welcome to the AWS S3 Storage Shell (S5) \nYou are now connected to your S3 storage"
ON_CONNECTION_FAIL_TEXT = "Welcome to the AWS S3 Storage Shell (S5)\nYou are could not be connected to your S3 storage\nPlease review procedures for authenticating your account on AWS S3"
running_platform = platform.system()
print(running_platform)


try:
    s3 = boto3.client('s3')
    print(ON_CONNECTION_SUCCESS_TEXT)

except:
    print(ON_CONNECTION_FAIL_TEXT)
    sys.exit(0)


# Listen to a command input
value = ""
# while value != "exit" or value != "quit":
while True:

    value = input("S5> ")
    # if input is exit or quit, then quit the program
    if value == "exit" or value == "quit":
        print("Exiting the S5 Shell Program Now...")
        sys.exit(0)

    print(f'You entered {value}')



