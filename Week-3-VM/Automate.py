import configparser
# https://docs.python.org/3/library/configparser.html
import copy
import getpass
import os
import shutil
import subprocess
import sys
import time

from tabulate import tabulate
from termcolor import colored
from colorama import init

from AutomateAzure import automate_create_azure, delete_all_azure_instance
from AutomateGCP import automate_create_gcp, delete_all_gcp_instance
from DecoratorLib import try_catch

# this function will check the existence of gcp.conf and azure.conf,
# and call AutomateGCP and AutomateAzure respectively
#
# After Successfully Created the VM, AutomateGCP -> GoogleLog.txt
# After Successfully Created the VM, AutomateGCP -> AzureLog.txt
#
# Then, this function will check the existence of these two log files.
# It will merge these two log file and put the time stamp as the filename
# move the config file after this and put time stamp in the file names
@try_catch
def vmcreate():
    date_stamp_of_vm = time.strftime("%Y-%m-%dT%H-%M-%S")  # this is the timestamp for the filename
    saved_log_file_name = "VMcreation_" + date_stamp_of_vm + ".txt"

    if os.path.isfile('./gcp.conf'):
        automate_create_gcp()
    if os.path.isfile('./azure.conf'):
        automate_create_azure()

    handle_temp_log_file(saved_log_file_name) # delete and put the log file together
    handle_config_file(date_stamp_of_vm) # move the original log file into the Archive folder

@try_catch
def vmdelete():
    delete_all_azure_instance()
    delete_all_gcp_instance()


def handle_temp_log_file(saved_log_file_name=""):
    if not saved_log_file_name:
        date_stamp_of_vm = time.strftime("%Y-%m-%dT%H-%M-%S")  # this is the timestamp for the filename
        saved_log_file_name = "VMcreation_" + date_stamp_of_vm + ".txt"

    if not os.path.isfile('./GoogleLog.txt') and not os.path.isfile('./AzureLog.txt'):
        return
    if os.path.isfile('./GoogleLog.txt') and os.path.isfile('./AzureLog.txt'):
        file1 = file2 = ""
        with open("./GoogleLog.txt",encoding='utf-8') as fp: # read file1 as string
            file1 = fp.read()
        with open("./AzureLog.txt",encoding='utf-8') as fp: # read file2 as string
            file2 = fp.read()

        file2 += "================================================================================\n"
        file2 += "================================================================================\n"
        file2 += "================================================================================\n"
        file2 += file1 # merge them together
        fp.close()

        file = open(saved_log_file_name, "w")
        file.write(file2)
        file.close()
        os.remove('./GoogleLog.txt') # delete these two tempfiles
        os.remove('./AzureLog.txt')

    elif os.path.isfile('./GoogleLog.txt') and not os.path.isfile('./AzureLog.txt'):
        os.rename('./GoogleLog.txt', saved_log_file_name)
    else:
        os.rename('./AzureLog.txt', saved_log_file_name)

def handle_config_file(date_stamp_of_vm=""):
    if not date_stamp_of_vm:
        date_stamp_of_vm = time.strftime("%Y-%m-%dT%H-%M-%S")  # this is the timestamp for the filename

    if not os.path.isfile('./gcp.conf') and not os.path.isfile('./azure.conf'): # if no conf files, just return
        return

    if os.path.isfile('./gcp.conf'):
        shutil.move('./gcp.conf', "./Archive/gcp_"+date_stamp_of_vm+".conf")

    if os.path.isfile('./azure.conf'):
        shutil.move('./azure.conf', "./Archive/azure_"+date_stamp_of_vm+".conf")


if __name__ == '__main__':
    # print("Unit Test")
    # handle_temp_log_file()
    # handle_config_file()
    vmcreate()