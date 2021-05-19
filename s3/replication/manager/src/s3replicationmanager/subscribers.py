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

class Subscribers:
    def __init__(self):
        """Initialise Subscribers collection"""
        # Dictionary holding subscriber_id and attributes
        # e.g. : Subscriber = {'testsubscriber': {'foo':'bar'}}
        self._subscribers = {}

    def get_keys(self):
        """Returns subscribers ids"""
        return self._subscribers.keys()

    def add_subscriber(self, subscriber):
        """Adds subscriber to the subscribers dict"""
        self._subscribers.update(subscriber)

    def check_presence(self, sub_id):
        """Check if sub_id exist in the list"""
        if sub_id in self._subscribers.keys():
            return True
        else:
            return False

    def remove_subscriber(self, sub_id):
        """Remove subscriber from the list"""
        subscriber_attr = None
        if sub_id in self._subscribers:
            subscriber_attr = self._subscribers.pop(sub_id)
        else:
            # Subscriber with sub_id not found.
            subscriber_attr = None
        return subscriber_attr
