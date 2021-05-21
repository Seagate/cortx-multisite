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
from s3replicationcommon.jobs import Jobs
from s3replicationcommon.job import JobJsonEncoder
import json

LOG = logging.getLogger('s3replicator')

# Route table declaration
routes = web.RouteTableDef()


@routes.get('/jobs')  # noqa: E302
async def list_jobs(request):
    """List_jobs
    Handler to list in-progress jobs
    """
    jobs = request.app['all_jobs']

    LOG.debug('Number of jobs in-progress {}'.format(jobs.count()))
    return web.json_response(jobs, dumps=Jobs.dumps, status=200)


@routes.get('/jobs/{job_id}')  # noqa: E302
async def get_job(request):
    """Get job attribute
    Handler to get job attributes for given job_id
    """
    job_id = request.match_info['job_id']
    job = request.app['all_jobs'].get_job(job_id)

    if job is not None:
        LOG.debug('Job found with job_id : {} '.format(job_id))
        return web.json_response({"job": job.get_dict()}, status=200)
    else:
        LOG.debug('Job missing with job_id : {} '.format(job_id))
        return web.json_response(
            {'ErrorResponse': 'Job Not Found!'}, status=404)


@routes.post('/jobs')  # noqa: E302
async def add_job(request):
    """Add job in the queue
    Handler to add jobs to the queue
    """
    job_record = await request.json()
    # XXX deduplicate?
    job = request.app['all_jobs'].add_job_using_json(job_record)
    LOG.debug('Added Job with job_id : {} '.format(job.get_job_id()))
    LOG.debug('Added Job : {} '.format(json.dumps(job, cls=JobJsonEncoder)))
    return web.json_response({'job': job.get_dict()}, status=201)


@routes.delete('/jobs/{job_id}')  # noqa: E302
async def abort_job(request):
    """Abort a job
    Handler to abort a job with given job_id
    """
    job_id = request.match_info['job_id']
    LOG.debug('Aborting Job with job_id {}'.format(job_id))
    # XXX Perform real abort...
    job = request.app['all_jobs'].remove_job(job_id)
    if job is not None:
        LOG.debug('Aborted Job with job_id {}'.format(job_id))
        return web.json_response({'job_id': job_id}, status=204)
    else:
        LOG.debug('Missing Job with job_id {}'.format(job_id))
        return web.json_response(
            {'ErrorResponse': 'Job Not Found!'}, status=404)
