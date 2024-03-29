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
from aiohttp import web
import logging

_logger = logging.getLogger('s3inmem')


async def on_startup(app):
    _logger.debug("Starting S3 server...")


async def on_shutdown(app):
    _logger.debug("Performing cleanup on shutdown...")

# Route table declaration
routes = web.RouteTableDef()


# PUT Object API.
@routes.put('/{bucket_name}/{object_name}')  # noqa: E302
async def put_object(request):
    """Handler to Update job attributes."""
    bucket_name = request.match_info['bucket_name']
    object_name = request.match_info['object_name']
    print('API: PUT /{}/{}'.format(bucket_name, object_name))

    data = await request.read()

    hash_obj = hashlib.md5()
    hash_obj.update(data)
    md5 = hash_obj.hexdigest()
    headers = {
        "ETag": "\"{}\"".format(md5)
    }
    print("API: PUT /{}/{} - md5 = {}".format(bucket_name, object_name, md5))

    return web.json_response(status=200, headers=headers)


# GET Object API.
@routes.get('/{bucket_name}/{object_name}')  # noqa: E302
async def get_object(request):
    """Handler to Update job attributes."""
    bucket_name = request.match_info['bucket_name']
    object_name = request.match_info['object_name']
    print('API: GET /{}/{}'.format(bucket_name, object_name))

    object_size = int(object_name.rsplit("_sz")[1])

    data = bytearray(object_size)
    hash_obj = hashlib.md5()
    hash_obj.update(data)
    md5 = hash_obj.hexdigest()
    headers = {
        "ETag": "\"{}\"".format(md5)
    }

    return web.Response(body=data, status=200, headers=headers)


if __name__ == '__main__':
    app = web.Application()

    # Setup application routes.
    app.add_routes(routes)

    # Setup startup/shutdown handlers
    app.on_startup.append(on_startup)
    app.on_shutdown.append(on_shutdown)

    # Start the REST server.
    web.run_app(app, host="0.0.0.0", port="80")
