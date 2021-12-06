import logging

import azure.functions as func
from azure.storage.blob import BlobServiceClient
from azure.storage.blob import ContainerClient

CONNECTION_STRING = "DefaultEndpointsProtocol=https;AccountName=cis4010;AccountKey=QHinGrxrxW082ZzBvBmQ7nd4JXzNQUbAWzKjwlLG4VBf7QXi+MIguhCmO2pEU9A0txPJMkM6zTcdlcBu4XT0vg==;EndpointSuffix=core.windows.net"
func.HttpResponse(
    f"===================== Hello, Mayson. ==============================")


def main(req: func.HttpRequest) -> func.HttpResponse:
    # make a container when a new file was added
    container_client = ContainerClient.from_connection_string(conn_str=CONNECTION_STRING,
                                                              container_name="mymaysoncontainer")

    container_client.create_container()

    logging.info('Python HTTP trigger function processed a request.')

    name = req.params.get('name')
    if not name:
        try:
            req_body = req.get_json()
        except ValueError:
            pass
        else:
            name = req_body.get('name')

    if name:
        return func.HttpResponse(f"Hello, {name}. This HTTP triggered function executed successfully. Mayson Mayson")
    else:
        return func.HttpResponse(
            "This HTTP triggered function executed successfully. Pass a name in the query string or in the request body for a personalized response.",
            status_code=200
        )
