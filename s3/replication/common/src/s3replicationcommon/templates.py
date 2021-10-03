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

import json
import os


def replication_job_template():
    """Returns Replication job template loaded from json file."""
    template_path = os.path.join(
        os.path.dirname(__file__),
        '..', 'templates',
        'replication_job_template.json')

    with open(template_path, 'r') as template_file:
        template = json.load(template_file)

    return template


def fdmi_record_template():
    """Returns fdmi record template loaded from json file."""
    template_path = os.path.join(
        os.path.dirname(__file__),
        '..', 'templates',
        'fdmi_record_template.json')

    with open(template_path, 'r') as template_file:
        template = json.load(template_file)

    return template


def fdmi_record_tag_template():
    """Returns fdmi record template with tag loaded from json file."""
    template_path = os.path.join(
        os.path.dirname(__file__),
        '..', 'templates',
        'fdmi_record_tag_template.json')

    with open(template_path, 'r') as template_file:
        template = json.load(template_file)

    return template


def subscribe_payload_template():
    """Returns subscribe payload template loaded from json file."""
    template_path = os.path.join(
        os.path.dirname(__file__),
        '..', 'templates',
        'subscribe_payload_template.json')

    with open(template_path, 'r') as template_file:
        template = json.load(template_file)

    return template
