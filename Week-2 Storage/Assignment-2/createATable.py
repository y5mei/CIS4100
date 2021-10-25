#
#   Example code to create and populate a NoSQL DynamoDB table 
#   named UN_country_codes that will be used in Assignment 2
# 
#   The name in this code has been changed so that you cannot
#   accidently try to overwrite the table if you just execute 
#   this code
#
import boto3
import csv

# Establish a connection to the AWS resource dynamodb
# Replace xxxx with your name
session = boto3.Session(profile_name='default', region_name='ca-central-1')
dynamodb = session.resource('dynamodb', region_name='ca-central-1')

# Create a new table called <username>UN_country_codes

try:
    table = dynamodb.create_table(
        TableName='ymei_country_codes',  # replace myUN_country_codes with <username>UN_country_codes
        KeySchema=[
            {
                'AttributeName': 'iso3',
                'KeyType': 'HASH'  # Partition key
            },
            {
                'AttributeName': 'Area',
                'KeyType': 'RANGE'  # sort key
            },
        ],
        AttributeDefinitions=[
            {
                'AttributeName': 'iso3',
                'AttributeType': 'S'
            },
            {
                'AttributeName': 'Area',
                'AttributeType': 'N'
            },
        ],
        ProvisionedThroughput={
            'ReadCapacityUnits': 10,
            'WriteCapacityUnits': 10
        }
    )
    print("Table status:", table.table_status, table.table_name)
    table.wait_until_exists()
    print("Table ", table.table_name, " created")
except Exception as e:
    print(e)

table = dynamodb.Table('ymei_country_codes')  # replace myUN_country_codes with <username>UN_country_codes

###############################################################################################################
#
# These are the CRUD examples
# Re： https://boto3.amazonaws.com/v1/documentation/api/latest/guide/dynamodb.html
###############################################################################################################

########## To Create ##########################################################################################
# this program will assume the input csv always contain a header
with open('shortlist_area.csv', 'r') as file:
    reader = csv.DictReader(file)
    header = reader.fieldnames

    for row in reader:
        print(row)
        item1 = table.put_item(
            Item={
                'iso3': row['ISO3'],
                'name': row['Country Name'],
                'Area': int(row["Area"]),

            }
        )
        print(item1)

print("Database records loaded")
########### To Read ##########################################################################################
response = table.get_item(
    Key={
        'iso3': "ALB",
        'Area': 1,
    }
)

item = response['Item']
print(item['Area'])
########### To Update ##########################################################################################
################################################################################################################
# The thing is, key can not be updated, in order to update a key, we need to delete and re-new a new element
################################################################################################################
table.update_item(
    Key={
        'iso3': "ALB",
        'Area': 1,
    },
    UpdateExpression='SET #field1 = :val1, #field2 = :val2', # field name need a # in the front, values need a : in the front
    ExpressionAttributeNames={
        "#field1": "age",
        "#field2": "name",
    },
    ExpressionAttributeValues={
        ':val1': 26,
        ':val2': "pig country",
    },
)

# If we attach a new attribute, the other elements that does not have this attribute will not even return this attribute
response = table.get_item(
    Key={
        'iso3': "DZA",
        'Area': 2,
    }
)
item = response['Item']
print(item)

response = table.get_item(
    Key={
        'iso3': "ALB",
        'Area': 1,
    },
)
item = response['Item']
print(item)
########### To delete ##########################################################################################
table.delete_item(
    Key = {
        'iso3': "DZA",
        'Area': 2,
    }
)

# attribute can be a list as well: L

# https://docs.aws.amazon.com/amazondynamodb/latest/APIReference/API_AttributeValue.html