import os

import vertexai
from vertexai.preview.generative_models import GenerativeModel

import os

# Suppress logging warnings
os.environ["GRPC_VERBOSITY"] = "ERROR"
os.environ["GLOG_minloglevel"] = "2"

PROJECT_ID = "scratchzone"  # @param {type: "string", placeholder: "[your-project-id]" isTemplate: true}
LOCATION = "us-central1"

vertexai.init(project=PROJECT_ID, location=LOCATION)
model = GenerativeModel("gemini-1.5-pro")
chat = model.start_chat()

response = chat.send_message(
    """You are an astronomer, knowledgeable about the solar system.
How many moons does Mars have? Tell me some fun facts about them.
"""
)

print(response.text)

response = chat.send_message(
    """
How many starts does Mars have? Tell me some fun facts about them.
"""
)

print(response.text)