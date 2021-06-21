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


class S3RequestState(Enum):
    INITIALISED = 1
    RUNNING = 2  # start or resume
    PAUSED = 4  # pause
    COMPLETED = 5  # after successful/failed processing
    ABORTED = 6  # explicitly aborted
    FAILED = 7


def move_across_sets(source_set, target_set, element):
    """Move element from one set to another."""
    source_set.remove(element)
    target_set.add(element)


def make_baseurl(scheme, host, port=None):
    """Creates URL using given parameters.

    Args
    -----
        scheme (str): http or https
        host (str): hostname
        port (int, optional): Port number as integer

    Returns
    -------
        Formatted URL to use with http apis.
    """
    base_url = None
    if port is None:
        base_url = "{}://{}".format(scheme, host)
    else:
        base_url = "{}://{}:{}".format(scheme, host, port)
    return base_url


def url_with_resources(base_url, resources=None):
    """Creates URL using given parameters.

    Args
    -----
        base_url (str): Base url, example http://somehost
        resources (list[str], optional): Resource name. Defaults to None.

    Returns
    -------
        Formatted URL to use with http apis.
    """
    if resources is None:
        return base_url
    else:
        return "{}/{}".format(base_url.rstrip('/'), "/".join(resources))
