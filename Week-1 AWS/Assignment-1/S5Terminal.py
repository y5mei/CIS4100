from collections import deque
import ReadCredentials
import boto3
import sys
import os
import platform
import botocore
from colorama import init
from termcolor import colored
import requests
from tabulate import tabulate
from shlex import split as shlexsplit
from pathlib import Path

# detected the current running environment
running_platform = platform.system()
if running_platform !="Windows":
    import readline

# use Colorama to make Termcolor work on Windows too
# ref： https://pypi.org/project/colorama/
init()

# from os import path
# from pynput.keyboard import Key, Controller

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
    # print(e)
    sys.exit(0)

##########################################################################################
# Main Entrance of this program
##########################################################################################

# print(running_platform)
# detect the current local working directory
local_working_directory = os.getcwd()
# print(local_working_directory)
global s3_working_directory
global s3_bucket_name
s3_working_directory = ""
s3_bucket_name = ""


# How to use python to do function dispatch
# https://softwareengineering.stackexchange.com/questions/182093/why-store-a-function-inside-a-python-dictionary/182095

def do_lc_copy(args: str) -> int:
    """lc_copy <full or relative pathname of local file><bucket name>:<full pathname of S3 object> """
    # use shlex to handle the case if the user input has quotes
    shell_arg_list = shlexsplit(args)
    # print(shell_arg_list)

    if len(shell_arg_list) != 2:
        print(colored("lc_copy need two arguments: the local file path, and the bucketname:full_path_of_S3_object",
                      "red"))
        print(colored("but you are giving " + str(len(shell_arg_list)) + " arguments:", "red"))
        print(colored(shell_arg_list, "red"))
        return UNSUCCESS
    # print(shell_arg_list)

    # I am trying to save my old codes, so I have to use the argList interface, this is just a adapter
    # seperate the argument by both space and :
    argsList = []
    argsList.append(shell_arg_list[0])
    cloud_argsList = shell_arg_list[1].split(":", 1)

    for i in cloud_argsList:
        argsList.append(i)
    # print(argsList)
    # argsList = re.split(" |:", args)
    # 0. check if the parameter list has 3 variables
    if len(argsList) != 3 or argsList[-1] == "":
        print(colored("S5 Error: The input is missing some arguments, please double check your input", "red"))
        print(colored("The input should be in the format of: lc_copy <full or relative pathname of local file><bucket "
                      "name>:<full pathname of S3 object>", "red"))
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
        error_message = "S5 Error: Invalid path name for the local file: " + argsList[0]
        print(colored(error_message, "red"))
        return UNSUCCESS

    # 2. check if the bucket is available
    try:
        resource.meta.client.head_bucket(Bucket=bucket_name)
        # if does not have permission to get access to this bucket
    except botocore.exceptions.ClientError as e:
        print(e)
        error_code = e.response['Error']['Code']
        if error_code == "404" or error_code == "400":
            error_message = "S5 Error: Not able to get access to Bucket: " + bucket_name + "\nPlease check your " \
                                                                                           "Permission to get access " \
                                                                                           "to this Bucket "
            print(colored(error_message, "red"))
        # print(error_code)
        return UNSUCCESS
        # if does not have a valid bucket name, i.e. has # or $ in the bucket name
    except botocore.exceptions.ParamValidationError as e:
        print(colored("bucket" + bucket_name + " name is not available", "red"))
        print(e)
        return UNSUCCESS
        # if no internet connection
    except botocore.exceptions.EndpointConnectionError as e:
        print("S5 Error: You do not have Internet connection or your Internet connection is too slow.")
        print(e)
        return UNSUCCESS

    # 3. check if we can successfully upload the file to AWS
    try:
        # need to add a function to add sub-folders along the path
        # for the file name, check that there are no two slash together and not star from a slash

        if not __check_no_two_slash_together_and_not_start_with_slash__(pathname3_s3_obj):
            print(colored("S5 Error: The input: " + pathname3_s3_obj + " is illegal!", "red"))
            print(colored("The filepath should not start with '/' or have more than two '/' side by side.", "red"))
            return UNSUCCESS
        # resolve the path name first
        pathname3_s3_obj = __reslove_a_path(pathname3_s3_obj, False)
        if pathname3_s3_obj:
            pathname3_s3_obj_list = pathname3_s3_obj.split("/")

        if pathname3_s3_obj_list[-1] == "":  # 1/2/3/
            print(colored("S5 Error: destination file name is either empty or end with '/': ", "red"))
            print(colored(pathname3_s3_obj_list, "red"))
            return UNSUCCESS
        else:
            pathname3_s3_obj_list.pop()  # prepare the subfodler list for checking if they exist or not

        # need to check if all the sub folders are exist
        if not __validate_folder_helper(bucket_name, pathname3_s3_obj_list):
            badPath = bucket_name + ":" + "/".join(pathname3_s3_obj_list)
            print(colored("S5 Error: The input folder: " + badPath + "/ does not exist!", "red"))
            return UNSUCCESS

        # need to check if there is a that file already, we will stop copy the file if it is already there

        # the source must exist
        fromPathName = __reslove_a_path(pathname3_s3_obj, False)
        if __present_of_a_path(bucket_name, pathname3_s3_obj):
            print(colored("Unsuccessful lc_copy, destination file already exist, please give it another name!", "red"))
            return UNSUCCESS

        response = client.upload_file(local_file_path, bucket_name, pathname3_s3_obj)

        # # also need to create all the suborders associated with this object
        # __create_folder_helper(bucket_name, pathname3_s3_obj_list)

        return SUCCESS
    except BaseException as e:
        print(colored("Not able to upload the file:", "red"))
        print(e)
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
    # print("currently working with " + temp_s3_bucket_name + "  :  " + temp_s3_working_directory)
    # use the shlex to handle the user input for double quotes
    shell_arg_list = shlexsplit(args)
    args = "".join(shell_arg_list)

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


