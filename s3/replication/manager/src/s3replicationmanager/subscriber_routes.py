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

from aiohttp import web
import logging
from .subscribers import Subscribers

_logger = logging.getLogger('s3replicationmanager')

# Route table declaration
routes = web.RouteTableDef()


@routes.post('/subscribers')  # noqa: E302
async def add_subscriber(request):
    """Handler to add subscriber."""
    # Get subscriber details from payload
    subscriber = await request.json()
    _logger.debug('API: POST /subscribers\nContent : {}'.format(subscriber))

    subscribers_list = request.app['subscribers']

    # Check if subscriber is already present
    subscriber_obj = subscribers_list.add_subscriber(subscriber)
    _logger.debug('Subscriber added  : {}'.format(
        subscriber_obj.get_dictionary()))

    return web.json_response(subscriber_obj.get_dictionary(),
                             status=201)


@routes.get('/subscribers')  # noqa: E302
async def list_subscribers(request):
    """Handler to list subscribers."""
    _logger.debug('API: GET /subscribers')
    subscribers = request.app['subscribers']

    _logger.debug('Number of subscribers {}'.format(subscribers.count()))
    return web.json_response(subscribers, dumps=Subscribers.dumps, status=200)
    # return web.json_response(subscribers, status=200)


@routes.get('/subscribers/{subscriber_id}')  # noqa: E302
async def get_subscriber(request):
    """Handler to get subscriber attributes."""
    subscriber_id = request.match_info['subscriber_id']
    _logger.debug('API: GET /subscribers/{}'.format(subscriber_id))

    subscribers = request.app['subscribers']

    subscriber = subscribers.get_subscriber(subscriber_id)

    if subscriber is not None:
        _logger.debug('Subscriber found with subscriber_id : {} '.
                      format(subscriber_id))
        _logger.debug('Subscriber details : {} '.format(
            subscriber.get_dictionary()))
        return web.json_response(subscriber.get_dictionary(), status=200)
    else:
        _logger.debug('Subscriber missing with subscriber_id : {} '.
                      format(subscriber_id))
        return web.json_response(
            {'ErrorResponse': 'Subscriber Not Found!'}, status=404)


@routes.delete('/subscribers/{subscriber_id}')  # noqa: E302
async def remove_subscriber(request):
    """Handler to remove subscriber."""
    subscribers = request.app['subscribers']

    subscriber_id = (request.match_info['subscriber_id'])
    _logger.debug('API: DELETE /subscribers/{}'.format(subscriber_id))

    # Check if subscriber is already present
    if subscribers.is_subscriber_present(subscriber_id):
        subscriber = subscribers.remove_subscriber(subscriber_id)
        _logger.debug('Subscriber removed  : {}'.format(
            subscriber.get_dictionary()))
        return web.json_response({'subscriber_id': subscriber_id}, status=204)
    else:
        return web.json_response(
            {'ErrorResponse': 'Subscriber Not Found!'}, status=404)
