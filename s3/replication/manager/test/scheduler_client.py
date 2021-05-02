#!/usr/bin/env python3

# scheduler client
#
# This file contains scheduler client
# which makes various REST api calls

import sys
import aiohttp
import asyncio
import logging
sys.path.append("../../common")
from log import setup_logging

LOG = logging.getLogger('multisite')#TBD

async def main():
    """Main function

    Main function calls REST apis

    """
    # Client session starts here

    setup_logging()

    fetch_cnt = 2 # Added default count for pre-fetch request

    async with aiohttp.ClientSession() as session:

        # Get Jobs in Progress
        async with session.get(
        'http://0.0.0.0:8080/jobs', params={"inProgress": "true"}) as response:
            LOG.info("Status: {}".format(response.status))
            html = await response.json()
            LOG.info("Body: {}".format(html))


        # Get jobs list
        async with session.get('http://0.0.0.0:8080/jobs')as response:
            LOG.info("Status: {}".format(response.status))
            html = await response.json()
            LOG.info("Body: {}".format(html))

        # Get subscriber list
        async with session.get(
        'http://0.0.0.0:8080/subscribers') as response:
            LOG.info("Status: {}".format(response.status))
            html = await response.json()
            LOG.info("Body: {}".format(html))

        # Update subscriber list
        async with session.post(
        'http://0.0.0.0:8080/subscribers', json={'sub_id': sys.argv[2] }) as response:
            LOG.info("Status: {}".format(response.status))
            html = await response.json()
            LOG.info("Body: {}".format(html))

        # Get Prefetch count
        async with session.get(
        'http://0.0.0.0:8080/jobs',
        params={"prefetch": fetch_cnt, "subscriber_id": "sub1"}) as response:
            LOG.info("Status: {}".format(response.status))
            html = await response.json()
            LOG.info("Body: {}".format(html))

        # Update Job's attributes
        async with session.put(
        'http://0.0.0.0:8080/jobs/' + sys.argv[1], json={"K2": "V2"}) as resp:
            LOG.info("Status: {}".format(response.status))
            html = await response.json()
            LOG.info("Body: {}".format(html))

loop = asyncio.get_event_loop()
loop.run_until_complete(main())
