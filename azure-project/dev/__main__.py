"""An Azure RM Python Pulumi program"""

from requests import get
import pulumi
import pulumi_azure_native as azure_native
import pulumi_azuread as azuread
import pulumi_azure as azure
from helper import (
    create_azure_credentials,
    create_config_file,
    create_function_config_file,
)

AZURE_WEBAPP_NAME = "akrelativityapp"
B2C_TENANT_NAME = "akrelativity"
AZURE_FUNCTIONAPP_NAME = "akrelativityapp-fun"
locations = ["eastus", "eastus2", "southcentralus", "westus2", "westus3", "centralus"]

resource_group = azure_native.resources.get_resource_group("resource_group")
current_user = azuread.get_client_config()
b2c_tenant = azure_native.azureactivedirectory.get_b2_c_tenant(
    resource_group.name, f"{B2C_TENANT_NAME}.onmicrosoft.com"
)
current_subscription = azure.core.get_subscription()

app_insights = azure.appinsights.Insights(
    "appinsights",
    name="appinsights",
    location=locations[3],
    resource_group_name=resource_group.name,
    application_type="web",
)


admin_group = azuread.Group(
    "adminsgroup",
    display_name="Admins",
    owners=[current_user.object_id],
    security_enabled=True,
)

test_admin = azuread.User(
    "testadmin",
    user_principal_name=f"test_admin@{B2C_TENANT_NAME}.onmicrosoft.com",
    display_name="Admin User",
    given_name="Admin",
    surname="Test",
    password="!P@ssw0rd1",
    mail="test_admin@gmail.com",
)

example_group_member = azuread.GroupMember(
    "testadmingroupmember",
    group_object_id=admin_group.id,
    member_object_id=test_admin.id,
)

test_user = azuread.User(
    "testuser",
    user_principal_name=f"test_user@{B2C_TENANT_NAME}.onmicrosoft.com",
    display_name="User Test",
    surname="User",
    given_name="Test",
    password="1P@ssw0rd!",
    mail="test_user@gmail.com",
)

email_service = azure_native.communication.EmailService(
    "emailservice",
    data_location="United States",
    email_service_name="emailservice",
    location="Global",
    resource_group_name=resource_group.name,
)

communication_service = azure_native.communication.CommunicationService(
    "commservice",
    communication_service_name=f"commservice-{AZURE_WEBAPP_NAME}",
    data_location="United States",
    location="Global",
    resource_group_name=resource_group.name,
)

email_domain = azure_native.communication.Domain(
    "AzureManagedDomain",
    domain_management="AzureManaged",
    email_service_name=email_service.name,
    location="Global",
    resource_group_name=resource_group.name,
)

app_service_plan = azure_native.web.AppServicePlan(
    "appsp",
    kind="app",
    location=locations[4],
    name="appsp",
    reserved=True,
    resource_group_name=resource_group.name,
    sku=azure_native.web.SkuDescriptionArgs(
        capacity=1,
        family="F",
        name="F1",
        size="F1",
        tier="Free",
    ),
)

app_dev_service_plan = azure_native.web.AppServicePlan(
    "appspdev",
    kind="app",
    location=locations[5],
    name="appspdev",
    reserved=True,
    resource_group_name=resource_group.name,
    sku=azure_native.web.SkuDescriptionArgs(
        capacity=1,
        family="F",
        name="F1",
        size="F1",
        tier="Free",
    ),
)

cicd_application = azuread.Application(
    "cicdapp",
    display_name="CICD",
    sign_in_audience="AzureADandPersonalMicrosoftAccount",
    api=azuread.ApplicationApiArgs(
        requested_access_token_version=2,
    ),
    optional_claims=None,
    owners=[current_user.object_id],
)

cicd_application_password = azuread.ApplicationPassword(
    "cicdpassword",
    application_object_id=cicd_application.object_id,
    display_name="rbac",
    end_date_relative="4380h",
)

cicd_service_principal = azuread.ServicePrincipal(
    "cicdappsp",
    application_id=cicd_application.application_id,
    app_role_assignment_required=False,
    owners=[current_user.object_id],
)

msgraph_service_principal = azuread.ServicePrincipal(
    "msgraphappsp",
    application_id="00000003-0000-0000-c000-000000000000",
    use_existing=True,
)

