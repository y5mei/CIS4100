from collections import defaultdict
from decimal import Decimal
import boto3
from termcolor import colored
import csv


def bulk_load_to_a_DynamoDB_table(table_name: str, dynamodb: object, csv_file: str):
    """ create a table from the csv file
    Reference https://docs.aws.amazon.com/amazondynamodb/latest/APIReference/API_AttributeDefinition.html
    :param table_name: a str value as the name of the table user wants to setup
    :param dynamodb: this is a dynamodb resource object, you can obtain one of this instance by boto3.resource("dynamodb")
    :param csv_file: this is the location string to a data csv file
    """
    try:
        # prepare the keys:
        key_dict = __get_attribute_keys__(table_name,dynamodb)
        partition_key = key_dict["partition_key"]
        partition_key_type = key_dict["partition_key_type"]
        range_key = key_dict["range_key"]
        range_key_type = key_dict["range_key_type"]
        # print(key_dict.items())
        # error handling to check input
        if not range_key_type and range_key:
            raise Exception("You must define range_key_type if you want to setup the table with range_key")
        if range_key_type and not range_key:
            raise Exception("You do not need to assign the range_key_type if you do not want to setup a range_key for "
                            "your table")
        if partition_key_type and partition_key_type not in ["S", "N", "B"]:
            raise Exception("partition_key_type must be either S, N, or B")
        if range_key_type and range_key_type not in ["S", "N", "B"]:
            raise Exception("range_key_type must be either S, N, or B")

        # error handling to make sure keys present

        file = open(csv_file, 'r')
        reader = csv.DictReader(file)
        header = reader.fieldnames  # header is a list

        # check if the keyshchemas are in the header:
        __check_KeySchemas_present__(header, partition_key, range_key)

        # get the table
        table = dynamodb.Table(table_name)

        # load each of the data from the CSV file to the table
        for row in reader:
            # convert data type to number or bool if necessary
            if partition_key_type == "N":
                row[partition_key] = Decimal(row[partition_key])
            if range_key_type == "N":
                row[range_key] = Decimal(row[range_key])

            if partition_key_type == "B":
                row[partition_key] = bool(row[partition_key])
            if range_key_type == "B":
                row[range_key] = bool(row[range_key])
            # if there are elements without a title (key), we delete it
            if None in row:
                del row[None]

            item1 = table.put_item(
                Item=row
            )

    except Exception as e:
        error = "Can not bulk_load to the table: " + table_name + " due to the reason below:\n" + str(e)
        error_message = colored(error, "red")
        print(error_message)
        # print(e)
def __get_attribute_keys__(table_name: str, dynamodb: object):
    """
    This function return a dict of partion key, key type and range key, and key type, if no range key, return empty str
    :param table_name:
    :param dynamodb:
    :return:
    """
    try:  # get a client from the resource
        client = dynamodb.meta.client
        if table_name not in client.list_tables()['TableNames']:
            raise RuntimeError("The table :" + table_name + "  does not exist")

        keyschema = client.describe_table(TableName=table_name)["Table"]["KeySchema"]
        arrtributeDef = client.describe_table(TableName=table_name)["Table"]["AttributeDefinitions"]
        # print(keyschema)
        # print(arrtributeDef)

        # prepare the keys
        key_dict = defaultdict(lambda: "")

        if len(keyschema) == 1:  # if no range key
            key_dict["partition_key"] = keyschema[0]["AttributeName"]
            key_dict["partition_key_type"] = arrtributeDef[0]["AttributeType"]

        if len(keyschema) == 2:  # if there are both hash keys and range keys
            temp1 = keyschema[0]  # temp1 is the hash key
            temp2 = keyschema[1]  # temp2 is the range key

            if temp1["KeyType"] == "RANGE":
                temp1, temp2 = temp2, temp1

            temp3 = arrtributeDef[0]  # temp3 is the hash key type definitions
            temp4 = arrtributeDef[1]  # temp4 is the range key type definitions

            if temp3["AttributeName"] != temp1["AttributeName"]:
                temp3, temp4 = temp4, temp3

            key_dict["partition_key"] = temp3["AttributeName"]
            key_dict["partition_key_type"] = temp3["AttributeType"]
            key_dict["range_key"] = temp4["AttributeName"]
            key_dict["range_key_type"] = temp4["AttributeType"]

            if not (temp1["KeyType"] == 'HASH' and temp2["KeyType"] == 'RANGE'):
                raise ValueError("We only support upload to a table with ONE Hash Key and ONE Range Key so far!")

        if not (len(keyschema) == 1 or len(keyschema) == 2):
            raise ValueError(
                "We only support upload to a table with ONE hashkey or with ONE hashkey and ONE rangekey so far!\nBut "
                "we found " + str(
                    len(keyschema)) + " keys in this table")

        return key_dict

    except Exception as e:
        raise e