def do_delete_bucket(args: str) -> int:
    global s3_working_directory
    global s3_bucket_name
    # you can not delete the bucket you are currently in
    if args == s3_bucket_name:
        print(colored("Can not delete the bucket, please see the exception message below:", "red"))
        print(colored("You cannot delete the bucket that you are currently in, please ch_folder /, then repeat the "
                      "delete_bucket command", "red"))
        return UNSUCCESS
    try:
        response = client.delete_bucket(Bucket=args, )
        # print(colored("Bucket: " + args + ", has been successfully deleted.", "green"))
        return SUCCESS
    except BaseException as e:
        print(colored("Can not delete the bucket, please see the exception message below:", "red"))
        print(e)
        return UNSUCCESS

    # for the purpose of this assignement, let us assume there is no space in pathname


def do_copy_object(args: str) -> int:
    # will not work for object contains a ":" in its pathName
    global s3_working_directory
    global s3_bucket_name
    # fromPathName = ""
    # toPathName = ""
    # fromBucketName = ""
    # toBucketName = ""

    # If no argument, report as error
    if not args:
        print(colored("ccopy command need two full or indirect pathname as arguments ", "red"))
        return UNSUCCESS

    # need to support delete on full path and indirect pathname
    args = args.strip()
    arglist = __split_args__(args)  # use this helper function to handle the case if input has ""
    if len(arglist) != 2:
        print(colored("ccopy command need exactly two full or indirect pathname as arguments ", "red"))
        print(colored("But " + str(len(arglist)) + " is given:", "red"))
        print(colored(arglist, "red"))
        return UNSUCCESS

    # seperate two path an get the 4 names:
    fromPath = arglist[0]
    toPath = arglist[1]
    fromBucketName = ""
    toBucketName = ""
    fromPathName = ""
    toPathName = ""

    # print (fromPath)
    # print (toPath)
    if len(fromPath.split(":", 1)) == 1:  # if no bucket Name
        if not s3_bucket_name:
            print(colored("ccopy error: no 'source bucket' name defined", "red"))
            print(colored("Give the source a full path with bucketname or ch_folder to a bucket before ccopy", "red"))
            return UNSUCCESS
        fromBucketName = s3_bucket_name
        fromPathName = s3_working_directory + fromPath.split(":")[0]
    elif len(fromPath.split(":", 1)) == 2:  # if has bucket Name
        fromBucketName = fromPath.split(":", 1)[0]
        fromPathName = fromPath.split(":", 1)[1]
    else:
        mylist = fromPath.split(":", 1)
        print(colored("ccopy command need the correct source bucket name and file path name", "red"))
        print(colored("Give the source a full path with bucketname or ch_folder to a bucket before ccopy", "red"))
        print(colored(mylist, "red"))
        return UNSUCCESS

    if len(toPath.split(":", 1)) == 1:  # if no bucket Name
        if not s3_bucket_name:
            print(colored("ccopy error: no 'destination bucket' name defined", "red"))
            print(colored("Give the destination a full path with bucketname or ch_folder to a bucket before ccopy",
                          "red"))
            return UNSUCCESS
        toBucketName = s3_bucket_name
        toPathName = s3_working_directory + toPath.split(":", 1)[0]
    elif len(toPath.split(":", 1)) == 2:  # if has bucket Name
        toBucketName = toPath.split(":", 1)[0]
        toPathName = toPath.split(":", 1)[1]
    else:
        mylist = toPath.split(":", 1)
        print(colored("ccopy command need the correct destination bucket name and file path name", "red"))
        print(colored("Give the destination a full path with bucketname or ch_folder to a bucket before ccopy", "red"))
        print(colored(mylist, "red"))
        return UNSUCCESS

    # now resolve all the file path names:
    # they can not be ended with "/" because they are not folders
    if fromPathName and fromPathName[-1] == "/":
        print(colored("ccopy of a Folder is not supported according to assignment-1 requirements, the source must be "
                      "a file object not a folder", "red"))
        return UNSUCCESS
    if toPathName and toPathName[-1] == "/":
        print(colored("ccopy to a Folder is not supported according to assignment-1 requirements, you need to give "
                      "destination object a name", "red"))
        return UNSUCCESS

    # the from path and the to path must have no two slash together
    # print(fromPathName)
    # print(toPathName)
    if not __check_no_two_slash_together_and_not_start_with_slash__(fromPathName):
        print(colored("ccopy error, source file format error: " + fromPathName, "red"))
        return UNSUCCESS
    if not __check_no_two_slash_together_and_not_start_with_slash__(toPathName):
        print(colored("ccopy error, destination file format error: " + toPathName, "red"))
        return UNSUCCESS

    # the source must exist
    fromPathName = __reslove_a_path(fromPathName, False)
    toPathName = __reslove_a_path(toPathName, False)

    if not fromPathName:
        print(colored("ccopy error, you have to provide the name of the source file to copy from", "red"))
        return UNSUCCESS

    if not __present_of_a_path(fromBucketName, fromPathName):
        print(colored("ccopy error, source file does not exist", "red"))
        return UNSUCCESS

    ###############################################################################
    ## need to add a function here to make sure all the subfolders are avaliable!!!
    ################################################################################

    # suppore I only copy file objects, so pathName will be like
    # a/b/c/filea
    # a/fileb

    try:
        if toPathName:
            toPathNameList = toPathName.split("/")
            if toPathNameList:
                toPathNameList.pop()  # remove the file object name, only keep the path
            else:
                toPathNameList = []

            if not __validate_folder_helper(toBucketName, toPathNameList):
                print(colored("S5 Error: Can not copy due to destination file path invalid", "red"))
                badPath = toBucketName+": "
                badPath += "/".join(toPathNameList)
                print(colored("This PATH does not exist: " + badPath, "red"))
                return UNSUCCESS
    except BaseException as e:
        print(colored("Can not make copy", "red"))

    if not toPathName:
        print(colored("ccopy error, you have to give a name to the destination file", "red"))
        return UNSUCCESS

    # and the destination must not exist
    if __present_of_a_path(toBucketName, toPathName):
        print(colored("ccopy error, destination file already exist", "red"))
        return UNSUCCESS

    ################# up to here, I have 2 valid bucket name and 2 valid pathname####################
    return do_copy_object_need_a_warpper(fromBucketName, fromPathName, toBucketName, toPathName)


