from pynput import keyboard
from enum import IntEnum
import ReadCredentials
import boto3
import sys
import os
import platform
import re
import botocore
from colorama import init
from termcolor import colored
import requests

# use Colorama to make Termcolor work on Windows too
# ref： https://pypi.org/project/colorama/
init()

from os import path
from pynput.keyboard import Key, Controller

ON_CONNECTION_SUCCESS_TEXT = "Welcome to the AWS S3 Storage Shell (S5) \nYou are now connected to your S3 storage"
ON_CONNECTION_FAIL_TEXT = "Welcome to the AWS S3 Storage Shell (S5)\nYou could not be connected to your S3 " \
                          "storage\nPlease review procedures for authenticating your account on AWS S3 "
SUCCESS = 0
UNSUCCESS = 1

# read the credentials as a dictionary
d = ReadCredentials.buildCredentialDict()


# check if the S5 shell can connect to the internet
def check_internet_connection():
    url = "http://www.amazon.com"
    timeout = 3
    try:
        request = requests.get(url, timeout=timeout)
        return True
    except (requests.ConnectionError, requests.Timeout) as exception:
        return False


# check if the S5 terminal has the correct credentials as well as internet connections
def check_credentials() -> bool:
    if not check_internet_connection():
        print(colored("S5 Error: You do not have Internet Connection. Please check your internet settings.", "red"))
        return False
    try:
        test1_client = boto3.client(
            's3',
            aws_access_key_id=d["aws_access_key_id"],
            aws_secret_access_key=d["aws_secret_access_key"],
        )

        response = test1_client.list_buckets()
        return True
    except:
        print(
            colored("You are disconnected with AWS, please check your credentials. ", 'red'))
        return False


if not check_internet_connection():
    print("=========================================================================")
    print(colored(ON_CONNECTION_FAIL_TEXT, "red"))
    print("=========================================================================")
    sys.exit(0)
try:
    # if no internet connection, exit the program
    # connect to AWS via boto3
    client = boto3.client(
        's3',
        aws_access_key_id=d["aws_access_key_id"],
        aws_secret_access_key=d["aws_secret_access_key"],
    )

    resource = boto3.resource('s3',
                              aws_access_key_id=d["aws_access_key_id"],
                              aws_secret_access_key=d["aws_secret_access_key"], )
    # List all of the possible waiters for both clients
    response = client.list_buckets()
    # print(response)
    print("==========================================")
    print(colored(ON_CONNECTION_SUCCESS_TEXT, "green"))
    print("==========================================")

except BaseException as e:
    print(colored(ON_CONNECTION_FAIL_TEXT, "red"))
    print(e)
    sys.exit(0)


# How to use python to do function dispatch
# https://softwareengineering.stackexchange.com/questions/182093/why-store-a-function-inside-a-python-dictionary/182095

def do_lc_copy(args: str) -> int:
    """lc_copy <full or relative pathname of local file><bucket name>:<full pathname of S3 object> """
    # seperate the argument by both space and :
    argsList = re.split(" |:", args)

    # 0. check if the parameter list has 3 variables
    if len(argsList) != 3:
        print("S5 Error: The input is missing some arguments, please double check your input")
        print("The input should be in the format of: lc_copy <full or relative pathname of local file><bucket "
              "name>:<full pathname of S3 object>")
        return UNSUCCESS
    else:
        local_file_path = argsList[0]
        bucket_name = argsList[1]
        pathname3_s3_obj = argsList[2]

    # 1. check if the local file present
    try:
        # path.exists(argsList[0])
        open(argsList[0], "r")
    except:
        print("S5 Error: Invalid path name for the local file: ", argsList[0])
        return UNSUCCESS

    # 2. check if the bucket is available
    try:
        resource.meta.client.head_bucket(Bucket=bucket_name)
        # if does not have permission to get access to this bucket
    except botocore.exceptions.ClientError as e:
        print(e)
        error_code = e.response['Error']['Code']
        if error_code == "404":
            print("S5 Error: Not able to get access to Bucket: ", bucket_name, "\nPlease check your Permission "
                                                                               "to get access to this Bucket ")
        # print(error_code)
        return UNSUCCESS
        # if does not have a valid bucket name, i.e. has # or $ in the bucket name
    except botocore.exceptions.ParamValidationError as e:
        print(e)
        return UNSUCCESS
        # if no internet connection
    except botocore.exceptions.EndpointConnectionError as e:
        print("S5 Error: You do not have Internet connection or your Internet connection is too slow.")
        print(e)
        return UNSUCCESS

    # 3. check if we can successfully upload the file to AWS
    try:
        response = client.upload_file(local_file_path, bucket_name, pathname3_s3_obj)
        return SUCCESS
    except RuntimeError:
        print("Not able to upload the file:")
        return UNSUCCESS
    #
    return SUCCESS


