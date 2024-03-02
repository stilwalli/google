from typing import Optional
from typing import List

from google.api_core.client_options import ClientOptions
from google.cloud import discoveryengine
from google.cloud import storage
import requests

def get_project_id():
    metadata_server_url = "http://metadata.google.internal/computeMetadata/v1/project/project-id"
    headers = {"Metadata-Flavor": "Google"}
    response = requests.get(metadata_server_url, headers=headers)
    project_id = response.text
    return project_id

print(get_project_id())

def get_api_endpoint(location):
    if location != "global":
        return f'{location}-discoveryengine.googleapis.com'
    else:
        return None # Or a default global endpoint if you have one 
    
def refresh_document_store(
    project_id: str,
    location: str,
    data_store_id: str,
    gcs_bkt: str,

) -> str:
    client_options = ClientOptions(api_endpoint=get_api_endpoint(location))
    client = discoveryengine.DocumentServiceClient(client_options=client_options)
    parent = client.branch_path(
        project=project_id,
        location=location,
        data_store=data_store_id,
        branch="default_branch",
    )
    
    storage_client = storage.Client()
    bucket = storage_client.bucket(gcs_bkt)
    
    gcs_url_lst = []
    blobs = bucket.list_blobs()
    for blob in blobs:
        gcs_uri = "gs://" + gcs_bkt + "/" + blob.name
        gcs_url_lst.append(gcs_uri)

    
    request = discoveryengine.ImportDocumentsRequest(
        parent=parent,
        gcs_source=discoveryengine.GcsSource(
                input_uris=gcs_url_lst, data_schema="content"##"custom"
        ),
        # Options: `FULL`, `INCREMENTAL`
        reconciliation_mode=discoveryengine.ImportDocumentsRequest.ReconciliationMode.FULL,
        )
    
    operation = client.import_documents(request=request)
    response = operation.result()
    print ("result=", response)
    # Once the operation is complete,
    # get information from operation metadata
    metadata = discoveryengine.ImportDocumentsMetadata(operation.metadata)
    print (metadata)


get_project_id()