# Covid Infrastructure

## Usage
### Running the scheduled tasks:
This should be done under cron using `~/run_batch.sh` located in the home directory. It can be manually triggered using the following steps:
2) run the task with the following command `~/run_batch.sh`, with optional flags. Help on these can be found with `~/run_batch.sh -h`. Key flags are: 
   * `-p / --production` use production mode not test
   * `--flags=xyz` which passes the flags on to the rscript as -x -y -z (in addition to timeouts, etc) 

### Running a single task:
1) connect to the cronbox
2) run the task with the following command `~/run_one <dataset name>`
To get help on the available commands run `~/run_one -h`. This should accept the same flags as running a complete set plus additional flags that normally come from the schedule definition:
   * `-c` specifies the name is of a collated derivative not a dataset
   * `-t` specifies the timeout of the stan threads (default = 7200 seconds)
   * `-w` specifies the maximum wallclock time of the task (default = 300 minutes)
   * `-p / --production` use production mode not test

### accessing results and logs

### republishing results to dataverse or resummarising results 
1) connect to the cronbox
2) run the task with the following command `~/rerun.sh <type> <dataset name>`
To get help on the available commands run `~/rerun.sh -h`. This should accept the same flags as running a complete set plus additional flags that normally come from the schedule definition:
   * type - this should be either "s" for summary or "p" for publish
   * `-c` specifies the name is of a collated derivative not a dataset (type republish only)
   * `-p / --production` use production mode not test



### syncing runtime / status csv files with github
This should be run automatically by the <todo: script details here>. This script is set to sweep hourly.

## Configuration

The rscript configuration is copied from includes/config.R and includes/testconfig.R which provides the config.R file for production and test environments respectively
The azure batch configuration is broken up amongst the contents of the env_config directory, with files that hopefully break down where things are specified. One area that is easy to confuse is pool includes the hardware that is being run whilst batch_vm specifies the os that is being run on that hardware.

## Setup from scratch
Jobs are submitted to azure with a "Scheduling VM".
This is a small VM that uses cron to trigger the submission of jobs to azure.

Create a VM on azure, the smallest possible VM will be fine.
Any version of linux should be fine, this was tested on Ubuntu Server 18.04 LTS.

Connect via Bastion or SSH using the administrator account, as sudo permissions 
will be needed
Enter the command   
```nano install.sh```  
This will open up a text editor. Copy and paste the contents of install.sh into 
the text editor. Save it (Ctrl + O) and exit (Ctrl + x).  
Enter the following command to make the script executable 
```chmod +x install.sh``` 

#### Service Principal and Applications

This infrastructure already exists and shouldn't need altering or re-creating, but is here for completeness sake.

Depending on the context the entitiy we are talking about can be called an Application or a Service Principal.
Microsoft's justification is "The application object is the global representation of your application for use across all tenants, and the service principal is the local representation for use in a specific tenant."
I will just refer to it as an Application, but when you see Service Principal in the Azure portal, it's referring to the same thing

We need parts of our code to be able to send commands to azure. To do this we 
need to create an "Application".
Applications can be created in Azure Active Directory / App registrations.
From within the newly created Application go to "Certificates & secrets" and create a new client secret.
We now need to give our Application permissions to be able to submit batch jobs. The user account used to grant permissions must be a "Member" account and not a "Guest" account.
Go to Batch accounts and click on the appropriate Batch account. From within the subscription go Access control (IAM).
From here you can give your Application the "contributor" role. This will allow the Application to send commands to that batch account.

#### Secrets and Key Vault
Quite a few other sensitive bits of data are needed for this code to operate.
Using the same method as giving permissions the batch and account, we can give our app permissions to the Key Vault.
Go to Key Vaults and click on the appropriate key vault. From here go to 
The same thing will need to be done for the Key Vault Access control (IAM).
From here you can give your Application the "contributor" role. This will allow the Application to create a key vault object that contains all other secrets needed by accounts.py.

#### Personal Access Token

The covid-rt-estimates-infra repo is private, so the script will need a Github "Personal Access Token" from an account that has access to this repo (which you should have if you are reading this!).
In github, go to settings, Developer settings and Personal access tokens. 
From here you can create a personal access token. Ensure that "Full control of private repositories" is checked, otherwise the token will not have the access that we need.
Github will now display a long string, this is your personal access token.
When the repository is first cloned, the personel access information is stored in the .git folder. This will allow the repo to keep itself up to date for as long as the personal access token is valid. 

The script all also need three other things. 
The Azure tenant ID. this can be found from within the portal of your azure account. 
Client ID. This is the ID of the Application that has permissions to submit batch requests
Client Secret. The secret token that is associated with the Application

We will now execute our install script with our personal access token, if our git access token was "123", the command would be  
```./install.sh 123 AZURE_TENANT_ID AZURE_CLIENT_ID AZURE_CLIENT_SECRET```

The script will do the following things:
* Install the needed python azure libraries 
 (The installation of azure-storage-file causes a segmentation fault for an unknown reason. Do not be alarmed, the library will still be installed properly. Believe this to be a Microsoft issue)  
* Creation of a script called ```run_batch.sh``` that ensures the git repo is updated before submitting a job  
* Creates a cron job that will execute ```run_batch.sh``` everyday at midnight

The script will take a few minutes to run.
Access to the scheduler VM will need to be controlled as it needs to keep a record of the AZURE_TENANT_ID, AZURE_CLIENT_ID and AZURE_CLIENT_SECRET.

### Environment assumptions:
