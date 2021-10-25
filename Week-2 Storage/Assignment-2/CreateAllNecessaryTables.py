# Just run the main function of this python file,
# it will delete any tables start with ymei
# and it will create new tables as per the 5 CSV files

import time
from collections import defaultdict

from termcolor import colored

import DynamoDBPythonLib.deleteATable
import DynamoDBPythonLib.createATable
import DynamoDBPythonLib.addFieldToATable
import DynamoDBPythonLib.readATable
import DynamoDBPythonLib.bulkLoadATable
from DynamoDBPythonLib import *
import boto3
import csv

def __clean_language_data_set_to_a_list_of_dict__(csv_file="shortlist_languages.csv"):
    try:
        # error handling to make sure keys present
        file = open(csv_file, 'r')
        reader = csv.DictReader(file)
        header = reader.fieldnames  # header is a list
        listRow = []
        # load each of the data from the CSV file to the table
        for row in reader:
            if None not in row:
                row["Languages"] = [row["Languages"]]
            else:
                row["Languages"] = [row["Languages"]] + row[None]
                del row[None]

            listRow.append(row)

        return listRow
    except Exception as e:
        raise e


# upload all the non-econ data to a DynamoDB table called "ymei_country_non_econ“
def make_non_econ_table(areaFile="shortlist_area.csv", capitalsFile="shortlist_capitals.csv",
                        languagesFile="shortlist_languages.csv"):
    try:
        # create a dynamodb object
        dynamodb = boto3.resource('dynamodb')
        # get the low level client
        client = dynamodb.meta.client

        # read all the CSV files
        table_name = "ymei_country_non_econ"
        partition_key = "Country Name"
        # create a empty DynamoDB table:
        DynamoDBPythonLib.createATable.create_a_DynamoDB_table(table_name, dynamodb, partition_key="Country Name",
                                                               partition_key_type="S")
        # bulk load the area csv file to the empty table
        DynamoDBPythonLib.bulkLoadATable.bulk_load_to_a_DynamoDB_table(table_name, dynamodb, areaFile)
        # add capitals Field from a csv file to the table
        DynamoDBPythonLib.addFieldToATable.add_field_to_a_table(table_name, dynamodb, capitalsFile)
        # clean the language csv file and save it as a lis to dict
        rowList = __clean_language_data_set_to_a_list_of_dict__(languagesFile)
        # add the language field to the table
        DynamoDBPythonLib.addFieldToATable.__update_a_DynamoDB_table_from_a_valid_list_of_dict(table_name, dynamodb,
                                                                                               rowList, partition_key)
        # read the default name table provided by Prof. from AWS table
        nameList = DynamoDBPythonLib.readATable.read_a_DynamoDBTable_as_a_list_of_dict("UN_country_codes", dynamodb)
        # add the default name table content to the non econ table
        DynamoDBPythonLib.addFieldToATable.__update_a_DynamoDB_table_from_a_valid_list_of_dict(table_name, dynamodb,
                                                                                               nameList, partition_key,
                                                                                               file_partition_key="name")
        # # download the table and have a look at it
        # DynamoDBPythonLib.readATable.read_a_DynamoDBTable_to_CSV(table_name,dynamodb,"myfinalresult.csv")

    except Exception as e:
        error = "Can not create the table the non econ table due to the reason below:\n" + str(e)
        error_message = colored(error, "red")
        print(error_message)


def make_econ_table(gdppcFile="shortlist_gdppc.csv"):
    try:
        # use a nest dict to store all the econ data, and then save them in a csv file
        data_dict = defaultdict(lambda : {
            "Country": "NA",
            "Year":"NA",
            "GDP":"NA",
        })

        file2 = open(gdppcFile, 'r',encoding='utf-8-sig')
        reader2 = csv.DictReader(file2)
        header2 = reader2.fieldnames  # header is a list
        for row in reader2:
            countryName = row["Country"]
            del row["Country"]
            for k,v in row.items():
                year = k
                if not v:
                    v = "NA"
                # update the nested dict
                combinedKey = countryName+"#"+year
                data_dict[combinedKey]["GDP"] = v
                data_dict[combinedKey]["Country"] = countryName
                data_dict[combinedKey]["Year"] = year

        # prepare the file to write into
        file = open("temp_econ_data.csv", 'w+', newline='')  # need the last parameter to avoid blank line in between
        # write to file
        response = list(data_dict.values())
        dict_writer = csv.DictWriter(file, response[0].keys())
        dict_writer.writeheader()
        dict_writer.writerows(response)
        file.close()

        # now upload the temp file to the AWS as a table:
        # create a dynamodb object
        dynamodb = boto3.resource('dynamodb')
        # get the low level client
        client = dynamodb.meta.client
        econ_table_name = "ymei_econ_table"
        DynamoDBPythonLib.createATable.create_a_DynamoDB_table(econ_table_name, dynamodb, "Country", "S",
                                                               range_key="Year", range_key_type="N")
        DynamoDBPythonLib.bulkLoadATable.bulk_load_to_a_DynamoDB_table(econ_table_name, dynamodb, "temp_econ_data.csv")

    except Exception as e:
        error = "Can not create the table the econ table due to the reason below:\n" + str(e)
        error_message = colored(error, "red")
        print(error_message)

