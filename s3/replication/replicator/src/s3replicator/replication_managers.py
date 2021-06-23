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
from collections import OrderedDict
from .replication_manager import ReplicationManagerJsonEncoder


class ReplicationManagers(OrderedDict):
    @staticmethod
    def dumps(obj):
        """Helper to format json."""
        return json.dumps(obj, cls=ReplicationManagerJsonEncoder)

    def __init__(self):
        """Initialise ReplicationManagers collection."""
        # Dictionary holding manager_id and attributes
        # E.g. : manager =
        #     {'id':'some-uuid','endpoint':'http://localhost:8080'}
        # managers = {some-uuid': ReplicationManager(endpoint), ...}
        super(ReplicationManagers, self).__init__()

    async def close(self):
        """Resets and closes all replication manager sessions."""
        for manager in self.values():
            await manager.close()
