import configparser
# https://docs.python.org/3/library/configparser.html
import getpass
import os
import subprocess
import sys
import time

from tabulate import tabulate
from termcolor import colored
from colorama import init
from DecoratorLib import try_catch

GCP_REQUIRED_KEYS = ["image", "imageproject", "zone"]
GCP_OPTIONAL_KEYS = ["custom-cpu", "custom-memory", "create-disk"]
# possible_choice = ["micro","1GB","size=1GB,device-name=test","tcp:80,tcp:443"] create-disk = size=1GB,device-name=test???
# reference https://cloud.google.com/sdk/gcloud/reference/compute/instances/create
GCP_ADDITIONAL_INFO = ["Project", "Purpose", "Team", "OS"]
SYSTEM_ADMIN_FLAG = "system-admin-name" # this is optional
OPEN_PORT = "open_port" # this is optional too

# to support http and https port for GCP:
# https://cloud.google.com/vpc/docs/using-firewalls

# actually how to open a filewall
# https://stackoverflow.com/questions/21065922/how-to-open-a-specific-port-such-as-9090-in-google-compute-engine
#  gcloud compute firewall-rules create bbb --allow=tcp:100,tcp:101 --source-tags=linuxserver04
# gcloud compute instances list --format="text" --filter="name=linuxserver04"
# allowed[].ports[] string
#
# An optional list of ports to which this rule applies. This field is only applicable for the UDP or TCP protocol. Each entry must be either an integer or a range. If not specified, this rule applies to connections through any port.
#  gcloud compute firewall-rules list
# Example inputs include: ["22"], ["80","443"], and ["12345-12349"].


# get all the available Machine List
# gcloud compute machine-types list --sort-by CPUS  --filter "zone=northamerica-northeast1-a"


# The LINK to all the GCP create flags:
# https://cloud.google.com/sdk/gcloud/reference/compute/instances/create


init()


# this is the real case, create each instance
# read the config file and try to create VM according to the dicts
@try_catch
def automate_create_gcp():
    config = configparser.ConfigParser()
    config.read("gcp.conf")
    VM_Counter = 0
    Error_Counter = 0
    file = ""

    for vm in config.sections():
        dict = config[vm]
        __GCP_VM_input_validation__(dict)  # check if the input has all the required fields
        command = __print_gcp_instance__(dict)  # prepare the command line argument for creating the VM
        name_of_vm = dict["name"]
        project_of_vm = dict["Project"]
        purpose_of_vm = dict["Purpose"]
        team_of_vm = dict["Team"]
        os_of_vm = dict["OS"]

        try:
            # create the VM based on the config file
            process = os.popen(command)
            output = process.read()
            process.close()

            if not output: # if failed to create the VM
                Error_Counter+=1
                continue

            print(colored(output, "green")) # print out green if successfully made the VM


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


# this method will list all the available GCP VM instances
@try_catch
def list_all_gcp_instance(*args):
    command = "gcloud compute instances list --format=\"table[title=My_VM_Instance_List] (creationTimestamp,name,zone,networkInterfaces[].networkIP:label=Internal_IP,networkInterfaces[0].accessConfigs[0].natIP[]:label=External_IP,status)\""
    process = os.popen(command)
    output = process.read()
    process.close()

    if not output:
        print("Currently, there are no VM instance under this Google Account.")
        return 0
    else:
        os.system(command)


def get_running_VM_status():
    # reference:
    # https://cloud.google.com/blog/products/it-ops/filtering-and-formatting-fun-with
    # get all the name of current VM and the status of the current VM, then separate them by comma
    # return is a dict name -> status
    command = 'gcloud compute instances list --format="csv(name,status)"'
    process = os.popen(command)
    output = process.read()
    process.close()
    result = {}
    if not output:
        return result
    else:
        lines = output.split("\n")[1:-1]
        for line in lines:
            key, val = line.split(",")
            result[key] = val
        return result
        print(result)


