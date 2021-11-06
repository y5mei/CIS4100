import configparser
# https://docs.python.org/3/library/configparser.html
import getpass
import os
import subprocess
import sys
import time
import copy
import json

from tabulate import tabulate
from termcolor import colored
from colorama import init
from DecoratorLib import try_catch

AZURE_REQUIRED_KEYS = ["name", "resource-group", "image","location","admin-username"]
AZURE_OPTIONAL_KEYS = ["custom-cpu", "custom-memory", "create-disk"]
AZURE_ADDITIONAL_INFO = ["purpose", "team", "os"]
SYSTEM_ADMIN_PASSWORD = "admin_password"
OPEN_PORT = "open_port" # this is optional too

init()

# check if I have all the required keys for create VM
# check if I have all the requried keys for document
# check if this is a windows server, if yes, check if I have the admin password

#check and create the resource group
#wrap the cli command to create the vm
#check if the vm exist, if exist, raise an error
#try to create the VM
#get the status of the vm
#open the ports for th vm
#write all the inforamtion to the config file

@try_catch
def automate_create_azure():
    config = configparser.ConfigParser()
    config.read("Azure.conf")
    VM_Counter = 0
    Error_Counter = 0
    file = ""

    for vm in config.sections():
        dict = config[vm]
        __Azure_VM_input_validation__(dict)  # check if the input has all the required fields
        command = __print_azure_instance__(dict)  # prepare the command line argument for creating the VM
        resource_image_command = __print_azure_resource_group__(dict)

        name_of_vm = dict["name"]
        project_of_vm = dict["resource-group"]
        purpose_of_vm = dict["purpose"]
        team_of_vm = dict["team"]
        os_of_vm = dict["os"]

        try:
            # 1) create the resource group
            process = os.popen(resource_image_command)
            output = process.read()
            process.close()

            # get the output in the format of json and printout as a table
            data = json.loads(output)
            header = list(data.keys())
            value = []
            for k in header:
                val = data[k]
                if k=="id":
                    val = val.split("/")[-1]
                value.append(val)
            print(colored("Resource-Group Created: ", "green")) # print out green if successfully made the resource grp
            print(tabulate([header,value],headers="firstrow",tablefmt="pretty"))


            # 2) create the VM based on the config file
            process = os.popen(command)
            output = process.read()
            process.close()

            if not output: # if failed to create the VM
                Error_Counter+=1
                continue

            # get the output in the format of json and printout as a table
            data = json.loads(output)
            header = list(data.keys())
            value = []
            for k in header:
                val = data[k]
                if k=="id":
                    val = val.split("/")[-1]
                value.append(val)
            print(colored("VM Created: ", "green"))  # print out green if successfully made the resource grp
            print(tabulate([header,value],headers="firstrow",tablefmt="pretty"))
            # print(colored(output, "green")) # print out green if successfully made the VM
            continue


            # create the firewall rules if exist
            if OPEN_PORT in dict.keys():
                command = "gcloud compute firewall-rules create "+name_of_vm +" --allow="+dict[OPEN_PORT]+" --source-tags="+name_of_vm
                print(command)
                process = os.popen(command)
                output = process.read()
                process.close()

            if not output: # if failed to create the VM
                Error_Counter+=1
                continue

            print(colored(output, "green"))  # print out green if successfully made the VM

            #  after 1) created the VM, 2) applied the rules, now we write the log file

            dict_of_vm_status = get_running_VM_status()
            VM_Counter += 1
            # if this is the 1st successful created VM, start creating a file itself
            if VM_Counter == 1:
                # get the date stamp and system admin name
                date_stamp_of_vm = time.strftime("%Y-%m-%dT%H-%M-%S")  # this is the timestamp for the filename
                admin_of_vm = getpass.getuser()
                # if SYSTEM_ADMIN_FLAG has already in the dict, when we use the given value

                if SYSTEM_ADMIN_FLAG in dict.keys():
                    admin_of_vm = dict[SYSTEM_ADMIN_FLAG]

                file = open("VMcreation_" + date_stamp_of_vm + ".txt", "w")
                date1 = date_stamp_of_vm.split("T")[0]
                time1 = ":".join(date_stamp_of_vm.split("T")[1].split("-"))
                timestamp_of_vm = date1 + ":" + time1

                file.write("Date stamp: " + timestamp_of_vm + "\n")
                file.write("System Admin Name: " + admin_of_vm + "\n")

            # check the status, then generate the documentation file if the vm exist
            status_of_vm = dict_of_vm_status[name_of_vm]

            # start writing into the file
            file.write("================================================================================\n")
            file.write("NAME: " + name_of_vm + "\n")
            file.write("Project: " + project_of_vm + "\n")
            file.write("Purpose: " + purpose_of_vm + "\n")
            file.write("Team: " + team_of_vm + "\n")
            file.write("OS: " + os_of_vm + "\n")
            file.write("Status: " + status_of_vm + "\n")
            file.write("==================== All Relevant Info about this VM Below ======================\n")
            new_command = "gcloud compute instances list --format=\"text\" --filter=\"name="+name_of_vm+"\""
            process = os.popen(new_command)
            additional_info  = process.read()
            process.close()
            file.write(additional_info)

        except Exception as e:
            Error_Counter += 1
            print(e)

    if file:
        file.close()
    # if there are any error occurred, raise an error to return 1
    if Error_Counter > 0:
        error_message = "There are totally "+str(Error_Counter)+" errors in this Config file! Please refer to the details above!"
        error_message = "There are totally "+str(VM_Counter)+" created from this Config file."
        raise Exception (error_message)

