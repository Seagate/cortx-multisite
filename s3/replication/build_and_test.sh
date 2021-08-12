#!/bin/bash
#
# Copyright (c) 2021 Seagate Technology LLC and/or its Affiliates
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
# For any questions about this software or licensing,
# please email opensource@seagate.com or cortx-questions@seagate.com.

#
# build-runalltest.sh allows to build all multisite moudles,
# create virtual environment, populating service files with
# correct paths, copying to default systemd location and
# starting background processes and running load transfer tests for
# s3replicator and s3replicationmanager.
#
# Usage : sh ./build_and_test.sh
# 

# Project root directory
MULTISITE_ROOT_DIR="$(cd ../../; pwd)"
echo "Project directory : "$MULTISITE_ROOT_DIR

# Replication directory
REPLICATION_DIR="$(pwd)"
echo "Replication directory :" $REPLICATION_DIR

REPLICATION_VENV=$REPLICATION_DIR/s3env/bin
echo "Virtual environment directory : "$REPLICATION_VENV

# Module directory
S3_REPLICATION_COMMON_SRC_DIR=$REPLICATION_DIR/common/src
S3_REPLICATION_MANAGER_SRC_DIR=$REPLICATION_DIR/manager/src
S3_REPLICATOR_SRC_DIR=$REPLICATION_DIR/replicator/src

# Test directory
S3_REPLICATION_COMMON_TEST_DIR=$REPLICATION_DIR/common/tests/system
S3_REPLICATION_MANAGER_TEST_DIR=$REPLICATION_DIR/manager/tests/system
S3_REPLICATOR_TEST_DIR=$REPLICATION_DIR/replicator/tests/system

echo "Module directories -"
echo "Common module directory :" $S3_REPLICATION_COMMON_SRC_DIR
echo "Manager module directory :" $S3_REPLICATION_MANAGER_SRC_DIR
echo "Replicator module directory :" $S3_REPLICATOR_SRC_DIR

