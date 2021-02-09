import datetime
import logging
import os
import shutil
import json
import azure.core.exceptions as azure_exception
import azure.batch.models as batch_models
import azure.storage.file as file_service
import azure.storage.blob as blob
import requests

from azure_utils.batch_utils import create_job, create_processing_pool, \
    create_commit_pool, get_batch_client, print_batch_exception
from definitions.processable_entities import Dataset, Derivative, Publication
from definitions.schedule import SCHEDULE
from env_config.accounts import RESOURCE_GROUP, STORAGE_ACCOUNT_KEY, \
    STORAGE_ACCOUNT_NAME, SAS_TOKEN, BATCH_ACCOUNT_KEY, BATCH_ACCOUNT_NAME, \
    APP_USER_NAME, APP_PASSWORD, TENANT_ID, ANCIL_FILES_URL, FILE_SHARE_NAME, \
    TEMP_FILE_STORAGE, RESULTS_CONTAINER, TEST_RESULTS_CONTAINER,\
    CONFIG_CONTAINER, PROCESS_LOG_CONTAINER, COMMIT_LOG_CONTAINER
from env_config.batch_vm import DOCKER_CONTAINER_URL
from env_config.job import PROCESSING_JOB_ID, COMMIT_JOB_ID, CONFIG_FILE, \
    CONFIG_FOLDER
from env_config.pool import PROCESSING_POOL_ID, COMMIT_POOL_ID
from env_config.task import generate_task_name
from env_config.accounts import GITHUB_USER_NAME, GITHUB_EMAIL
from definitions.date_standards import DATETIME_NOWISH

LOGGER = logging.getLogger("covid-r-batch")


def generate_tasks(job_id, dataset_list, production, flags):
    """
    Adds a task for each input file in the collection to the specified job.
    :param str job_id: The ID of the job to which to add the tasks.
    :param list dataset_list: A collection of datasets names. One task will be
     created for each dataset.
    :param bool production: True if in production mode
    :param str flags: extra single letter flags to pass in
    """

    LOGGER.info('Adding {} tasks to job [{}]...'.format(
        len(dataset_list), job_id))

    tasks = list()

    for dataset in dataset_list:

        # Ensures that the container for the JSON config files exists
        blob_service_client = blob.BlobServiceClient(
            account_url=f"https://{STORAGE_ACCOUNT_NAME}.blob.core.windows.net",
            credential=SAS_TOKEN)
        try:
            container = blob_service_client.create_container(
                name=CONFIG_FOLDER)
        except azure_exception.ResourceExistsError:
            LOGGER.info(f"Container \"{CONFIG_FOLDER}\" already exists")
        if production:
            create_json_config(dataset, blob_service_client)
        flag_list = [
            f"--log ${{AZ_BATCH_NODE_ROOT_DIR}}/fsmounts/{FILE_SHARE_NAME}/"
            f"logs/{DATETIME_NOWISH}/{dataset.name}/${{AZ_BATCH_TASK_ID}}.log"
            ]
        for flag in flags:
            # Stops the force flag getting sent to derivatives
            if flag == "f" and isinstance(dataset, Derivative):
                continue
            else:
                flag_list.append(f"-{flag}")

        dependencies = []

        if isinstance(dataset, Dataset):
            flag_list.append(f"-t {dataset.timeout}")
            flag_list.append(f"-i '{dataset.name}/*'")
        elif isinstance(dataset, Derivative):  # these are derivatives
            # Create dependency
            dependencies = [generate_task_name(dependency) for dependency in
                            dataset.dependencies]
            flag_list.append(f"-d '{dataset.name}'")
        elif isinstance(dataset, Publication) and dataset.is_derivative:
            flag_list.append("-c")
            flag_list.append(f"-i '{dataset.name}/*'")
        command = generate_full_command(
            f"{dataset.base_fn} {' '.join(flag_list)}", production, dataset)

        tasks.append(
                create_task(dataset, command, dependencies,
                            dataset.max_wall_clock_minutes, production))
    return tasks


