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
from .config import Config
from s3replicationcommon.log import setup_logging

# Setup log
LOG = setup_logging('replicator_proc')

# Dictionary holding job_id and fdmi record
# e.g. : jobs = {"job1": {"obj_name": "foo"}}
jobs = {}

# List of active subscriber
schedulers = []

# List of jobs in progress
jobs_inprogress = []

# Route table declaration
routes = web.RouteTableDef()

@routes.get('/jobs')  # noqa: E302
async def list_jobs(request):
    """List_jobs

    Handler to list in-progress jobs

    """
    LOG.debug('Number of jobs in progress {}'.format(len(jobs_inprogress)))
    return web.json_response({'jobs': jobs_inprogress})

@routes.get('/jobs/{job_id}')  # noqa: E302
async def get_job(request):
    """Get job attribute

    Handler to get job attributes for given job_id

    """
    id = request.match_info['job_id']
    LOG.debug('id is : {} '.format(id))
    if id in jobs.keys():
        return web.json_response({id: jobs[id]})
    else:
        return web.json_response({'ErrorResponse': 'Job is not present!'})

@routes.put('/jobs')  # noqa: E302
async def add_job(request):
    """Add job in the queue

    Handler to add jobs to the queue

    """
    job_record = await request.json()
    LOG.debug(job_record)
    jobs.update(job_record)
    return web.json_response({'Response': 'Job updated!'})

@routes.post('/jobs/{job_id}')  # noqa: E302
async def abort_job(request):
    """Abort a job

    Handler to abort a job with given job_id

    """
    id = (request.match_info['job_id'])
    LOG.debug('id is {}'.format(id))
    if id in jobs.keys():
        try:
            jobs_inprogress.remove(id)
        except id is not None:
            return web.json_response({'ErrorResponse': 'Job is not present!'})
        del jobs[id]
        return web.json_response({'Response': 'Job Aborted'})
    else:
        return web.json_response({'ErrorResponse': 'Job is not present!'})


class ReplicatorApp:
    def __init__(self, configfile):
        """Initialise logger and configuration"""

        self.config = Config(configfile)

        LOG.debug('HOST is : {}'.format(self.config.host))
        LOG.debug('PORT is : {}'.format(self.config.port))

    def run(self):
        """Start replicator"""
        app = web.Application()
        app.add_routes(routes)
        web.run_app(app, host=self.config.host, port=self.config.port)
