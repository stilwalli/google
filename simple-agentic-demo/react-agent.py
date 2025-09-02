import vertexai
from vertexai.generative_models import GenerativeModel
import json


# Initialize Vertex AI and model
def init_chat(project_id):
    vertexai.init(project=project_id)
    model = GenerativeModel("gemini-1.5-pro")
    return model.start_chat()

def calculate(what):
    return eval(what)

def average_dog_weight(name):
    if name in "Scottish Terrier": 
        return("Scottish Terriers average 20 lbs")
    elif name in "Border Collie":
        return("a Border Collies average weight is 37 lbs")
    elif name in "Toy Poodle":
        return("a toy poodles average weight is 7 lbs")
    else:
        return("An average dog weights 50 lbs")

known_actions = {
    "calculate": calculate,
    "average_dog_weight": average_dog_weight
}



# Basic prompt
PROMPT = """
You run in a loop of Thought, Action, PAUSE, Observation.
At the end of the loop you output an Answer
Use Thought to describe your thoughts about the question you have been asked.
Use Action to run one of the actions available to you - then return PAUSE.
Observation will be the result of running those actions.

Your available actions are:

calculate:
e.g. calculate: 4 * 7 / 3
Runs a calculation and returns the number - uses Python so be sure to use floating point syntax if necessary

average_dog_weight:
e.g. average_dog_weight: Collie
returns average weight of a dog when given the breed

Example session:

Question: How much does a Bulldog weigh?
Thought: I should look the dogs weight using average_dog_weight
Action: average_dog_weight: Bulldog
PAUSE

You will be called again with this:

Observation: A Bulldog weights 51 lbs

You then output:

Answer: A bulldog weights 51 lbs
""".strip()



# Example usage
def main():
    # Initialize
    chat = init_chat("scratchzone")
    abot = Agent(prompt)
    
    # Run some queries
    print("Query 1: What is 25 * 3 and can you search for Python programming")
    run_agent(chat, "What is 25 * 3 and can you search for Python programming?")
    
    #print("\nQuery 2: Basic search")
    #run_agent(chat, "Search for AI tutorials")

if __name__ == "__main__":
    main()