project_application = azuread.Application(
    f"{AZURE_WEBAPP_NAME}-app",
    display_name=f"{AZURE_WEBAPP_NAME}-app",
    sign_in_audience="AzureADandPersonalMicrosoftAccount",
    api=azuread.ApplicationApiArgs(
        requested_access_token_version=2,
    ),
    fallback_public_client_enabled=True,
    web=azuread.ApplicationWebArgs(
        redirect_uris=[f"https://{AZURE_WEBAPP_NAME}.azurewebsites.net/auth/redirect"],
        implicit_grant=azuread.ApplicationWebImplicitGrantArgs(
            access_token_issuance_enabled=True,
            id_token_issuance_enabled=True,
        ),
    ),
    required_resource_accesses=[
        azuread.ApplicationRequiredResourceAccessArgs(
            resource_app_id="00000003-0000-0000-c000-000000000000",
            resource_accesses=[
                azuread.ApplicationRequiredResourceAccessResourceAccessArgs(
                    id="7427e0e9-2fba-42fe-b0c0-848c9e6a8182",
                    type="Scope",
                ),
                azuread.ApplicationRequiredResourceAccessResourceAccessArgs(
                    id="37f7f235-527c-4136-accd-4a02d197296e",
                    type="Scope",
                ),
                azuread.ApplicationRequiredResourceAccessResourceAccessArgs(
                    id=msgraph_service_principal.app_role_ids["User.Read.All"],
                    type="Role",
                ),
                azuread.ApplicationRequiredResourceAccessResourceAccessArgs(
                    id=msgraph_service_principal.app_role_ids["Directory.Read.All"],
                    type="Role",
                ),
                azuread.ApplicationRequiredResourceAccessResourceAccessArgs(
                    id=msgraph_service_principal.app_role_ids[
                        "IdentityUserFlow.ReadWrite.All"
                    ],
                    type="Role",
                ),
            ],
        )
    ],
    owners=[current_user.object_id],
)

project_service_principal = azuread.ServicePrincipal(
    "projectappsp",
    application_id=project_application.application_id,
    app_role_assignment_required=False,
)

app_role_assignment1 = azuread.AppRoleAssignment(
    "projectapproleassignment1",
    app_role_id=msgraph_service_principal.app_role_ids["User.Read.All"],
    principal_object_id=project_service_principal.object_id,
    resource_object_id=msgraph_service_principal.object_id,
)
app_role_assignment2 = azuread.AppRoleAssignment(
    "projectapproleassignment2",
    app_role_id=msgraph_service_principal.app_role_ids["Directory.Read.All"],
    principal_object_id=project_service_principal.object_id,
    resource_object_id=msgraph_service_principal.object_id,
)

app_role_assignment3 = azuread.AppRoleAssignment(
    "projectapproleassignment3",
    app_role_id=msgraph_service_principal.app_role_ids[
        "IdentityUserFlow.ReadWrite.All"
    ],
    principal_object_id=project_service_principal.object_id,
    resource_object_id=msgraph_service_principal.object_id,
)

app_role_assignment4 = azuread.ServicePrincipalDelegatedPermissionGrant(
    "projectapproleassignment4",
    service_principal_object_id=project_service_principal.object_id,
    resource_service_principal_object_id=msgraph_service_principal.object_id,
    claim_values=["offline_access", "openid"],
)

project_application_password = azuread.ApplicationPassword(
    "projectpassword",
    application_object_id=project_application.object_id,
    display_name="app secret",
    end_date_relative="4380h",
)

storage_account = azure_native.storage.StorageAccount(
    "strgacc",
    resource_group_name=resource_group.name,
    sku=azure_native.storage.SkuArgs(
        name=azure_native.storage.SkuName.STANDARD_LRS,
    ),
    kind=azure_native.storage.Kind.STORAGE_V2,
)

blob_media_container = azure_native.storage.BlobContainer(
    "blobmediacontainer",
    public_access=azure_native.storage.PublicAccess.BLOB,
    account_name=storage_account.name,
    container_name="media",
    default_encryption_scope="encryptionscope185",
    deny_encryption_scope_override=True,
    resource_group_name=resource_group.name,
)

blob_static_container = azure_native.storage.BlobContainer(
    "blobstaticcontainer",
    public_access=azure_native.storage.PublicAccess.BLOB,
    account_name=storage_account.name,
    container_name="static",
    default_encryption_scope="encryptionscope185",
    deny_encryption_scope_override=True,
    resource_group_name=resource_group.name,
)

