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

# import sys
# import argparse
# import json
from aiohttp import web
import logging
from urllib.parse import urlparse, parse_qs
from config import Config
from s3replicationcommon.log import setup_logging

LOG = logging.getlogger('manager_proc')

HOST = '127.0.0.1'
PORT = 8080

# Dictionary holding job_id and fdmi record
#  e.g. jobs = {'jobA': {'K1': 'V1'}}
jobs = {}

# List of active subscriber
subscribers = []

# List of jobs in progress
jobs_inprogress = {}

# Route table declaration
routes = web.RouteTableDef()

@routes.get('/jobs')
async def list_jobs(request):
    """List active jobs

    Handler api to handle multiple query

    """
    url = request.path_qs
    url_ob = urlparse(url)
    query = parse_qs(url_ob.query)

    # Return in progress jobs
    if 'inProgress' in query:
        LOG.debug('InProgress query param: {}'.format(query['inProgress']))
        return web.json_response({'inProgress': jobs_inprogress})
    # Return job counts
    elif 'count' in query:
        return web.json_response({'Number of jobs present': len(jobs)})
    # Return requested jobs
    elif 'prefetch' in query:
        req_list1 = query['prefetch']
        pf_cnt = req_list1[0]
        req_list2 = query['subscriber_id']
        sub_id = req_list2[0]
        LOG.debug("sub_id is : {}".format(sub_id))
        LOG.debug("subscribers are : {}".format(subscribers))

        if sub_id in subscribers:
            LOG.debug(" jobs' keys : {}".format(list(jobs.keys())))
            LOG.debug(" jobs in progress : {}".format(jobs_inprogress))
            unscheduled_jobs = list(set(jobs.keys()) - set(jobs_inprogress))
            LOG.debug("Unscheduled keys : {}".format(unscheduled_jobs))
            if int(pf_cnt) <= len(jobs):
                response = unscheduled_jobs[:int(pf_cnt)]
                LOG.debug('would be response : {}'.format(response))
                jobs_inprogress.extend(unscheduled_jobs[:int(pf_cnt)])
            else:
                response = unscheduled_jobs[:len(jobs)]
                jobs_inprogress.extend(unscheduled_jobs[:len(jobs)])
                LOG.debug('would be response : {}'.format(response))
            return web.json_response({'Response': response})
        else:
            return web.json_response({'Response': 'INVALID subscriber'})

    else:
        return web.json_response({'jobs': list(jobs.keys())})

@routes.get('/jobs/{job_id}')
async def get_job(request):
    """Get job attribute

    Handler api to fetch job attributes

    """
    id = request.match_info['job_id']

    # Get job's attribute
    if id in jobs.keys():
        return web.json_response(jobs[id])
    else:
        return web.json_response({'Response': 'ERROR : Job is not present!'})

@routes.post('/jobs')
async def add_job(request):
    """Add jobs

    Handler to add jobs to the job queue

    """
    entries = await request.json()
    # Add job to the list
    jobs.update(entries)
    LOG.debug('Job list : {}'.format(jobs))
    return web.json_response({'Response': 'jobs added!'})

@routes.post('/subscribers')
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
        return web.json_response({'subscribers': subscribers})

@routes.get('/subscribers')
async def list_subscribers(request):
    """List subscriber

    Handler to get subscriber list

    """
    return web.json_response({'subscribers': subscribers})

@routes.put('/jobs/{job_id}')
async def update_job_attr(request):
    """Update job attributes

    Update attributes for job_id

    """
    val = await request.json()
    id = (request.match_info['job_id'])
    LOG.debug('id is {}'.format(id))

    # Check if key is present
    if id in jobs.keys():
        jobs[id] = val
        return web.json_response({id: jobs[id]})
    else:
        jobs.update({id: val})
        # jobs_inprogress.append(id)
        return web.json_response({'jobs': jobs})

class ReplicationManagerApp:
    def __init__(self, configfile='/root/config.yaml'):  # TODO
        """Initialise logger and configuration."""

        confReplicator = Config(configfile)

        HOST = confReplicator.host
        PORT = confReplicator.port

        # setup logging
        setup_logging()

        LOG.debug("HOST is : {}".format(HOST))
        LOG.debug("PORT is : {}".format(PORT))

    def run(self):
        app = web.Application()
        app.add_routes(routes)
        web.run_app(app, host=HOST, port=PORT)