def generate_full_command(execute_command, production, dataset):

    command = f"""/bin/bash -c "
curl -sL https://aka.ms/InstallAzureCLIDeb | sudo bash &&
sudo rm runtimes.csv &&
sudo rm status.csv &&
sudo rm -r last-update && 
sudo mkdir -p ${{AZ_BATCH_NODE_ROOT_DIR}}/fsmounts/{FILE_SHARE_NAME}/logs/{DATETIME_NOWISH}/{dataset.name} &&
"""
    mount_files = [("runtimes.csv", "runtimes.csv"),
                   ("status.csv", "status.csv"),
                   ("last-update", "last-update")]
    if production:
        mount_files.append(("config.R", "data/runtime/config.R"))
    else:
        mount_files.append(("testconfig.R", "data/runtime/config.R"))

    for (vm_file, docker_file) in mount_files:
        command += f"sudo ln -s ${{AZ_BATCH_NODE_ROOT_DIR}}/fsmounts/" \
                   f"{FILE_SHARE_NAME}/{vm_file} {docker_file} && " + os.linesep

    command += f"{execute_command} 2>&1;" + os.linesep

    if production:
        command += create_commit_task(dataset)
    # Deletes the JSON config file from the working dir so it doesn't
    # end up in the results
    command += f'''sudo rm -f ${{AZ_BATCH_TASK_WORKING_DIR}}/{dataset.name}{CONFIG_FILE} &&''' + os.linesep
    # Copy the results into blob storage
    command += f"sudo mkdir ${{AZ_BATCH_TASK_WORKING_DIR}}/results && " \
               f"sudo cp -R /home/rstudio/covid-rt-estimates/" \
               f"{dataset.data_dir}/* ${{AZ_BATCH_TASK_WORKING_DIR}}/results\""
    return command


def create_commit_task(dataset):

    """This appends appends commands that commits the results to the repo
    Only used when in production mode"""

    command = f'''
az login --service-principal --username {APP_USER_NAME} \\
--password {APP_PASSWORD} \\
--tenant {TENANT_ID} &&
az batch account login --name {BATCH_ACCOUNT_NAME} \\
--resource-group {RESOURCE_GROUP} &&
az batch task create --job-id {COMMIT_JOB_ID} \\
--account-key {BATCH_ACCOUNT_KEY} \\
--account-name {BATCH_ACCOUNT_NAME} \\
--json-file ${{AZ_BATCH_TASK_WORKING_DIR}}/{dataset.name}{CONFIG_FILE} &&
'''
    if isinstance(dataset, Derivative):
        command += f"export LANG=en_US.UTF-8 &&" \
                   f"az storage blob download-batch -d . " \
                   f"--pattern **/summary/*.csv " \
                   f"-s results " \
                   f"--account-name {STORAGE_ACCOUNT_NAME} " \
                   f"--auth-mode login && "
    return command


