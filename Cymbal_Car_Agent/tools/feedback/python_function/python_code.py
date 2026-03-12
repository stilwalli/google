import uuid
def feedback(message:str) -> dict:
 """
 Allows the user to provide feedback and returns with the ticket number.
 Args:
   message (str): user's feedback
 Returns:
   Ticket number.
 """
 return {
  "ticket_number": f"{uuid.uuid4()}",
  "status": "ticket successfully submitted"
 }