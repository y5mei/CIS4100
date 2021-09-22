import cmd, sys
from turtle import *
import platform
import boto3

# session = boto3.Session(aws_access_key_id="AKIA6OYXELHFFSCVWP5H",
#                         aws_secret_access_key="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")
# s3 = session.resource('s3')
#
# bucket = s3.Bucket(name = "cis4010-ymei")
#
# for file in bucket.objects.all():
#     print(file.key)


# https://www.youtube.com/watch?v=qsPZL-0OIJg
client = boto3.client(
    's3',
    aws_access_key_id="AKIA6OYXELHFFSCVWP5H",
    aws_secret_access_key="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",
)

def upload_file(file_name, bucket, object_name=None, args=None):
    if object_name is None:
        object_name = file_name

    response = client.upload_file(file_name, bucket, object_name, ExtraArgs=args)
    print(response)


response = client.list_buckets()["Buckets"]
for i, r in enumerate(response):
    print (i+1,": ",r["Name"])
# print(response)

# # upload_file('main.py', 'cis4010-ymei')
#
# import glob
#
#  # * is from the current directory, / is the root directory
# files = glob.glob('*')
# print(files)
#
# s3 = boto3.resource(
#     's3',
#     aws_access_key_id="AKIA6OYXELHFFSCVWP5H",
#     aws_secret_access_key="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",
# )
#
# print (list(s3.buckets.all()))
# print(client.list_buckets())
#
# bucket = s3.Bucket("cis4010-ymei")
# files = list(bucket.objects.all())
# print(files[0].key)
def rE(myint):
    try:
        b = myint%2
        print(b)
        return 0
    except:
        print(str(myint))
        return 100

    finally:
        return 10010012



print(rE("pig"))