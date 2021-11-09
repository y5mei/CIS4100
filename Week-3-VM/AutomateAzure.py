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
SYSTEM_ADMIN_PASSWORD = "admin-password" # this is optional for linux, required for windows
SYSTEM_ADMIN_FLAG = "system-admin-name" # this is optional
OPEN_PORT = "port" # this is optional too

init()

# check if I have all the required keys for create VM
# check if I have all the requried keys for document
# check if this is a windows server, if yes, check if I have the admin password

# check and create the resource group
# wrap the cli command to create the vm
# check if the vm exist, if exist, raise an error
# try to create the VM
# get the status of the vm
# open the ports for th vm
# write all the inforamtion to the config file

@try_catch
def automate_create_azure():
    config = configparser.ConfigParser()
    config.read("azure.conf")
    VM_Counter = 0
    Error_Counter = 0
    file = ""

    for vm in config.sections():
        dict = config[vm]
        __Azure_VM_input_validation__(dict)  # check if the input has all the required fields
        command = __print_azure_instance__(dict)  # prepare the command line argument for creating the VM
        resource_image_command = __print_azure_resource_group__(dict)
        vmname_resourcegroup_dict = __list_all_azure_instance__()
        resourcegroup_location_dict = __list_all_azure_images_resource__()

        name_of_vm = dict["name"]
        project_of_vm = dict["resource-group"]
        # project_of_vm = dict["resource-group"].upper() # need to covert this to capital chars
        purpose_of_vm = dict["purpose"]
        team_of_vm = dict["team"]
        os_of_vm = dict["os"]
        admin_of_vm = dict[SYSTEM_ADMIN_FLAG]

        try:
            # if the VM already exist, raise an error and exist
            if vmname_resourcegroup_dict and name_of_vm in list(vmname_resourcegroup_dict.keys()):
                raise Exception("Error: A VM with name {} is already existed, please either delete the previous one or change this one to another name".format(name_of_vm))

            # if the resource group does not exist, create it
            if not resourcegroup_location_dict or project_of_vm not in list(resourcegroup_location_dict.keys()):
                # 1) create the resource group if not exist
                print(colored("The Required Resource-Group Does Not Exist, Going to Create it:","yellow"))
                process = os.popen(resource_image_command)
                output = process.read()
                process.close()

                # get the output in the format of json and printout as a table
                data = json.loads(output)
                header = list(data.keys())
                value = []
                for k in header:
                    val = data[k]
                    if k == "id":
                        val = val.split("/")[-1]
                    value.append(val)
                print(colored("\nResource-Group Created: ","green"))  # print out green if successfully made the resource grp
                print(tabulate([header, value], headers="firstrow", tablefmt="pretty"))



            # 2) create the VM based on the config file
            process = os.popen(command)
            output = process.read()
            process.close()

            if not output or output =="\n": # if failed to create the VM
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
            print(colored("\nVM has benn Created: ","green"))  # print out green if successfully made the resource grp
            print(tabulate([header,value],headers="firstrow",tablefmt="pretty"))
            # continue


            # create the firewall rules if exist
            if OPEN_PORT in dict.keys():
                command = "az vm open-port --name "+name_of_vm +" --resource-group "+ project_of_vm +" --port "+dict[OPEN_PORT]
                print(command)
                process = os.popen(command)
                output = process.read()
                process.close()

            if not output or output =="\n": # if failed to create the VM
                Error_Counter+=1
                continue
            output = "\nVM Port "+str(dict[OPEN_PORT])+" has been opened"
            print(colored(output,"green"))  # print out green if successfully made the VM

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

                # file = open("VMcreation_" + date_stamp_of_vm + ".txt", "w")
                file = open("AzureLog.txt", "w")
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
            file.write("================================================================================\n")
            file.write("=============  All Relevant Info from the Azure Config File  ===================\n")
            mydict = {}
            for line in dict.items():
                if len(line) == 2:
                    k = line[0]
                    v = line[1]
                    mydict[k] = v
            additional_info = json_dict_flater(mydict)
            file.write(additional_info)
            file.write("================================================================================\n")
            file.write("========== All Relevant Info about this VM (from az vm show command) ===========\n")

            command = "az vm show --resource-group {} --name {}".format(project_of_vm, name_of_vm)
            process = os.popen(command)
            output = process.read()
            process.close()
            additional_info = json_dict_flater(json.loads(output))
            file.write(additional_info)

        except Exception as e:
            Error_Counter += 1
            print(e)

    if file:
        file.close()
    # if there are any error occurred, raise an error to return 1
    if Error_Counter > 0:
        error_message = "There are totally "+str(Error_Counter)+" errors in this azure.conf file! Please refer to the details above!"
        error_message += "There are totally "+str(VM_Counter)+" Azure VMs created wihtout any error from this azure.conf file."
        raise Exception (error_message)

# this method will check if the AZURE input tag for a VM has all the requirement fields
# raise error accordingly if missing any field
def __Azure_VM_input_validation__(dict):
    for key in AZURE_REQUIRED_KEYS:
        if key not in dict:
            error_message = "CAN NOT CREATE VM: Missing Requirement Field in the azure.conf File to Create a GCP VM instance: " + key
            raise KeyError(error_message)

    vm_os = dict["os"]
    if vm_os=="windows" and "admin-password" not in dict:
        error_message = "CAN NOT CREATE VM: You must setup the --admin_password for a windows VM in the azure.conf file "
        raise KeyError(error_message)

    for key in AZURE_ADDITIONAL_INFO:
        if key not in dict:
            error_message = "CAN NOT CREATE VM: Missing Requirement Field in the azure.conf File to Create the LOG File: " + key
            raise KeyError(error_message)
    # if there is no system admin name, assign the user name to it
    admin_of_vm = getpass.getuser()
    if SYSTEM_ADMIN_FLAG not in dict:
        dict[SYSTEM_ADMIN_FLAG] = admin_of_vm