# Helper method to stop background services.
stop_replication_services()
{
    systemctl stop s3_in_memory.service
    systemctl stop s3replicationmanager.service
    systemctl stop s3replicator.service

    # Check if any service name is passed or not.
    # If passed then it's an error case. Print an error message and exit.
    if [ $# -eq 0 ]; then
        echo "Shut down all processes!"
    else
        FAILED_SVC=$1
        echo "ERROR : $FAILED_SVC service activation failed!"
        exit -1
    fi
}

# Active an environment
python3 -m venv $REPLICATION_DIR/s3env
source $REPLICATION_DIR/s3env/bin/activate

# Check and download dependencies
pip3 install --upgrade setuptools

cd $REPLICATION_DIR
make install

# Create and copy files
S3_IN_MEMRORY_SVC_FILE=$S3_REPLICATION_COMMON_SRC_DIR/systemd/s3_in_memory.service
MANGER_SVC_FILE=$S3_REPLICATION_MANAGER_SRC_DIR/systemd/s3replicationmanager.service
REPLICATOR_SVC_FILE=$S3_REPLICATOR_SRC_DIR/systemd/s3replicator.service

# Systemd service files
SYSD_S3_IN_MEMORY_SVC_FILE=/etc/systemd/system/s3_in_memory.service
SYSD_REPLICATION_MANAGER_SVC_FILE=/etc/systemd/system/s3replicationmanager.service 
SYSD_REPLICATOR_SVC_FILE=/etc/systemd/system/s3replicator.service

# Create creadential file in home directory with below path.
# ~/.cortxs3/credentials.yaml
CORTX_S3_CRED_FILE=~/.cortxs3/credentials.yaml
CORTX_S3_DIR="$(dirname "$CORTX_S3_CRED_FILE")"
if [ -f "$CORTX_S3_CRED_FILE" ]; then
    echo "$CORTX_S3_CRED_FILE exist!"
else
    if [ -d $CORTX_S3_DIR]; then
        echo "$CORTX_S3_DIR exist!"
    else
        mkdir $CORTX_S3_DIR
    fi
    touch $CORTX_S3_CRED_FILE
    # Placeholder for keys to run against in-memory s3 server.
    echo "access_key: '<your access_key>'" > $CORTX_S3_CRED_FILE
    echo "secret_key: '<your secret_key>'" >> $CORTX_S3_CRED_FILE
fi

rm -f $SYSD_S3_IN_MEMORY_SVC_FILE 
rm -f $SYSD_REPLICATION_MANAGER_SVC_FILE
rm -f $SYSD_REPLICATOR_SVC_FILE

# Strip hardcoded lines
head -n -1 $S3_IN_MEMRORY_SVC_FILE > $SYSD_S3_IN_MEMORY_SVC_FILE
head -n -1 $MANGER_SVC_FILE > $SYSD_REPLICATION_MANAGER_SVC_FILE
head -n -1 $REPLICATOR_SVC_FILE > $SYSD_REPLICATOR_SVC_FILE

echo "ExecStart=$REPLICATION_VENV/python3 $S3_REPLICATION_COMMON_TEST_DIR/s3_in_memory.py" >> $SYSD_S3_IN_MEMORY_SVC_FILE
echo "ExecStart=$REPLICATION_VENV/python3 -m s3replicationmanager" >> $SYSD_REPLICATION_MANAGER_SVC_FILE
echo "ExecStart=$REPLICATION_VENV/python3 -m s3replicator" >> $SYSD_REPLICATOR_SVC_FILE

# Start background process
DAEMON_SVC_DIR=/etc/systemd/system 

echo "Service files created at : "$DAEMON_SVC_DIR

sudo systemctl daemon-reload

# Starting s3_in_memory service 
systemctl start s3_in_memory.service
svc_status=$(systemctl is-active s3_in_memory.service)
if [ $svc_status != "active" ]
then
    stop_replication_services "s3_in_memory"
fi

# Starting s3replicationmanager service 
systemctl start s3replicationmanager.service
svc_status=$(systemctl is-active s3replicationmanager.service)
if [ $svc_status != "active" ]
then
    stop_replication_services "s3replicationmanager"
fi

# Starting s3replictor service 
systemctl start s3replicator.service
svc_status=$(systemctl is-active s3replicator.service)
if [ $svc_status != "active" ]
then
    stop_replication_services "s3replicator"
fi

# Start load transfer tests
echo "----------------- s3replicationmanager test started -------------------"
sleep 2 # For better logging
$REPLICATION_VENV/python3 $S3_REPLICATION_MANAGER_TEST_DIR/load_transfer_test.py
if [[ $? = 0 ]]; then
    echo "success"
    MANAGER_LOAD_TRANSFER_TEST_RESULT="PASSED"
else
    echo "failure: $?"
    MANAGER_LOAD_TRANSFER_TEST_RESULT="FAILED"
fi
echo "------------------ s3replicationmanager test ended --------------------"

echo "- - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -"

echo "---------------------- s3replicator test started ----------------------"
sleep 2
$REPLICATION_VENV/python3 $S3_REPLICATOR_TEST_DIR/load_transfer_test.py
if [[ $? = 0 ]]; then
    echo "success"
    REPLICATOR_LOAD_TRANSFER_TEST_RESULT="PASSED"
else
    echo "failure: $?"
    REPLICATOR_LOAD_TRANSFER_TEST_RESULT="FAILED"
fi
echo "---------------------- s3replicator test ended ------------------------"

# Stopping all the started background processes
echo "Shutting down all started processes..."
stop_replication_services
sleep 2

# Test Summary 
echo "========================= Test Summary ==========================="
echo "Test 1: Load transfer for s3replicationmaanger [$MANAGER_LOAD_TRANSFER_TEST_RESULT]"
echo "Test 2: Load transfer for s3replicatior [$REPLICATOR_LOAD_TRANSFER_TEST_RESULT]"
echo "=================================================================="

# Exit the environment
deactivate
cd $MULTISITE_ROOT_DIR

echo "Exiting successfully..."
