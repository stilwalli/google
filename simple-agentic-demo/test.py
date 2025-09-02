import vertexai
from vertexai.generative_models import GenerativeModel
import json
import re

class Tool:
    def __init__(self, name, func, description):
        self.name = name
        self.func = func
        self.description = description
    
    def __call__(self, *args, **kwargs):
        return self.func(*args, **kwargs)

class ReactAgent:
    def __init__(self, project_id, location="us-central1"):
        # Initialize Vertex AI
        vertexai.init(project=project_id, location=location)
        self.model = GenerativeModel("gemini-1.5-pro")
        self.chat = self.model.start_chat()
        self.tools = {}
        
        # Base prompt for the agent
        self.base_prompt = """You are a helpful AI assistant that can use tools to accomplish tasks.
Follow this format for your responses:

Thought: Reason about what needs to be done
Action: tool_name(parameters)
Observation: Result from tool
... (continue until task is complete)
Final Answer: The final response to the user's request

Available tools:
{tool_descriptions}

Remember to:
1. Use tools when needed
2. Think step by step
3. Provide a Final Answer when done
4. Use proper JSON format for tool parameters"""
    
    def add_tool(self, tool: Tool):
        """Add a tool to the agent's toolkit."""
        self.tools[tool.name] = tool
    
    def get_tool_descriptions(self):
        """Get formatted descriptions of all available tools."""
        return "\n".join([f"- {name}: {tool.description}" 
                         for name, tool in self.tools.items()])
    
    def extract_action(self, text):
        """Extract tool name and parameters from action text."""
        match = re.search(r'Action: (\w+)\((.*)\)', text)
        if not match:
            return None, None
        
        tool_name = match.group(1)
        params_str = match.group(2)
        
        try:
            # Handle empty parameters
            if not params_str.strip():
                params = {}
            else:
                params = json.loads(params_str)
            return tool_name, params
        except json.JSONDecodeError:
            return None, None
    
    def __call__(self, query):
        """Process a query using the RE-ACT framework."""
        # Initialize conversation with tools description
        prompt = self.base_prompt.format(
            tool_descriptions=self.get_tool_descriptions()
        )
        
        # Send initial prompt
        self.chat.send_message(prompt)
        
        # Send user query
        response = self.chat.send_message(query)
        full_response = []
        
        while True:
            response_text = response.text
            full_response.append(response_text)
            
            # Check if we've reached a final answer
            if "Final Answer:" in response_text:
                return "\n".join(full_response)
            
            # Extract and execute tool action
            tool_name, params = self.extract_action(response_text)
            
            if tool_name is None:
                return "Error: Could not parse action"
            
            if tool_name not in self.tools:
                return f"Error: Unknown tool {tool_name}"
            
            # Execute tool and get observation
            try:
                tool_result = self.tools[tool_name](**params)
                observation = f"Observation: {tool_result}"
                response = self.chat.send_message(observation)
            except Exception as e:
                return f"Error executing tool {tool_name}: {str(e)}"

# Example usage and tools
def main():
    # Example tools
    def search_web(query):
        return f"Simulated web search results for: {query}"
    
    def calculate(expression):
        return eval(expression)
    
    def get_weather(city):
        return f"Simulated weather for {city}: 22°C, Sunny"
    
    # Initialize agent
    agent = ReactAgent(project_id="your-project-id")
    
    # Add tools
    agent.add_tool(Tool(
        "search",
        search_web,
        "Search the web. Parameters: {\"query\": \"search query\"}"
    ))
    
    agent.add_tool(Tool(
        "calculate",
        calculate,
        "Perform mathematical calculations. Parameters: {\"expression\": \"math expression\"}"
    ))
    
    agent.add_tool(Tool(
        "weather",
        get_weather,
        "Get weather for a city. Parameters: {\"city\": \"city name\"}"
    ))
    
    # Example queries
    queries = [
        "What's the weather in London and what's 25 * 4?",
        "Search for Python programming and calculate 15 + 7"
    ]
    
    for query in queries:
        print(f"\nQuery: {query}")
        response = agent(query)
        print(f"Response:\n{response}")

if __name__ == "__main__":
    main()