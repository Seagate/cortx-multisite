#!/usr/bin/env python3

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

import hashlib
import os
from s3replicationcommon.s3_common import S3RequestState

# Test case will allocate a single block of data and reuse it


class GlobalTestDataBlock:
    @classmethod
    def create(cls, block_size):
        assert block_size, "block_size should be non zero."
        assert block_size == cls._block_size, \
            "Invalid use. Only one size supported."

        if cls._block is None:
            cls._block_size = block_size
            cls._block = os.urandom(block_size)

            hash = hashlib.md5()
            hash.update(cls._block)
            cls._md5 = hash.hexdigest()

        return cls._block

    @classmethod
    def get_md5(cls):
        assert cls._md5, "Class instance not initialised by calling create()."
        return cls._md5

    @classmethod
    def destroy(cls):
        cls._block = None
        cls._block_size = None
        cls._md5 = None

# Fixed size object, where fetch will be called only once.


class FixedObjectDataGenerator:
    def __init__(self, logger, object_name, object_size):
        """Initialise."""
        self._logger = logger

        self.object_name = object_name
        self.object_size = object_size

        self._hash = hashlib.md5()
        self._data = GlobalTestDataBlock.create(object_size)
        self._md5 = GlobalTestDataBlock.get_md5()

        self._state = S3RequestState.INITIALISED

    def get_state(self):
        """Returns current request state."""
        return self._state

    def get_md5(self):
        if self._state == S3RequestState.COMPLETED:
            return self._md5
        return None

    async def fetch(self, chunk_size):
        assert chunk_size == self.object_size, \
            "chunk_size should be same as object_size"

        self._state = S3RequestState.RUNNING
        yield self._data
        self._state = S3RequestState.COMPLETED
        return self._state
