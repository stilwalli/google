from vertexai.preview.generative_models import GenerativeModel
import vertexai


class Agent:
    def __init__(self, project_id, location="us-central1", system=""):
        # Initialize Vertex AI
        vertexai.init(project=project_id, location=location)
        
        # Initialize the model
        self.model = GenerativeModel("gemini-1.5-pro")

        chat = self.model.start_chat()

        response = chat.send_message(system)

        
        # Store conversation history
        self.messages = []
        
        # If there's a system prompt, add it as the first message
        if system:
            self.messages.append({"role": "system", "content": system})
    
    def __call__(self, message):
        response = self.chat.send_message(message)
        return response.text
    

project_id = "scratchzone"
system_prompt = "You are a helpful AI assistant."
    
agent = Agent(
        project_id=project_id,
        system=system_prompt
    )

response = agent("Hello, how are you?")
print(response)