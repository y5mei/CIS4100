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
from tabulate import tabulate
from pathlib import Path

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

##########################################################################################
# Main Entrance of this program
##########################################################################################
# detected the current running environment
running_platform = platform.system()
print(running_platform)
# detect the current local working directory
local_working_directory = os.getcwd()
print(local_working_directory)
global s3_working_directory
global s3_bucket_name
s3_working_directory = ""
s3_bucket_name = ""


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
    global s3_working_directory
    global s3_bucket_name

    if args != "":
        print(colored("S5 Error: No Token should follow the cwf command name.", "red"))
        return UNSUCCESS

    if s3_bucket_name == "":
        print("/")
    else:
        result = s3_bucket_name + ":" + s3_working_directory
        if result[-1] == "/":
            result = result[:-1]
        print(result)
    return SUCCESS


# need to finish this!!!!
#
#
#
#
#
def __check_folder_avaliable__(bucket_name, file_path_name) -> bool:
    global s3_working_directory
    global s3_bucket_name

    bucket_name = s3_bucket_name
    file_path_name = s3_working_directory
    try:
        bucket = resource.Bucket(s3_bucket_name)
        for object_summary in bucket.objects.filter(Prefix=file_path_name):
            return True
        return False
    except BaseException as e:
        print(colored(e, "yellow"))


def do_change_folder(args: str) -> int:
    global s3_working_directory
    global s3_bucket_name
    temp_s3_working_directory = s3_working_directory
    temp_s3_bucket_name = s3_bucket_name
    print("currently working with " + temp_s3_bucket_name + "  :  " + temp_s3_working_directory)

    if args == "" or args == ".":
        return SUCCESS

    if args == "/":
        s3_bucket_name = ""
        s3_working_directory = ""
        return SUCCESS

    if ":" in args:  # this is a absolute path
        s3_bucket_name = args.split(":", 1)[0]
        s3_working_directory = args.split(":", 1)[1]
        # make sure this is a slash at the end
        if s3_working_directory != "" and s3_working_directory[-1] != "/":
            s3_working_directory += "/"
    if ":" not in args:
        if s3_bucket_name == "":  # in this case, this is a absolute path, lead to a bucket
            s3_bucket_name = args
            s3_working_directory = ""
        else:  # in this case, this is a relative path, lead to a folder inside of the current bucket
            s3_working_directory += args
            if args[-1] != "/":
                s3_working_directory += "/"
            # print ("now the raw cwf is " +s3_working_directory )

            # print all the keys in the bucket:
            # bucket = resource.Bucket(s3_bucket_name)
            # for item in bucket.objects.all():
            #     print(item)
    #########################################################################
    # This is the difficult part, we need to resolve the relative path here
    #########################################################################
    folder_list = s3_working_directory.split("/")
    result = []

    for i in folder_list:
        if i == ".":
            pass
        if i != "..":
            result.append(i)
        if i == ".." and result:
            result.pop()

    s3_working_directory = "/".join(result)
    # print("now the cooked cwf is " + s3_working_directory)
    # Finally, try to check if this folder is valid or not, if not valid, change back to the pre folder
    try:
        if s3_working_directory != "":
            fullPath = s3_bucket_name + ": " + s3_working_directory
            errorMessage = "\nThe input folder " + fullPath + " does not exist!"
            item = resource.Object(s3_bucket_name, s3_working_directory).get()
            return SUCCESS
        else:
            fullPath = s3_bucket_name
            errorMessage = "\nThe input bucket " + fullPath + " does not exist!"
            bucket = resource.meta.client.head_bucket(Bucket=s3_bucket_name)
            return SUCCESS

    except BaseException as e:
        print(colored("S5 Error: Can not change folder due to invalid input: " + s3_working_directory + errorMessage,
                      "red"))
        print(e)
        s3_working_directory = temp_s3_working_directory
        s3_bucket_name = temp_s3_bucket_name
        return UNSUCCESS


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


