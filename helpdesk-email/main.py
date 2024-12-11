# Import statements
from google.cloud import storage, discoveryengine_v1 as discoveryengine
from google.api_core.client_options import ClientOptions
from datetime import datetime, timezone
from email import message_from_string
from vertexai.generative_models import (
    GenerationConfig,
    GenerativeModel,
    HarmCategory,
    HarmBlockThreshold
)
import functions_framework
import vertexai
import json
import os
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail

# Configuration
DEFAULT_CONFIG = {
    'PROJECT_ID': 'scratchzone',
    'LOCATION': 'us-central1',
    'BUCKET_NAME': 'ninja-email-helpdesk',
    'MODEL_ID': 'gemini-1.5-flash-001',
    'ENGINE_ID': 'ninja-app_1731338638113'
}

def init_vertex_ai():
    """Initialize Vertex AI with project settings"""
    project_id = os.environ.get("GOOGLE_CLOUD_PROJECT", DEFAULT_CONFIG['PROJECT_ID'])
    location = os.environ.get("GOOGLE_CLOUD_REGION", DEFAULT_CONFIG['LOCATION'])
    vertexai.init(project=project_id, location=location)

def get_model_config():
    """Get model configuration settings"""
    generation_config = GenerationConfig(
        temperature=0.5,
        top_p=1.0,
        top_k=32,
        candidate_count=1,
        max_output_tokens=8192
    )
    
    safety_settings = {
        HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_LOW_AND_ABOVE,
        HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_LOW_AND_ABOVE,
        HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_LOW_AND_ABOVE,
        HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_LOW_AND_ABOVE
    }
    
    return generation_config, safety_settings

def extract_email_body(email_content):
    """Extract plain text body from email content"""
    msg = message_from_string(email_content)
    body = ''
    
    if msg.is_multipart():
        for part in msg.walk():
            if part.get_content_type() == 'text/plain':
                body = part.get_payload(decode=True).decode()
                break
    elif msg.get_content_type() == 'text/plain':
        body = msg.get_payload(decode=True).decode()
    
    return body

def store_email(email_data):
    """Store email content in GCP bucket"""
    storage_client = storage.Client()
    bucket = storage_client.bucket(DEFAULT_CONFIG['BUCKET_NAME'])
    
    timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
    clean_sender = email_data['sender'].split('@')[0].replace('.', '_')
    base_filename = f"{timestamp}_{clean_sender}"
    
    content_blob = bucket.blob(f"emails/{base_filename}/content.json")
    content_blob.upload_from_string(
        json.dumps(email_data),
        content_type='application/json'
    )


def get_ai_response(content, system_instructions):
    """Get AI-generated response using Vertex AI"""
    init_vertex_ai()
    model = GenerativeModel(
        DEFAULT_CONFIG['MODEL_ID'],
        system_instruction=system_instructions
    )
    
    generation_config, safety_settings = get_model_config()
    response = model.generate_content(
        [f"User input: {content}\nAnswer:"],
        generation_config=generation_config,
        safety_settings=safety_settings
    )
    
    return response.text

def identify_topics(email_content):
    """Identify topics from email content using AI"""
    system_instructions = [
        "You are a skilled customer support agent.",
        "Users will contact you with diverse questions and problems.",
        "Your primary task is to accurately identify the issue in each user's query.",
        "Give response in JSON object",
        """Example {"issues": [{"issue": "First issue"}, {"issue": "Second issue"}]}"""
    ]
    
    response = get_ai_response(email_content, system_instructions)
    json_response = response.replace('```json', '').replace('```', '').strip()
    
    try:
        json_data = json.loads(json_response)
        return [item['issue'] for item in json_data['issues']]
    except Exception as e:
        print(f"Error parsing topics: {e}")
        return []