cosmos_account = azure.cosmosdb.Account(
    "cosmosacc",
    name=f"cosmosacc-{AZURE_WEBAPP_NAME}",
    location=locations[1],
    resource_group_name=resource_group.name,
    offer_type="Standard",
    kind="MongoDB",
    enable_automatic_failover=True,
    capabilities=[
        azure.cosmosdb.AccountCapabilityArgs(
            name="EnableAggregationPipeline",
        ),
        azure.cosmosdb.AccountCapabilityArgs(
            name="mongoEnableDocLevelTTL",
        ),
        azure.cosmosdb.AccountCapabilityArgs(
            name="MongoDBv3.4",
        ),
        azure.cosmosdb.AccountCapabilityArgs(
            name="EnableMongo",
        ),
    ],
    consistency_policy=azure.cosmosdb.AccountConsistencyPolicyArgs(
        consistency_level="BoundedStaleness",
        max_interval_in_seconds=300,
        max_staleness_prefix=100000,
    ),
    geo_locations=[
        azure.cosmosdb.AccountGeoLocationArgs(
            location=locations[1],
            failover_priority=0,
        )
    ],
)

cosmos_database = azure.cosmosdb.MongoDatabase(
    "cosmosdb",
    resource_group_name=resource_group.name,
    account_name=cosmos_account.name,
    throughput=400,
)

app = azure_native.web.WebApp(
    "app",
    name=AZURE_WEBAPP_NAME,
    location=app_service_plan.location,
    resource_group_name=resource_group.name,
    server_farm_id=app_service_plan.id,
    identity=azure_native.web.ManagedServiceIdentityArgs(
        type="SystemAssigned",
    ),
    site_config=azure_native.web.SiteConfigArgs(
        linux_fx_version="PYTHON|3.9",
        app_settings=[
            azure_native.web.NameValuePairArgs(
                name="APPINSIGHTS_INSTRUMENTATIONKEY",
                value=app_insights.instrumentation_key,
            ),
            azure_native.web.NameValuePairArgs(
                name="APPLICATIONINSIGHTS_CONNECTION_STRING",
                value=app_insights.instrumentation_key.apply(
                    lambda instrumentation_key: f"InstrumentationKey={instrumentation_key}"
                ),
            ),
            azure_native.web.NameValuePairArgs(
                name="ApplicationInsightsAgent_EXTENSION_VERSION",
                value="~2",
            ),
        ],
    ),
)

app_dev = azure_native.web.WebApp(
    "appdev",
    name=f"{AZURE_WEBAPP_NAME}-dev",
    location=app_dev_service_plan.location,
    resource_group_name=resource_group.name,
    server_farm_id=app_dev_service_plan.id,
    identity=azure_native.web.ManagedServiceIdentityArgs(
        type="SystemAssigned",
    ),
    site_config=azure_native.web.SiteConfigArgs(
        linux_fx_version="PYTHON|3.9",
        app_settings=[
            azure_native.web.NameValuePairArgs(
                name="APPINSIGHTS_INSTRUMENTATIONKEY",
                value=app_insights.instrumentation_key,
            ),
            azure_native.web.NameValuePairArgs(
                name="APPLICATIONINSIGHTS_CONNECTION_STRING",
                value=app_insights.instrumentation_key.apply(
                    lambda instrumentation_key: f"InstrumentationKey={instrumentation_key}"
                ),
            ),
            azure_native.web.NameValuePairArgs(
                name="ApplicationInsightsAgent_EXTENSION_VERSION",
                value="~2",
            ),
        ],
    ),
)

storage_account_key1 = (
    pulumi.Output.all(resource_group.name, storage_account.name)
    .apply(
        lambda args: azure_native.storage.list_storage_account_keys(
            resource_group_name=args[0], account_name=args[1]
        )
    )
    .apply(lambda accountKeys: accountKeys.keys[0].value)
)

storage_account_key2 = (
    pulumi.Output.all(resource_group.name, storage_account.name)
    .apply(
        lambda args: azure_native.storage.list_storage_account_keys(
            resource_group_name=args[0], account_name=args[1]
        )
    )
    .apply(lambda accountKeys: accountKeys.keys[1].value)
)

email_connection_string = (
    pulumi.Output.all(resource_group.name, communication_service.name)
    .apply(
        lambda args: azure_native.communication.list_communication_service_keys(
            resource_group_name=args[0], communication_service_name=args[1]
        )
    )
    .apply(lambda keys: keys.primary_connection_string)
)

pulumi.export(
    "functionconfig",
    pulumi.Output.all(
        email_domain.mail_from_sender_domain, email_connection_string
    ).apply(lambda args: create_function_config_file(*args)),
)

function_storage_account = azure.storage.Account(
    "funsa",
    resource_group_name=resource_group.name,
    location=locations[2],
    account_tier="Standard",
    account_replication_type="LRS",
)