def do_delete_object(args: str) -> int:
    global s3_working_directory
    global s3_bucket_name

    # If no argument, report as error
    if not args:
        print(colored("cdelete command need a full or indirect pathname of object as argument ", "red"))
        return UNSUCCESS

    # need to support delete on full path and indirect pathname
    arglist = args.split(":", 1)

    if (len(arglist) == 1):
        # this is a relative path, try to delete the object
        my_bucket_name = s3_bucket_name
        my_object_name = s3_working_directory + arglist[0]
        my_object_name = __reslove_a_path(my_object_name)

    elif len(arglist) == 2:  # in the format of bucket:objectname
        # this is a absolute path
        my_bucket_name = arglist[0]
        my_object_name = arglist[1]
        my_object_name = __reslove_a_path(my_object_name)
    else:
        print(colored("S5 Error: ", args, " is not a valid command.", "red"))
        return UNSUCCESS

    # check if the object is present, and then check if the folder is empty, if both true, then delete it
    try:
        obj = resource.Object(my_bucket_name, my_object_name)
        # client code handle the no such key exception, this is the trick to check if a object is present.
        client.get_object(Bucket=my_bucket_name, Key=my_object_name)
        # also need to check if this object is empty!!!
        bucket = resource.Bucket(my_bucket_name)
        object_list = []
        for object_summary in bucket.objects.filter(Prefix=my_object_name):
            print(object_summary)
            object_list.append(object_summary)
            if len(object_list) > 1:
                print(colored(
                    "S5 Error: The folder " + my_object_name + " is not empty so we can not delete it.",
                    "red"))
                return UNSUCCESS
        # obj.delete()
        print(colored(" I can delete the folder" + my_object_name, "green"))
        return SUCCESS
    except client.exceptions.NoSuchKey as e:
        print(colored(
            "S5 Error: The object " + my_object_name + " does not exist. \nPlease see the error message below:",
            "red"))
        print(e)
        return UNSUCCESS
    except BaseException as e:
        print(colored("S5 Error: Cannot perform delete! Please see the error message below:", "red"))
        print(e)
        return UNSUCCESS


def do_delete_bucket(args: str) -> int:
    try:
        response = client.delete_bucket(Bucket=args, )
        print(colored("Bucket: " + args + ", has been successfully deleted.", "green"))
        return SUCCESS
    except BaseException as e:
        print(colored("Can not delete the bucket, please see the exception message below:", "red"))
        print(e)
        return UNSUCCESS


# for a bucketName and a pathName, print all the Absolute keys for objects
def __get_all_keys(bucketName, pathName):
    result = []
    # if inside of a folder
    if bucketName and pathName:
        try:
            bucket = resource.Bucket(bucketName)
            result = []

            for object_summary in bucket.objects.filter(Prefix=pathName):
                myStrkey = object_summary.key[len(pathName):]
                num_of_slash = myStrkey.count('/')
                # only print the items with Zero slash or 1 slash at the end
                if num_of_slash == 0 or (num_of_slash == 1 and myStrkey[-1] == "/"):
                    if myStrkey: result.append(object_summary.key)
            return result
        except BaseException as e:
            print(e)
            return ["UNSUCCESS"]
    # if inside of a bucket:
    if bucketName:
        bucket = resource.Bucket(bucketName)
        try:
            result = []
            for file in bucket.objects.all():
                myStrkey = file.key
                num_of_slash = myStrkey.count('/')
                # only print the items with Zero slash or 1 slash at the end
                if num_of_slash == 0 or (num_of_slash == 1 and myStrkey[-1] == "/"):
                    if myStrkey: result.append(myStrkey)
            return result
        except BaseException as e:
            print(e)
            return ["UNSUCCESS"]

    return result


# return true if a bucketname and pathname is valid to visit
def __validate_a_path(bucketName, pathName) -> bool:
    if bucketName == "":
        print("No bucket name defined!")
        return False
    if pathName == "":
        try:
            fullPath = bucketName
            errorMessage = "\nThe input bucket " + fullPath + " does not exist!"
            bucket = resource.meta.client.head_bucket(Bucket=bucketName)
            return True
        except BaseException as e:
            print(
                colored("S5 Error: Bucket Name invalid: " + bucketName + errorMessage,
                        "red"))
            print(e)
            return False
        # validate bucketName
    else:
        try:  # validate the full path
            fullPath = bucketName + ": " + pathName
            errorMessage = "\nThe input folder " + fullPath + " does not exist!"
            item = resource.Object(bucketName, pathName).get()
            return True
        except BaseException as e:
            print(
                colored("S5 Error: Object Not Exist: " + fullPath + errorMessage,
                        "red"))
            print(e)
            return False


