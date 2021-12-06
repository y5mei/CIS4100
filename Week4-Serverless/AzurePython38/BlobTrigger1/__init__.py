import logging

import azure.functions as func
# samples-workitems/220.png

# from azure.storage.blob import BlobServiceClient
# from azure.storage.blob import BlockBlobService
from azure.storage.blob import ContainerClient
# from azure.storage.blob import PublicAccess
# from azure.storage.blob import ContentSettings


# how to use the SDK: https://pypi.org/project/azure-storage-blob/
# CONNECTION_STRING = "DefaultEndpointsProtocol=https;AccountName=cis4010;AccountKey=QHinGrxrxW082ZzBvBmQ7nd4JXzNQUbAWzKjwlLG4VBf7QXi+MIguhCmO2pEU9A0txPJMkM6zTcdlcBu4XT0vg==;EndpointSuffix=core.windows.net"
# MY_ACCOUNT_NAME = "cis4010"
# MY_ACCOUNT_KEY = "QHinGrxrxW082ZzBvBmQ7nd4JXzNQUbAWzKjwlLG4VBf7QXi+MIguhCmO2pEU9A0txPJMkM6zTcdlcBu4XT0vg=="

# My local settings

# Display name:MyEmulator
# Account name:devstoreaccount1
# Account key:Eby8vdM02xNOcqFlqUwJPLlmEtlCDXJ1OUzFT50uSRZ6IFsuFq2UVErCz4I6tq/K1SZFPTOtr/KBHBeksoGMGw ==
# Default endpoints protocol:
# http
# Blob endpoint:
# http: // 127.0.0.1: 10000/devstoreaccount1
# Queue endpoint:
# http: // 127.0.0.1: 10001/devstoreaccount1
# Table endpoint:
# http: // 127.0.0.1: 10002/devstoreaccount1

def main(myblob: func.InputStream):

    try:
        logging.info(str(myblob))

        logging.info(f"Python blob Mayson trigger function processed blob \n"
                     f"Name: {myblob.name}\n"
                     f"Blob Size: {myblob.length} bytes")

        # make a container when a new file was added
        # container_client = ContainerClient.from_connection_string(conn_str=CONNECTION_STRING,
        #                                                           container_name="logfile")

        # container_client.create_container()

        # block_blob_service = BlockBlobService(
        #     account_name=MY_ACCOUNT_NAME, account_key=MY_ACCOUNT_KEY)

        # block_blob_service.create_container(
        #     'mycontainer', public_access=PublicAccess.Container)

    except Exception as e:
        raise e
