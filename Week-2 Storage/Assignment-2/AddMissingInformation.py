import platform
import sys
import boto3
from termcolor import colored
from colorama import init
from shlex import split as shlexsplit

import DynamoDBPythonLib
from CreateReport import cached_country_report, cached_global_report
from DynamoDBPythonLib.addFieldToATable import __add_missing_info_with_sort_key, \
    __update_a_DynamoDB_table_from_a_valid_dict
import DynamoDBPythonLib.deleteATable
import DynamoDBPythonLib.createATable
import DynamoDBPythonLib.addFieldToATable
import DynamoDBPythonLib.readATable
import DynamoDBPythonLib.bulkLoadATable
from DynamoDBPythonLib import *
import boto3
# detected the current running environment
running_platform = platform.system()
if running_platform !="Windows":
    import readline

# use Colorama to make Termcolor work on Windows too
# ref： https://pypi.org/project/colorama/
init()

# this is the function that add missing information for the 1st part of the missing info txt file
# this is basically just to insert a new data into the database, so if the user type anything wrong, there is no way I can catch this
from DynamoDBPythonLib.readATable import read_a_DynamoDBTable_as_a_list_of_dict, \
    read_a_DynamoDBTable_item_with_partition_key


def update_curpop_data(year: int, countryName: str, population: float):
    try:
        # create a dynamodb object
        dynamodb = boto3.resource('dynamodb')
        # get the low level client
        client = dynamodb.meta.client
        population_table_name = "ymei_population_table"
        # call the library function to update population
        __add_missing_info_with_sort_key(population_table_name, dynamodb, countryName, year, "Population", population)

        # get back the updated data and print it out
        data = read_a_DynamoDBTable_item_with_partition_key(population_table_name, dynamodb, parition_key=countryName, order_key =year)
        outputStr = "The population data for "+countryName+" at Year "+str(year)+" has been successfully updated to "+str(data['Population'])
        print(colored(outputStr, "green"))
    except Exception as e:
        error = "Can not update the table: " + population_table_name + " due to the reason below:\n" + str(e)
        error_message = colored(error, "red")
        print(error_message)

# this is the second functionality that append a missing language to the ymei_country_non_econ table
def update_language_data(iso3Str: str, language: str):
    try:
        # create a dynamodb object
        dynamodb = boto3.resource('dynamodb')
        # get the low level client
        client = dynamodb.meta.client
        non_econ_table_name = "ymei_country_non_econ"
        hashmap_table_name = "UN_country_codes"
        # need to find out the counter name [partition key] based on the iso3, I need a hashmap
        # read a list of hash map from the table provided by professor
        iso3_hashmap_list = read_a_DynamoDBTable_as_a_list_of_dict(hashmap_table_name, dynamodb)
        # print(iso3_hashmap_list)
        # need to build a hashmap between iso3 to countryname
        iso3_hashmap = {}
        for country in iso3_hashmap_list:
            iso_str = country['iso3']
            country_name = country['name']
            iso3_hashmap[iso_str]=country_name
        # need to build a helper function to update a give language value based on the partition key and value input
        if iso3Str not in iso3_hashmap:
            raise ValueError("The input ISO3: "+iso3Str+" does not valid")
        data = read_a_DynamoDBTable_item_with_partition_key(non_econ_table_name,dynamodb,parition_key=iso3_hashmap[iso3Str])
        # print(data['Languages'])

        row = {}
        row['Languages'] = data['Languages']+[language]
        row['Country Name'] = iso3_hashmap[iso3Str]
        #call the helper function to update the language section:
        __update_a_DynamoDB_table_from_a_valid_dict(
            non_econ_table_name, dynamodb, row, partition_key="Country Name")


        # print it again to see how it looks
        data = read_a_DynamoDBTable_item_with_partition_key(non_econ_table_name, dynamodb,
                                                            parition_key=iso3_hashmap[iso3Str])
        outputStr = "Language for "+iso3_hashmap[iso3Str] +" has been successfully updated to "+ str(data['Languages'])
        print(colored(outputStr, "green"))

    except Exception as e:
        error = "Can not update the table: " + non_econ_table_name + " due to the reason below:\n" + str(e)
        error_message = colored(error, "red")
        print(error_message)

def do_quit(*args):
    endingStr = "Exiting the S5 Shell Program Now...\n"
    endingStr+= "Thank you for using S5, See you next time!"
    print(colored(endingStr,"blue"))
    sys.exit(0)

def add_population(*args):
    if len(args)!=3:
        print(colored("Need exactly 3 inputs, Year, Country Name, and Population", "red"))
        return False
    try:
        year = int(args[0])
    except Exception as e:
        print(colored("Year input must be a number", "red"))

    if year <1970 or year>2019:
        print(colored("Year out of range: [1970-2019] ", "red"))
        return False
    try:
        population = int(args[2])
    except Exception as e:
        print(colored("Population input must be a number", "red"))

    try:
        countryName = args[1]
        update_curpop_data(year, countryName,population)
        return True
    except Exception as e:
        print(colored(e, "red"))

