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
from urllib.parse import urlparse, parse_qs
from .config import Config
from s3replicationcommon.log import setup_logging

LOG = setup_logging('manager_proc')

# Dictionary holding job_id and fdmi record
#  e.g. jobs = {'jobA': {'K1': 'V1'}}
jobs = {}

# List of active subscriber
subscribers = []

# List of jobs in progress
jobs_inprogress = {}

# Route table declaration
routes = web.RouteTableDef()

@routes.post('/subscribers')  # noqa: E302
async def add_subscriber(request):
    """Add subscriber

    Handler for Subscriber

    """
    subscriber = await request.json()
    LOG.debug('subscriber is : {}'.format(subscriber.get('sub_id')))
    sub_id = subscriber.get('sub_id')

    # Check if subscriber is already present
    if sub_id in subscribers:
        return web.json_response({'Response': 'Replicator is Already subscribed!'})
    else:
        subscribers.append(subscriber.get('sub_id'))
        LOG.debug(subscribers)
        return web.json_response({'Response': 'subscriber added!'})

@routes.get('/subscribers')  # noqa: E302
async def list_subscribers(request):
    """List subscriber

    Handler to get subscriber list

    """
    return web.json_response({'subscribers': subscribers})

@routes.post('/jobs')  # noqa: E302
async def add_job(request):
    """Add jobs

    Handler to add jobs to the job queue

    """
    job_record = await request.json()
    # Add job to the list
    jobs.update(job_record)
    LOG.debug('Job count : {}'.format(len(jobs)))
    return web.json_response({'Response': 'job added!'})

@routes.get('/jobs/{job_id}')  # noqa: E302
async def get_job(request):
    """Get job attribute

    Handler api to fetch job attributes

    """
    id = request.match_info['job_id']

    # Get job's attribute
    if id in jobs.keys():
        return web.json_response({id: jobs[id]})
    else:
        return web.json_response({'ErrorResponse': 'Job is not present!'})

@routes.get('/jobs')  # noqa: E302
async def list_jobs(request):
    """List active jobs

    Handler api to handle multiple query

    """
    global jobs
    url = request.path_qs
    url_ob = urlparse(url)
    query = parse_qs(url_ob.query)

    # Return in progress jobs
    if 'inprogress' in query:
        LOG.debug('InProgress query param: {}'.format(query['inprogress']))
        return web.json_response({'inprogress': list(jobs_inprogress.keys())})
    # Return total job counts
    elif 'count' in query:
        return web.json_response({'count': len(jobs)+len(jobs_inprogress)})
    # Return requested jobs
    elif 'prefetch' in query:
        prefetch_count = int(query['prefetch'][0])
        sub_id = query['subscriber_id'][0]
        LOG.debug('sub_id is : {}'.format(sub_id))
        LOG.debug('subscribers are : {}'.format(subscribers))

        # Validate subscriber and server request
        if sub_id in subscribers:
            # Remove prefetch_count entries from jobs and add to inprogress
            if prefetch_count < len(jobs):
                add_inprogress = dict(list(jobs.items())[:prefetch_count])
                jobs=dict(list(jobs.items())[prefetch_count:])
                jobs_inprogress.update(add_inprogress)
            # Add all jobs to inprogress
            else:
                jobs_inprogress.update(jobs)
                jobs.clear()
            LOG.debug('jobs in progress : {}'.format(jobs_inprogress))
            return web.json_response({'Response': list(jobs_inprogress.keys())})
        # Subscriber is not in the list
        else:

            return web.json_response({'ErrorResponse': 'Invalid subscriber'})
    else:
        return web.json_response({'Response': list(jobs.keys())})

@routes.put('/jobs/{job_id}')  # noqa: E302
async def update_job_attr(request):
    """Update job attributes

    Update attributes for job_id

    """
    val = await request.json()
    id = (request.match_info['job_id'])
    LOG.debug('id is {}'.format(id))

    # Check and update if job_id is present
    if id in jobs.keys():
        jobs[id] = val
        return web.json_response({'Response': 'Requested job updated'})
    else:
        return web.json_response({'ErrorResponse': 'Job is not present'})

class ReplicationManagerApp:
    def __init__(self, configfile):
        """Initialise logger and configuration."""

        self.config = Config(configfile)

        LOG.debug('HOST is : {}'.format(self.config.host))
        LOG.debug('PORT is : {}'.format(self.config.port))

    def run(self):
        app = web.Application()
        app.add_routes(routes)
        web.run_app(app, host=self.config.host, port=self.config.port)
