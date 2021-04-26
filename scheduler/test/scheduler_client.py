#!/usr/bin/env python3

## @scheder scheduler client
#
#  This file contains scheduler client
#  which makes various REST api calls

import sys
import aiohttp
import asyncio

job_url = 'http://0.0.0.0:8080/jobs'
sub_url = 'http://0.0.0.0:8080/subscribers'

## @main main function
#
#  Main functioncalls All REST api


async def main():

    # Client session starts here
    async with aiohttp.ClientSession() as session:

        # Get Jobs in Progress
        async with session.get(
        'http://0.0.0.0:8080/jobs', params={"inProgress": "true"}) as response:
            print("Status: ", response.status)
            html = await response.text()
            print("Body: ", html)

        # Get Prefetch count
        async with session.get(
        'http://0.0.0.0:8080/jobs',
        params={"prefetch": "10", "subscriber_id": "sub1"}) as response:
            print("Status: ", response.status)
            html = await response.text()
            print("Body: ", html)

        # Get jobs list
        async with session.get('http://0.0.0.0:8080/jobs')as response:
            print("Status :", response.status)
            html = await response.text()
            print("Body :", html)

        # Update subscriber list
        async with session.post(
        'http://0.0.0.0:8080/subscribers', json={'rep1': 'R1'}) as resp:
            print("Status :", response.status)
            print(str(resp.url))
            html = await resp.text()
            print("Body :", html)

        # Update Job's attributes
        async with session.put(
        'http://0.0.0.0:8080/jobs/' + sys.argv[1], json={"K2": "V2"}) as resp:
            print("Status :", response.status)
            print(str(resp.url))
            html = await resp.text()
            print("Body :", html)

loop = asyncio.get_event_loop()
loop.run_until_complete(main())