def search_knowledge_base(topic):
    """Search knowledge base for relevant information"""
    client_options = ClientOptions(api_endpoint=f"global-discoveryengine.googleapis.com")
    client = discoveryengine.SearchServiceClient(client_options=client_options)
    
    serving_config = (
        f"projects/{DEFAULT_CONFIG['PROJECT_ID']}/locations/global/collections/"
        f"default_collection/engines/{DEFAULT_CONFIG['ENGINE_ID']}/servingConfigs/default_config"
    )
    
    content_search_spec = discoveryengine.SearchRequest.ContentSearchSpec(
        snippet_spec=discoveryengine.SearchRequest.ContentSearchSpec.SnippetSpec(
            return_snippet=False
        ),
        summary_spec=discoveryengine.SearchRequest.ContentSearchSpec.SummarySpec(
            summary_result_count=1,
            include_citations=False,
            ignore_adversarial_query=True,
            ignore_non_summary_seeking_query=True
        )
    )
    
    request = discoveryengine.SearchRequest(
        serving_config=serving_config,
        query=topic,
        page_size=1,
        content_search_spec=content_search_spec
    )
    
    response = client.search(request)
    return response.summary.summary_text if response.summary else ""


def generate_email_response(search_results):
    """Generate final email response using AI"""
    system_instructions = [
        "You are a skilled customer support agent.",
        "You are responding to the customer on an email",
        "Summarize the email content.",
        "Keep original response as is"
    ]
    
    return get_ai_response(search_results, system_instructions)


def extract_email_info(email_string):
   # Initialize variables
   name = email_string
   email = ""
   
   # If email format contains <, extract both name and email
   if '<' in email_string:
       # Split into name and email parts
       name = email_string.split('<')[0].strip()
       email = email_string.split('<')[1].replace('>', '').strip()
   
   return {
       'name': name,
       'email': email
   }

@functions_framework.http
def handle_inbound_email(request):
    """Handle incoming email webhook"""
    try:
        print ("handle_inbound_email....")
        form_data = request.form
        sender = form_data.get('from', 'unknown-sender')
        subject = form_data.get('subject', 'no-subject')
        email_content = form_data.get('email', '')
        result = extract_email_info(sender)
        sender_name = result['name']
        email = result['email']
        # Extract email body
        body = extract_email_body(email_content)
        # Store email
        email_data = {
            'sender': sender,
            'subject': subject,
            'Body': body,
            'timestamp': datetime.now(timezone.utc).isoformat()
        }
        #store_email(email_data)
        # Process and generate response
        topics = identify_topics(body)
        print ("Main Topics of the Email: ", topics)
        search_results = []
        for topic in topics:
            result = search_knowledge_base(topic)
            print ("result: ", result)
            if result:
                search_results.append(result)
        
        print("Search Results: ", search_results)
        final_response = generate_email_response("\n".join(search_results))
        sendEmail(sender_name, email, subject, final_response)
        return ('Email processed successfully', 200)
    
    except Exception as e:
        print(f"Error processing email: {str(e)}")
        return ('Error processing email', 500)
    

def test_inbound_email(sender_name, email, subject, body):
    """Handle incoming email webhook"""
    try:        
        # Process and generate response
        topics = identify_topics(body)
        print ("Main Topics of the Email: ", topics)
        search_results = []
        for topic in topics:
            result = search_knowledge_base(topic)
            if result:
                search_results.append(result)
        
        #print("search_results: ", search_results)
        final_response = generate_email_response("\n".join(search_results))
        print (final_response)
        sendEmail(sender_name, email, subject, final_response)
        
        return ('Email processed successfully', 200)
    
    except Exception as e:
        print(f"Error processing email: {str(e)}")
        return ('Error processing email', 500)
    
def generate_email(name, email_body):
  """Generates an email using a template.

  Args:
    name: The name of the recipient.
    email_body: The body of the email.

  Returns:
    A string containing the formatted email.
  """
  email_template = f"""
  Hello Customer,
  <br/><br/>
  {email_body}
  <br/> <br/><br/>
  Sincerely,
  <br/>
  AI Bot
  """
  return email_template
    
def sendEmail(name, email, subject, message):
    print("Sending...Email...")
    body = generate_email(name, message)
    key = "<>"
    message = Mail(
        from_email='no-reply@cloud-demos.live',
        to_emails=email,
        subject='Re: '+ subject,
        html_content=body
        )
    try:
        sg = SendGridAPIClient(key)
        response = sg.send(message)
    except Exception as e:
        print(e.message)

#sendEmail()
#test_inbound_email("Hitesh W", "stilwalli@google.com", "Forex", "Will I need separate data subscriptions platforms?")