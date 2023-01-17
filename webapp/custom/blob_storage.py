from storages.backends.azure_storage import AzureStorage
from project.settings import AZURE_CONFIG


class AzureMediaStorage(AzureStorage):
    account_name = AZURE_CONFIG.azure_blob_storage.account_name
    account_key = AZURE_CONFIG.azure_blob_storage.account_media_key
    azure_container = "media"
    expiration_secs = None


class AzureStaticStorage(AzureStorage):
    account_name = AZURE_CONFIG.azure_blob_storage.account_name
    account_key = AZURE_CONFIG.azure_blob_storage.account_static_key
    azure_container = "static"
    expiration_secs = None