def create_task(dataset, command, dependencies, max_wall_clock, production):

    if production:
        container = RESULTS_CONTAINER
    else:
        container = TEST_RESULTS_CONTAINER + "/" + \
                    generate_task_name(dataset.name)

    output_files = [
        # Upload results
        batch_models.OutputFile(
            file_pattern="$AZ_BATCH_TASK_WORKING_DIR/results/**/*",
            upload_options=batch_models.OutputFileUploadOptions(
                upload_condition=batch_models.
                OutputFileUploadCondition.task_success),
            destination=batch_models.OutputFileDestination(
                container=batch_models.OutputFileBlobContainerDestination(
                    path=dataset.data_dir,
                    container_url=container + SAS_TOKEN))),
        batch_models.OutputFile(
            file_pattern=f"$AZ_BATCH_NODE_ROOT_DIR/fsmounts/{FILE_SHARE_NAME}/*.csv",
            upload_options=batch_models.OutputFileUploadOptions(
                upload_condition=batch_models.
                    OutputFileUploadCondition.task_success),
            destination=batch_models.OutputFileDestination(
                container=batch_models.OutputFileBlobContainerDestination(
                    container_url=container + SAS_TOKEN))),
        batch_models.OutputFile(
            file_pattern=f"$AZ_BATCH_NODE_ROOT_DIR/fsmounts/{FILE_SHARE_NAME}/last-update/*",
            upload_options=batch_models.OutputFileUploadOptions(
                upload_condition=batch_models.
                    OutputFileUploadCondition.task_success),
            destination=batch_models.OutputFileDestination(
                container=batch_models.OutputFileBlobContainerDestination(
                    path="last-update",
                    container_url=container + SAS_TOKEN))),
        # Upload stderr and stdout
        batch_models.OutputFile(
            file_pattern="$AZ_BATCH_TASK_DIR/std*.txt",
            upload_options=batch_models.OutputFileUploadOptions(
                upload_condition=batch_models.
                OutputFileUploadCondition.task_completion),
            destination=batch_models.OutputFileDestination(
                container=batch_models.OutputFileBlobContainerDestination(
                    path=DATETIME_NOWISH + "/" + generate_task_name(dataset.name),
                    container_url=PROCESS_LOG_CONTAINER + "/" + SAS_TOKEN)))]

    return batch_models.TaskAddParameter(
        id=generate_task_name(dataset.name),
        display_name=(dataset.name + "_python_script_job"),
        command_line=command,
        resource_files=[batch_models.ResourceFile(
            storage_container_url=CONFIG_CONTAINER + SAS_TOKEN,
            blob_prefix=dataset.name + CONFIG_FILE)],
        depends_on=batch_models.TaskDependencies(
            task_ids=dependencies),
        user_identity=batch_models.UserIdentity(
            auto_user=batch_models.AutoUserSpecification(
                scope='pool',
                elevation_level='admin')),
        container_settings=batch_models.TaskContainerSettings(
            image_name=DOCKER_CONTAINER_URL,
            container_run_options='-w /home/rstudio/covid-rt-estimates'),
        constraints=batch_models.TaskConstraints(
            max_wall_clock_time=datetime.timedelta(minutes=max_wall_clock)),
        output_files=output_files)


def populate_file_share():
    """
        Populate File Share
        Generates a new file share if one doesn't exist and sets all the files
        into place.
    """
    file_share = file_service.FileService(account_name=STORAGE_ACCOUNT_NAME,
                                          account_key=STORAGE_ACCOUNT_KEY)

    # Creates a file share for input / output storage.
    if not file_share.create_share(share_name=FILE_SHARE_NAME, quota=1):
        LOGGER.info("File share already exists...")
    else:

        file_share.create_directory(share_name=FILE_SHARE_NAME,
                                    directory_name='logs')
        file_share.create_directory(share_name=FILE_SHARE_NAME,
                                    directory_name='last-update')
        # Create temp directory for file storage
        try:
            os.mkdir(TEMP_FILE_STORAGE)
        except FileExistsError as e:
            LOGGER.info(e)

        LOGGER.info("File share did not exist. Populating files")
        files = [f'{processable.name}.rds' for processable in
                 filter(lambda x: isinstance(x, Dataset), SCHEDULE)]

        for file in files:
            r = requests.get(ANCIL_FILES_URL + 'last-update/' + file)
            with open(TEMP_FILE_STORAGE + file, 'wb') as f:
                f.write(r.content)
            file_share.create_file_from_path(
                    share_name=FILE_SHARE_NAME,
                    directory_name='last-update',
                    file_name=file,
                    local_file_path=TEMP_FILE_STORAGE + file)

        r = requests.get(ANCIL_FILES_URL + 'runtimes.csv')
        with open(TEMP_FILE_STORAGE + 'runtimes.csv', 'wb') as f:
            f.write(r.content)
        file_share.create_file_from_path(
                share_name=FILE_SHARE_NAME,
                directory_name="",
                file_name='runtimes.csv',
                local_file_path=TEMP_FILE_STORAGE + 'runtimes.csv')

        r = requests.get(ANCIL_FILES_URL + 'status.csv')
        with open(TEMP_FILE_STORAGE + 'status.csv', 'wb') as f:
            f.write(r.content)
        file_share.create_file_from_path(
                share_name=FILE_SHARE_NAME,
                directory_name="",
                file_name='status.csv',
                local_file_path=TEMP_FILE_STORAGE + 'status.csv')

        file_share.create_file_from_path(
                share_name=FILE_SHARE_NAME,
                directory_name="",
                file_name='env_config.R',
                local_file_path='env_config.R')

        shutil.rmtree(TEMP_FILE_STORAGE)