def __print_azure_resource_group__(dict):
    name = dict["resource-group"]
    location = dict["location"]
    command = "az group create --name {} --location {}".format(name, location)
    # print (command)
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

    tags_to_remove = AZURE_ADDITIONAL_INFO +["port", SYSTEM_ADMIN_FLAG] # the port to open and the name of the user is optional
    for tag in tags_to_remove:
        dict.pop(tag,None)

    prefix = "az vm create "
    # all the required information must be provided
    for key in dict:
        if not dict[key]:
            prefix += "--" + key +" " # if val is none
        elif dict[key] == "\"\"":
            prefix += "--" + key + " \"" + "\" " # if val is ""
        else:
            prefix += "--" + key + " \"" + dict[key] + "\" "
    print(prefix)
    # build the string for additional information for the VM:
    return prefix
# this method will return a dict,
# key is the vm name, val is the status
def get_running_VM_status():
    command = "az vm list --query \"[].{Name:name,  Status:powerState}\" -d -o table"
    process = os.popen(command)
    output = process.read()
    process.close()
    # print(output)
    result = {}
    if not output or output =="\n":
        return result
    else:
        lines = output.split("\n")[0:-1]
        header = lines[0].split()
        # print(header)
        for line in lines[2:]:
            line = line.split(" ",1)
            # print(line)
            key = line[0] # this is the VM name
            val = line[1] # this is the status
            # print(val)
            # val = line[1]+"---"+line[2] # this is the resourcegroup---location
            result[key] = val
        return result

# this method will return a dict,
# key is the vm name, val is the ResourceGroup
def __list_all_azure_instance__():
    command = "az vm list --query \"[].{Name:name,  ResourceGroup:resourceGroup, Location:location}\" -d -o table"
    process = os.popen(command)
    output = process.read()
    process.close()

    result = {}
    if not output or output =="\n":
        return result
    else:
        lines = output.split("\n")[0:-1]
        header = lines[0].split()
        # print(header)
        for line in lines[2:]:
            line = line.split()
            # print(line)
            key = line[0] # this is the VM name
            val = line[1] # this is the resource group
            # val = line[1]+"---"+line[2] # this is the resourcegroup---location
            result[key] = val
        return result

# this method list all the current available azure instance in a table
@try_catch
def __print_all_azure_images_resource__():
    command = "az group list --output table"
    process = os.popen(command)
    output = process.read()
    process.close()
    print(output)

# this method will return a dict,
# key is the image resource names, val is the locations
def __list_all_azure_images_resource__():
    command = "az group list --query \"[].{Name:name, Location:location}\" -o table"
    process = os.popen(command)
    output = process.read()
    process.close()

    result = {}
    if not output or output =="\n":
        return result
    else:
        lines = output.split("\n")[0:-1]
        header = lines[0].split()
        # print(header)
        for line in lines[2:]:
            line = line.split()
            key = line[0] # this is the VM name
            val = line[1] # this is the resource group
            # val = line[1]+"---"+line[2] # this is the resourcegroup---location
            result[key] = val
        return result

@try_catch
def list_all_azure_instance():
    command = "az vm list -d -o table"
    process = os.popen(command)
    output = process.read()
    process.close()
    if not output or output =="\n":
        print("Currently, there are no VM instance under this Azure Account.")
    else:
        print(output)

@try_catch
# this method will delete all the azure vms as well as resource groups silently
def delete_all_azure_instance(*args):
    vm_name_dict = __list_all_azure_instance__() # all the existing vms
    img_resource_name_dict = __list_all_azure_images_resource__() # all the existing image resource -> locations

    if not vm_name_dict:
        vm_name_dict = {}
    if not img_resource_name_dict:
        img_resource_name_dict = {}

    if not vm_name_dict and not img_resource_name_dict: # if no vms:
        print("There are no VM instance/Img Resource Group under this Azure account. So no VMs can be deleted.")
        return
    else:
        for instance in vm_name_dict:
            command = "az vm delete --resource-group " + vm_name_dict[instance] + " --name " + instance + " --yes"
            print(command)
            os.system(command)
        for instance in img_resource_name_dict:
            command = "az group delete --name " + instance + " --yes"
            print(command)
            os.system(command)


# return a string of a flattend json dict
def json_dict_flater(d, prefix=""):
    result = ""
    if not d:
        return result
    if type(d) is dict:
        for k in d:
            if not d[k]: # if the value is empty
                d[k] = "Null"
            if type(d[k]) is list: # if the value is a list of dictionary
                for i in d[k]:
                    result += json_dict_flater(i, prefix=str(k))
            elif type(d[k]) is not dict: # if the value is just a string
                if not prefix:
                    header = str(k)
                else:
                    header = prefix+"___"+str(k)
                result += header +":    "+str(d[k])+"\n"
            else:
                result += json_dict_flater(d[k], prefix=str(k)) # if the value is a dictionary
    return result


# get all the sections from the config object and
# call a helper function to print out the key-value pairs
if __name__ == '__main__':
    print("Unit Test")
    # test()
    automate_create_azure()
    # file.write(additional_info)
    # __list_all_azure_images_resource__()