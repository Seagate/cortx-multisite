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
from .prepare_job import PrepareReplicationJob
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


@routes.get('/subscribers/{subscriber_id}')  # noqa: E302
async def get_subscriber(request):
    """Handler to get job attributes."""
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


@routes.post('/jobs')  # noqa: E302
async def add_job(request):
    """Handler to add job to job queue."""
    fdmi_job = await request.json()
    _logger.debug('API: POST /jobs\nContent : {}'.format(fdmi_job))

    job_record = PrepareReplicationJob.from_fdmi(fdmi_job)

    job = request.app['all_jobs'].add_job_using_json(job_record)
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

    job = request.app['all_jobs'].get_job(job_id)

    if job is None:
        return web.json_response(
            {'ErrorResponse': 'job is not present'}, status=404)
    else:
        request.app['all_jobs']._jobs[job.get_job_id()] = job_record
        _logger.debug('Updated Job with job_id : {} '.format(job.get_job_id()))
        _logger.debug(
            'Update Job : {} '.format(
                json.dumps(
                    job,
                    cls=JobJsonEncoder)))


@routes.get('/jobs')  # noqa: E302
async def list_jobs(request):
    """List active jobs."""
    url = request.path_qs
    url_ob = urlparse(url)
    query = parse_qs(url_ob.query)

    _logger.debug('API: GET /jobs\n Query: {}'.format(query))

    progressing_jobs_obj = request.app['jobs_in_progress']
    all_jobs_obj = request.app['all_jobs']

    # Return in progress jobs
    if 'inprogress' in query:
        _logger.debug('InProgress query param: {}'.format(query['inprogress']))
        return web.json_response(
            {'inprogress jobs': json.dumps(
                list(progressing_jobs_obj.get_keys()))})

    # Return total job counts
    elif 'count' in query:
        return web.json_response(
            {'count': progressing_jobs_obj.count() + all_jobs_obj.count()})

    # Return requested jobs
    elif 'prefetch' in query:
        prefetch_count = int(query['prefetch'][0])
        sub_id = query['subscriber_id'][0]
        _logger.debug('sub_id is : {}'.format(sub_id))

        # Validate subscriber and server request
        if request.app['subscribers'].is_subscriber_present(sub_id):

            # Remove prefetch_count jobs from all_jobs and add to inprogress

            add_inprogress = all_jobs_obj.remove_jobs(prefetch_count)
            progressing_jobs_obj.add_jobs(add_inprogress)

            _logger.debug('jobs in progress : {}'.format(
                list(progressing_jobs_obj.get_keys())))
            return web.json_response(
                {'Response': json.dumps(
                    list(progressing_jobs_obj.get_keys()))})

        # Subscriber is not in the list
        else:
            return web.json_response({'ErrorResponse': 'Invalid subscriber'})
    else:
        return web.json_response(
            {'Response': json.dumps(list(all_jobs_obj.get_keys()))})


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