def get_running_VM_zones():
    # reference:
    # https://cloud.google.com/blog/products/it-ops/filtering-and-formatting-fun-with
    # get all the name of current VM and the zone of the current VM, then separate them by comma
    command = 'gcloud compute instances list --format="csv(name,zone)"'
    process = os.popen(command)
    output = process.read()
    process.close()
    result = {}
    if not output:
        return result
    else:
        lines = output.split("\n")[1:-1]
        for line in lines:
            key, val = line.split(",")
            result[key] = val
        return result
        print(result)

def get_current_VM_FireWall_rules():
    # reference:
    # # https://cloud.google.com/sdk/gcloud/reference/compute/firewall-rules/delete
    # get all the names of existing VM firewall rules, and the "Disabled" option for the rules, then seperate them by comma
    # return is a dict Name -> Disabled
    command = 'gcloud compute firewall-rules list --format="csv(NAME,DISABLED)"'
    process = os.popen(command)
    output = process.read()
    process.close()
    result = {}
    if not output:
        return result
    else:
        lines = output.split("\n")[1:-1]
        for line in lines:
            key, val = line.split(",")
            result[key] = val
        return result
        # print(result)


def delete_firewall_rules():
    instance = "linuxserver01"
    command = command = "gcloud compute firewall-rules delete " + instance + " --quiet"
    os.system(command)


# this method will delete all the GCP VM instances under the current account
# also delete all the rules which are having the same name as the VM instance if they exist
@try_catch
def delete_all_gcp_instance(*args):
    vm_name_list = list(get_running_VM_zones().keys()) # all the existing vms
    vm_filewall_rule_list = list(get_current_VM_FireWall_rules().keys()) # all the existing firewall rules

    if not vm_name_list: # if no vms:
        print("There are no VM instance under this google account. So nothing can be deleted.")
        return
    else:
        for instance in vm_name_list:
            command = "gcloud compute instances delete " + instance + " --zone=" + get_running_VM_zones()[
                instance] + " --delete-disks=all --quiet"
            print(command)
            os.system(command)
            if instance in vm_filewall_rule_list: # if there is a firewall rule associate with the VM with the same name
                delete_firewall_command = "gcloud compute firewall-rules delete " + instance + " --quiet"
                print(delete_firewall_command)
                os.system(delete_firewall_command)





@try_catch
def short_command(*args):
    os.system("gcloud compute instances list --uri")


def __print_tags_in_config_file__(tag):
    for key_value_pair in tag.items():
        print(key_value_pair)
    print("===================================")


# this method will create a GCP VM based on the command input
def __create_gcp_instance__(dict):
    command = __print_gcp_instance__(dict)
    os.system(command)


# this method will check if the GCP input tag for a VM has all the requirement fields
# raise error accordingly if missing any field
def __GCP_VM_input_validation__(dict):
    for key in GCP_REQUIRED_KEYS:
        if key not in dict:
            error_message = "CAN NOT CREATE VM: Missing Requirement Field in the gcp.conf File to Create a GCP VM instance: " + key
            raise KeyError(error_message)

    for key in GCP_ADDITIONAL_INFO:
        if key not in dict:
            error_message = "CAN NOT CREATE VM: Missing Requirement Field in the gcp.conf File to Create the LOG File: " + key
            raise KeyError(error_message)


# this method will paraphrase all the requirements and fine tuned parameters into a command string
def __print_gcp_instance__(dict):
    prefix = " gcloud compute instances create \"" + dict["name"] + "\" "
    # all the required information must be provided
    for key in GCP_REQUIRED_KEYS:
        prefix += "--" + key + " \"" + dict[key] + "\" "

    # all the fine tune parameters can also be added
    for key in GCP_OPTIONAL_KEYS:
        if key in dict.keys():
            prefix += "--" + key + " \"" + dict[key] + "\" "

    # replace the imageproject to --image-project
    prefix = prefix.replace("--imageproject", "--image-project")
    print(prefix)

    # build the string for additional information for the VM:
    additional_info = ""
    return prefix


# get all the sections from the config object and
# call a helper function to print out the key-value pairs
if __name__ == '__main__':
    print("Unit Test")
    # list_all_gcp_instance("")
    automate_create_gcp()
