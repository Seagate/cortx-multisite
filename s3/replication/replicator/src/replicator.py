#!/usr/bin/env python3

# s3 replicator server
#
# Replicator script which host different end points

import sys
import json
from aiohttp import web
import logging
sys.path.append("../../common")
from log import setup_logging

logging.basicConfig(filename="replicator.log",
            format='%(asctime)s [%(levelname)s] [%(filename)s: %(lineno)d] %(message)s', filemode='w')

LOG = logging.getLogger('multisite')

# Dictionary holding job_id and fdmi record
# e.g. : jobs = {"job1": {"obj_name": "foo"}}
jobs = {}

# List of active subscriber
schedulers = []

# List of jobs in progress
jobs_inprogress = []

# Route table declaration
routes = web.RouteTableDef()

@routes.get('/jobs')
async def list_jobs(request):
    """
    list_jobs list jobs

    Handler to list in-progress jobs
    """
    LOG.debug(jobs_inprogress)
    # Returns jobs_inprogress
    return web.Response(text="In-Progress jobs : {}".format(jobs_inprogress))

@routes.get('/jobs/{job_id}')
async def get_job_attr(request):
    """
    get_job_attr get attributes

    Handler to get job attributes
    """
    ID = (request.match_info['job_id'])
    LOG.debug('ID is : {} '.format(ID))
    if ID in jobs.keys():
        #return web.Response(text="Job attributes : {}".format(jobs[ID]))
        return web.json_response(jobs[ID])
    else:
        return web.Response(text="ERROR : Job is not present!")

@routes.put('/jobs')
async def add_jobs(request):
    """
    add_jobs add jobs

    Handler to add jobs to the queue
    """
    entries = await request.json()
    LOG.debug(entries)
    jobs.update(entries)
    return web.Response(text="Present jobs are : {}".format(jobs))

@routes.post('/jobs/{job_id}')
async def abort_job(request):
    """
    abort_job abort job

    Handler to abort a job with given job_id
    """
    ID = (request.match_info['job_id'])
    LOG.debug("ID is {}".format(ID))
    if ID in jobs.keys():
        jobs_inprogress.remove(ID)
        del jobs[ID]
        # do fini if required
        return web.Response(text="Job Aborted")
    else:
        return web.Response(text="ERROR : No such job present!")


if __name__ == '__main__':

    #setup logging
    setup_logging()

    app = web.Application()
    app.add_routes(routes)
    web.run_app(app)