def generate_pool_start_task():
    """Creates a start task for the processing pool. This mounts the fileshare
    that contains runtimes.csv, config.R and the last updates folder"""
    # make directory for the file mount
    task = f"/bin/bash -c 'sudo mkdir ${{AZ_BATCH_NODE_ROOT_DIR}}/fsmounts/" \
           f"{FILE_SHARE_NAME} &&" + os.linesep
    # if there's no directory for the smb credentials then make it too
    task += f"""if [ ! -d "/etc/smbcredentials" ]; then
    sudo mkdir /etc/smbcredentials
    fi &&""" + os.linesep
    # check if there are smb credentials and if not create them
    task += f"""if [ ! -f "/etc/smbcredentials/{STORAGE_ACCOUNT_NAME}.cred" ]; then
        echo "username={STORAGE_ACCOUNT_NAME}" >> /etc/smbcredentials/{STORAGE_ACCOUNT_NAME}.cred
        echo "password={STORAGE_ACCOUNT_KEY}" >> /etc/smbcredentials/{STORAGE_ACCOUNT_NAME}.cred
    fi &&"""
    # set the right perms on the file
    task += f"sudo chmod 600 /etc/smbcredentials/" \
            f"{STORAGE_ACCOUNT_NAME}.cred &&" + os.linesep
    # dump the smb connection string into a file for use later
    task += f"echo \"//{STORAGE_ACCOUNT_NAME}.file.core.windows.net/" \
            f"{FILE_SHARE_NAME} ${{AZ_BATCH_NODE_ROOT_DIR}}/fsmounts/" \
            f"{FILE_SHARE_NAME} cifs nofail,vers=3.0,credentials=/etc/" \
            f"smbcredentials/{STORAGE_ACCOUNT_NAME}.cred,dir_mode=0777," \
            f"file_mode=0777,serverino\" >> /etc/fstab &&"
    # mount the disk with the credentials
    task += f"sudo mount -t cifs //{STORAGE_ACCOUNT_NAME}.file.core.windows." \
            f"net/{FILE_SHARE_NAME} ${{AZ_BATCH_NODE_ROOT_DIR}}/fsmounts/" \
            f"{FILE_SHARE_NAME} -o vers=3.0,credentials=/etc/smbcredentials/" \
            f"{STORAGE_ACCOUNT_NAME}.cred," \
            f"dir_mode=0777,file_mode=0777,serverino'"
    return task