def do_current_work_folder(args: str) -> int:
    if args != "":
        print(colored("S5 Error: No Token should follow the cwf command name.", "red"))
        return UNSUCCESS
    print(s3_working_directory)
    return SUCCESS

# need to finish this!!!!
#
#
#
#
#
def do_change_directory(args: str) -> int:
    print(args)
    b = resource.Bucket("cis4010-ymei")
    for file in b.objects.all():
        print(file.key)
    print("the bucket is : ", b)
    return SUCCESS

def do_create_bucket(args: str) -> int:
    s3_location = {
        'LocationConstraint': 'us-east-2'}
    try:
        bucket = resource.create_bucket(Bucket=args, CreateBucketConfiguration=s3_location)
        return SUCCESS
    except BaseException as e:
        print(colored("Can not create bucket! Please see the exception message below:", "red"))
        print(e)
        return UNSUCCESS
    # I do not know why client does not work!!!
    # Maybe I need to do something with location constraint object???
    # try:
    #     s3_location ={
    #     'LocationConstraint': 'af-south-1'}
    #     response = client.create_bucket(Bucket=args, CreateBucketConfiguration=s3_location)
    #     return SUCCESS
    # except BaseException as e:
    #     print(e)
    #     print(colored("S5 Error: Can not create the bucket: " + args, "red"))
    #     return UNSUCCESS


def do_delete_bucket(args: str) -> int:
    try:
        response = client.delete_bucket(Bucket=args, )
        print(colored("Bucket: " + args + ", has been successfully deleted.", "green"))
        return SUCCESS
    except BaseException as e:
        print(colored("Can not delete the bucket, please see the exception message below:", "red"))
        print(e)
        return UNSUCCESS


def do_list(input=""):
    # list all the buckets at the root of the S3
    if input == "/":
        response = client.list_buckets()["Buckets"]
        for i, r in enumerate(response):
            print(i + 1, ": ", r["Name"])
    # list all the files under the current local directory
    if input == "" or input == "-l":
        if running_platform == "Windows":
            if input == "":
                myinput = "/b"
            if input == "-l":
                myinput = "/x /l"
            os.system("dir " + myinput)
        else:
            os.system("ls" + input)


def do_quit(*args):
    print("Exiting the S5 Shell Program Now...")
    print("Thank you for using S5, See you next time!")
    sys.exit(0)


dispatch = {
    "lc_copy": do_lc_copy,
    "quit": do_quit,
    "exit": do_quit,
    "list": do_list,
    "cb": do_create_bucket,
    "create_bucket": do_create_bucket,
    "db": do_delete_bucket,
    "delete_bucket": do_delete_bucket,
    "q": do_quit,
    "cwf": do_current_work_folder,
    "cf": do_change_directory,
}

# detected the current running environment
running_platform = platform.system()
print(running_platform)
# detect the current local working directory
local_working_directory = os.getcwd()
s3_working_directory = "/"
print(local_working_directory)

while True:

    user_input = input("S5> ")

    # check if AWS connection is still available, if not available, send a message to the user,
    if not check_internet_connection():
        print(colored("No Internet Connection, exit S5 shell Now. \nPlease check your Internet Setting.", "red"))
        sys.exit(1)

    # Requirment 3 1) if the input command is not a required function,
    # call the os.sys() method to use the system shell to handle it
    if len(user_input.split(" ", 1)) > 1:  # if input contains argument
        command, arg = user_input.split(" ", 1)[0], user_input.split(" ", 1)[1]
    else:
        command, arg = user_input.split(" ", 1)[0], ""  # if input does not contains argument, argument is ""

    if command not in set(dispatch.keys()):
        # if the command is not a controlled method, pass it directly to the system shell
        try:
            if os.system(user_input) != 0:
                raise Exception("this command does not exist")
        except:
            print("S5 shell had some problem to run this command:")
    # if we have a def of the command already, then dispatch it from the dict.
    else:
        # if it is available, then we dispatch the command
        status_val = dispatch[command](arg)

# response = client.list_buckets()
# print(response)
# # Output the bucket names
# print("Existing buckets:")
# for bucket in response['Buckets']:
#     print(f'{bucket["Name"]}')


## Questions for TA's

# 1) should I worry about what if the user changed the credential files while S5 is running?
# 2) If the user suddenly lost internet connection, or admin deleted the user account while S5 is running, should I just break from the main while loop to let user to restart the S5 shell? Or should I keep the S5 Running, so that local command such as echo, cd can still be supported?
