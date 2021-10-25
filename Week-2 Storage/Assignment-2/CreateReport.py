import os

import boto3
from collections import defaultdict

from tabulate import tabulate
from termcolor import colored

from DynamoDBPythonLib.readATable import read_a_DynamoDBTable_item_with_partition_key, \
    read_a_DynamoDBTable_item_with_partition_key_order_key_if_NA_return_None, read_a_DynamoDBTable_as_a_list_of_dict


# return a list of all country names from professor's table
def __get_a_list_of_all_country_names__():
    # create a dynamodb object
    dynamodb = boto3.resource('dynamodb')
    # get the low level client
    client = dynamodb.meta.client
    non_econ_table_name = "ymei_country_non_econ"
    econ_table_name = "ymei_econ_table"
    population_table_name = "ymei_population_table"
    # get a name list of all the country names around the world
    country_name_list = []
    hashmap_table_name = "UN_country_codes"
    # need to find out the counter name [partition key] based on the iso3, I need a hashmap
    # read a list of hash map from the table provided by professor
    iso3_hashmap_list = read_a_DynamoDBTable_as_a_list_of_dict(hashmap_table_name, dynamodb)
    # print(iso3_hashmap_list)
    # need to build a hashmap between iso3 to countryname
    for country in iso3_hashmap_list:
        country_name = country['name']
        country_name_list.append(country_name)
    return country_name_list


def cached_country_report(country_name: str):
    # create a dynamodb object
    dynamodb = boto3.resource('dynamodb')
    # get the low level client
    client = dynamodb.meta.client
    non_econ_table_name = "ymei_country_non_econ"
    econ_table_name = "ymei_econ_table"
    population_table_name = "ymei_population_table"
    hashmap_table_name = "UN_country_codes"

    # cache a dict to map country name and area
    cached_country_data = read_a_DynamoDBTable_as_a_list_of_dict(non_econ_table_name, dynamodb)
    country_info_hashmap = {}
    area_list_for_all_countries = []  # this is a additonal information prepare for the header, I am only saving area, country name
    for data in cached_country_data:
        country = data["Country Name"]
        country_info_hashmap[country] = data
        area_list_for_all_countries.append((float(data["Area"]), data["Country Name"]))
    # print(country_info_hashmap["China"])
    # {'iso3': 'CHN', 'Languages': ['Standard Chinese'], 'iso2': 'CN', 'Country Name': 'China', 'Area': '9596961',
    # 'Capital': 'Beijing', 'officialname': "the People's Republic of China", 'ISO3': 'CHN'}

    #################################################################################################################
    #
    # Wash the population data
    #
    #################################################################################################################

    # cached all the population data to local, and put them in hashmap by year
    cached_population_table = read_a_DynamoDBTable_as_a_list_of_dict(population_table_name, dynamodb)
    # but them in a bin
    global_population_result_by_year = defaultdict(lambda: [])
    for data in cached_population_table:
        # {'Currency': 'Argentine Peso', 'Country': 'Argentina', 'Year': Decimal('2018'), 'Population': '44361150'}, {'Currency': 'Kwanza', 'Country': 'Angola', 'Year': Decimal('2018'), 'Population': '30809787'}
        #
        if not data["Population"] or data["Population"] == "NA":
            continue

        # have to make sure data has the population field
        year = data['Year']
        country = data["Country"]
        area = country_info_hashmap[country]["Area"]
        # calculate population density
        population = data['Population']
        population_density = float(population) / float(area)
        data['Population Num'] = float(population)
        data['Population Density'] = population_density
        global_population_result_by_year[year].append(data)

    population_result_for_a_country = []
    for year in range(1970, 2020, 1):
        this_year_global_population_data_list = global_population_result_by_year[year]
        this_year_global_population_data_list.sort(key=lambda x: -x["Population Num"])
        for i, data in enumerate(this_year_global_population_data_list):
            if data["Country"] == country_name:
                data["Population Rank"] = i + 1

        this_year_global_population_data_list.sort(key=lambda x: -x["Population Density"])
        for i, data in enumerate(this_year_global_population_data_list):
            if data["Country"] == country_name:
                data["Population Density Rank"] = i + 1
                population_result_for_a_country.append(data)

    population_table_content = []
    for data in population_result_for_a_country:
        population_table_content.append(
            [data["Year"], data["Population"], data["Population Rank"], data["Population Density"],
             data["Population Density Rank"]])
    # population_result_for_a_country[0] =
    # {'Currency': 'Yuan Renminbi', 'Country': 'China', 'Year': Decimal('2019'), 'Population': '1433783686',
    #  'Population Num': 1433783686.0, 'Population Density': 149.39976165371516, 'Population Rank': 1,
    #  'Population Density Rank': 8}

    #################################################################################################################
    #
    # Wash the econ data
    #
    #################################################################################################################
    # get the curreny:
    pCurrency = "Currency: "+ str(population_result_for_a_country[0]["Currency"])

    # cached all the econ data and put them in a hashmap
    cached_econ_table = read_a_DynamoDBTable_as_a_list_of_dict(econ_table_name, dynamodb)
    # but them in a bin
    global_econ_result_by_year = defaultdict(lambda: [])
    for data in cached_econ_table:
        # data = {'GDP': '234', 'Country': 'Burundi', 'Year': Decimal('2010')}
        # print(data)
        if not data["GDP"] or data["GDP"] == "NA":
            continue
        #
        # have to make sure data has the GDP field
        year = data['Year']
        country = data["Country"]
        GDP = data["GDP"]
        data['GDP Num'] = float(GDP)
        global_econ_result_by_year[year].append(data)
    #
    econ_result_for_a_country = []
    for year in range(1970, 2020, 1):
        this_year_global_econ_data_list = global_econ_result_by_year[year]
        this_year_global_econ_data_list.sort(key=lambda x: -x["GDP Num"])
        for i, data in enumerate(this_year_global_econ_data_list):
            if data["Country"] == country_name:
                data["GDP Rank"] = i + 1
                econ_result_for_a_country.append(data)

    econ_table_content = []
    for data in econ_result_for_a_country:
        econ_table_content.append(
            [data["Year"], data["GDP"], data["GDP Rank"]])

    # Let's prepare the header section
    cif = country_info_hashmap[country_name]
    pNameofCountry = cif["Country Name"]
    pOfficialName = "Official Names: " + str(cif["officialname"])
    pArea = str(cif["Area"])
    # need a workrank
    area_list_for_all_countries.sort(reverse=True)  # sort all the area from big to small
    for i, n in enumerate(area_list_for_all_countries):
        if n[1] == pNameofCountry:
            pAreaRank = str(i+1)
    pOfficialLan = "/".join(cif["Languages"])
    pCapitalCity = str(cif["Capital"])
    # print(pAreaRank)

    print("Country Level Report:")
    print(colored(pNameofCountry, 'green'))
    print(colored(pOfficialName, 'green'))
    print(tabulate([["Official/National Languages: " + pOfficialLan + "\nCapital City:     " + pCapitalCity]],
                   ["Area: " + pArea + " sq km (World Rank: " + pAreaRank + " )"], tablefmt='fancy_grid'))

    # let's prepare the population density table now:
    print(colored("POPULATION", 'green'))
    population_table_headers = ["Year", "Population", "Rank", "Population Desity \n(People/sq km)", "Rank"]
    print(tabulate(population_table_content, population_table_headers, tablefmt='fancy_grid'))

    # let's perpare the econ gdp table
    print(colored("ECONOMICS", 'green'))
    # NEED TO GET TEH CURRENCY
    print(colored(pCurrency, 'green'))
    econ_table_headers = ["Year", "GDPPC", "Rank"]
    print(tabulate(econ_table_content, econ_table_headers, tablefmt='fancy_grid'))

