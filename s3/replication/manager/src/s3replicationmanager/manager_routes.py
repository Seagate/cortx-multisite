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
import logging
# from s3replicationcommon.jobs import Jobs
from s3replicationcommon.job import JobJsonEncoder
# from .subscribers import Subscribers
import json


LOG = logging.getLogger('manager')

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
    if request.app['subscribers'].check_presence(sub_id):
        return web.json_response(
            {'Response': 'Replicator is Already subscribed!'})
    else:
        request.app['subscribers'].add_subscriber(sub_id)
        LOG.debug(request.app['subscribers'].get_subscribers())
        return web.json_response({'Response': 'subscriber added!'})


@routes.get('/subscribers')  # noqa: E302
async def list_subscribers(request):
    """List subscriber

    Handler to get subscriber list

    """
    return web.json_response(
        {'subscribers': request.app['subscribers'].get_subscribers()})


@routes.delete('/subscribers/{sub_id}')  # noqa: E302
async def remove_subscriber(request):
    """Add subscriber

    Handler for Subscriber

    """
    sub_id = (request.match_info['sub_id'])
    # Check if subscriber is already present
    if request.app['subscribers'].check_presence(sub_id):
        request.app['subscribers'].remove_subscriber(sub_id)
        return web.json_response(
            {'Response': 'subscriber removed!'})
    else:
        return web.json_response({'ErrorResponse': 'subscriber not present!'})


@routes.post('/jobs')  # noqa: E302
async def add_job(request):
    """Add jobs

    Handler to add jobs to the job queue

    """
    job_record = await request.json()

    # Get first key and find if already present
    job_id = next(iter(job_record))
    job = request.app['all_jobs'].get_job(job_id)

    if job is not None:
        return web.json_response(
            {'ErrorResponse': 'job already present'}, status=201)
    else:
        job = request.app['all_jobs'].add_job_using_json(job_record)
        LOG.debug('Added Job with job_id : {} '.format(job.get_job_id()))
        LOG.debug(
            'Added Job : {} '.format(
                json.dumps(
                    job,
                    cls=JobJsonEncoder)))
        return web.json_response({'job': job.get_dict()}, status=201)


@routes.get('/jobs/{job_id}')  # noqa: E302
async def get_job(request):
    """Get job attribute

    Handler api to fetch job attributes

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


@routes.put('/jobs/{job_id}')  # noqa: E302
async def update_job_attr(request):
    """Update job attributes

    Update attributes for job_id

    """
    job_record = await request.json()

    # Get key
    job_id = next(iter(job_record))
    job = request.app['all_jobs'].get_job(job_id)

    if job is None:
        return web.json_response(
            {'ErrorResponse': 'job is not present'}, status=404)
    else:
        request.app['all_jobs']._jobs[job.get_job_id()] = job_record
        LOG.debug('Updated Job with job_id : {} '.format(job.get_job_id()))
        LOG.debug(
            'Update Job : {} '.format(
                json.dumps(
                    job,
                    cls=JobJsonEncoder)))


@routes.get('/jobs')  # noqa: E302
async def list_jobs(request):
    """List active jobs

    Handler api to handle multiple query

    """
    url = request.path_qs
    url_ob = urlparse(url)
    query = parse_qs(url_ob.query)

    progressing_jobs_obj = request.app['jobs_in_progress']
    all_jobs_obj = request.app['all_jobs']

    all_jobs = request.app['all_jobs'].get_all_jobs()
    progressing_jobs = request.app['jobs_in_progress'].get_all_jobs()

    LOG.debug('progressing jobs are : {}'.format(list(progressing_jobs)))
    LOG.debug('all jobs are : {}'.format(list(all_jobs)))
    # Return in progress jobs
    if 'inprogress' in query:
        LOG.debug('InProgress query param: {}'.format(query['inprogress']))
        return web.json_response(
            {'inprogress jobs': list(progressing_jobs.keys())})

    # Return total job counts
    elif 'count' in query:
        return web.json_response(
            {'count': progressing_jobs_obj.count() + all_jobs_obj.count()})

    # Return requested jobs
    elif 'prefetch' in query:
        prefetch_count = int(query['prefetch'][0])
        sub_id = query['subscriber_id'][0]
        LOG.debug('sub_id is : {}'.format(sub_id))

        # Validate subscriber and server request
        if request.app['subscribers'].check_presence(sub_id):

            # Remove prefetch_count entries from jobs and add to inprogress
            if prefetch_count < all_jobs_obj.count():
                add_inprogress = dict(list(all_jobs.items())[:prefetch_count])
                all_jobs = dict(list(all_jobs.items())[prefetch_count:])
                progressing_jobs.update(add_inprogress)
            # Add all jobs to inprogress
            else:
                progressing_jobs.update(all_jobs)
                all_jobs.clear()

            LOG.debug('jobs in progress : {}'.format(list(progressing_jobs)))
            return web.json_response(
                {'Response': list(progressing_jobs.keys())})

        # Subscriber is not in the list
        else:
            return web.json_response({'ErrorResponse': 'Invalid subscriber'})
    else:
        return web.json_response({'Response': list(all_jobs.keys())})
