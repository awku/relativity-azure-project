"""An Azure RM Python Pulumi program"""
import pulumi_azure_native as azure_native

B2C_TENANT_NAME="akrelativity"

resource_group = azure_native.resources.ResourceGroup('resourcegroup', resource_group_name="resource_group")

b2c_tenant = azure_native.azureactivedirectory.B2CTenant("b2ctenant",
    location="United States",
    properties=azure_native.azureactivedirectory.CreateTenantRequestBodyPropertiesArgs(
        country_code="US",
        display_name="B2C Tenant",
    ),
    resource_group_name=resource_group.name,
    resource_name_=f"{B2C_TENANT_NAME}.onmicrosoft.com",
    sku=azure_native.azureactivedirectory.B2CResourceSKUArgs(
        name=azure_native.azureactivedirectory.B2CResourceSKUName.PREMIUM_P1,
        tier=azure_native.azureactivedirectory.B2CResourceSKUTier.A0,
    ))