def cached_global_report(input_year: int):
    # create a dynamodb object
    dynamodb = boto3.resource('dynamodb')
    # get the low level client
    client = dynamodb.meta.client
    non_econ_table_name = "ymei_country_non_econ"
    econ_table_name = "ymei_econ_table"
    population_table_name = "ymei_population_table"
    hashmap_table_name = "UN_country_codes"

    # cache a dict to map country name and area
    cached_country_data = read_a_DynamoDBTable_as_a_list_of_dict(non_econ_table_name, dynamodb)
    country_info_hashmap = {}
    area_list_for_all_countries = []  # this is a additonal information prepare for the header, I am only saving area, country name
    for data in cached_country_data:
        country = data["Country Name"]
        country_info_hashmap[country] = data
        area_list_for_all_countries.append((float(data["Area"]), data["Country Name"]))
    # print(country_info_hashmap["China"])
    # {'iso3': 'CHN', 'Languages': ['Standard Chinese'], 'iso2': 'CN', 'Country Name': 'China', 'Area': '9596961',
    # 'Capital': 'Beijing', 'officialname': "the People's Republic of China", 'ISO3': 'CHN'}
    ####################################################################
    # The 2nd global Area table
    ####################################################################
    # need a workrank
    area_list_for_all_countries.sort(reverse=True)  # sort all the area from big to small
    # print(area_list_for_all_countries)
    area_table_content=[]
    for i, data in enumerate(area_list_for_all_countries):
        countryName = data[1]
        countryArea  = str(data[0])
        # print(countryName)
        rank = i+1
        area_table_content.append([countryName, countryArea, rank])
    #################################################################################################################
    #
    # Wash the population data
    #
    #################################################################################################################

    # cached all the population data to local, and put them in hashmap by year
    cached_population_table = read_a_DynamoDBTable_as_a_list_of_dict(population_table_name, dynamodb)
    # but them in a bin, key is year
    global_population_result_by_year = defaultdict(lambda: [])
    for data in cached_population_table:
        # {'Currency': 'Argentine Peso', 'Country': 'Argentina', 'Year': Decimal('2018'), 'Population': '44361150'}, {'Currency': 'Kwanza', 'Country': 'Angola', 'Year': Decimal('2018'), 'Population': '30809787'}
        #
        if not data["Population"] or data["Population"] == "NA":
            continue

        # have to make sure data has the population field
        year = data['Year']
        country = data["Country"]
        area = country_info_hashmap[country]["Area"]
        # calculate population density
        population = data['Population']
        population_density = float(population) / float(area)
        data['Population Num'] = float(population)
        data['Population Density'] = population_density
        global_population_result_by_year[year].append(data)

    ####################################################################
    # The 1st global population table
    ####################################################################
    population_table_content = []
    this_year_global_population_data_list = global_population_result_by_year[input_year]
    this_year_global_population_data_list.sort(key=lambda x: -x["Population Num"])
    for i, data in enumerate(this_year_global_population_data_list):
        data["Population Rank"] = i + 1
        population_table_content.append([ data["Country"], data["Population"], data["Population Rank"]])
    ####################################################################
    # The 3rd global population density table
    ####################################################################
    population_density_table_content=[]
    this_year_global_population_data_list.sort(key=lambda x: -x["Population Density"])
    for i, data in enumerate(this_year_global_population_data_list):
        data["Population Density Rank"] = i + 1
        population_density_table_content.append([ data["Country"], data["Population Density"], data["Population Density Rank"]])

    # population_result_for_a_country[0] =
    # {'Currency': 'Yuan Renminbi', 'Country': 'China', 'Year': Decimal('2019'), 'Population': '1433783686',
    #  'Population Num': 1433783686.0, 'Population Density': 149.39976165371516, 'Population Rank': 1,
    #  'Population Density Rank': 8}


    #################################################################################################################
    #
    # Print out the report
    #
    #################################################################################################################
    # Let's prepare the header section
    # cif = country_info_hashmap[country_name]
    pyear = "Year: "+str(input_year)
    pNumofCountrys = "Number of Countries: "+str(len(country_info_hashmap))

    print("GLOBAL REPORT:")
    print(colored(pyear, 'green'))
    print(pNumofCountrys)

    print(colored("TABLE OF COUNTRIES RANKED BY POPULATION (largest to smallest)", 'green'))
    print(tabulate(population_table_content, ["Country Name", "Population","Rank"],tablefmt='fancy_grid'))

    print(colored("TABLE OF COUNTRIES RANKED BY AREA (largest to smallest)", 'green'))
    print(tabulate(area_table_content, ["Country Name", "Area (sq km)", "Rank"], tablefmt='fancy_grid'))

    print(colored("TABLE OF COUNTRIES RANKED BY DENSITY (largest to smallest)", 'green'))
    print(tabulate(population_density_table_content, ["Country Name", "Density (people/ sq km)", "Rank"], tablefmt='fancy_grid'))


    #################################################################################################################
    #
    # Wash the econ data
    #
    #################################################################################################################


    # cached all the econ data and put them in a hashmap
    cached_econ_table = read_a_DynamoDBTable_as_a_list_of_dict(econ_table_name, dynamodb)
    # but them in a bin
    global_econ_result_by_country = defaultdict(lambda: [])
    for data in cached_econ_table:
        # data = {'GDP': '234', 'Country': 'Burundi', 'Year': Decimal('2010')}
        # print(data)
        if not data["GDP"] or data["GDP"] == "NA":
            continue
        #
        # have to make sure data has the GDP field
        year = data['Year']
        country = data["Country"]
        GDP = data["GDP"]
        data['GDP Num'] = float(GDP)
        global_econ_result_by_country[country].append(data)
    #

    # get the name list of all the countries
    country_name_list = list(country_info_hashmap.keys())
    country_name_list.sort()

    for star_year in range(1970, 2020, 10):
        result_for_1970 = []
        for c in country_name_list:
            this_country_global_econ_data_list = global_econ_result_by_country[c]
            this_country_result = []
            this_country_result.append(c)

            for y in range(star_year, star_year + 10):
                found_data = False
                for data in this_country_global_econ_data_list:
                    if data["Year"] == y:
                        found_data = True
                        this_country_result.append(data['GDP Num'])
                if not found_data:
                    this_country_result.append(' ')

            result_for_1970.append(this_country_result)

        header_for_1970 = ["Country Name"]
        for i in range(star_year, star_year + 10, 1):
            header_for_1970.append(str(i))

        print(colored("GDP Per Capita for all Countries", 'green'))
        print(colored(str(star_year) + " Table", 'green'))
        print(tabulate(result_for_1970, header_for_1970,
                       tablefmt='fancy_grid'))




if __name__ == '__main__':
    # print the country report to console
    cached_country_report("Canada")
    # print the global report to console
    # cached_global_report(1999)
