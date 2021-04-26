#!/usr/bin/env python3

## @scheduler.py scheduler server
#
#  This file contains scheduler sever
#  which exposes various REST endpoints

from aiohttp import web
from urllib.parse import urlparse, parse_qs

## Dictionary holding job_id and fdmi record
jobs = {'jobA': {'K1': 'V1'}}  # dummy record is passed.

## List of active subscriber
subscribers = ['sub1']

## List of jobs in progress
jobs_inprogress = ['jobA']

# Route table declaration
routes = web.RouteTableDef()

## @list_jobs Get in-progress jobs
#
#  Handler api to handle multiple query


@routes.get('/jobs')
async def list_jobs(request):
    url = request.path_qs
    url_ob = urlparse(url)
    query = parse_qs(url_ob.query)
    # Return in progress jobs
    if 'inProgress' in query:
        print('InProgress is : {}'.format(query['inProgress']))
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
        print(pf_cnt)
        print("sub_id is : {}".format(sub_id))
        if sub_id in subscribers:
            if int(pf_cnt) <= len(jobs):
                return web.Response(text='{}'.format(pf_cnt))
            else:
                return web.Response(text='{}'.format(len(jobs)))
    else:
        return web.Response(text='List of jobs : {}'.format(jobs.keys()))

## @get_job_attr Get in progress jobs
#
#  Handler api to fetch job attributes


@routes.get('/jobs/{job_id}')
async def get_job_attr(request):
    ID = (request.match_info['job_id'])
    if ID in jobs.keys():
        return web.Response(text='attributes are : {}'.format(jobs['job_id']))
    else:
        return web.Response(text='ERROR : Job is not present!')

## @add_jobs add jobs
#
#  Handler to add jobs to the job queue


@routes.post('/jobs')
async def add_jobs(request):
    entries = await request.json()
    print(entries)
    jobs.update(entries)
    print('Job list : {}'.format(jobs))

## @add_subscriber add subscriber
#
#  Handler for Subscriber


@routes.post('/subscribers')
async def add_subscriber(request):
    sub_id = await request.json()
    print('subscriber is : {}'.format(sub_id))
    if sub_id in subscribers:
        return web.Response(text='Replicator is Already subscribed!')
    else:
        subscribers.append(sub_id)
        print(subscribers)
        return web.Response(text='Replicator added! : {}'.format(subscribers))

## @list_subscribers List subscriber
#
#  Handler to list subscribers


@routes.get('/subscribers')
async def list_subscribers(request):
    return web.Response(text='subscribers are : {} '.format(subscribers))

## update_job_attr update job attributes
#
#  Update attributes for job_id


@routes.put('/jobs/{job_id}')
async def update_job_attr(request):
    val = await request.json()  # ToDo
    ID = (request.match_info['job_id'])
    print('ID is {}'.format(ID))
    if ID in jobs.keys():
        jobs[ID] = val
        return web.Response(text='{} attributs are: {}'.format(ID, jobs[ID]))
    else:
        jobs.update({ID: val})
        jobs_inprogress.append(ID)
        return web.Response(text='updated list is {}!'.format(jobs))

app = web.Application()
app.add_routes(routes)
web.run_app(app)
