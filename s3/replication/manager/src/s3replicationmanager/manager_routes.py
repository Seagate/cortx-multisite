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
from s3replicationcommon.job import JobJsonEncoder
import json


LOG = logging.getLogger('manager')

# Route table declaration
routes = web.RouteTableDef()


@routes.post('/subscribers')  # noqa: E302
async def add_subscriber(request):
    """Add subscriber

    Handler for Subscriber
    """
    # Get subscriber
    subscriber = await request.json()
    LOG.debug('subscriber args are  : {}'.format(subscriber))

    # Get subscriber id
    sub_id = next(iter(subscriber))
    subscriber_obj = request.app['subscribers']

    # Check if subscriber is already present
    if subscriber_obj.check_presence(sub_id):
        return web.json_response(
            {'Response': 'Replicator is Already subscribed!'})
    else:
        subscriber_obj.add_subscriber(subscriber)
        LOG.debug(subscriber_obj.get_keys())
        return web.json_response({'Response': 'subscriber added!'})


@routes.get('/subscribers')  # noqa: E302
async def list_subscribers(request):
    """List subscriber

    Handler to get subscriber list

    """
    return web.json_response(
        {'subscribers': str(request.app['subscribers'].get_keys())},
        status=200)


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

    # LOG.debug(
    #        'progressing jobs : {}'.format(list(progressing_jobs_obj.keys())))
    # LOG.debug('all jobs : {}'.format(list(all_jobs_obj.keys())))

    # Return in progress jobs
    if 'inprogress' in query:
        LOG.debug('InProgress query param: {}'.format(query['inprogress']))
        return web.json_response(
            {'inprogress jobs': str(progressing_jobs_obj.get_keys())})

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
                add_inprogress = dict(
                    list(
                        all_jobs_obj.get_all_jobs())[
                        :prefetch_count])
                trimmed_all_jobs = dict(
                    list(
                        all_jobs_obj.get_all_jobs())[
                        prefetch_count:])
                progressing_jobs_obj.update_jobs(add_inprogress)
                all_jobs_obj.update_jobs(trimmed_all_jobs)
            # Add all jobs to inprogress
            else:
                all_jobs = dict(list(all_jobs_obj.get_all_jobs()))
                progressing_jobs_obj.update_jobs(all_jobs)
                all_jobs_obj.clear_jobs()

            LOG.debug('jobs in progress : {}'.format(
                list(progressing_jobs_obj.get_keys())))
            return web.json_response(
                {'Response': str(progressing_jobs_obj.get_keys())})

        # Subscriber is not in the list
        else:
            return web.json_response({'ErrorResponse': 'Invalid subscriber'})
    else:
        return web.json_response({'Response': str(all_jobs_obj.get_keys())})
