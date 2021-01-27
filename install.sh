#!/usr/bin/env bash
AZURE_TENANT_ID=$1
AZURE_CLIENT_ID=$2
AZURE_CLIENT_SECRET=$3

if [[ "$1" = "" ]]; then
    echo "This script requires the following arguments"
    echo "The Azure Tenant ID"
    echo "The Azure Client ID"
    echo "The Azure Client Secret"
elif [[ "$2" = "" ]]; then
    echo "This script requires the following arguments"
    echo "The Azure Tenant ID"
    echo "The Azure Client ID"
    echo "The Azure Client Secret"
elif [[ "$3" = "" ]]; then
    echo "This script requires the following arguments"
    echo "The Azure Tenant ID"
    echo "The Azure Client ID"
    echo "The Azure Client Secret"
else

# Install required libraries
echo 'Installing libraries...'
sudo apt-get install software-properties-common -y
sudo apt-add-repository universe -y
sudo apt-get update -y
sudo apt install python3-pip -y

yes | pip3 install azure-batch
yes | pip3 install azure-storage-file
yes | pip3 install azure-keyvault
yes | pip3 install azure-storage-blob
yes | pip3 install azure-identity
echo 'Libraries installed'


KEYS="export AZURE_TENANT_ID=$1
export AZURE_CLIENT_ID=$2
export AZURE_CLIENT_SECRET=$3"
# Create shell script that the cron job will run
echo "#!/usr/bin/env bash
$KEYS
git pull origin master
python3 batch_scheduler.py \$*" >> run_batch.sh
echo 'Created run_batch.sh'
echo "#!/usr/bin/env bash
$KEYS
python3 single_scheduler.py \$*" >> run_one.sh
echo 'Created run_one.sh'
echo "#!/usr/bin/env bash
git pull origin master
$KEYS
python3 ~/covid-rt-estimates-batch/re_scheduler.py \$*" >> rerun.sh
echo 'Created rerun.sh'

chmod +x run_batch.sh
chmod +x run_one.sh
chmod +x rerun.sh


# Create Cron job
crontab -l > mycron
echo "0 0 * * * ~/run_batch.sh --production" >> mycron
crontab mycron
rm mycron
echo "Created cron job"

echo "Scheduler installed"
fi