# return true if a bucketname or a pathname is present
def __present_of_a_path(bucketName, pathName) -> bool:
    if bucketName == "":
        # print("No bucket name defined!")
        return False
    if pathName == "":
        try:
            fullPath = bucketName
            errorMessage = "\nThe input bucket " + fullPath + " does not exist!"
            bucket = resource.meta.client.head_bucket(Bucket=bucketName)
            return True
        except BaseException as e:
            # print(
            #     colored("S5 Error: Bucket Name invalid: " + bucketName + errorMessage,
            #             "red"))
            # print(e)
            return False
        # validate bucketName
    else:
        try:  # validate the full path
            fullPath = bucketName + ": " + pathName
            errorMessage = "\nThe input folder " + fullPath + " does not exist!"
            item = resource.Object(bucketName, pathName).get()
            return True
        except BaseException as e:
            # print(
            #     colored("S5 Error: Object Not Exist: " + fullPath + errorMessage,
            #             "red"))
            # print(e)
            return False


# resolve a relative path, and if needed, we add a ending slash at the end of the output path
# note that in S3, all the folder object is ending with / but file object does not ending with /
def __reslove_a_path(args: str, addEndingSlash=True):
    if args == "":
        return args

    # remove the leading and ending spaces
    args = args.strip()

    # add a slash at the end if addEndingSlash is True
    if addEndingSlash and args[-1] != "/":
        args += "/"

    folder_list = args.split("/")
    result = []

    # handle the cases where ".." is in the path
    for i in folder_list:
        if i == ".":
            pass
        if i != "..":
            result.append(i)
        if i == ".." and result:
            result.pop()

    args = "/".join(result)
    return args


def do_test(args: str):
    global s3_working_directory
    global s3_bucket_name
    # l = __get_all_keys("cis4010-ymei","")
    # print(l)
    # print ("=================")
    # bucketName = "cis4010-rwiskail"
    # bucket = resource.Bucket(bucketName)
    # for item in bucket.objects.all():
    #     print(item)

    pathName = ""
    bucketName = "cis4010b01"
    mykeys = __get_all_keys(bucketName, pathName)
    print(mykeys)
    data = []

    # for k in mykeys:
    #     try:
    #         # object = resource.Object(bucketName, "../").get()
    #         # print(object)
    #         response = client.get_object(Bucket=bucketName, Key="../")
    #         print(response)
    #     except BaseException as e:
    #         print(e)
    #     d = [str(object["ContentLength"]), k[len(s3_working_directory):], str(object["LastModified"])]
    #     data.append(d)
    # if data: print(tabulate(data, headers=["Size", "Name", "Last_Modified_Date"]))


def do_list(args: str):
    # remove the leading and ending spaces
    args = args.strip()

    if not args:
        return do_short_list("")
    arg_list = args.split(" ")
    if (len(args) >= 2 and args[:2] == "-l"):  # if args == "-l bucket:folderbalabala"
        args = args[2:].strip()
        return do_long_list(args)
    else:  # if args = "bucket:folderbalabala
        args = args
        return do_short_list(args)