def do_copy_object_need_a_warpper(fromBucketName, fromPathName, toBucketName, toPathName):
    # I have to assume the two inputs are valid and not null
    # I have to also assume that both of them are full path including bucketName
    copy_source = {
        'Bucket': fromBucketName,
        'Key': fromPathName
    }

    try:
        resource.meta.client.copy(copy_source, toBucketName, toPathName)
        # or you can also use just the resource to copy item
        # bucket = resource.Bucket(toBucketName)
        # bucket.copy(copy_source, toPathName)
        return SUCCESS
    except BaseException as e:
        print(colored("Can not perform the copy operation, please see the error message below:", "red"))
        print(e)
        return UNSUCCESS


# need to have a warpper to
# validate bucketName
# validate from PathName
# covert the pathName ot absolutelocalPathName
# make sure localPathName is empty


def do_copy_from_cloud_need_a_warpper(fromBucketName, fromPathName, absolutelocalPathName):
    try:
        client.download_file(fromBucketName, fromPathName, absolutelocalPathName)
        return SUCCESS
    except BaseException as e:
        print(colored("Can not perform the download operation, please see the error message below:", "red"))

        if "404" in str(e) or "400" in str(e):
            error_message = "S5 Error: Not able to get access to Bucket: " + fromBucketName + "\nPlease check your " \
                                                                                              "Permission to get access " \
                                                                                              "to this Bucket "
        else:
            error_message = str(e)
        print(colored(e, "red"))
        return UNSUCCESS


# make a pathName become a absolute pathName
# input localPathName can not be null
def __helper__make_a_full_path(localPathName):
    myPath = Path(localPathName).absolute()
    #     # print(myPath)
    return str(myPath)