def create_json_config(dataset, blob_client):

    """Creates a JSON file that contains information for the task that commits
     the data back to the repo. This is needed because sudo permissions are
     required for this command and admin privileges are not possible using
     the azure CLI"""

    json_config = {"id": f"{generate_task_name(dataset.name)}_commit",
                   "commandLine": f"/bin/bash -c 'export LANG=en_US.UTF-8 && "
                                  f"cd ${{AZ_BATCH_NODE_SHARED_DIR}} && "
                                  f"az login --service-principal "
                                  f"--username {APP_USER_NAME} "
                                  f"--password {APP_PASSWORD} "
                                  f"--tenant {TENANT_ID} && "
                                  f"az storage blob download-batch -d . "
                                  f"""--pattern "{dataset.data_dir}/**/latest/*" """
                                  f"-s results "
                                  f"--account-name {STORAGE_ACCOUNT_NAME} "
                                  f"--auth-mode login && "
                                  f"az storage blob download-batch -d . "
                                  f"""--pattern "{dataset.data_dir}/**/summary/*" """
                                  f"-s results "
                                  f"--account-name {STORAGE_ACCOUNT_NAME} "
                                  f"--auth-mode login && "
                                  f"az storage blob download-batch -d . "
                                  f"""--pattern "last-update/*" """
                                  f"-s results "
                                  f"--account-name {STORAGE_ACCOUNT_NAME} "
                                  f"--auth-mode login && "
                                  f"az storage blob download-batch -d . "
                                  f"""--pattern "*.csv" """
                                  f"-s results "
                                  f"--account-name {STORAGE_ACCOUNT_NAME} "
                                  f"--auth-mode login && "
                                  f"sudo cp -p -r {dataset.data_dir}/* "
                                  f"${{AZ_BATCH_NODE_SHARED_DIR}}/covid-rt-estimates/{dataset.data_dir}/ && "
                                  f"sudo cp -p -r *.csv "
                                  f"${{AZ_BATCH_NODE_SHARED_DIR}}/covid-rt-estimates/ && "
                                  f"sudo cp -p -r last-update/* "
                                  f"${{AZ_BATCH_NODE_SHARED_DIR}}/covid-rt-estimates/last-update/ && "
                                  f"cd ${{AZ_BATCH_NODE_SHARED_DIR}}/covid-rt-estimates && "
                                  f"git add -A && "
                                  f"git commit -m {dataset.name}_batch_automated_commit "
                                  f"--author \"{GITHUB_USER_NAME} <{GITHUB_EMAIL}>\" && "
                                  f"git pull -Xours && "
                                  f"git push'",
                   "waitForSuccess": True,
                   "outputFiles": [
                        {"filePattern": "$AZ_BATCH_TASK_DIR/std*.txt",
                         "destination": {
                             "container": {
                                 "path": DATETIME_NOWISH + "/" +
                                         generate_task_name(dataset.name),
                                 "containerURL": COMMIT_LOG_CONTAINER + "/" +
                                                 SAS_TOKEN
                             }},
                         "uploadOptions": {
                            "uploadCondition": "TaskCompletion"
                            },
                         }],
                   "userIdentity": {
                       "autoUser": {
                           "elevationLevel": "admin",
                           "scope": "pool"
                       },
                       "userName": None}
                   }
    with open(generate_task_name(dataset.name) +
              CONFIG_FILE, "w") as file:
        json.dump(json_config, file)

    blob_client = blob_client.get_blob_client(
        container=CONFIG_FOLDER,
        blob=dataset.name + CONFIG_FILE)
    with open(generate_task_name(dataset.name) +
              CONFIG_FILE, "rb") as data:
        blob_client.upload_blob(data, overwrite=True)

    os.remove(generate_task_name(dataset.name) +
              CONFIG_FILE)


def run(datasets, production, flags):

    populate_file_share()
    batch_client = get_batch_client()

    try:
        create_processing_pool(batch_client, generate_pool_start_task())
        create_commit_pool(batch_client)
        create_job(batch_client, PROCESSING_JOB_ID, PROCESSING_POOL_ID)
        create_job(batch_client, COMMIT_JOB_ID, COMMIT_POOL_ID)

        tasks = generate_tasks(PROCESSING_JOB_ID, datasets, production, flags)
        batch_client.task.add_collection(job_id=PROCESSING_JOB_ID, value=tasks)
        LOGGER.info("Tasks added to Job")

    except batch_models.BatchErrorException as err:
        print_batch_exception(err)
        raise