def do_long_list(args: str):
    global s3_working_directory
    global s3_bucket_name
    # if we need to print long ls at the root
    if args == "/":
        response = client.list_buckets()["Buckets"]
        for i, r in enumerate(response):
            print(i + 1, ": ", r["Name"])
        return SUCCESS

    # if we are going to printout the long ls at the current folder:
    if args == "":
        if s3_bucket_name == "" and s3_working_directory == "":
            return do_short_list("/")
        mykeys = __get_all_keys(s3_bucket_name, s3_working_directory)
        if len(mykeys) == 1 and mykeys[0] == "UNSUCCESS":
            print(colored("S5 Error: can not find information for the dir:" + s3_working_directory, "red"))
            return UNSUCCESS
        else:
            data = []
            for k in mykeys:
                if k == "../":
                    pass  # this is a bug in AWS
                else:
                    object = resource.Object(s3_bucket_name, k).get()
                    d = [str(object["ContentLength"]), k[len(s3_working_directory):], str(object["LastModified"])]
                    data.append(d)
            if data: print(tabulate(data, headers=["Size", "Name", "Last_Modified_Date"]))
            return SUCCESS

    # if user specified a bucket name with (or without a path)
    if args:
        arg_list = args.split(":", 1)
        bucketName = arg_list[0]
        if len(arg_list) == 1:
            pathName = ""
        else:
            pathName = arg_list[1]
            # transform the pathNama here:
        pathName = __reslove_a_path(pathName)

        if not __validate_a_path(bucketName, pathName):  # if the path is not valid, return false
            return UNSUCCESS

        mykeys = __get_all_keys(bucketName, pathName)
        if len(mykeys) == 1 and mykeys[0] == "UNSUCCESS":
            print(colored("S5 Error: can not find information for the dir:" + pathName, "red"))
            return UNSUCCESS
        else:
            data = []
            for k in mykeys:
                if k == "../":
                    pass  # this is a bug in AWS
                else:
                    object = resource.Object(bucketName, k).get()
                    d = [str(object["ContentLength"]), k[len(pathName):], str(object["LastModified"])]
                    data.append(d)
            if data: print(tabulate(data, headers=["Size", "Name", "Last_Modified_Date"]))
            return SUCCESS


def do_short_list(args: str):
    global s3_working_directory
    global s3_bucket_name

    # list all the buckets at the root of the S3
    if args == "/":
        response = client.list_buckets()["Buckets"]
        for i, r in enumerate(response):
            print(i + 1, ": ", r["Name"])
        return SUCCESS
    # list all the files under the current local directory
    # this is wrong, I should list all the object in the current s3 directroy
    if args == "":
        if s3_bucket_name == "" and s3_working_directory == "":
            return do_short_list("/")
        # if currently in a folder, print the content of the folder
        if s3_working_directory and s3_bucket_name:
            try:
                bucket = resource.Bucket(s3_bucket_name)
                result = []

                for object_summary in bucket.objects.filter(Prefix=s3_working_directory):
                    myStrkey = object_summary.key[len(s3_working_directory):]
                    num_of_slash = myStrkey.count('/')
                    # only print the items with Zero slash or 1 slash at the end
                    if num_of_slash == 0 or (num_of_slash == 1 and myStrkey[-1] == "/"):
                        if myStrkey: result.append(myStrkey)
                if result: print("    ".join(result))
                return SUCCESS
            except BaseException as e:
                print(e)
                return UNSUCCESS

        # if currently in a bucket, print the content of the bucket
        if s3_bucket_name:
            bucket = resource.Bucket(s3_bucket_name)
            try:
                result = []
                for file in bucket.objects.all():
                    myStrkey = file.key
                    num_of_slash = myStrkey.count('/')
                    # only print the items with Zero slash or 1 slash at the end
                    if num_of_slash == 0 or (num_of_slash == 1 and myStrkey[-1] == "/"):
                        if myStrkey: result.append(myStrkey)
                if result: print("    ".join(result))
                return SUCCESS
            except BaseException as e:
                print(e)
                return UNSUCCESS
    # if user specified a bucket name with (or without a path)
    if args:
        arg_list = args.split(":", 1)
        bucketName = arg_list[0]
        if len(arg_list) == 1:
            pathName = ""
        else:
            pathName = arg_list[1]
            # transform the pathNama here:
        pathName = __reslove_a_path(pathName)

        if not __validate_a_path(bucketName, pathName):  # if the path is not valid, return false
            return UNSUCCESS

        if pathName and bucketName:
            try:
                bucket = resource.Bucket(bucketName)
                result = []

                for object_summary in bucket.objects.filter(Prefix=pathName):
                    myStrkey = object_summary.key[len(pathName):]
                    num_of_slash = myStrkey.count('/')
                    # only print the items with Zero slash or 1 slash at the end
                    if num_of_slash == 0 or (num_of_slash == 1 and myStrkey[-1] == "/"):
                        if myStrkey: result.append(myStrkey)
                if result: print("    ".join(result))
                return SUCCESS
            except BaseException as e:
                print(e)
                return UNSUCCESS

            # if currently in a bucket, print the content of the bucket
        if bucketName:
            bucket = resource.Bucket(bucketName)
            try:
                result = []
                for file in bucket.objects.all():
                    myStrkey = file.key
                    num_of_slash = myStrkey.count('/')
                    # only print the items with Zero slash or 1 slash at the end
                    if num_of_slash == 0 or (num_of_slash == 1 and myStrkey[-1] == "/"):
                        if myStrkey: result.append(myStrkey)
                if result: print("    ".join(result))
                return SUCCESS
            except BaseException as e:
                print(e)
                return UNSUCCESS