# download a file from AWS to local directory
# I used a lot of helper function to handle error
# this is the last method I wrote, and this is the best method so far
def do_copy_cloud(args: str) -> bool:
    try:
        user_input = __helper__split_args__(args, expact_arguments_num=2) # make sure the input has two parts
        # print(user_input)
        my_bucket_name, my_object_path = __helper__validate_bucketName_and_Path__(user_input[0]) # get the S3 pathes
        my_local_object_path = __helper__make_a_full_path(user_input[1]) # get the local object path
        # print(my_bucket_name, my_object_path, my_local_object_path)
        __helper__check_if_a_loca_file_name_is_avaliable(my_local_object_path)
        return do_copy_from_cloud_need_a_warpper(my_bucket_name, my_object_path,my_local_object_path)
    except BaseException as e:
        print(colored(e,"red"))


def do_delete_object(args: str) -> int:
    # will not work for object contains a ":" in its pathName
    global s3_working_directory
    global s3_bucket_name

    # If no argument, report as error
    if not args:
        print(colored("cdelete command need a full or indirect pathname of object as argument ", "red"))
        return UNSUCCESS

    # if args is not none, we have to separate full path or relative path:
    # use the shlex to handle the user input for double quotes
    shell_arg_list = shlexsplit(args)
    args = "".join(shell_arg_list)

    # need to support delete on full path and indirect pathname
    arglist = args.split(":", 1)
    # print(arglist)

    if (len(arglist) == 1):
        # this is a relative path, try to delete the object
        my_bucket_name = s3_bucket_name
        my_object_name = s3_working_directory + arglist[0]
        # print(my_object_name)
        my_object_name = __reslove_a_path(my_object_name, my_object_name[-1] == "/")
        # print(my_object_name)

    elif len(arglist) == 2:  # in the format of bucket:objectname
        # this is a absolute path
        my_bucket_name = arglist[0]
        my_object_name = arglist[1]
        my_object_name = __reslove_a_path(my_object_name, my_object_name[-1] == "/")
    else:
        print(colored("S5 Error: ", args, " is not a valid command.", "red"))
        return UNSUCCESS
    # give a error message if bucket name is none or pathname is none:
    if not my_bucket_name:
        print(colored("S5 can not delete the file due to no bucket name is defined,\nYou need to be in a bucket or "
                      "give the full path including the bucket name!", "red"))
        return UNSUCCESS
    if not my_object_name:
        print(colored("S5 can not delete the file due to no path name is defined!", "red"))
        return UNSUCCESS

    # give user a warning that cdelete command will treat everything as a file object, if you want to delete
    # a directory, make sure you end the pathname with a forward slash
    if my_object_name and my_object_name[-1] != "/":
        print(colored("================ WARNING ================", "blue"))
        print(colored("S5 will treat all the pathname input without the ending '/' as the pathname of a FILE,\n" +
                      "If you are trying to delete a FOLDER, you MUST end the pathname input with a '/'", "blue"))
        print(colored("=========================================", "blue"))

    # check if the object is present, and then check if the folder is empty, if both true, then delete it
    try:
        # print(my_object_name)
        obj = resource.Object(my_bucket_name, my_object_name)
        # client code handle the no such key exception, this is the trick to check if a object is present.
        client.get_object(Bucket=my_bucket_name, Key=my_object_name)
        # also need to check if this object is empty!!!
        bucket = resource.Bucket(my_bucket_name)
        object_list = []

        # if it is a file object, not end with "/", we can delete it directly
        if my_object_name and my_object_name[-1] != "/":
            obj.delete()
            # print(colored(" The object " + my_object_name + " has been deleted", "green"))
            return SUCCESS

        # if it is a folder object, we need to check if there are any subfolders inside
        for object_summary in bucket.objects.filter(Prefix=my_object_name):
            # print(object_summary)
            object_list.append(object_summary)
            if len(object_list) > 1:
                print(colored(
                    "S5 Error: The folder " + my_object_name + " is not empty so we can not delete it.",
                    "red"))
                return UNSUCCESS

        # print(s3_working_directory)
        # print(obj.key)

        # remove the last portion of s3_working_directory if in the same directory:
        objkey = obj.key
        obj.delete()
        if objkey and s3_working_directory:
            if objkey == s3_working_directory:
                mylist = s3_working_directory.split("/")
                mylist.pop()  # remove the lasting empty ""
                if mylist:
                    mylist.pop()  # remove the last folder
                    if mylist:
                        s3_working_directory = "/".join(mylist) + "/"  # put the path structure back
                    else:
                        s3_working_directory = ""
        # print(colored(" The object " + my_object_name + " has been deleted", "green"))
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


