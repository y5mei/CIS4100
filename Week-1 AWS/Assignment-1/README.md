# CIS4100
---
# F21 CIS4100 Cloud Computing Assignment-1
This is the 1st assignment for CIS4010 F21 class. In this assignment, we build a python shell script, **S5**, that can operate AWS S3.
## 1. Getting Started
To obtain a local copy and get the **S5 Shell** running, please follow these simple example steps below:
### 1.1. Prerequisites
- You must have **Python 3.8** availiable on your machine;
- You must have the **AWS_ACCESS_KEY_ID** and **AWS_SECRET_ACCESS_KEY** availiable with proper S3 Authorization.
### 1.2 Installation
The installation including three parts: 
1) Prepare the credential file,
2) Double check your folder structure
3) Install the required python packages.

- To Prepare Your Cerdential File, **S5-S3conf**: put your **AWS_ACCESS_KEY_ID** and **AWS_SECRET_ACCESS_KEY** inside of the S5-S3conf file: 
```
[default]
aws_access_key_id = XXXXXXXXXXX
aws_secret_access_key = XX/XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX
```
- To double check the folder structure: This **S5-S3conf** file should be in the same folder with the S5Terminal.py file and the ReadCredentials.py file. The overall folder structure should look like this:
```
--------some-folder-name
          |----S5-S3conf
          |----S5Terminal.py
          |----ReadCredentials.py
          |----requirements.txt
          |----cis4010_assignment-1_environment.yaml (optional)
```
- To Install the packages from requirement list: 
Your IDE should automatically install all the packages from the requirement.txt if you open the whole folder as a project.
In case if your IDE didn't. Use pip3 to install all the packages, or use conda to install the python environment:
```
pip3 install -r requirements.txt
```
Or
```
conda env create --file cis4010_assignment-1_environment.yaml
```

## 2. Usage
Start the S5 Shell from running the **S5Terminal.py** file
```
python S5Terminal.py
```
All the Command in the Assignment-1 specification are supported. Please follow the Assignment-1.pdf to use each of the function.

## 3. Special Cases
1. All the copy command, lc_copy, cl_copy, and ccopy will **not overwrite** an object if it has been exist already. S5 will just give user a warnning in this case and return unsuccess. 
2. The delete command, cdelete, will delete the object with the key exactly as what you type in. If you want to delete an empty folder, please add a "/" at the end. For example, if you have two objects, a file object: cis4010b01:images/cat and a folder object cis4010b01:images/cat/, the cdelete command will work as the following: 
```
# This command will delete the cat object
S5> cdelete cis4010b01:images/cat

# This command will delete the empty cat folder (you must have the ending "/")
S5> cdelete cis4010b01:images/cat/
```

3. list command does not support relative path as what bash's ls command does. It only list a bucket, or list a full path.
4. The limitation of S5 shell is that the number of objects inside of any bucket can not be greater than 1000, as this is the limitation of Boto3 SDK's list_objects() method.
5. The system cd command does not need a /d flag when switching between drives on the Windows environment. You can directly use cd E: to switch from C drive to E drive:
```
REM On Windows, the following cd command with a "/d" flg is not supported:
S5> cd /d E:

REM But you can do this directly withiout put the "/d"
S5> cd E:
```

<!---
---
| Assignment| Topic| Due Date|
|-----------|------|---------|
| Assign-1 | Storage| Week3 October 3|
| Assign-2 | Database| Week5 October 17|
| Assign-3 | Computation VM's| Week8 November 7|
| Assign-4 | Serverless | Week10 November 21|
| Assign-5 | Multi/Hybrid Cloud| Week12 December 5|

----
# Some Notes for BAT Command:
1. Use /d to change directory: cd /d E:
2. Change to the current user's home directory: cd %userprofile% 
-->
