#!/usr/bin/env python3

## @package replicator.py
#
#  Replicator script which host different end points

from aiohttp import web

# Dictionary holding job_id and fdmi record
jobs = {"job1": {"Bucket-Name": "testbucket"}}

# List of active subscriber
schedulers = []

# List of jobs in progress
jobs_inprogress = ['job1']

# Route table declaration
routes = web.RouteTableDef()

## @list_jobs list jobs
#
#  Handler to list in-progress jobs


@routes.get('/jobs')
async def list_jobs(request):
    print(jobs_inprogress)
    # Returns jobs_inprogress
    return web.Response(text="In-Progress jobs : {}".format(jobs_inprogress))

## @get_job_attr get attributes
#
#  Handler to get job attributes


@routes.get('/jobs/{job_id}')
async def get_job_attr(request):
    ID = (request.match_info['job_id'])
    print('ID is : {} '.format(ID))
    if ID in jobs.keys():
        return web.Response(text="Job attributes : {}".format(jobs[ID]))
    else:
        return web.Response(text="ERROR : Job is not present!")

## @add_jobs add jobs
#
#  Handler to add jobs to the queue


@routes.put('/jobs')
async def add_jobs(request):
    entries = await request.json()
    print(entries)
    jobs.update(entries)
    return web.Response(text="Present jobs are : {}".format(jobs))

## @abort_job abort job
#
#  Handler to abort a job with given job_id


@routes.post('/jobs/{job_id}')
async def abort_job(request):
    ID = (request.match_info['job_id'])
    print("ID is {}".format(ID))
    if ID in jobs.keys():
        jobs_inprogress.remove(ID)
        del jobs[ID]
        # do fini if required
        return web.Response(text="Job Aborted")
    else:
        return web.Response(text="ERROR : No such job present!")

app = web.Application()
app.add_routes(routes)
web.run_app(app)