# for a bucketName and a pathName, print all the Absolute keys for objects
# This is nor required by the assignment, I can delete this latter
def __print_all_keys_for_debug_(bucketName, pathName):
    result = []
    # if inside of a folder
    if bucketName and pathName:
        try:
            bucket = resource.Bucket(bucketName)
            result = []

            for object_summary in bucket.objects.filter(Prefix=pathName):
                myStrkey = object_summary.key[len(pathName):]  # get the key after the pathName
                num_of_slash = myStrkey.count('/')
                # only print the items with Zero slash or 1 slash at the end
                if num_of_slash == 0 or (num_of_slash == 1 and myStrkey[-1] == "/"):
                    if myStrkey: result.append(object_summary.key)
            for i in result:
                print(i)
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
            for i in result:
                print(i)
            return result
        except BaseException as e:
            print(e)
            return ["UNSUCCESS"]

    return result


# for a bucketName and a pathName, print all the Absolute keys for objects
# This is not required by the assignment, I can delete this latter
def __print_keys__(args):
    argsList = args.split(":", 1)
    if len(argsList) != 2:
        print("You have to use the full path including the bucket name")
        return UNSUCCESS
    # remove all the leading and ending spaces
    bucketName = argsList[0].strip()
    pathName = argsList[1].strip()
    pathName = __reslove_a_path(pathName)
    if not __validate_a_path(bucketName, pathName):
        return UNSUCCESS

    try:
        __print_all_keys_for_debug_(bucketName, pathName)
        return True
    except BaseException as e:
        print(e)
        return False


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
    # print (args)
    # handle the cases where ".." is in the path
    for i in folder_list:
        if i == ".":
            pass
        if i and i != "..":
            result.append(i)
        if i == ".." and result:
            result.pop()

    args = "/".join(result)

    if args and addEndingSlash and args[-1] != "/":
        args += "/"
    return args


# check if the input arguments has two // together
# return False for //a//
# return True for a/b/c
def __check_no_two_slash_together_and_not_start_with_slash__(args: str):
    if args:
        # remove the leading and ending spaces
        args = args.strip()
        # print(args)

        l = deque(list(args))
        slow = l.popleft()

        if slow == "/":
            return False  # return False if starting with "/"

        while l:
            fast = l.popleft()
            if slow == "/" and fast == "/":
                return False  # return false if two slash are together
            else:
                slow = fast

    return True


# this is a helper function to split the user input if the user put double quote with the input

def __split_args__(args: str):
    my_real_command = shlexsplit(args)
    return my_real_command


# this is a helper function to split the user input into expected parts.
# if the number of input did't math the expacted argument number, an error will be raise
# if any part of the input is empty, raise an error
def __helper__split_args__(args: str, expact_arguments_num=2):
    my_real_command = shlexsplit(args)
    # check to see if the num of argument meats the requirements
    if len(my_real_command) != expact_arguments_num:
        error_message = "This command is expecting " + str(expact_arguments_num) + " arguments, but " + str(
            len(my_real_command)) + " are given:\n"
        count = 1
        for i in my_real_command:
            error_message +=str(count)+":   "+str(i)+"\n"
            count +=1
        raise RuntimeError("S5 Error: " + error_message[:-1])

    # check to see if any of the argument is Null
    for i in my_real_command:
        if i=="":
            error_message = "Found an empty string as part of the input argument!"
            raise RuntimeError("S5 Error: " + error_message)
    return my_real_command

# this is a helper function that check if a bucket name is present and if the key to an object present
# if the name of bucket is not there, raise an error
# if the key of the object is not there, raise an error
# return a list [bucketName, Full_Path] if success
def __helper__validate_bucketName_and_Path__(args:str, justFileObject=True):
    global s3_working_directory
    global s3_bucket_name
    # print(args)
    # check if bucketname is there:
    if not args:
        error_message = "Need full or relative pathname of S3 file, but Null is given."
        raise RuntimeError("S5 Error: " + error_message)

    # makesure it is not start with "/"
    if args[1] == "/":
        error_message = "Wrong Path Name: "+args
        raise RuntimeError("S5 Error: " + error_message)

    # make sure the file object is not end with "/"
    if justFileObject and args[-1] == "/":
        error_message = "This command is expecting to work with a S3 File object, but the input is a Folder Object: " + args
        error_message = "\nMake sure you do not have '/' at the end for an file object"
        raise RuntimeError("S5 Error: " + error_message)


    # check if this is a relative path or a absolute path:
    argsList = args.split(":",1)
    if len(argsList) == 1: # if this is a relative path
        my_bucket_name = s3_bucket_name
        my_working_name = s3_working_directory+argsList[0]
    else:               # if this is a absolute path
        my_bucket_name =  argsList[0]
        my_working_name = argsList[1]

    # bucket Name should not be empty:
    if not my_bucket_name:
        error_message = "No valid bucket Name available, make sure you type in the correct bucket name or ch_folder to go inside a bucket"
        error_message += "\nThe input bucket name is: "+my_bucket_name +", the input file path name is  "+my_working_name+"."
        raise RuntimeError("S5 Error: " + error_message)

    # path to the file object should not be empty:
    if not my_working_name:
        error_message = "No valid object path name available."
        error_message += "\nThe input bucket name is: " + my_bucket_name + ", the input file path name is  " + my_working_name+"."
        raise RuntimeError("S5 Error: " + error_message)

    # make sure the bucket name present
    try:
        bucket = resource.meta.client.head_bucket(Bucket=my_bucket_name)
    except BaseException as e:
        error_message = "Bucket Name "+my_bucket_name+" Does Not exist. Detail Info See Below:\n"
        error_message += str(e)
        raise RuntimeError("S5 Error: " + error_message)

    # maker sure the file object is there
    # __present_of_a_path()
    pathName = __reslove_a_path(my_working_name, False)
    try:
        item = resource.Object(my_bucket_name, pathName).get()
    except BaseException as e:
        error_message = "Object Key "+pathName+" Does not exist. Detail Info See Below:\n"
        error_message += str(e)
        raise RuntimeError("S5 Error: " + error_message)

    return [my_bucket_name, pathName]

