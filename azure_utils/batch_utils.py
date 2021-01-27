import datetime
import logging

import azure.batch
from azure.batch import batch_auth as batch_auth, models as batch_models

from env_config.accounts import BATCH_ACCOUNT_KEY, BATCH_ACCOUNT_NAME, \
    BATCH_LOCATION, REGISTRY_ACCOUNT_PASSWORD, REGISTRY_ACCOUNT_USER, \
    FILE_SHARE_NAME, STORAGE_ACCOUNT_NAME, STORAGE_ACCOUNT_KEY
from env_config.batch_vm import DOCKER_CONTAINER_URL, REGISTRY_SERVER, \
    VM_AGENT_SKU, get_image_reference
from env_config.pool import PROCESSING_POOL_ID, PROCESSING_POOL_SCALE_FORMULA, \
    PROCESSING_POOL_SCALE_INTERVAL_MINUTES, PROCESSING_POOL_VM_SIZE, \
    COMMIT_POOL_ID, COMMIT_POOL_VM_SIZE, COMMIT_POOL_SCALE_INTERVAL_MINUTES, \
    COMMIT_POOL_START_TASK, COMMIT_POOL_SCALE_FORMULA

LOGGER = logging.getLogger("covid-r-batch")


def get_batch_client():
    credentials = batch_auth.SharedKeyCredentials(
            BATCH_ACCOUNT_NAME,
            BATCH_ACCOUNT_KEY)

    batch_service_client = azure.batch.BatchServiceClient(
            credentials,
            batch_url=f"https://{BATCH_ACCOUNT_NAME}.{BATCH_LOCATION}.batch.azure.com")

    return batch_service_client


def print_batch_exception(batch_exception):
    """
    Prints the contents of the specified Batch exception.
    :param batch_exception:
    """
    message = ""
    if batch_exception.error and \
            batch_exception.error.message and \
            batch_exception.error.message.value:
        message += batch_exception.error.message.value
        if batch_exception.error.values:
            message += "\n"
            for message in batch_exception.error.values:
                message += '{}:\t{}'.format(message.key, message.value)
    LOGGER.exception(message)


def create_processing_pool(batch_service_client, start_task):
    """
    Creates a pool of compute nodes with the specified OS settings.
    :param batch_service_client: A Batch service client.
    :param str start_task: task start command.
    :type batch_service_client: `azure.batch.BatchServiceClient`

    """
    LOGGER.info(f'Creating pool [{PROCESSING_POOL_ID}]...')

    image_ref_to_use = get_image_reference()

    container_registry = \
        batch_models.ContainerRegistry(
            registry_server=REGISTRY_SERVER,
            user_name=REGISTRY_ACCOUNT_USER,
            password=REGISTRY_ACCOUNT_PASSWORD)

    container_conf = batch_models.ContainerConfiguration(
            container_image_names=[DOCKER_CONTAINER_URL],
            container_registries=[container_registry])

    new_pool = batch_models.PoolAddParameter(
            id=PROCESSING_POOL_ID,
            virtual_machine_configuration=
            batch_models.VirtualMachineConfiguration(
                image_reference=image_ref_to_use,
                container_configuration=container_conf,
                node_agent_sku_id=VM_AGENT_SKU),
            vm_size=PROCESSING_POOL_VM_SIZE,
            start_task=batch_models.StartTask(
                command_line=start_task,
                user_identity=batch_models.UserIdentity(
                    auto_user=batch_models.AutoUserSpecification(
                        scope='pool',
                        elevation_level='admin'))
                    ),
            enable_auto_scale=True,
            auto_scale_evaluation_interval=datetime.timedelta(
                minutes=PROCESSING_POOL_SCALE_INTERVAL_MINUTES),
            auto_scale_formula=PROCESSING_POOL_SCALE_FORMULA)
    try:
        batch_service_client.pool.add(new_pool)
        LOGGER.info("Processing Pool Created")
    except batch_models.BatchErrorException as err:
        if 'The specified pool already exists.' in err.error.message.value:
            LOGGER.info("Pool already exists...")
        else:
            raise
    

def create_commit_pool(batch_service_client):
    """
    Creates a pool of compute nodes with the specified OS settings.
    :param batch_service_client: A Batch service client.
    :type batch_service_client: `azure.batch.BatchServiceClient`

    """
    LOGGER.info(f'Creating pool [{PROCESSING_POOL_ID}]...')

    image_ref_to_use = batch_models.ImageReference(
            publisher='canonical',
            offer='ubuntuserver',
            sku='18.04-lts',
            version='latest')

    new_pool = batch_models.PoolAddParameter(
            id=COMMIT_POOL_ID,
            virtual_machine_configuration=
            batch_models.VirtualMachineConfiguration(
                image_reference=image_ref_to_use,
                node_agent_sku_id="batch.node.ubuntu 18.04"),
            vm_size=COMMIT_POOL_VM_SIZE,
            start_task=batch_models.StartTask(
                command_line=COMMIT_POOL_START_TASK,
                user_identity=batch_models.UserIdentity(
                    auto_user=batch_models.AutoUserSpecification(
                        scope='pool',
                        elevation_level='admin'))
                    ),
            enable_auto_scale=True,
            auto_scale_evaluation_interval=datetime.timedelta(
                minutes=COMMIT_POOL_SCALE_INTERVAL_MINUTES),
            auto_scale_formula=COMMIT_POOL_SCALE_FORMULA)
    try:
        batch_service_client.pool.add(new_pool)
        LOGGER.info("Commit Pool Created")
    except batch_models.BatchErrorException as err:
        if 'The specified pool already exists.' in err.error.message.value:
            LOGGER.info("Pool already exists...")
        else:
            raise


def create_job(batch_service_client, job_id, pool_id):
    """
    Creates a job with the specified ID, associated with the specified pool.
    :param batch_service_client: A Batch service client.
    :type batch_service_client: `azure.batch.BatchServiceClient`
    :param str job_id: The ID for the job.
    :param str pool_id: The ID for the pool.
    """
    LOGGER.info('Creating job [{}]...'.format(job_id))

    job = batch_models.JobAddParameter(
            id=job_id,
            pool_info=batch_models.PoolInformation(pool_id=pool_id),
            uses_task_dependencies=True)
    try:
        batch_service_client.job.add(job)
        LOGGER.info("Job Created")
    except batch_models.BatchErrorException as err:
        if 'The specified job already exists.' in err.error.message.value:
            LOGGER.info("Job already exists...")
        else:
            raise


