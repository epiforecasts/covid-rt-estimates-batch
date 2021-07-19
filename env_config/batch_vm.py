from azure.batch import models as batchmodels

DOCKER_CONTAINER_URL = 'docker.pkg.github.com/epiforecasts/covid-rt-estimates/covidrtestimates' \
                       ':latest'
REGISTRY_SERVER = "docker.pkg.github.com"


def get_image_reference():
    return batchmodels.ImageReference(
            publisher='microsoft-azure-batch',
            offer='ubuntu-server-container',
            sku='20-04-lts',
            version='latest')


VM_AGENT_SKU = 'batch.node.ubuntu 20.04'
