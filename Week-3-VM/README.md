# Assignment-3 

_Virtual Machines With Google Cloud Platform and Azure_
---
This is the 3rd assignment for CIS4010 F21 Class. In this assignment, we build a python script, Automate.py, 
that will read two config files, namely to be azure.conf and gcp.conf, and will create VMs as described in these files.

## 1. Getting Started
To get the Automate.py running, please follow these simple steps below:
### 1.1 Prerequisites
- You must have **Python 3.8** available on your machine;
- You must have already installed **Azure CLI** on your machine, and have already logged in;
- You must have already installed **GCP CLI** on your machine, and you must have logged in <span style="color:red">and have a valid **project** in active</span>. 

As per the assignment specification: 

Automate.py will not create GCP "projects" for user automatically.
To create projects for GCP, follow [this link](https://cloud.google.com/sdk/gcloud/reference/projects/create) and use command ```gcloud projects create [PROJECT_ID]```

In the contrary, Automate.py will create **Resource Group** for Azure automatically according to the azure.conf file's `resource-group` tag

### 1.2 Installation
The installation including three parts:
1) Prepare the config files
2) Double-check your folder structure
3) Install the required python packages

#### 1.2.1 To prepare the config files, please put supported option flags in the config files. 

These are all the [supported flags](https://docs.microsoft.com/en-us/cli/azure/vm?view=azure-cli-latest#az_vm_create) for Azure, and These are all the [supported flags](https://cloud.google.com/sdk/gcloud/reference/compute/instances/create) for GCP.

**FOR EXAMPLE:** to set GCP's CPU numbers to be 4, and Memory Size to be 5GB, and set Azure's VM size to be a balanced CPU-to-memory ratio Ds1 and open port 80 and 403:
```json
[gcp01]
...
custom-cpu = 4
custom-memory = 5GB
...
[azure02]
...
size = Standard_DS1
port = 80,403
...
```

If a flag takes <span style="color:red"> **a nested dictionary as value**</span>, in the config file, type a string to represent the nested dictionary.

**FOR EXAMPLE:** If you want to open port 80 and 443 for GCP VM, the CLI command takes a nested dict flag value: `--allow=PROTOCOL[:PORT[-PORT]],[…]`

[Note that this is a special case, as `port` is not one of the GCP `create` flags, this flag is a customized Automate.py flag, translated from the `--allow` flag from [GCP firewall rules](https://cloud.google.com/sdk/gcloud/reference/compute/firewall-rules/create#:~:text=of%3A%20ALLOW%2C%20DENY.-,--allow%3DPROTOCOL%5B%3APORT%5B-PORT%5D%5D%2C%5B%E2%80%A6%5D,-A%20list%20of)]
```json
[gcp02]
...
port = tcp:80,tcp:443
...
```

**FOR EXAMPLE:** If you want to customize the hard disk for the GCP VM, the CLI command takes a nested dict flag value: `[--create-disk=[PROPERTY=VALUE,…]]`
```json
[gcp02]
...
create-disk = size=15GB,device-name=test
...
```


If a flag <span style="color:red"> **does not need a value** </span>, in the config file, just leave the value to be empty after the "=" char.

**FOR EXAMPLE:** to make the GCP VM don't automatically restart on failure, and set the Azure's VM to automatically generate ssh keys:
```json
[gcp01]
...
restart-on-failure = 
...
[azure02]
...
generate-ssh-keys =
...
```

If a flag has  <span style="color:red"> **an empty string as value** </span>, "", in the config file, just type "" on the right hand side of the "=" char

**FOR EXAMPLE:** If you decide to specify "" as the value for the --public-ip-address flag for Azure:
```json
[azure02]
...
public-ip-address = ""
...
```
#### 1.2.2 To double-check the folder structure
To prepare for the folder structure, please make sure you have the azure.conf or gcp.conf or both of them at the same level as the Automate.py file

```
--------some-folder-name
          |----azure.conf
          |----gcp.conf
          |----DecoratorLib.py
          |----AutomateAzure.py
          |----AutomateGCP.py
          |----Automate.py
          |----S5Shell.py (optional)
```
#### 1.2.3 To Install the required Python Packages:
```shell
pip3 install -r requirements.txt
```

## 2. Usage
1. User can run the **Automate.py** directly via the command line as per the requirement for assignment-3.
```shell
path-to-the-folder> python .\Automate.py
```

Additionally, I have also wrapped this assignment into the S5 Shell. Start the S5 Shell from a terminal:
```shell
path-to-the-folder> python .\S5Shell.py
```
```shell
# This command create GCP and Azure VMs according to the config files, and generate a log file for each VM created
S5> vmcreate
# This command delete all the GCP and Azure VMs as well as FireWall Rules (for GCP) and Resource-Groups (for Azure)
S5> vmdelete
# This command quit the S5 Terminal, alternatively, you can also use exit, Q, or q command to quit the S5 Terminal
S5> quit
#########################################################################################
# Additionally, You can also use the following S5 command to only operate GCP and Azure
#########################################################################################
# This command list all the GCP VM instances under the current google account
S5> glist
# This command list all the Azure VM instance under the current Azure account
S5> alist
# This command delete all the GCP instance and any FireWall Rules associated with the VMs
S5> gdelete
# This command delete all the Azure VMs and the Resource-Groups associated with the VMs
S5> adelete
```

## 3. Special Cases

1. If either azure.conf or gcp.conf is missing, Automate.py will just work the config files that is available;
2. Automate.py will return whatever `gcloud` or `az` returns insufficient information or miss-spelled variable names;
3. Automate.py will print out all the CLI command before executing it;
4. Automate.py will print out whatever the CLI command returns. Since GCP returns a table, while Azure returns a json string, I have converted the Azure json to a table to match the format of GCP. 
5. Log file will be generated with name `VMcreatetion_<date_stamp>.txt`
   1. date_stamp is in the format of `yyyy-mm-ddThh-mm-ss`
   2. System Admin Name is the computer's current user's name
   3. For each VM created, the log file will have 3 parts of information:
      1. Name, Project, Purpose, Team, OS, and the **Status of the VM** [as per the assignment-3 requirements]
      2. All the relevant information about the VM obtained from the config file
      3. All the relevant information about the VM obtained from `gcloud compute instances list` and `az vm show` command
6. The Automate.py supports finely tune the VM via the config files for both Azure and GCP. To see the instruction about how to write the config files, please refer to Section 1.2 in this readme file
7. After the creation of the VMs, move the azure.conf and gcp.conf files to the Archive Folder with name `azure_<date stamp>.conf` and `gcp_<date stamp>.conf`


Specifically, to let user specify that certain ports should be open (like port 80 for http and 443 for https)
```json
[gcp01]
...
port = tcp:80,tcp:443
...
[azure02]
...
port = 80,403
...
```
To let user specify the CPU choice, memory size, disk space:
```json
[gcp01]
...
custom-cpu = 4
custom-memory = 5GB
create-disk = size=15GB,device-name=test
...
[azure02]
...
size Standard_DS2_v2
data-disk-sizes-gb 15
...
```