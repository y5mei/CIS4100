from decimal import Decimal
import boto3
from termcolor import colored
import csv
from tabulate import tabulate

from DynamoDBPythonLib.bulkLoadATable import __get_attribute_keys__


def read_a_DynamoDBTable_to_CSV(table_name: str, dynamodb: object, file_name: str):
    """ This function read a table from Dynamodb and save it locally as a csv file
    :param table_name: the name of the Dynamodb table that user want to read
    :param dynamodb: this is a dynamodb object, can be created via boto3.resource('dynamodb').
    :param file_name: this is the name of the CSV file that user want to save to
    """
    try:
        # prepare the file to write into
        file = open(file_name, 'w+', newline='') # need the last parameter to avoid blank line in between
        # get a reference of the table we want to read
        table = dynamodb.Table(table_name)
        response = {}
        response = table.scan()["Items"]


        # write to file
        dict_writer = csv.DictWriter(file, response[0].keys())
        dict_writer.writeheader()
        dict_writer.writerows(response)
        file.close()

    except Exception as e:
        error = "Can not read the table: " + table_name + " and save it locally, due to the reason below:\n" + str(e)
        error_message = colored(error, "red")
        print(error_message)


def read_a_DynamoDBTable_to_Console(table_name: str, dynamodb: object):
    """ This function read a table from Dynamodb and print it to the console
    :param table_name: the name of the Dynamodb table that user want to read
    :param dynamodb: this is a dynamodb object, can be created via boto3.resource('dynamodb').
    :param file_name: this is the name of the CSV file that user want to save to
    """
    try:
        # get a reference of the table we want to read
        table = dynamodb.Table(table_name)
        response = {}
        response = table.scan()["Items"]
        header = list(response[0].keys())
        content = []
        for line in response:
            content.append(list(line.values()))

        print(tabulate(content,headers=header,tablefmt='orgtbl'))
        #
        #
        # # write to file
        # dict_writer = csv.DictWriter(file, response[0].keys())
        # dict_writer.writeheader()
        # dict_writer.writerows(response)
        # file.close()

    except Exception as e:
        error = "Can not read the table: " + table_name + " and save it locally, due to the reason below:\n" + str(e)
        error_message = colored(error, "red")
        print(error_message)

def read_a_DynamoDBTable_as_a_list_of_dict(table_name: str, dynamodb: object):
    """ This function read a table from Dynamodb and print it to the console
    :param table_name: the name of the Dynamodb table that user want to read
    :param dynamodb: this is a dynamodb object, can be created via boto3.resource('dynamodb').
    :param file_name: this is the name of the CSV file that user want to save to
    """
    try:
        # get a reference of the table we want to read
        table = dynamodb.Table(table_name)
        response = {}
        response = table.scan()["Items"]
        # header = list(response[0].keys())
        # content = []
        return response
        # for line in response:
        #     print(line)
            # content.append(list(line.values()))



    except Exception as e:
        error = "Can not read the table: " + table_name + " and save it locally, due to the reason below:\n" + str(e)
        error_message = colored(error, "red")
        print(error_message)

def read_a_DynamoDBTable_item_with_partition_key(table_name: str, dynamodb: object, parition_key: str, order_key = ""):
    """ This function read a element from Dynamodb and return it as d dictionary
    :param table_name: the name of the Dynamodb table that user want to read
    :param dynamodb: this is a dynamodb object, can be created via boto3.resource('dynamodb').
    :param file_name: this is the name of the CSV file that user want to save to
    """
    try:
        # get a reference of the table we want to read
        table = dynamodb.Table(table_name)
        key_dict = __get_attribute_keys__(table_name,dynamodb)
        if not order_key:
            keys = {
                key_dict["partition_key"]: parition_key,
            }
        else:
            keys = {
                key_dict["partition_key"]: parition_key,
                key_dict["range_key"]: order_key,
            }

        response = {}
        response = table.get_item(Key=keys)
        # header = list(response[0].keys())
        # content = []
        return response["Item"]
        # for line in response:
        #     print(line)
            # content.append(list(line.values()))



    except Exception as e:
        error = "Can not read the table: " + table_name + " and save it locally, due to the reason below:\n" + str(e)
        error_message = colored(error, "red")
        print(error_message)

# this is a better function that return None if does not exist or got a empty value in col : non_empty_col_name
def read_a_DynamoDBTable_item_with_partition_key_order_key_if_NA_return_None(table_name: str, dynamodb: object, parition_key: str, order_key = "", non_empty_col_name = ""):
    """ This function read a element from Dynamodb and return it as d dictionary
    :param table_name: the name of the Dynamodb table that user want to read
    :param dynamodb: this is a dynamodb object, can be created via boto3.resource('dynamodb').
    :param file_name: this is the name of the CSV file that user want to save to
    """
    try:
        # get a reference of the table we want to read
        table = dynamodb.Table(table_name)
        key_dict = __get_attribute_keys__(table_name,dynamodb)
        if not order_key:
            keys = {
                key_dict["partition_key"]: parition_key,
            }
        else:
            keys = {
                key_dict["partition_key"]: parition_key,
                key_dict["range_key"]: order_key,
            }
        response = table.get_item(Key=keys)
        # check the col name we are interested  value is not NA
        # like "Population, GDP
        if non_empty_col_name:
            if response["Item"][non_empty_col_name]=="NA":
                return None
        return response["Item"]


    except Exception as e:
        return None
# Unit Test
if __name__ == "__main__":
    # create a dynamodb object
    dynamodb = boto3.resource('dynamodb')
    # define the table name
    table_name = 'UN_country_codes'
    another_table_name = "ymei_country_codes"
    # create the table
    # read_a_DynamoDBTable_to_CSV(table_name, dynamodb, "../UN_country_codes.csv")
    # read_a_DynamoDBTable_to_Console(another_table_name, dynamodb)
    read_a_DynamoDBTable_as_a_list_of_dict(table_name,dynamodb)