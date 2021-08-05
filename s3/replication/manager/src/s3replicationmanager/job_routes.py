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
import json
from urllib.parse import urlparse, parse_qs
from s3replicationcommon.job import JobJsonEncoder
from s3replicationcommon.jobs import Jobs
from .prepare_job import PrepareReplicationJob

_logger = logging.getLogger('s3replicationmanager')

# Route table declaration
routes = web.RouteTableDef()


@routes.post('/jobs')  # noqa: E302
async def add_job(request):
    """Handler to add job to job queue."""
    fdmi_job = await request.json()
    _logger.debug('API: POST /jobs\nContent : {}'.format(fdmi_job))

    job_record = PrepareReplicationJob.from_fdmi(fdmi_job)

    if job_record is None:
        return web.json_response(
            {'ErrorResponse': 'BadRequest. Invalid Job!'}, status=400)

    jobs_list = request.app['all_jobs']
    if jobs_list.is_job_present(job_record["replication-id"]):
        # Duplicate job submitted.
        _logger.warn('Duplicate Job!')
        return web.json_response(
            {'ErrorResponse': 'Duplicate Job!'}, status=409)

    job = jobs_list.add_job_using_json(job_record)
    _logger.debug('Successfully added Job with job_id : {} '.
                  format(job.get_job_id()))
    return web.json_response(job.get_dict(), status=201)


@routes.get('/jobs/{job_id}')  # noqa: E302
async def get_job(request):
    """Handler to get job attributes."""
    job_id = request.match_info['job_id']
    _logger.debug('API: GET /jobs/{}'.format(job_id))

    job = request.app['all_jobs'].get_job_by_job_id(job_id)

    if job is not None:
        _logger.debug('Job found with job_id : {} '.format(job_id))
        _logger.debug('Job details : {} '.format(job.get_dict()))
        return web.json_response({"job": job.get_dict()}, status=200)
    else:
        _logger.debug('Job missing with job_id : {} '.format(job_id))
        return web.json_response(
            {'ErrorResponse': 'Job Not Found!'}, status=404)


@routes.put('/jobs/{job_id}')  # noqa: E302
async def update_job_attr(request):
    """Handler to Update job attributes."""
    job_record = await request.json()

    job_id = request.match_info['job_id']
    _logger.debug('API: PUT /jobs/{}'.format(job_id))

    jobs_list = request.app['all_jobs']
    job = jobs_list.get_job_by_job_id(job_id)

    if job is None:
        _logger.error('Job Not Found! job_id : {} '.format(job.get_job_id()))
        return web.json_response(
            {'ErrorResponse': 'Job Not Found!'}, status=404)
    else:
        subscriber_id = job.get_subscriber_id()
        subscriber = request.app['subscribers'].get_subscriber(subscriber_id)
        subscriber.job_acknowledged(1)

        if job_record["status"] == "completed":
            job.mark_completed()
        elif job_record["status"] == "failed":
            job.mark_failed()
        elif job_record["status"] == "aborted":
            job.mark_aborted()

        jobs_list.move_to_complete(job.get_replication_id())

        _logger.info('Updated Job with job_id : {} '.format(job.get_job_id()))
        _logger.debug(
            'Updated Job : {} '.format(json.dumps(job, cls=JobJsonEncoder)))
        return web.json_response(job.get_dict(), status=200)


@routes.get('/jobs')  # noqa: E302
async def get_jobs(request):
    """List active jobs."""
    url = request.path_qs
    url_ob = urlparse(url)
    query = parse_qs(url_ob.query, keep_blank_values=True)

    _logger.debug('API: GET /jobs\n Query: {}'.format(query))

    all_jobs_list = request.app['all_jobs']

    if 'count' in query:
        if 'queued' in query:
            # Return queued jobs count
            return web.json_response(
                {'count': all_jobs_list.queued_count()}, status=200)
        elif 'inprogress' in query:
            # Return in-progress jobs count
            return web.json_response(
                {'count': all_jobs_list.inprogress_count()}, status=200)
        elif 'completed' in query:
            # Return completed jobs count
            return web.json_response(
                {'count': all_jobs_list.completed_count()}, status=200)
        else:
            # Return total jobs count
            return web.json_response(
                {'count': all_jobs_list.count()}, status=200)

    elif 'queued' in query:
        # Return queued jobs not yet distributed.
        queued_jobs = all_jobs_list.get_queued()
        _logger.debug('Returning Jobs Queued, count = {}'.format(
            len(queued_jobs)))
        return web.json_response(
            queued_jobs, dumps=Jobs.list_dumps, status=200)

    elif 'inprogress' in query:
        # Return in progress jobs that are distributed.
        inprogress_jobs_list = all_jobs_list.get_inprogress()

        _logger.debug('Returning Jobs In-Progress, count = {}'.format(
            len(inprogress_jobs_list)))
        return web.json_response(
            inprogress_jobs_list, dumps=Jobs.list_dumps, status=200)

    elif 'completed' in query:
        # Return completed and acknowledged jobs.
        completed_jobs = all_jobs_list.get_completed()
        _logger.debug('Returning Jobs completed, count = {}'.format(
            len(completed_jobs)))
        return web.json_response(
            completed_jobs, dumps=Jobs.list_dumps, status=200)

    else:
        # return jobs that are not yet distributed.
        _logger.debug('Returning All Jobs, count = {}'.format(
            all_jobs_list.count()))
        return web.json_response(
            all_jobs_list, dumps=Jobs.dumps, status=200)


@routes.delete('/jobs/{job_id}')  # noqa: E302
async def remove_job(request):
    """Handler to get job attributes."""
    job_id = request.match_info['job_id']
    _logger.debug('API: DELETE /jobs/{}'.format(job_id))

    jobs_list = request.app['all_jobs']
    job = jobs_list.remove_job_by_job_id(job_id)

    if job is not None:
        _logger.debug('Deleted job with job_id : {} '.format(job_id))
        return web.json_response({"job_id": job_id}, status=204)
    else:
        _logger.debug('Job missing with job_id : {} '.format(job_id))
        return web.json_response(
            {'ErrorResponse': 'Job Not Found!'}, status=404)