def make_population_table(curpopFile = "shortlist_curpop.csv"):
    try:
        # use a nest dict to store all the econ data, and then save them in a csv file
        data_dict = defaultdict(lambda : {
            "Country": "NA",
            "Year":"NA",
            "Currency": "NA",
            "Population":"NA",
        })

        # read the curpop data
        file = open(curpopFile, 'r',encoding='utf-8-sig')
        reader = csv.DictReader(file)
        header = reader.fieldnames  # header is a list

        # load each of the data from the CSV file to the table
        for row in reader:
            countryName = row["Country"]
            currency = row["Currency"]
            del row["Country"]
            del row["Currency"]
            for k,v in row.items():
                if k == "Population 1970":
                    year = "1970"
                else:
                    year = k
                if not v:
                    v = "NA"
                # update the nested dict
                combinedKey = countryName+"#"+year
                data_dict[combinedKey]["Country"]=countryName
                data_dict[combinedKey]["Year"] = year
                data_dict[combinedKey]["Currency"] = currency
                data_dict[combinedKey]["Population"] = v

        file = open("temp_population_data.csv", 'w+', newline='')  # need the last parameter to avoid blank line in between
        # write to file
        response = list(data_dict.values())
        dict_writer = csv.DictWriter(file, response[0].keys())
        dict_writer.writeheader()
        dict_writer.writerows(response)
        file.close()

        # now upload the temp file to the AWS as a table:
        # create a dynamodb object
        dynamodb = boto3.resource('dynamodb')
        # get the low level client
        client = dynamodb.meta.client
        econ_table_name = "ymei_population_table"
        DynamoDBPythonLib.createATable.create_a_DynamoDB_table(econ_table_name, dynamodb, "Country", "S",
                                                               range_key="Year", range_key_type="N")
        DynamoDBPythonLib.bulkLoadATable.bulk_load_to_a_DynamoDB_table(econ_table_name, dynamodb, "temp_population_data.csv")

    except Exception as e:
        error = "Can not create the table the population table due to the reason below:\n" + str(e)
        error_message = colored(error, "red")
        print(error_message)

def createAllTables(areaFile="../InputDataFiles/shortlist_area.csv", capitalsFile="../InputDataFiles/shortlist_capitals.csv",
                        languagesFile="../InputDataFiles/shortlist_languages.csv", gdppcFile="../InputDataFiles/shortlist_gdppc.csv",curpopFile = "../InputDataFiles/shortlist_curpop.csv"):
    try:
        # create a dynamodb object
        dynamodb = boto3.resource('dynamodb')
        # get the low level client
        client = dynamodb.meta.client

        # read all the CSV files
        # non_econ_table_name = "ymei_country_non_econ"
        # econ_table_name = "ymei_econ_table"
        # population_table_name = "ymei_population_table"

        # Delete these files if they are already there
        # DynamoDBPythonLib.deleteATable.delete_a_DynamoDB_table(non_econ_table_name, dynamodb)
        # DynamoDBPythonLib.deleteATable.delete_a_DynamoDB_table(population_table_name, dynamodb)
        # DynamoDBPythonLib.deleteATable.delete_a_DynamoDB_table(econ_table_name, dynamodb)
        make_non_econ_table(areaFile,capitalsFile,languagesFile)
        make_econ_table(gdppcFile)
        make_population_table(curpopFile)
        # return True
    except Exception as e:
        error = "Can not create the table due to the reason below:\n" + str(e)
        error_message = colored(error, "red")
        print(error_message)

def deleteAllMyTables():
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

if __name__ == '__main__':
    # create a dynamodb object
    dynamodb = boto3.resource('dynamodb')
    # get the low level client
    client = dynamodb.meta.client
    existing_tables = client.list_tables()['TableNames']
    # print(existing_tables)
    # read all the CSV files
    non_econ_table_name = "ymei_country_non_econ"
    econ_table_name = "ymei_econ_table"
    population_table_name = "ymei_population_table"

    # Delete these files if they are already there
    if non_econ_table_name in existing_tables:
        # print("delete"+non_econ_table_name)
        DynamoDBPythonLib.deleteATable.delete_a_DynamoDB_table(non_econ_table_name, dynamodb)
    if econ_table_name in existing_tables:
        # print("delete"+econ_table_name)
        DynamoDBPythonLib.deleteATable.delete_a_DynamoDB_table(econ_table_name, dynamodb)
    if population_table_name in existing_tables:
        # print("delete"+population_table_name)
        DynamoDBPythonLib.deleteATable.delete_a_DynamoDB_table(population_table_name, dynamodb)
    time.sleep(10)
    createAllTables()
    # make_non_econ_table()
    # make_population_table()
    # make_econ_table()