def __helper__check_if_a_loca_file_name_is_avaliable(args:str):
    if not args:
        error_message = "Need a valid local file path, but Null is given."
        raise RuntimeError("S5 Error: " + error_message)

    if os.path.isfile(args):
        error_message = "There is a file with this name already: "+args
        error_message += "\nPlease give it another name to avoid overwrite"
        raise RuntimeError("Unsuccessful cl_copy: " + error_message)

    return True

def do_test(args: str):
    global s3_working_directory
    global s3_bucket_name
    # test for shlex

    # print(__present_of_a_path("cis4010-ymei","a space/"))
    # mypath = __helper__make_a_full_path(args)
    # print(mypath)
    # return do_copy_from_cloud_need_a_warpper("cis4010b01", "main.py", mypath)

    if __present_of_a_path(toBucketName, toPathName):
        print(colored("ccopy error, destination file already exist", "red"))
        return UNSUCCESS




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

# This is a helper function that calculate the bin size
def __calculate_bucket_size__(mybucket):
    try:
        bucket = resource.Bucket(mybucket)
        mysize = 0
        for object in bucket.objects.all():
            mysize += object.size

        return str(mysize)

    except BaseException as e:
        error_message = str(e) +"\nS5 is going to display NA for the size of this bucket."
        # print(colored(error_message,"red"))
        # print("The BucketName: "+mybucket+" is not exist!")
        return "NA"

def __get_object_acl__(bucket_name, object_name):
    """Retrieve the access control list of an Amazon S3 object.
    :param bucket_name: string
    :param object_name: string
    :return: Dictionary defining the object's access control policy consisting
     of owner and grants. If error, return None.
    """
    # reference https://github.com/davidclin/scripts/blob/master/s3-get-object-acl.py

    # Retrieve the bucket ACL
    try:
        response = client.get_object_acl(Bucket=bucket_name, Key=object_name)
        print(response)
        return {'Owner': response['Owner'], 'Grants': response['Grants']}

    except BaseException as e:
        # AllAccessDisabled error == bucket not found
        # logging.error(e)
        response = {"Owner":{'ID': 'NA'} ,
                    "Grants": [{'Grantee': {'ID': 'NA', 'Type': 'NA'}, 'Permission': 'NA'}]
        }
        return {'Owner': response['Owner'], 'Grants': response['Grants']}
    # Return both the Owner and Grants keys
    # The Owner and Grants settings together form the Access Control Policy.
    # The Grants alone form the Access Control List.
    # name = client.describe_account(AccountId=response['Owner']["ID"]).get('Account').get('Name')


def __get_bucket_owner(mybucket):
    try:

        result = "NA"
        response = client.get_bucket_acl(
            Bucket=mybucket,
            # ExpectedBucketOwner='string'
        )

        return response['Owner']['ID']

    except BaseException as e:
        error_message = str(e)
        # print(colored(error_message,"red"))
        # print("The BucketName: "+mybucket+" is not exist!")
        return "NA"

