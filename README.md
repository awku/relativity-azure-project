To "automatically" set up the application:
1. Download pulumi and az
2. Login to az (az login)
3. Go to azure-project/tenant and run 'pulumi --stack tenant up'
4. Assign a subscription to the new B2C tenant ( https://learn.microsoft.com/en-us/azure/active-directory/fundamentals/active-directory-how-subscriptions-associated-directory optional delete the old tenant https://learn.microsoft.com/en-us/azure/active-directory/enterprise-users/directory-delete-howto )
5. Login once again to the new tenant (az login --tenant DIRECTORY_ID), if theres an error wait a while or try az logout first
6. Edit AZURE_WEBAPP_NAME and AZURE_FUNCTIONAPP_NAME in azure-project\dev\__main__.py and .github\workflows\workflow.yaml. Change B2C_TENANT_NAME in azure-project\tenant\__main__.py and azure-project\dev\__main__.py 
6. Go to azure-project/dev and run 'pulumi --stack dev up'
7. Set up the secrets for GitHub actions from file AZURE_FUNCTIONAPP_CREDENTIALS.json and AZURE_WEBAPP_CREDENTIALS.json: AZURE_FUNCTIONAPP_CREDENTIALS and AZURE_WEBAPP_CREDENTIALS (https://github.com/USERNAME/REPONAME/settings/secrets/actions)