function_service_plan = azure_native.web.AppServicePlan(
    "funsp",
    kind="functionapp",
    location=locations[2],
    name="funsp",
    reserved=True,
    resource_group_name=resource_group.name,
    sku=azure_native.web.SkuDescriptionArgs(
        capacity=1,
        family="Y",
        name="Y1",
        size="Y1",
        tier="Dynamic",
    ),
)

function_app = azure_native.web.WebApp(
    "funapp",
    name=AZURE_FUNCTIONAPP_NAME,
    resource_group_name=resource_group.name,
    server_farm_id=function_service_plan.id,
    location=function_service_plan.location,
    storage_account_required=False,
    identity=azure_native.web.ManagedServiceIdentityArgs(
        type="SystemAssigned",
    ),
    kind="functionapp,linux",
    site_config=azure_native.web.SiteConfigArgs(
        linux_fx_version="PYTHON|3.9",
        app_settings=[
            azure_native.web.NameValuePairArgs(
                name="AzureWebJobsStorage",
                value=function_storage_account.primary_connection_string,
            ),
            azure_native.web.NameValuePairArgs(
                name="FUNCTIONS_WORKER_RUNTIME",
                value="python",
            ),
            azure_native.web.NameValuePairArgs(
                name="FUNCTIONS_EXTENSION_VERSION",
                value="~4",
            ),
            azure_native.web.NameValuePairArgs(
                name="APPINSIGHTS_INSTRUMENTATIONKEY",
                value=app_insights.instrumentation_key,
            ),
            azure_native.web.NameValuePairArgs(
                name="APPLICATIONINSIGHTS_CONNECTION_STRING",
                value=app_insights.instrumentation_key.apply(
                    lambda instrumentation_key: f"InstrumentationKey={instrumentation_key}"
                ),
            ),
        ],
    ),
)

function_key = (
    pulumi.Output.all(resource_group.name, function_app.name)
    .apply(
        lambda args: azure_native.web.list_web_app_host_keys(
            resource_group_name=args[0], name=args[1]
        )
    )
    .apply(lambda keys: keys.function_keys["default"])
)

pulumi.export(
    "githubwebappcredentials",
    pulumi.Output.all(
        app.id,
        cicd_application_password.value,
        current_subscription.subscription_id,
        resource_group.name,
        AZURE_WEBAPP_NAME,
        "AZURE_WEBAPP_CREDENTIALS",
    ).apply(lambda args: create_azure_credentials(*args)),
)

pulumi.export(
    "githubwebappdevcredentials",
    pulumi.Output.all(
        app_dev.id,
        cicd_application_password.value,
        current_subscription.subscription_id,
        resource_group.name,
        f"{AZURE_WEBAPP_NAME}-dev",
        "AZURE_WEBAPP_DEV_CREDENTIALS",
    ).apply(lambda args: create_azure_credentials(*args)),
)

pulumi.export(
    "githubfunctionappcredentials",
    pulumi.Output.all(
        function_app.id,
        cicd_application_password.value,
        current_subscription.subscription_id,
        resource_group.name,
        AZURE_FUNCTIONAPP_NAME,
        "AZURE_FUNCTIONAPP_CREDENTIALS",
    ).apply(lambda args: create_azure_credentials(*args)),
)

pulumi.export(
    "azureconfig",
    pulumi.Output.all(
        app.name,
        project_application.application_id,
        project_application_password.value,
        b2c_tenant.name,
        b2c_tenant.tenant_id,
        storage_account.name,
        storage_account_key1,
        storage_account_key2,
        cosmos_account.connection_strings,
        function_key,
        function_app.name,
        app_insights.instrumentation_key,
        app_insights.connection_string,
    ).apply(lambda args: create_config_file(*args)),
)


b2c_analytics_workspace = azure.operationalinsights.AnalyticsWorkspace(
    "b2canwrkspce",
    name="b2canalyticsworkspace",
    location=locations[3],
    resource_group_name=resource_group.name,
    sku="PerGB2018",
    retention_in_days=30,
)

diagnostic_setting = azure_native.aadiam.DiagnosticSetting(
    "diagnosticSetting",
    workspace_id=b2c_analytics_workspace.id,
    logs=[
        {
            "category": "AuditLogs",
            "enabled": True,
            "retentionPolicy": azure_native.aadiam.RetentionPolicyArgs(
                days=0,
                enabled=False,
            ),
        },
        {
            "category": "SignInLogs",
            "enabled": True,
            "retentionPolicy": azure_native.aadiam.RetentionPolicyArgs(
                days=0, enabled=False
            ),
        },
    ],
    name="b2c_settings",
)

