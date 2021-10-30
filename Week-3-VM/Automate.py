import configparser
# https://docs.python.org/3/library/configparser.html
import os
from DecoratorLib import try_catch

config = configparser.ConfigParser()
GCP_REQUIRED_KEYS = ["image", "imageproject", "zone"]
GCP_OPTIONAL_KEYS = ["CPU","memory_size","disk_size","PORT_OPEN"]

# The LINK to all the GCP create flags:
# https://cloud.google.com/sdk/gcloud/reference/compute/instances/create




# this is a test case, just printout the command
def run_automate():
    config.read("gcp.conf")
    for tag in config.sections():
        dict = config[tag]
        __print_gcp_instance__(dict)

# this is the real case, create each instance
def automate_create():
    config.read("gcp.conf")
    for tag in config.sections():
        dict = config[tag]
        __create_gcp_instance__(dict)
@try_catch
def list_all_gcp_instance(*args):
    command = "gcloud compute instances list "
    for myarg in args:
        command +=myarg+" "
    # if "uri" in command:
    #     raise Exception("Sorry not support uri")
    os.system(command)

@try_catch
def delete_all_gcp_instance(*args):
    process = os.popen("gcloud compute instances list")
    output = process.read()
    process.close()
    VM_instance_name_list = []
    ##################################################################
    # get all the vm instance names
    ##################################################################
    for i, line in enumerate(output.split("\n")): #seperate by line
        if i==0:
            continue # skip the title line
        name = line.split()
        if name:
            name = name[0] # get the name of each of the vm instance, which is the 1st col
            VM_instance_name_list.append(name)
    if not VM_instance_name_list:
        print("Nothing to delete")

    for instance in VM_instance_name_list:
        command = "gcloud compute instances delete "+instance
        print(command)
        os.system(command)
    # print(VM_instance_name_list)
    # print(output)
    # command = "gcloud compute instances delete"
    # if not args:
    #     os.system(command)


@try_catch
def short_command(*args):
    os.system("gcloud compute instances list --uri")

def __print_tags_in_config_file__(tag):
    for key_value_pair in tag.items():
        print(key_value_pair)
    print("===================================")

def __create_gcp_instance__(dict):
    os.system(__print_gcp_instance__(dict))

def __print_gcp_instance__(dict):
    prefix=" gcloud compute instances create \"" +dict["name"]+"\" "
    for key in GCP_REQUIRED_KEYS:
        prefix+= "--"+key+" \""+dict[key]+"\" "

    # replace the imageproject to --image-project
    prefix = prefix.replace("--imageproject", "--image-project")
    print(prefix)
    return prefix

def print_gcp_instance_list():
    os.system("gcloud compute images list")

# get all the sections from the config object and
# call a helper function to print out the key-value pairs
if __name__ == '__main__':
    for tag in config.sections():
        dict = config[tag]
        __create_gcp_instance__(dict)
        # print_tags_in_config_file(config[tag])