def do_create_folder(args: str):
    global s3_working_directory
    global s3_bucket_name

    if args == "":
        print(colored("S5 Error: The args for this command can not be null!", "red"))
        return UNSUCCESS
    # if args is not none, we have to seperate full path or relatrive path:
    args_list = args.split(":", 1)

    if len(args_list) > 1:  # if this is the full path with bucket name
        bucketName = args_list[0]
        pathName = args_list[1]

        # put a slash at the end of the path name and validate a path
        pathName = __reslove_a_path(pathName)

        # pathName should not be none
        if pathName == "":
            print(colored("S5 Error: Can not create folder due to Folder Name is Null!", "red"))
            return UNSUCCESS

        # the bucket should present
        if not __present_of_a_path(bucketName, ""):
            print(colored("S5 Error: Can not create folder due to bucket not exist!", "red"))
            return UNSUCCESS
        # the folder should not be present
        if __present_of_a_path(bucketName, pathName):
            print(colored("S5 Error: Can not create folder due to File Already Exists!", "red"))
            return UNSUCCESS
        # everything good, we are going to create a object
        try:
            # actually, I can not directly put the object here, I have to do this folder by folder
            pathList = pathName.split("/")
            __create_folder_helper(bucketName, pathList)
            # response = client.put_object(Bucket =bucketName, Key =  pathName)
            return SUCCESS
        except BaseException as e:
            print(colored("S5 Error: Can not create folder.", "red"))
            print(e)
            return UNSUCCESS

    else:  # if this is just the folder path without bucket name
        bucketName = s3_bucket_name
        # put a slash at the end of the path name and validate a path
        pathName = s3_working_directory + args_list[0]
        pathName = __reslove_a_path(pathName)

        # pathName should not be none
        if pathName == "":
            print(colored("S5 Error: Can not create folder due to Folder Name is Null!", "red"))
            return UNSUCCESS
            # the bucket should present
        if not __present_of_a_path(bucketName, ""):
            print(colored("S5 Error: Can not create folder due to bucket not exist!", "red"))
            return UNSUCCESS
            # the folder should not be present
        if __present_of_a_path(bucketName, pathName):
            print(colored("S5 Error: Can not create folder due to File Already Exists!", "red"))
            return UNSUCCESS
            # everything good, we are going to create a object
        try:
            # actually, I can not directly put the object here, I have to do this folder by folder
            pathList = pathName.split("/")
            __create_folder_helper(bucketName, pathList)
            # response = client.put_object(Bucket=bucketName, Key=pathName)
            return SUCCESS
        except BaseException as e:
            print(colored("S5 Error: Can not create folder.", "red"))
            print(e)
            return UNSUCCESS


# recursively create intermediate folders along the path of a list of path names
def __create_folder_helper(bucketName, pathNameList):
    base = ""
    for name in pathNameList:
        name = name + "/"
        base += name
        if __present_of_a_path(bucketName, base):
            pass
        else:
            try:
                client.put_object(Bucket=bucketName, Key=base)
            except:
                raise RuntimeError(" In Valid PathName List" + str(pathNameList))


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
    "cf": do_change_folder,
    "cdelete": do_delete_object,
    "t": do_test,
    "create_folder": do_create_folder,
}

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
        except BaseException as e:
            print("S5 Error: Please see the error message below:")
            print(colored(e, "red"))
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