workbook = azure_native.insights.Workbook(
    resource_name="85b3e8bb-fc93-40be-83f2-98f6",
    category="workbook",
    display_name="b2cworkbook",
    kind="shared",
    location=locations[3],
    resource_group_name=resource_group.name,
    serialized_data=get(
        "https://raw.githubusercontent.com/azure-ad-b2c/siem/master/workbooks/dashboard.json"
    ).text,
    source_id=b2c_analytics_workspace.id,
)

api_connection_name = "azureloganalyticsdatacollector"
id_for_connection = f"/subscriptions/{current_subscription.subscription_id}/providers/Microsoft.Web/locations/{locations[3]}/managedApis/{api_connection_name}"

api_connection = azure_native.web.Connection(
    "connection",
    connection_name=api_connection_name,
    location=locations[3],
    resource_group_name=b2c_analytics_workspace.resource_group_name,
    properties=azure_native.web.ApiConnectionDefinitionPropertiesArgs(
        display_name="azureloganalyticsdatacollector",
        api=azure_native.web.ApiReferenceArgs(
            id=id_for_connection,
        ),
        parameter_values={
            "username": b2c_analytics_workspace.workspace_id,
            "password": b2c_analytics_workspace.primary_shared_key,
        },
    ),
)

admin_group_object_id = pulumi.Output.all(admin_group).apply(
    lambda keys: keys.object_id
)

workflow = azure_native.logic.Workflow(
    "workflow",
    definition={
        "$schema": "https://schema.management.azure.com/providers/Microsoft.Logic/schemas/2016-06-01/workflowdefinition.json#",
        "actions": {
            "Initialize_variable": {
                "inputs": {
                    "variables": [
                        {
                            "name": "Next",
                            "type": "string",
                            "value": f"https://graph.microsoft.com/v1.0/groups/{admin_group_object_id}/members",
                        }
                    ]
                },
                "runAfter": {},
                "type": "InitializeVariable",
            },
            "Until_2": {
                "actions": {
                    "HTTP": {
                        "inputs": {
                            "authentication": {
                                "audience": "https://graph.microsoft.com/",
                                "clientId": project_application.application_id,
                                "secret": project_application_password.value,
                                "tenant": b2c_tenant.tenant_id,
                                "type": "ActiveDirectoryOAuth",
                            },
                            "method": "GET",
                            "uri": "@variables('Next')",
                        },
                        "runAfter": {},
                        "type": "Http",
                    },
                    "Parse_JSON": {
                        "inputs": {
                            "content": "@body('HTTP')",
                            "schema": {
                                "properties": {
                                    "@@odata.context": {"type": "string"},
                                    "@@odata.nextLink": {"type": "string"},
                                    "value": {"type": "array"},
                                },
                                "type": "object",
                            },
                        },
                        "runAfter": {"HTTP": ["Succeeded"]},
                        "type": "ParseJson",
                    },
                    "Send_Data": {
                        "inputs": {
                            "body": "@body('Parse_JSON')?['value']",
                            "headers": {"Log-Type": "ITPC_CTX_ADUsers"},
                            "host": {
                                "connection": {
                                    "name": "@parameters('$connections')['azureloganalyticsdatacollector_1']['connectionId']"
                                }
                            },
                            "method": "post",
                            "path": "/api/logs",
                        },
                        "runAfter": {"Set_variable": ["Succeeded"]},
                        "type": "ApiConnection",
                    },
                    "Set_variable": {
                        "inputs": {
                            "name": "Next",
                            "value": "@body('Parse_JSON')?['@odata.nextLink']",
                        },
                        "runAfter": {"Parse_JSON": ["Succeeded"]},
                        "type": "SetVariable",
                    },
                },
                "expression": "@equals(variables('Next'), '')",
                "limit": {"count": 60, "timeout": "PT1H"},
                "runAfter": {"Initialize_variable": ["Succeeded"]},
                "type": "Until",
            },
        },
        "contentVersion": "1.0.0.0",
        "outputs": {},
        "parameters": {"$connections": {"defaultValue": {}, "type": "Object"}},
        "triggers": {
            "Recurrence": {
                "evaluatedRecurrence": {"frequency": "Hour", "interval": 6},
                "recurrence": {"frequency": "Hour", "interval": 6},
                "type": "Recurrence",
            }
        },
    },
    location=locations[3],
    parameters={
        "$connections": azure_native.logic.WorkflowParameterArgs(
            value={
                "azureloganalyticsdatacollector_1": {
                    "connectionName": api_connection_name,
                    "connectionId": api_connection.id,
                    "id": id_for_connection,
                },
            },
        ),
    },
    resource_group_name=resource_group.name,
    workflow_name="injectb2cdata",
)
