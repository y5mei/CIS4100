from decimal import Decimal
import boto3
from termcolor import colored
import csv


def create_a_DynamoDB_table(table_name: str, dynamodb: object, partition_key: str,
                            partition_key_type: str="S",
                            range_key: str = None, range_key_type: str = None) -> None:
    """ create and return an empty DynamoDB table
    Reference https://docs.aws.amazon.com/amazondynamodb/latest/APIReference/API_AttributeDefinition.html
    :param table_name: a str value as the name of the table user wants to setup
    :param dynamodb: this is a dynamodb resource object, you can obtain one of this instance by boto3.resource("dynamodb")
    :param partition_key: this is the string value for the hash key of the DynamoDB table
    :param partition_key_type: this is the str represent the data type of the hash key, either S, N, or B
    :param range_key: this is the str represent the key type of the order key of the DynamoDB table,
    :param range_key_type: this is the string value for the data type of the optional order key, either S, N, or B
    """
    try:
        # error handling to check input
        if not range_key_type and range_key:
            raise Exception("You must define range_key_type if you want to setup the table with range_key")
        if range_key_type and not range_key:
            raise Exception("You do not need to assign the range_key_type if you do not want to setup a range_key for "
                            "your table")
        if partition_key_type and partition_key_type not in ["S","N","B"]:
            raise Exception("partition_key_type must be either S, N, or B")
        if range_key_type and range_key_type not in ["S","N","B"]:
            raise Exception("range_key_type must be either S, N, or B")

        # create the dynamodb table now
        table = __create_DynamoDB_table__(table_name, dynamodb,partition_key,partition_key_type,range_key,range_key_type)
        return table


    except Exception as e:
        error = "Can not create the table: " + table_name + " due to the reason below:\n" + str(e)
        error_message = colored(error, "red")
        print(error_message)
        # print(e)

def __create_DynamoDB_table__(table_name: str, dynamodb: object, partition_key: str, partition_key_type: str, range_key: str,range_key_type: str) -> object:
    try:
        KeySchemaList = []
        AttributeDefinitionsList = []
        partition_key_dict = {
            'AttributeName': partition_key,
            'KeyType': 'HASH'  # Partition key
        }
        partition_key_type_dict = {
            'AttributeName': partition_key,
            'AttributeType': partition_key_type
        }

        range_key_dict = {
            'AttributeName': range_key,
            'KeyType': 'RANGE'  # sort key
        }
        range_key_type_dict = {
            'AttributeName': range_key,
            'AttributeType': range_key_type
        }

        KeySchemaList.append(partition_key_dict)
        AttributeDefinitionsList.append(partition_key_type_dict)

        # if range key present, append it into the list
        if range_key:
            KeySchemaList.append(range_key_dict)
            AttributeDefinitionsList.append(range_key_type_dict)

        # print(AttributeDefinitionsList)
        # print(KeySchemaList)
        # return None

        table = dynamodb.create_table(
            TableName=table_name,  # replace myUN_country_codes with <username>UN_country_codes
            KeySchema=KeySchemaList,
            AttributeDefinitions=AttributeDefinitionsList,
            ProvisionedThroughput={
                'ReadCapacityUnits': 10,
                'WriteCapacityUnits': 10
            }
        )

        creating_table_string = "Table status: "+str(table.table_status)+"  "+str(table.table_name)
        print(colored(creating_table_string, "blue"))
        table.wait_until_exists()

        finished_creating_table = "Table "+str(table.table_name)+" created"
        print(colored(finished_creating_table, "green"))
        return table
    except Exception as e:
        raise e


# Unit Test
if __name__ == "__main__":
    # create a dynamodb object
    dynamodb = boto3.resource('dynamodb')
    # define the table name
    table_name = 'ymei_country_codes'
    # create the table
    create_a_DynamoDB_table(table_name, dynamodb, partition_key="Country Name", partition_key_type="S")