# this method will check if the AZURE input tag for a VM has all the requirement fields
# raise error accordingly if missing any field
def __Azure_VM_input_validation__(dict):
    for key in AZURE_REQUIRED_KEYS:
        if key not in dict:
            error_message = "CAN NOT CREATE VM: Missing Requirement Field in the azure.conf File to Create a GCP VM instance: " + key
            raise KeyError(error_message)

    vm_os = dict["os"]
    if vm_os=="windows" and "admin_password" not in dict:
        error_message = "CAN NOT CREATE VM: You must setup the --admin_password for a windows VM in the azure.conf file "
        raise KeyError(error_message)

    for key in AZURE_ADDITIONAL_INFO:
        if key not in dict:
            error_message = "CAN NOT CREATE VM: Missing Requirement Field in the azure.conf File to Create the LOG File: " + key
            raise KeyError(error_message)

def __print_azure_resource_group__(dict):
    name = dict["resource-group"]
    location = dict["location"]
    command = "az group create --name {} --location {}".format(name, location)
    print (command)
    return command

# this method will paraphrase all the requirements and fine tuned parameters into a command string
# it will remove all the keys in the optional list out of the key set
# it will also remove the port command out of the key set
# when it will put everything else in the create command
########################################################
#
#   Need to make a deepcopy of the dict
#
########################################################
def __print_azure_instance__(dict):
    # remove resource-group
    # remove Azure_optional_keys
    # remove port
    dict = copy.deepcopy(dict)

    tags_to_remove = AZURE_ADDITIONAL_INFO +["port"]
    for tag in tags_to_remove:
        dict.pop(tag,None)

    prefix = "az vm create "
    # all the required information must be provided
    for key in dict:
        prefix += "--" + key + " \"" + dict[key] + "\" "
    print(prefix)
    # build the string for additional information for the VM:
    return prefix

def __list_all_azure_instance__():
    command = "az vm list --query \"[].{Name:name,  ResourceGroup:resourceGroup, Location:location}\" -d -o table"
    process = os.popen(command)
    output = process.read()
    process.close()

    result = {}
    if not output:
        return result
    else:
        lines = output.split("\n")[0:-1]
        header = lines[0].split()
        print(header)
        for line in lines[2:]:
            line = line.split()
            print(line)
            # for i in range(len(header)):
            #     key = header[i]
            #     val = line[]
            # key, val = line.split(",")
            # result[key] = val
        # return result
        # print(result)
    # print(output)


# get all the sections from the config object and
# call a helper function to print out the key-value pairs
if __name__ == '__main__':
    print("Unit Test")
    # list_all_gcp_instance("")
    automate_create_azure()
    __list_all_azure_instance__()