from azure.keyvault.secrets import SecretClient
from azure.identity import EnvironmentCredential

KEY_VAULT_NAME = "batch-covid-app-keyvault"
KVUri = f"https://{KEY_VAULT_NAME}.vault.azure.net"

credential = EnvironmentCredential()
client = SecretClient(vault_url=KVUri, credential=credential)

RESOURCE_GROUP = "epiforecasts-covid-r"

# Batch Account information
BATCH_ACCOUNT_NAME = "epinowcovidrbatch"
BATCH_ACCOUNT_KEY = client.get_secret("covid-r-batch-account-key").value
BATCH_LOCATION = "westeurope"

# Storage Account information
STORAGE_ACCOUNT_NAME = "epinowcovidrstorage"
STORAGE_ACCOUNT_KEY = client.get_secret("covid-r-storage-account-key").value
SAS_TOKEN = client.get_secret("SAS-TOKEN").value
CONFIG_CONTAINER = f"https://{STORAGE_ACCOUNT_NAME}.blob.core.windows.net"\
                   + "/json-configs/"
RESULTS_CONTAINER = f"https://{STORAGE_ACCOUNT_NAME}.blob.core.windows.net"\
                    + "/results/"
TEST_RESULTS_CONTAINER = f"https://{STORAGE_ACCOUNT_NAME}.blob.core.windows.net"\
                    + "/test-results/"
PROCESS_LOG_CONTAINER = f"https://{STORAGE_ACCOUNT_NAME}.blob.core.windows.net"\
                   + "/covid-r-process-logs/"
COMMIT_LOG_CONTAINER = f"https://{STORAGE_ACCOUNT_NAME}.blob.core.windows.net"\
                   + "/covid-r-commit-logs/"
FILE_SHARE_NAME = 'epinow-covid-r-fileshare'
ANCIL_FILES_URL = 'https://raw.githubusercontent.com/epiforecasts/covid-rt-estimates/master/'
TEMP_FILE_STORAGE = 'temp/'

# Information for obtaining the docker container
REGISTRY_ACCOUNT_USER = client.get_secret("github-container-username").value
REGISTRY_ACCOUNT_PASSWORD = client.get_secret("github-container-password").value

# Personal Access token from Github
GITHUB_USER_NAME = client.get_secret("github-username").value
GITHUB_EMAIL = client.get_secret("github-email").value
GITHUB_TOKEN = client.get_secret("github-token").value

# User name for the covid-batch-app
APP_USER_NAME = client.get_secret("APP-USER-NAME").value
APP_PASSWORD = client.get_secret("APP-PASSWORD").value
TENANT_ID = client.get_secret("TENANT-ID").value