def do_long_list(args: str):
    global s3_working_directory
    global s3_bucket_name
    # if we need to print long ls at the root
    if args == "/":

        response = client.list_buckets()["Buckets"]
        ownership = client.list_buckets()["Owner"]
        data = []

        warnings_message = "=========================================================================================="
        warnings_message += "\nThe owner of the buckets listed is: "+ownership["DisplayName"]+ "\nThe ID of the owner is: "+ownership["ID"]+"\n"
        warnings_message += "=========================================================================================="
        print(colored(warnings_message, "blue"))


        # print (ownership)
        # print(response)
        for i, r in enumerate(response):
            bucketName = str(r['Name'])
            # my_size = __calculate_bucket_size__(bucketName)
            # my_owner = ownership[i]["DisplayName"]
            # print(__calculate_bucket_size__())
            # d = [str(i), r['Name'], str(r['CreationDate']), my_size]
            # d = [str(i), r['Name'], str(r['CreationDate']), my_owner]
            d = [str(i), r['Name'], str(r['CreationDate'])]
            data.append(d)
            # print(i + 1, ": ", r)
        if data: print(tabulate(data, headers=["Num.","Name", "CreationDate"]))
        return SUCCESS

    # if we are going to printout the long ls at the current folder:
    if args == "":
        if s3_bucket_name == "" and s3_working_directory == "":
            #####################################################################################
            # I need to do something here to display a long version for the buckets
            #################################################################################
            # print("this is a long list with / or -l or both")
            return do_long_list("/")
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

                    ## get the permission for the object
                    # myacl = __get_object_acl__(s3_bucket_name, k)

                    # d = [str(object["ContentLength"]), k[len(s3_working_directory):], str(object["LastModified"]),
                    #      myacl["Owner"]["ID"], myacl["Grants"][0]["Permission"]]
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
                    ## get the permission for the object
                    # myacl = __get_object_acl__(bucketName, k)
                    # d = [str(object["ContentLength"]), k[len(s3_working_directory):], str(object["LastModified"]),
                    #      myacl["Owner"]["ID"], myacl["Grants"][0]["Permission"]]
                    d = [str(object["ContentLength"]), k[len(s3_working_directory):], str(object["LastModified"])]
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
    # if args is not none, we have to separate full path or relative path:
    # use the shlex to handle the user input for double quotes
    shell_arg_list = shlexsplit(args)
    args = "".join(shell_arg_list)

    args_list = args.split(":", 1)

    if len(args_list) > 1:  # if this is the full path with bucket name
        bucketName = args_list[0]
        pathName = args_list[1]

        # pathName should not be none
        if pathName == "":
            print(colored("S5 Error: Can not create folder due to Folder Name is Null!", "red"))
            return UNSUCCESS

        # the bucket should present
        if not __present_of_a_path(bucketName, ""):
            print(colored("S5 Error: Can not create folder due to bucket not exist!", "red"))
            return UNSUCCESS

        # make sure the path is not start with slash or have two slash together
        if not __check_no_two_slash_together_and_not_start_with_slash__(pathName):
            print(colored("S5 Error: The input: " + pathName + " is illegal!", "red"))
            print(colored("The filepath should not start with '/' or have more than two '/' side by side.", "red"))
            return UNSUCCESS

        # put a slash at the end of the path name and validate a path
        pathName = __reslove_a_path(pathName, addEndingSlash=True)
        # print(pathName)
        # pathName should not be none
        if pathName == "":
            print(colored("S5 Error: Can not create folder due to Folder Name is Null!", "red"))
            return UNSUCCESS

        # the folder should not be present
        if __present_of_a_path(bucketName, pathName):
            print(colored("S5 Error: Can not create folder due to Object Already Exists!", "red"))
            return UNSUCCESS

        # all the subfolders should be present

        # resolve the path name first
        if pathName:
            pathname3_s3_obj_list = pathName.split("/")

        # prepare the subfodler list for checking if they exist or not

        if pathname3_s3_obj_list[-1] == "":
            pathname3_s3_obj_list.pop()  # because the last char is "/", we remove the "" from the list

        if pathname3_s3_obj_list[-1]:
            pathname3_s3_obj_list.pop()  # remove the last item, so we can check subfolders

        # need to check if all the sub folders are exist
        if not __validate_folder_helper(bucketName, pathname3_s3_obj_list):
            badPath = bucketName + ":" + "/".join(pathname3_s3_obj_list)
            print(colored("S5 Error: The input folder: " + badPath + "/ does not exist!", "red"))
            return UNSUCCESS

        # everything good, we are going to create a object
        try:
            # actually, I can not directly put the object here, I have to do this folder by folder
            # pathList = pathName.split("/")
            # __create_folder_helper(bucketName, pathList)
            response = client.put_object(Bucket=bucketName, Key=pathName)
            return SUCCESS
        except BaseException as e:
            print(colored("S5 Error: Can not create folder.", "red"))
            print(e)
            return UNSUCCESS

    else:  # if this is just the folder path without bucket name
        bucketName = s3_bucket_name
        # put a slash at the end of the path name and validate a path
        pathName = s3_working_directory + args_list[0]
        # pathName = __reslove_a_path(pathName)

        # # pathName should not be none
        # if pathName == "":
        #     print(colored("S5 Error: Can not create folder due to Folder Name is Null!", "red"))
        #     return UNSUCCESS
        #     # the bucket should present
        # if not __present_of_a_path(bucketName, ""):
        #     print(colored("S5 Error: Can not create folder due to bucket not exist!", "red"))
        #     return UNSUCCESS
        #     # the folder should not be present
        # if __present_of_a_path(bucketName, pathName):
        #     print(colored("S5 Error: Can not create folder due to File Already Exists!", "red"))
        #     return UNSUCCESS
        #     # everything good, we are going to create a object

        # pathName should not be none
        if pathName == "":
            print(colored("S5 Error: Can not create folder due to Folder Name is Null!", "red"))
            return UNSUCCESS

        # make sure the path is not start with slash or have two slash together
        if not __check_no_two_slash_together_and_not_start_with_slash__(pathName):
            print(colored("S5 Error: The input: " + pathName + " is illegal!", "red"))
            print(colored("The filepath should not start with '/' or have more than two '/' side by side.", "red"))
            return UNSUCCESS

        # put a slash at the end of the path name and validate a path
        pathName = __reslove_a_path(pathName, addEndingSlash=True)
        # print(pathName)
        # pathName should not be none
        if pathName == "":
            print(colored("S5 Error: Can not create folder due to Folder Name is Null!", "red"))
            return UNSUCCESS

        # the folder should not be present
        if __present_of_a_path(bucketName, pathName):
            print(colored("S5 Error: Can not create folder due to Object Already Exists!", "red"))
            return UNSUCCESS

        # all the subfolders should be present

        # resolve the path name first
        if pathName:
            pathname3_s3_obj_list = pathName.split("/")

        # prepare the subfodler list for checking if they exist or not

        if pathname3_s3_obj_list[-1] == "":
            pathname3_s3_obj_list.pop()  # because the last char is "/", we remove the "" from the list

        if pathname3_s3_obj_list[-1]:
            pathname3_s3_obj_list.pop()  # remove the last item, so we can check subfolders

        # need to check if all the sub folders are exist
        if not __validate_folder_helper(bucketName, pathname3_s3_obj_list):
            badPath = bucketName + ":" + "/".join(pathname3_s3_obj_list)
            print(colored("S5 Error: The input folder: " + badPath + "/ does not exist!", "red"))
            return UNSUCCESS

        try:
            # actually, I can not directly put the object here, I have to do this folder by folder
            # pathList = pathName.split("/")
            # __create_folder_helper(bucketName, pathList)
            response = client.put_object(Bucket=bucketName, Key=pathName)
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


