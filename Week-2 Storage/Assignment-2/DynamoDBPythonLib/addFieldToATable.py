from collections import defaultdict
from decimal import Decimal
import boto3
from termcolor import colored
import csv

from DynamoDBPythonLib.bulkLoadATable import __get_attribute_keys__, __check_KeySchemas_present__


def add_field_to_a_table(table_name: str, dynamodb: object, csv_file: str, file_partition_key: str=""):
    """
    This function add a series of field to a dynamodb table, the csv file must contains the keys, partition key (and the
    range key if the dynamodb table contains)
    :param table_name:
    :param dynamodb:
    :param csv_file:
    :param file_partition_key:
    :param file_range_key:
    :return:
    """
    try:
        # get the keys from the table
        key_dict = __get_attribute_keys__(table_name,dynamodb)
        partition_key = key_dict["partition_key"]
        range_key = key_dict["range_key"]

        if range_key:
            raise ValueError("This add field function only works for Dynamodb without range key")

        file_range_key = ""

        if not file_range_key:
            file_range_key = range_key

        # error handling to make sure keys present
        file = open(csv_file, 'r')
        reader = csv.DictReader(file)
        header = reader.fieldnames  # header is a list

        # check if the keyshchemas are in the header:
        __check_KeySchemas_present__(header, file_partition_key, file_range_key)

        # load each of the data from the CSV file to the table
        for row in reader:
            __update_a_DynamoDB_table_from_a_valid_dict(table_name,dynamodb,row,partition_key,file_partition_key)

        return True
    except Exception as e:
        error = "Can not add new field to the table: " + table_name + " due to the reason below:\n" + str(e)
        error_message = colored(error, "red")
        print(error_message)


# we assume the input dict is valid (contains the hash key and the range key)
def __update_a_DynamoDB_table_from_a_valid_dict(table_name: str, dynamodb: object, row: dict, partition_key, file_partition_key=""):
    try:
        if not file_partition_key:
            file_partition_key = partition_key
        # print(row)
        table = dynamodb.Table(table_name)
        keys = {}
        expressionattributenames = {}
        exppressionattributevalues = {}
        updateexpression = "SET  "
        i = 0
        for k, v in row.items():
            i += 1
            if k == None:
                continue
            if k == file_partition_key:
                keys[partition_key] = row[file_partition_key]
                continue
            fieldName = "#field" + str(i)
            valueName = ":val" + str(i)
            updateexpression += fieldName + " = " + valueName + ", "
            expressionattributenames[fieldName] = k
            exppressionattributevalues[valueName] = v
        # print(keys)
        # print(updateexpression[:-2])
        # print(expressionattributenames)
        # print(exppressionattributevalues)
        table.update_item(Key=keys, UpdateExpression=updateexpression[:-2],
                          ExpressionAttributeNames=expressionattributenames,
                          ExpressionAttributeValues=exppressionattributevalues)
    except Exception as e:
        raise e


def __update_a_DynamoDB_table_from_a_valid_list_of_dict(table_name: str, dynamodb: object, listRow: dict, partition_key, file_partition_key=""):
    try:
        for row in listRow:
            __update_a_DynamoDB_table_from_a_valid_dict(table_name, dynamodb, row, partition_key, file_partition_key)
    except Exception as e:
        raise e

# this is the helper function for the 1st part of adding the missing information, this is not really a update, just create new fields
def __add_missing_info_with_sort_key(table_name: str, dynamodb: object,  partition_key: str, order_key:str, field_name: str, field_val: object):
    try:
        # print(row)
        table = dynamodb.Table(table_name)
        key_dict = __get_attribute_keys__(table_name,dynamodb)
        keys = {
            key_dict["partition_key"]:partition_key,
            key_dict["range_key"]:order_key,
        }
        # print(keys)
        # return True
        expressionattributenames = {}
        exppressionattributevalues = {}
        updateexpression = "SET  "
        row = {field_name:field_val}
        i = 0
        for k, v in row.items():
            i += 1
            if k == None:
                continue
            if k == partition_key:
                continue
            fieldName = "#field" + str(i)
            valueName = ":val" + str(i)
            updateexpression += fieldName + " = " + valueName + ", "
            expressionattributenames[fieldName] = k
            exppressionattributevalues[valueName] = v
        # print(keys)
        # print(updateexpression[:-2])
        # print(expressionattributenames)
        # print(exppressionattributevalues)
        table.update_item(Key=keys, UpdateExpression=updateexpression[:-2],
                          ExpressionAttributeNames=expressionattributenames,
                          ExpressionAttributeValues=exppressionattributevalues)
    except Exception as e:
        raise e

# Unit Test
if __name__ == "__main__":
    # create a dynamodb object
    dynamodb = boto3.resource('dynamodb')
    # get the low level client
    client = dynamodb.meta.client
    # check if the table name present or not
    # print(client.list_tables()['TableNames'])
    # define the table name
    table_name = 'ymei_country_codes'
    # print(list(__get_attribute_keys__(table_name, dynamodb).items()))
    # add_field_to_a_table(table_name, dynamodb, "../shortlist_capitals.csv")
    __add_missing_info_with_sort_key("ymei_population_table", dynamodb, "Australia",2019,"Population", 50111)
