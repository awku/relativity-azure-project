import logging
import os
import azure.functions as func
from azure.communication.email import EmailClient, EmailContent, EmailAddress, EmailRecipients, EmailMessage
import json

def find(name, path):
    for root, dirs, files in os.walk(path):
        if name in files:
            return os.path.join(root, name)

def main(req: func.HttpRequest) -> func.HttpResponse:
    logging.info('Python HTTP trigger function processed a request.')

    file_path = find("function_config.json", os.getcwd())
    with open(file_path) as file:
        config_data = json.load(file)

    try:
        req_body = req.get_json()
    except ValueError:
        pass
    else:
        email_address = req_body.get('email')
        order_id = req_body.get('order_id')

    azure_host = config_data['azure_host']
    if email_address and order_id:
        try:
            logging.info(f'Trigger for {email_address} and {order_id}')
            email_client = EmailClient.from_connection_string(config_data['email_connection_string'])
            content = EmailContent(
                subject="Order confirmation - Relativity Project AKus",
                html=f"<h3>Confirmation Number: {order_id}</h3><h4>Hello,</h4><p>We're happy to let you know that we've received your order.</p><p>Once your package ships, we will send you an email with a tracking number and link so you can see the movement of your package.</p><p>Till then, you can see the order details <a href='https://{azure_host}/order/{order_id}'>here</a></p><p>We are here to help!</p><small>Relativity project AKus team</small>",
            )
            recipient = EmailRecipients(to=[EmailAddress(email=email_address)])
            message = EmailMessage(
                sender=f"<donotreply@{config_data['email_domain']}>",
                content=content,
                recipients=recipient
            )
            response = email_client.send(message)
            logging.info(f'Response: {response}')
            return func.HttpResponse(status_code=200)
        except Exception as ex:
            logging.error(f'Exception: {ex}')
            return func.HttpResponse(status_code=417)
    return func.HttpResponse(status_code=400)
