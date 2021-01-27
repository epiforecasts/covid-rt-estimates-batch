from env_config.accounts import GITHUB_USER_NAME, GITHUB_TOKEN


PROCESSING_POOL_ID = 'covid-r-pool'
PROCESSING_POOL_VM_SIZE = 'STANDARD_D64_V3'
PROCESSING_POOL_MAX_VM = 10
PROCESSING_POOL_SCALE_FORMULA = f"""startingNumberOfVMs = 0;
maxNumberofVMs = {PROCESSING_POOL_MAX_VM};
pendingTaskSamplePercent = $PendingTasks.GetSamplePercent(180 * TimeInterval_Second);
pendingTaskSamples = pendingTaskSamplePercent < 70 ? startingNumberOfVMs : avg(
$PendingTasks.GetSample(180 * TimeInterval_Second));
$TargetLowPriorityNodes= (pendingTaskSamples > 1) ? min(maxNumberofVMs, (pendingTaskSamples * 0.6) + 1) : $TargetLowPriorityNodes;
$TargetLowPriorityNodes= (pendingTaskSamples==1) ? (1): $TargetLowPriorityNodes;
$TargetLowPriorityNodes= (pendingTaskSamples<1) ? (0): $TargetLowPriorityNodes;
$TargetDedicatedNodes=min(maxNumberofVMs, pendingTaskSamples * 0.4);
$TargetLowPriorityNodes= ($TargetLowPriorityNodes + $TargetDedicatedNodes < pendingTaskSamples) ? ($TargetLowPriorityNodes + 1): $TargetLowPriorityNodes;
$NodeDeallocationOption = taskcompletion;"""
PROCESSING_POOL_SCALE_INTERVAL_MINUTES = 5
COMMIT_POOL_ID = 'covid-r-commit-pool'
COMMIT_POOL_VM_SIZE = 'STANDARD_D4_V3'

COMMIT_POOL_START_TASK = f'''/bin/bash -c "cd ${{AZ_BATCH_NODE_SHARED_DIR}} &&
git clone -b batch_test --depth 100 https://{GITHUB_USER_NAME}:{GITHUB_TOKEN}@github.com/epiforecasts/covid-rt-estimates.git &&
curl -sL https://aka.ms/InstallAzureCLIDeb | sudo bash
"'''
COMMIT_POOL_SCALE_FORMULA = f"""startingNumberOfVMs = 0;
maxNumberofVMs = 1;
pendingTaskSamplePercent = $PendingTasks.GetSamplePercent(180 * TimeInterval_Second);
pendingTaskSamples = pendingTaskSamplePercent < 70 ? startingNumberOfVMs : avg(
$PendingTasks.GetSample(180 * TimeInterval_Second));
$TargetDedicatedNodes=min(maxNumberofVMs, pendingTaskSamples);
$NodeDeallocationOption = taskcompletion;"""
COMMIT_POOL_SCALE_INTERVAL_MINUTES = 15

