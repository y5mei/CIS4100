from pynput import keyboard

import ReadCredentials
import boto3
import sys
import os
import platform
import re
from pynput.keyboard import Key, Controller

ON_CONNECTION_SUCCESS_TEXT = "Welcome to the AWS S3 Storage Shell (S5) \nYou are now connected to your S3 storage"
ON_CONNECTION_FAIL_TEXT = "Welcome to the AWS S3 Storage Shell (S5)\nYou are could not be connected to your S3 " \
                          "storage\nPlease review procedures for authenticating your account on AWS S3 "

# read the credentials as a dictionary
d = ReadCredentials.buildCredentialDict()
# detected the current running environment
running_platform = platform.system()
print(running_platform)

try:
    # connect to AWS via boto3
    client = boto3.client(
        's3',
        aws_access_key_id=d["aws_access_key_id"],
        aws_secret_access_key=d["aws_secret_access_key"],
    )
    print(ON_CONNECTION_SUCCESS_TEXT)

except RuntimeError:
    print(ON_CONNECTION_FAIL_TEXT)
    sys.exit(0)


# How to use python to do function dispatch
# https://softwareengineering.stackexchange.com/questions/182093/why-store-a-function-inside-a-python-dictionary/182095

def do_lc_copy(args:str):
    argsList = re.split(" |:",args)
    if len(argsList)!=3:
        print("The argument list is not 3")
        return 1
    else:
        local_file_name,bucket_name,full_path_of_s3_object = argsList
    if full_path_of_s3_object is None:
        full_path_of_s3_object = local_file_name
    try:
        response = client.upload_file(local_file_name, bucket_name, full_path_of_s3_object)
    except RuntimeError:
        print("Not able to upload the file:")

    return 0


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
}

# Listen to a command input
value = ""
customized_function_list = ["exit", "quit"]
# while value != "exit" or value != "quit":
while True:

    user_input = input("S5> ")
    # if the input command is not a required function, call the os.sys() method to use the system shell to handle it
    if len(user_input.split(" ", 1)) > 1:
        command, arg = user_input.split(" ", 1)[0], user_input.split(" ", 1)[1]
    else:
        command, arg = user_input.split(" ", 1)[0], ""

    if command not in set(dispatch.keys()):
        # if the command is not a controlled method, pass it directly to the system shell
        try:
            if os.system(user_input) != 0:
                raise Exception("this command does not exist")
        except:
            print("S5 shell had some problem to run this command:")
            # keyboard.press(Key.enter)
            # keyboard.release(Key.enter)
    # if we have a def of the command already, then dispatch it from the dict.
    else:
        dispatch[command](arg)

# response = client.list_buckets()
# print(response)
# # Output the bucket names
# print("Existing buckets:")
# for bucket in response['Buckets']:
#     print(f'{bucket["Name"]}')
