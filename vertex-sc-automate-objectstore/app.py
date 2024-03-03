"""
Updates Vertex Search & Conversation Datastore
"""
import os
import google.cloud.logging
from flask import Flask, render_template
from flask import request
import appModel
import logging

# pylint: disable=C0103
app = Flask(__name__)

# Instantiates a client
client = google.cloud.logging.Client()
client.setup_logging()

@app.route('/')
def controller():
    location = request.args.get('location')
    bucketName = request.args.get('bucketName')
    data_store_id = request.args.get('data_store_id')
    if (location !=None and bucketName !=None and data_store_id !=None):
        response =  appModel.refresh_document_store(location, data_store_id, bucketName)
        logging.info("Object Store Update Response: " + str(response))
        return str(response)
    else:
        return "Missing Parameters"

# If `entrypoint` is not defined in app.yaml, App Engine will look for an app
# called `app` in `main.py`.

if __name__ == '__main__':
    server_port = os.environ.get('PORT', '8080')
    app.run(debug=False, port=server_port, host='0.0.0.0')
