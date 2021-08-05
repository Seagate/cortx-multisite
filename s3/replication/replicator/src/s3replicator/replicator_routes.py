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

import asyncio
from aiohttp import web
import json
import logging
from urllib.parse import urlparse, parse_qs
from s3replicationcommon.jobs import Job
from s3replicationcommon.jobs import Jobs
from s3replicationcommon.job import JobJsonEncoder
from .transfer_initiator import TransferInitiator

_logger = logging.getLogger('s3replicator')

# Route table declaration
routes = web.RouteTableDef()


@routes.get('/jobs')  # noqa: E302
async def list_jobs(request):
    """List all in-progress jobs."""
    url = request.path_qs
    url_ob = urlparse(url)
    query = parse_qs(url_ob.query, keep_blank_values=True)
    _logger.debug('API: GET /jobs\n Query: {}'.format(query))

    jobs = request.app['all_jobs']
    completed_jobs = request.app['completed_jobs']

    if 'count' in query:
        if 'inprogress' in query:
            return web.json_response({'inprogress-count':
                                      jobs.inprogress_count()}, status=200)
        elif 'completed' in query:
            return web.json_response({'completed-count':
                                      completed_jobs.count()}, status=200)
        else:
            return web.json_response({'count': jobs.count()}, status=200)
    elif 'completed' in query:
        _logger.debug('Completed jobs count {}'.format(completed_jobs.count()))
        return web.json_response(completed_jobs, dumps=Jobs.dumps, status=200)
    else:
        _logger.debug('Total replication jobs count {}'.format(jobs.count()))
        return web.json_response(jobs, dumps=Jobs.dumps, status=200)


@routes.get('/jobs/{job_id}')  # noqa: E302
async def get_job(request):
    """Get job details for given job_id."""
    job_id = request.match_info['job_id']
    _logger.debug('API: GET /jobs/{}'.format(job_id))

    job = request.app['all_jobs'].get_job_by_job_id(job_id)
    if job is None:
        # Check if its in completed cache.
        job = request.app['completed_jobs'].get_job_by_job_id(job_id)

    if job is not None:
        _logger.debug('Job found with job_id : {} '.format(job_id))
        return web.json_response({"job": job.get_dict()}, status=200)
    else:
        _logger.debug('Job missing with job_id : {} '.format(job_id))
        return web.json_response(
            {'ErrorResponse': 'Job Not Found!'}, status=404)


@routes.post('/jobs')  # noqa: E302
async def add_job(request):
    """Add job in the queue and trigger replication."""
    job_records = await request.json()
    _logger.debug('API: POST /jobs\nContent : {}'.format(job_records))

    jobs_list = request.app['all_jobs']

    # Accepted_jobs response format [{"replication-id": "job-id"}, ...].
    accepted_jobs = []

    # Discarded jobs with additional info as possible.
    # Format [{msg: "Job already exists.", record = {post in request}}, ...]
    discarded_jobs = []

    for record in job_records:
        _logger.debug('Processing record: {} '.format(record))
        job = Job(record)

        # Check if job already present.
        if job.is_valid() is False:
            discarded_jobs.append({
                "message": "Invalid job record.",
                "record": record
            })
            _logger.warn('Invalid job record: {} '.format(record))
        elif jobs_list.is_job_present(job.get_replication_id()):
            discarded_jobs.append({
                "message": "Job Already exists for replication-id {}.".
                format(job.get_replication_id()),
                "record": record
            })
            _logger.warn('Job Already exists: {} '.format(record))
        else:
            jobs_list.add_job(job)

            # Start the async replication.
            _logger.debug('Starting Replication Job : {} '.format(
                json.dumps(job, cls=JobJsonEncoder)))
            # XXX create task is only supported for python v3.7+
            asyncio.ensure_future(
                TransferInitiator.start(
                    job, request.app))

            jobs_list.move_to_inprogress(job.get_replication_id())

            # Populate the response.
            accepted_jobs.append({
                job.get_replication_id(): job.get_job_id()
            })

            _logger.info('Started Replication Job with job_id : {} '.format(
                job.get_job_id()))
            _logger.debug('Started Replication Job : {} '.format(
                json.dumps(job, cls=JobJsonEncoder)))

    # end of for each record.

    response_status = None
    if len(accepted_jobs) > 0:
        # Atleast one job accepted.
        response_status = 201  # Created.
    else:
        response_status = 400  # Bad Request.

    return web.json_response(
        {"accepted_jobs": accepted_jobs, "discarded_jobs": discarded_jobs},
        status=response_status)


@routes.delete('/jobs/{job_id}')  # noqa: E302
async def abort_job(request):
    """Abort a job with given job_id."""
    job_id = request.match_info['job_id']
    _logger.debug('API: DELETE /jobs/{}'.format(job_id))

    _logger.debug('Aborting Job with job_id {}'.format(job_id))
    # XXX Perform real abort...
    job = request.app['all_jobs'].remove_job_by_job_id(job_id)
    if job is not None:
        # Perform the abort
        job.abort()
        if request.app["config"].job_cache_enabled:
            # cache it, so status can be queried.
            request.app['completed_jobs'].add_job(job)
        _logger.debug('Aborted Job with job_id {}'.format(job_id))
        return web.json_response({'job_id': job_id}, status=204)
    else:
        _logger.debug('Missing Job with job_id {}'.format(job_id))
        return web.json_response(
            {'ErrorResponse': 'Job Not Found!'}, status=404)
