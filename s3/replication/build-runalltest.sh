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
# starting daemon processes and running load transfer tests for
# s3replicator and s3replicationmanager.
#
# Usage : sh ./build-runalltest.sh
# 


# Project root directory
MULTISITE_ROOT_DIR="$(cd ../../; pwd)"
echo "Project directory : "$MULTISITE_ROOT_DIR

# Replication directory
REPLICATION_DIR="$(pwd)"
echo "Replication directory :" $REPLICATION_DIR

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

# Active an environment
python3 -m venv $REPLICATION_DIR/s3env
source $REPLICATION_DIR/s3env/bin/activate

# Check and download dependencies
pip3 install --upgrade setuptools

pip3 install -r $REPLICATION_DIR/common/requirements.txt
pip3 install -r $REPLICATION_DIR/manager/requirements.txt
pip3 install -r $REPLICATION_DIR/replicator/requirements.txt

cd $REPLICATION_DIR
make clean install

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
    echo "access_key: '<your access_key>'" > $CORTX_S3_CRED_FILE
    echo "secret_key: '<your secret_key>'" >> $CORTX_S3_CRED_FILE
fi

rm -f $SYSD_S3_IN_MEMORY_SVC_FILE 
rm -f $SYSD_REPLICATION_MANAGER_SVC_FILE
rm -f $SYSD_REPLICATOR_SVC_FILE

# Strip hardcoded lines
head -n -2 $S3_IN_MEMRORY_SVC_FILE > $SYSD_S3_IN_MEMORY_SVC_FILE
head -n -2 $MANGER_SVC_FILE > $SYSD_REPLICATION_MANAGER_SVC_FILE
head -n -2 $REPLICATOR_SVC_FILE > $SYSD_REPLICATOR_SVC_FILE

# Setting environment and working directory in service files
Environment="PYTHONPATH=$S3_REPLICATION_COMMON_SRC_DIR"
echo "Environment=$Environment" >> $SYSD_S3_IN_MEMORY_SVC_FILE
echo "Environment=$Environment" >> $SYSD_REPLICATION_MANAGER_SVC_FILE
echo "Environment=$Environment" >> $SYSD_REPLICATOR_SVC_FILE

echo "WorkingDirectory=$S3_REPLICATION_COMMON_SRC_DIR" >> $SYSD_S3_IN_MEMORY_SVC_FILE
echo "ExecStart=/usr/bin/python3 $S3_REPLICATION_COMMON_TEST_DIR/s3_in_memory.py" >> $SYSD_S3_IN_MEMORY_SVC_FILE

echo "WorkingDirectory=$S3_REPLICATION_MANAGER_SRC_DIR" >> $SYSD_REPLICATION_MANAGER_SVC_FILE
echo "WorkingDirectory=$S3_REPLICATOR_SRC_DIR" >> $SYSD_REPLICATOR_SVC_FILE

# Start daemon process
DAEMON_SVC_DIR=/etc/systemd/system 

echo "Service files created at : "$DAEMON_SVC_DIR

sudo systemctl daemon-reload

systemctl enable s3_in_memory.service
systemctl enable s3replicationmanager.service
systemctl enable s3replicator.service

# Starting services
systemctl start s3_in_memory.service
svc_status=$(systemctl is-active s3_in_memory.service)

if [ $svc_status != "active" ]
then
    {echo "ERROR : s3_in_memory service activation failed!"; exit -1}
else
    echo "s3_in_memory service is actived"
    
    systemctl start s3replicationmanager.service
    svc_status=$(systemctl is-active s3replicationmanager.service)

    if [ $svc_status != "active" ]
    then
        $(systemctl stop s3_in_memory.service)
        {echo "ERROR : s3replicationmanager service activation failed!"; exit -1}
    else
        echo "s3replicationmanager service is actived"
        
        systemctl start s3replicator.service
        svc_status=$(systemctl is-active s3replicator.service)

        if [ $svc_status != "active" ]
        then
            $(systemctl stop s3_in_memory.service)
            $(systemctl stop s3replicationmanager.service)
            {echo "ERROR : s3replicator service activation failed!"; exit -1}
        else
            echo "s3replicator service is actived"
        fi
    fi
fi

# Start load transfer tests
echo "----------------- s3replicationmanager test started -------------------"
sleep 2 # For better logging
python3 $S3_REPLICATION_MANAGER_TEST_DIR/load_transfer_test.py
echo "------------------ s3replicationmanager test ended --------------------"

echo "- - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -"

echo "---------------------- s3replicator test started ----------------------"
sleep 2
python3 $S3_REPLICATOR_TEST_DIR/load_transfer_test.py
echo "---------------------- s3replicator test ended ------------------------"

# Stopping all the started daemon processes
echo "Shutting down all started processes..."
sleep 2

systemctl stop s3_in_memory.service
systemctl stop s3replicationmanager.service
systemctl stop s3replicator.service

# Clean the build
cd $REPLICATION_DIR
echo "Cleaning up the build..."
make clean

# Exit the environment
deactivate
cd $MULTISITE_ROOT_DIR

echo "Exiting successfully..."
