#!/usr/bin/env python3

# s3 replicator server
#
# Replicator script which host different end points

import sys
import json
from aiohttp import web
import logging
from log import setup_logging
from replicator_conf_init import Config

# logging.basicConfig(filename="replicator.log",
#             format='%(asctime)s [%(levelname)s] [%(filename)s: %(lineno)d] %(message)s', filemode='w')

LOG = logging.getLogger('replicator_proc')

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
    """List_jobs

    Handler to list in-progress jobs

    """
    LOG.debug(jobs_inprogress)
    # Returns jobs_inprogress
    return web.json_response({'jobs': jobs_inprogress})

@routes.get('/jobs/{job_id}')
async def get_job(request):
    """Get job attribute

    Handler to get job attributes for given job_id

    """
    id = request.match_info['job_id']
    LOG.debug('id is : {} '.format(id))
    if id in jobs.keys():
        return web.json_response({id:jobs[id]})
    else:
        return web.json_response({'Response' : 'ERROR : Job is not present!'})

@routes.put('/jobs')
async def add_job(request):
    LOG.debug(confReplicator.rep_conf.get("version_config"))
    """Add job in the queue

    Handler to add jobs to the queue

    """
    entries = await request.json()
    LOG.debug(entries)
    jobs.update(entries)
    return web.json_response({'jobs': jobs})

@routes.post('/jobs/{job_id}')
async def abort_job(request):
    """Abort a job

    Handler to abort a job with given job_id

    """
    id = (request.match_info['job_id'])
    LOG.debug("id is {}".format(id))
    if id in jobs.keys():
        try:
            jobs_inprogress.remove(id)
        except:
            return web.json_response({'Response' : 'ERROR : Job is not present!'})
        del jobs[id]
        return web.json_response({'Response' : 'Job Aborted'})
    else:
        return web.json_response({'Response' : 'ERROR : Job is not present!'})


if __name__ == '__main__':

    confReplicator = Config()

    HOST=confReplicator.host
    PORT=confReplicator.port

    # setup logging
    setup_logging()

    LOG.debug("HOST is : {}".format(HOST))
    LOG.debug("PORT is : {}".format(PORT))

    app = web.Application()
    app.add_routes(routes)
    web.run_app(app, host=HOST, port=PORT)
