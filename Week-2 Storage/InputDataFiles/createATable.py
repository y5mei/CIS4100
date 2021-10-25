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
session = boto3.Session(profile_name='xxxx',region_name='ca-central-1')
dynamodb = session.resource('dynamodb', region_name='ca-central-1')

# Create a new table called <username>UN_country_codes

table = dynamodb.create_table(
    TableName='myUN_country_codes',  # replace myUN_country_codes with <username>UN_country_codes
    KeySchema=[
        {
            'AttributeName': 'iso3',
            'KeyType': 'HASH'  #Partition key
        },
    ],
    AttributeDefinitions=[
        {
            'AttributeName': 'iso3',
            'AttributeType': 'S'
        },
    ],
    ProvisionedThroughput={
        'ReadCapacityUnits': 10,
        'WriteCapacityUnits': 10
    }
)

print("Table status:", table.table_status, table.table_name)

table.wait_until_exists()
print("Table ",table.table_name," created")

db = dynamodb.Table('myUN_country_codes')   # replace myUN_country_codes with <username>UN_country_codes

with open('un_shortlist.csv', 'r') as file:
    reader = csv.reader(file)
    for row in reader:
        print(row)
        item1 = db.put_item (
            Item={
            'iso3': row[0],
            'iso2': row[3],
            'name': row[1],
            'officialname': row[2]
            }
        )
        print (item1)

print ( "Database records loaded" )

