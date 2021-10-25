import boto3
from termcolor import colored


# reference:https://boto3.amazonaws.com/v1/documentation/api/latest/guide/dynamodb.html



def delete_a_DynamoDB_table(table_name: str, dynamodb: object) -> None:
    """ delete a table from the dynamoDB resource object
    :param table_name: a str value as the name of the table user wants to delete
    :param dynamodb: this is a dynamodb resource object, you can obtain one of this instance by boto3.resource("dynamodb")
    """
    try:
        table = dynamodb.Table(table_name)
        table.delete()
    except Exception as e:
        error = "Can not delete the table: "+table_name+" due to the reason below\n"+str(e)
        error_message = colored(error, "red")
        print(error_message)
        # print(e)

# Unit Test
if __name__ == "__main__":
    dynamodb = boto3.resource('dynamodb')
    table_name = 'ymei_country_codes'
    delete_a_DynamoDB_table(table_name, dynamodb)