# validate folder helper is going to recursively check if all the intermediate folders are available
# bucketName is the bucketName you want to check
# pathNameList is a list of intermediate subfolder names, for example, a/b/c/d.txt, we should
# only check a/, a/b/, and a/b/c exist, so pathNameList = [a,b,c]
# this function will return True if all subfolders exist
# and return False an error if any subfolder is missing

def __validate_folder_helper(bucketName, pathNameList):
    base = ""
    for name in pathNameList:
        name = name + "/"
        base += name
        if __present_of_a_path(bucketName, base):
            pass
        else:
            # print (bucketName +" and " + base +" does not exist!")
            return False
    return True

def do_cd(args):
    if not args:
        pass
    # elif platform.system() == "Windows":
    #     os.system("cd "+args)
    else:
        myargs = shlexsplit(args)
        os.chdir(myargs[0])

def do_quit(*args):
    endingStr = "Exiting the S5 Shell Program Now...\n"
    endingStr+= "Thank you for using S5, See you next time!"
    print(colored(endingStr,"blue"))
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
    "Q": do_quit,
    "cwf": do_current_work_folder,
    "cf": do_change_folder,
    "ch_folder": do_change_folder,
    "cdelete": do_delete_object,
    "t": do_test,
    "pkeys": __print_keys__,
    "create_folder": do_create_folder,
    "ccopy": do_copy_object,
    "cl_copy": do_copy_cloud,
    "cl": do_copy_cloud,
    "cd":do_cd,
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
                pass
                # raise Exception("this command does not exist")
        except BaseException as e:
            # print("S5 Error: Please see the error message below:")
            print(colored(e, "red"))
    # if we have a def of the command already, then dispatch it from the dict.
    else:
        if command in ["q","quit","exit","Q"]:
            dispatch["q"](arg)
        # if it is available, then we dispatch the command
        try:
            status_val = dispatch[command](arg)
        except BaseException as e:
            print(colored(e, "red"))
            print(colored("Please double check your arguments:" + arg, "red"))