def add_language(*args):
    if len(args)!=2:
        print(colored("Need exactly 2 inputs, ISO3, and Language to append", "red"))
        return False

    try:
        isostr = args[0]
        lan = args[1]
        update_language_data(isostr, lan)
        return True
    except Exception as e:
        print(colored(e, "red"))

def print_country_report(*args):
    if len(args)!=1:
        print(colored("Need exactly 1 inputs, Country Name", "red"))
        return False

    try:
        cached_country_report(args[0])
        return True
    except Exception as e:
        print(colored(e, "red"))

def print_global_report(*args):
    if len(args)!=1:
        print(colored("Need exactly 1 inputs, Year", "red"))
        return False

    try:
        cached_global_report(int(args[0]))
        return True
    except Exception as e:
        print(colored(e, "red"))

def del_all_tables(*args):
    try:
        # create a dynamodb object
        dynamodb = boto3.resource('dynamodb')
        # get the low level client
        client = dynamodb.meta.client
        existing_tables = client.list_tables()['TableNames']

        # read all the CSV files
        non_econ_table_name = "ymei_country_non_econ"
        econ_table_name = "ymei_econ_table"
        population_table_name = "ymei_population_table"

        # Delete these files if they are already there
        if non_econ_table_name in existing_tables:
            DynamoDBPythonLib.deleteATable.delete_a_DynamoDB_table(non_econ_table_name, dynamodb)
        if population_table_name in existing_tables:
            DynamoDBPythonLib.deleteATable.delete_a_DynamoDB_table(population_table_name, dynamodb)
        if econ_table_name in existing_tables:
            DynamoDBPythonLib.deleteATable.delete_a_DynamoDB_table(econ_table_name, dynamodb)
        # return True
    except Exception as e:
        error = "Can not delete the table due to the reason below:\n" + str(e)
        error_message = colored(error, "red")
        print(error_message)


dispatch = {
    "quit": do_quit,
    "exit": do_quit,
    "q": do_quit,
    "Q": do_quit,
    "add_population":add_population,
    "add_language": add_language,
    "country_report":print_country_report,
    "global_report": print_global_report,
    "del_tables":del_all_tables,
}

if __name__ == '__main__':
    print(colored("Welcome to S5 Shell","green"))
    print(colored("This shell only support 5 command: quit, del_tables, add_population, add_language, country_report, and global_report", "green"))
    while True:

        user_input = input("S5> ")

        # Requirment 3 1) if the input command is not a required function,
        # call the os.sys() method to use the system shell to handle it

        if len(user_input.split(" ", 1)) > 1:  # if input contains argument
            command, arg = user_input.split(" ", 1)[0], user_input.split(" ", 1)[1]
        else:
            command, arg = user_input.split(" ", 1)[0], ""  # if input does not contains argument, argument is ""

        if command not in set(dispatch.keys()):
            # if the command is not a controlled method, pass it directly to the system shell
            try:
                # if os.system(user_input) != 0:
                #     pass
                raise Exception("This shell only support 5 command: quit, add_population, add_language, country_report, and global_report")
            except BaseException as e:
                # print("S5 Error: Please see the error message below:")
                print(colored(e, "red"))
        # if we have a def of the command already, then dispatch it from the dict.
        else:
            if command in ["q", "quit", "exit", "Q"]:
                dispatch["q"](arg)
            # if it is available, then we dispatch the command
            try:
                arg = shlexsplit(arg) # need to use shellsplit to split the input into arguments
                status_val = dispatch[command](*arg)
            except BaseException as e:
                print(colored(e, "red"))
                print(colored("Please double check your arguments: " + arg, "red"))
    # update_curpop_data(2019,"Australia",25203198)
    # update_curpop_data
    # update_curpop_data(2019, "Bangladesh", 163046161)
    # update_curpop_data(2019, "Canada", 37411047)
    # update_curpop_data(2019, "Costa Rica", 5047561)
    #
    # update_language_data("COM", "French")
    # update_language_data("COK", "English")

    # # create a dynamodb object
    # dynamodb = boto3.resource('dynamodb')
    # # get the low level client
    # client = dynamodb.meta.client
    #
    # # read all the CSV files
    # non_econ_table_name = "ymei_country_non_econ"
    # econ_table_name = "ymei_econ_table"
    # population_table_name = "ymei_population_table"
    #
    #
    # ########### To Read ##########################################################################################
    # table = dynamodb.Table(population_table_name)
    # countryName = "Australia"
    # year = 2019
    # response = table.get_item(
    #     Key={
    #         'Country': countryName,
    #         'Year': year,
    #     }
    # )
    #
    # # item = response['Item']
    # # print(item)
    #