import json
import os
import requests

def create_user_flow(user_flow_type, id, tenant_id, client_credential, client_id):
    graphAccessUrl = f'https://login.microsoftonline.com/{tenant_id}/oauth2/v2.0/token'
    graphTokenBody = f'client_id={client_id}&scope=https%3A%2F%2Fgraph.microsoft.com%2F.default&client_secret={client_credential}&grant_type=client_credentials'
    tokenResponse = requests.post(graphAccessUrl, graphTokenBody)
    token = tokenResponse.json()['access_token']
    requests.post("https://graph.microsoft.com/beta/identity/b2cUserFlows", headers={"Authorization": 'Bearer ' + token, "Content-type": 'application/json'},
    data=json.dumps({
            "id": id,
            "userFlowType": user_flow_type,
            "userFlowTypeVersion": 3
        })
    )
    json_data = []
    if user_flow_type == "signUpOrSignIn":
        json_data = [
            {"userAttribute": {"id": "email"}, "isOptional": False, "requiresVerification":True, "userInputType": "emailBox", "displayName": "Email Address", "userAttributeValues":[]},
            {"userAttribute": {"id": "givenName"}, "isOptional": False, "requiresVerification":False, "userInputType": "textBox", "displayName": "Given Name", "userAttributeValues":[]},
            {"userAttribute": {"id": "surname"}, "isOptional": False, "requiresVerification":False, "userInputType": "textBox", "displayName": "Surname", "userAttributeValues":[]}]
    elif user_flow_type=="profileUpdate":
        json_data = [
            {"userAttribute": {'id': 'givenName'}, 'isOptional': False, 'requiresVerification': False, 'userInputType': 'textBox', 'displayName': 'Given Name', 'userAttributeValues': []},
            {"userAttribute": {'id': 'surname'}, 'isOptional': False, 'requiresVerification': False, 'userInputType': 'textBox', 'displayName': 'Surname', 'userAttributeValues': []}]

    for json_dat in json_data:
        requests.post(f"https://graph.microsoft.com/beta/identity/b2cUserFlows/B2C_1_{id}/userAttributeAssignments", headers={"Authorization": 'Bearer ' + token, "Content-type": 'application/json'},
            data=json.dumps(json_dat))


def create_azure_credentials(clientId, clientSecret, subscriptionId, resource_group, site_name, outputfile):
    os.system(f"az ad sp create-for-rbac --name \"creds{site_name}\" --role contributor --scopes /subscriptions/{subscriptionId}/resourceGroups/{resource_group}/providers/Microsoft.Web/sites/{site_name} --sdk-auth > {outputfile}.json")
    return True

def create_config_file(azure_host, client_id, client_credential, tenant_name, tenant_id, account_name, account_media_key, account_static_key, cosmosdb, key, domain, instrumentation_key, connection_string):
    username = cosmosdb[0].split(':')[1][2:]
    password = cosmosdb[0].split(':')[2].split("@")[0]

    data = {
        "azure_host": f"{azure_host}.azurewebsites.net",
        "azure_aad_b2c_tenant": {
            "client_id": client_id,
            "client_credential": client_credential,
            "tenant_name": tenant_name,
            "tenant_id": tenant_id
        },
        "azure_blob_storage": {
            "account_name": account_name,
            "account_media_key": account_media_key,
            "account_static_key": account_static_key
        },
        "azure_cosmos_database": {
            "host": f"{username}.mongo.cosmos.azure.com",
            "username": username,
            "password": password
        },
        "azure_function": {
            "key": key,
            "domain": domain
        },
        "azure_insights": {
            "instrumentation_key": instrumentation_key,
            "connection_string": connection_string
        }
    }
    with open("../../webapp/azure_config.json", "w") as file:
        json.dump(data, file, indent=4)

    
    create_user_flow(id="signupsignin", user_flow_type="signUpOrSignIn", tenant_id=tenant_id, client_credential=client_credential, client_id=client_id)
    create_user_flow(id="editprofile", user_flow_type="profileUpdate", tenant_id=tenant_id, client_credential=client_credential, client_id=client_id)
    create_user_flow(id="resetpassword", user_flow_type="passwordReset", tenant_id=tenant_id, client_credential=client_credential, client_id=client_id)

    return data

def create_function_config_file(azure_host, email_domain, email_connection_string):
    data = {
        "azure_host": azure_host,
        "email_domain": email_domain,
        "email_connection_string": email_connection_string
    }
    with open("../../function/HttpTrigger/function_config.json", "w") as file:
        json.dump(data, file, indent=4)
    return data
