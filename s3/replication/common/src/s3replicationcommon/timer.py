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

from enum import Enum
import time


class TimerState(Enum):
    INITIALISED = 1
    STARTED = 2
    STOPPED = 3


class Timer:
    def __init__(self):
        self._start = None
        self._end = None
        self._state = TimerState.INITIALISED

    def start(self):
        if self._state == TimerState.INITIALISED:
            self._start = time.perf_counter()
            self._state = TimerState.STARTED
        else:
            # report error
            return -1
        return 0

    def stop(self):
        if self._state == TimerState.STARTED:
            self._end = time.perf_counter()
            self._state = TimerState.STOPPED
        else:
            # report error
            return -1
        return 0

    def reset(self):
        self._start = None
        self._end = None
        self._state = TimerState.INITIALISED
        return 0

    def elapsed_time_ms(self):
        if self._state == TimerState.STOPPED:
            return int(round((self._end - self._start) * 1000))
        else:
            # report error
            return -1
