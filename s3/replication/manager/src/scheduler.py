#!/usr/bin/env python3

# scheduler server - replicator manager
#
# This file contains scheduler sever
# which exposes various REST endpoints
import sys
import json
from aiohttp import web
from urllib.parse import urlparse, parse_qs
import logging
sys.path.append("../../common")
from log import setup_logging

LOG = logging.getLogger('multisite')

logging.basicConfig(filename="scheduler.log",
            format='%(asctime)s [%(levelname)s] [%(filename)s: %(lineno)d] %(message)s', filemode='w')

# Dictionary holding job_id and fdmi record
#  e.g. jobs = {'jobA': {'K1': 'V1'}}
jobs = {}

# List of active subscriber
subscribers = []

# List of jobs in progress
jobs_inprogress = []

# Route table declaration
routes = web.RouteTableDef()

@routes.get('/jobs')
async def list_jobs(request):
    """
    list_jobs Get in-progress jobs

    Handler api to handle multiple query
    """
    url = request.path_qs
    url_ob = urlparse(url)
    query = parse_qs(url_ob.query)
    # Return in progress jobs
    if 'inProgress' in query:
        LOG.debug('InProgress jobs : {}'.format(query['inProgress']))
        return web.Response(text='InProgress jobs: {}'.format(jobs_inprogress))
    # Return job counts
    elif 'count' in query:
        return web.Response(text='Job List : {}'.format(jobs.keys()))
    # Return prefetch count
    elif 'prefetch' in query:
        req_list1 = query['prefetch']
        pf_cnt = req_list1[0]
        req_list2 = query['subscriber_id']
        sub_id = req_list2[0]
        LOG.debug(pf_cnt)
        LOG.debug("sub_id is : {}".format(sub_id))
        if sub_id in subscribers:
            if int(pf_cnt) <= len(jobs):
                return web.Response(text='{}'.format(pf_cnt))
            else:
                return web.Response(text='{}'.format(len(jobs)))
        else:
            return web.Response(text='INVALID subscriber')

    else:
        return web.Response(text='List of jobs : {}'.format(jobs.keys()))

@routes.get('/jobs/{job_id}')
async def get_job_attr(request):
    """
    get_job_attr Get in progress jobs

    Handler api to fetch job attributes
    """
    ID = (request.match_info['job_id'])
    if ID in jobs.keys():
        return web.json_response(jobs[ID])
        #return web.Response(text='attributes are : {}'.format(jobs['job_id']))
    else:
        return web.Response(text='ERROR : Job is not present!')

@routes.post('/jobs')
async def add_jobs(request):
    """
    add_jobs add jobs

    Handler to add jobs to the job queue
    """
    entries = await request.json()
    LOG.debug(entries)
    jobs.update(entries)
    LOG.debug('Job list : {}'.format(jobs))

@routes.post('/subscribers')
async def add_subscriber(request):
    """
    add_subscriber add subscriber

    Handler for Subscriber
    """
    sub_id = await request.json()
    LOG.debug('subscriber is : {}'.format(sub_id))
    if sub_id in subscribers:
        return web.Response(text='Replicator is Already subscribed!')
    else:
        subscribers.append(sub_id)
        LOG.debug(subscribers)
        return web.Response(text='Replicator added! : {}'.format(subscribers))

@routes.get('/subscribers')
async def list_subscribers(request):
    """
    list_subscribers List subscriber

    Handler to list subscribers
    """
    return web.Response(text='subscribers are : {} '.format(subscribers))

@routes.put('/jobs/{job_id}')
async def update_job_attr(request):
    """
    update_job_attr update job attributes

    Update attributes for job_id
    """
    val = await request.json()  # ToDo
    ID = (request.match_info['job_id'])
    LOG.debug('ID is {}'.format(ID))
    if ID in jobs.keys():
        jobs[ID] = val
        return web.Response(text='{} attributs are: {}'.format(ID, jobs[ID]))
    else:
        jobs.update({ID: val})
        jobs_inprogress.append(ID)
        return web.Response(text='updated list is {}!'.format(jobs))

if __name__ == '__main__':

    #setup logging
    setup_logging()

    app = web.Application()
    app.add_routes(routes)
    web.run_app(app)