def __check_KeySchemas_present__(header: dict, partition_key: str, range_key: str) -> bool:
    if partition_key and partition_key not in header:
        raise Exception("Partition_key: " + partition_key + ", not in the header of the input CSV file\nAvailable keys "
                                                            "are: " + str(header))

        # return False if partition_key not in header

    if range_key and range_key not in header:
        raise Exception(
            "Range_key: " + range_key + ", not in the header of the input CSV file\nAvailable keys are: " + str(header))

    return True

# def __bulk_load_a_DynamoDB_table_OLD__(table_name: str, dynamodb: object, csv_file: str, partition_key: str,
#                                        partition_key_type: str = "S",
#                                        range_key: str = None, range_key_type: str = None) -> None:
#     """ create a table from the csv file
#     Reference https://docs.aws.amazon.com/amazondynamodb/latest/APIReference/API_AttributeDefinition.html
#     :param table_name: a str value as the name of the table user wants to setup
#     :param dynamodb: this is a dynamodb resource object, you can obtain one of this instance by boto3.resource("dynamodb")
#     :param csv_file: this is the location string to a data csv file
#     :param partition_key: this is the string value for the hash key of the DynamoDB table
#     :param partition_key_type: this is the str represent the data type of the hash key, either S, N, or B
#     :param range_key: this is the str represent the key type of the order key of the DynamoDB table,
#     :param range_key_type: this is the string value for the data type of the optional order key, either S, N, or B
#     """
#     try:
#         # error handling to check input
#         if not range_key_type and range_key:
#             raise Exception("You must define range_key_type if you want to setup the table with range_key")
#         if range_key_type and not range_key:
#             raise Exception("You do not need to assign the range_key_type if you do not want to setup a range_key for "
#                             "your table")
#         if partition_key_type and partition_key_type not in ["S", "N", "B"]:
#             raise Exception("partition_key_type must be either S, N, or B")
#         if range_key_type and range_key_type not in ["S", "N", "B"]:
#             raise Exception("range_key_type must be either S, N, or B")
#
#         # error handling to make sure keys present
#         file = open(csv_file, 'r')
#         reader = csv.DictReader(file)
#         header = reader.fieldnames  # header is a list
#
#         # check if the keyshchemas are in the header:
#         __check_KeySchemas_present__(header, partition_key, range_key)
#
#         # create the dynamodb table now
#         table = __create_DynamoDB_table__(table_name, dynamodb, partition_key, partition_key_type, range_key,
#                                           range_key_type)
#
#         # load each of the data from the CSV file to the table
#         for row in reader:
#             # convert data type to number or bool if necessary
#             if partition_key_type == "N":
#                 row[partition_key] = Decimal(row[partition_key])
#             if range_key_type == "N":
#                 row[range_key] = Decimal(row[range_key])
#
#             if partition_key_type == "B":
#                 row[partition_key] = bool(row[partition_key])
#             if range_key_type == "B":
#                 row[range_key] = bool(row[range_key])
#
#             # if there are elements without a title (key), we delete it
#             if None in row:
#                 del row[None]
#
#             item1 = table.put_item(
#                 Item=row
#             )
#             print(item1)
#
#     except Exception as e:
#         error = "Can not create the table: " + table_name + " due to the reason below:\n" + str(e)
#         error_message = colored(error, "red")
#         print(error_message)
#         # print(e)





# def __create_DynamoDB_table__(table_name: str, dynamodb: object, partition_key: str, partition_key_type: str,
#                               range_key: str, range_key_type: str) -> object:
#     try:
#         KeySchemaList = []
#         AttributeDefinitionsList = []
#         partition_key_dict = {
#             'AttributeName': partition_key,
#             'KeyType': 'HASH'  # Partition key
#         }
#         partition_key_type_dict = {
#             'AttributeName': partition_key,
#             'AttributeType': partition_key_type
#         }
#
#         range_key_dict = {
#             'AttributeName': range_key,
#             'KeyType': 'RANGE'  # sort key
#         }
#         range_key_type_dict = {
#             'AttributeName': range_key,
#             'AttributeType': range_key_type
#         }
#
#         KeySchemaList.append(partition_key_dict)
#         AttributeDefinitionsList.append(partition_key_type_dict)
#
#         # if range key present, append it into the list
#         if range_key:
#             KeySchemaList.append(range_key_dict)
#             AttributeDefinitionsList.append(range_key_type_dict)
#
#         table = dynamodb.create_table(
#             TableName=table_name,  # replace myUN_country_codes with <username>UN_country_codes
#             KeySchema=KeySchemaList,
#             AttributeDefinitions=AttributeDefinitionsList,
#             ProvisionedThroughput={
#                 'ReadCapacityUnits': 10,
#                 'WriteCapacityUnits': 10
#             }
#         )
#         print("Table status:", table.table_status, table.table_name)
#         table.wait_until_exists()
#         print("Table ", table.table_name, " created")
#         return table
#     except Exception as e:
#         raise e




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
    bulk_load_to_a_DynamoDB_table(table_name, dynamodb, "../shortlist_area.csv")
