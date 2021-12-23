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

# Kafka consumer code
# Please note : Few changes are required in the replication
# manager module to add this consumer code.
# For more details, please refer the feature branch code:
# https://github.com/priyanka25081999/cortx-multisite/tree/ps/kafka

import json
from ast import literal_eval
from s3replicationmanager.prepare_job import PrepareReplicationJob
# Make sure to install aiokafka module using the command
# >> pip3 install aiokafka
# aiokafka version used for testing : aiokafka==0.7.2
from aiokafka import AIOKafkaConsumer
from aiokafka.structs import OffsetAndMetadata, TopicPartition


class KafkaMain:
    consumer = None

    '''
    Job id to offset mapping
      {
        "job_id": { <topic> : <topic_name>,
                    <partition> : <partition_name>
                    <offset> : <offset_value>
                  }
            ...
       }
    '''
    job_id_to_offset = {}
    last_commited_offset = 0

    def __init__(self):
        """Initialize."""

    # Initialize the kafka consumer
    # This method should be called from app.py class on startup.
    def initialize(self, app):
        self._app = app
        KafkaMain.consumer = AIOKafkaConsumer(
            'FDMI',
            bootstrap_servers='127.0.0.1:9092',
            group_id="test",
            auto_offset_reset='latest',
            enable_auto_commit=False)

    # Getter methods
    def get_topic(self, job_id):
        """Returns the topic."""
        return KafkaMain.job_id_to_offset[job_id]["Topic"]

    def get_partition(self, job_id):
        """Returns the partition."""
        return KafkaMain.job_id_to_offset[job_id]["Partition"]

    def get_offset(self, job_id):
        """Returns the offset."""
        return KafkaMain.job_id_to_offset[job_id]["Offset"]

    # Remove job from job-id to offset mapping after commit
    def remove_job_from_mapping(self, job_id):
        removed_key = KafkaMain.job_id_to_offset.pop(job_id, None)
        if removed_key is not None:
            print("Removed job id from mapping : {}".format(removed_key))
        else:
            print("Job id [{}] does not exist".format(job_id))

    # Send job for replication after consuming from kafka
    async def sendJob(self, data, topic, partition, offset):
        print("Sending Jobs...")
        fdmi_dict = literal_eval(data)
        job_record = PrepareReplicationJob.from_fdmi(fdmi_dict)

        if job_record is None:
            print("BadRequest")
            return

        jobs_list = self._app['all_jobs']
        if jobs_list.is_job_present(job_record["replication-id"]):
            # Duplicate job.
            print('Duplicate Job!')
            return

        job = jobs_list.add_job_using_json(job_record)
        job_id = job.get_job_id()
        print("Added Job : {}".format(job_id))

        KafkaMain.job_id_to_offset[job_id] = {
            "Topic": topic, "Partition": partition, "Offset": offset}
        print("Job-id to offset mapping : {}".format(KafkaMain.job_id_to_offset))

    # Start the consumer and add the consumer details into list
    async def consume(self):
        await KafkaMain.consumer.start()
        topic_partition = TopicPartition('FDMI', 0)
        position = await KafkaMain.consumer.position(topic_partition)

        try:
            print("In consumer loop")
            # Consume messages
            async for msg in KafkaMain.consumer:
                if msg.offset == position:
                    pass
                else:
                    obj = json.loads(msg.value.decode())
                    print("Event consumed : {}", obj['cr_val'])

                    # Send jobs for replication
                    await self.sendJob(obj['cr_val'], msg.topic, msg.partition, msg.offset)
        except Exception as e:
            print("Exception : {}".format(e))
        finally:
            await KafkaMain.consumer.stop()
            # Close the kafka consumer
            KafkaMain.consumer.close()

    # Manually commit offset after replication is completed
    # This method should be called from job_routes.py
    # After getting replication status as completed
    async def commit_job(self, job_id):
        """Manual commit to Kafka."""
        tp = TopicPartition(self.get_topic(job_id), self.get_partition(job_id))
        offsets = {tp: OffsetAndMetadata(self.get_offset(job_id), '')}
        await KafkaMain.consumer.commit(offsets=offsets)

        # Get the last committed offset
        KafkaMain.last_commited_offset = await KafkaMain.consumer.committed(tp)
        print(
            "Committed offset to kafka : {}".format(
                KafkaMain.last_commited_offset))

        # Remove the completed job from dictionary
        self.remove_job_from_mapping(job_id)
