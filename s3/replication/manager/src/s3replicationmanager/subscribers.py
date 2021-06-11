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
import uuid


class Subscriber:
    def __init__(self, sub_obj):
        """Initialise Subscriber object."""
        self.id = str(uuid.uuid4())
        self.endpoint = sub_obj["endpoint"]
        self.prefetch_count = sub_obj["prefetch_count"]
        self._jobs_sent_count = 0

    def get_dictionary(self):
        return {
            "id": self.id,
            "endpoint": self.endpoint,
            "prefetch_count": self.prefetch_count

        }

    def pending_capacity(self):
        """Returns count of jobs that can be sent to subscriber."""
        return self._prefetch_count - self._jobs_sent_count

    def jobs_sent(self, count):
        """Remember jobs sent to subscriber.

        Args:
            count (int): Number of jobs sent to subscriber.

        Returns:
            int: -1 on failure if subscriber does not have enough capacity
                 defined by prefetch_count, 0 on success
        """
        if count > self.pending_capacity():
            # Cannot send more than subscriber can handle.
            return -1
        else:
            self._jobs_sent_count += count

    def job_acknowledged(self, count):
        """Update (reduce) the jobs sent to subscriber.

        Args:
            count (int): Number of jobs acknowledged by subscriber.

        Returns:
            int: -1 on failure - cannot acknowledged more than we have sent,
                 0 on success
        """
        if count > self._jobs_sent_count:
            # Logical error, cannot acknowledged more than we have sent.
            return -1
        else:
            self._jobs_sent_count -= count
            return 0


class SubscriberJsonEncoder(json.JSONEncoder):
    def default(self, o):  # pylint: disable=E0202
        if isinstance(o, Subscriber):
            return o.get_dictionary()
        return super().default(o)


class Subscribers:
    @staticmethod
    def dumps(obj):
        """Helper to format json."""
        return json.dumps(obj._subscribers, cls=SubscriberJsonEncoder)

    def __init__(self):
        """Initialise Subscribers collection."""
        # Dictionary holding subscriber_id and attributes
        # E.g. : subscriber = {'id':'some-uuid','foo':'bar'}
        # _subscribers = {some-uuid': Subscriber(subscriber), ...}
        self._subscribers = {}

    def count(self):
        """
        Returns total subscribers in collection.

        Returns:
            int: Count of subscribers in collection.
        """
        return len(self._subscribers)

    def add_subscriber(self, subscriber):
        """Adds subscriber to the subscribers dict."""
        subscriber = Subscriber(subscriber)
        self._subscribers[subscriber.id] = subscriber
        return subscriber

    def is_subscriber_present(self, subscriber_id):
        """Check if subscriber_id exist in the list."""
        if subscriber_id in self._subscribers.keys():
            return True
        else:
            return False

    def remove_subscriber(self, subscriber_id):
        """Remove subscriber from the list."""
        subscriber = None
        if subscriber_id in self._subscribers:
            subscriber = self._subscribers.pop(subscriber_id, None)
        else:
            # Subscriber with subscriber_id not found.
            subscriber = None
        return subscriber
