from google.cloud import storage
from google.cloud import aiplatform as ai
from vertexai.language_models import (
    TextGenerationModel,
    TextEmbeddingModel,
    ChatModel,
    InputOutputTextPair,
    CodeGenerationModel,
    CodeChatModel,
)


def callGenAI(prompt):
    # Do something with the data
    ai.init(project="genai-387917", location="us-central1")
    generation_model = TextGenerationModel.from_pretrained("text-bison@001")
    response = generation_model.predict(prompt=prompt)
    return response.text
