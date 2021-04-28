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

LOG = logging.getLogger('multisite')

async def main():
    """
    main - main function

    Main function calls REST apis
    """
    # Client session starts here

    setup_logging()

    async with aiohttp.ClientSession() as session:

        # Get Jobs in Progress
        async with session.get(
        'http://0.0.0.0:8080/jobs', params={"inProgress": "true"}) as response:
            LOG.info("Status: {}".format(response.status))
            html = await response.text()
            LOG.info("Body: {}".format(html))

        # Get Prefetch count
        async with session.get(
        'http://0.0.0.0:8080/jobs',
        params={"prefetch": "10", "subscriber_id": "sub1"}) as response:
            LOG.info("Status: {}".format(response.status))
            html = await response.text()
            LOG.info("Body: {}".format(html))

        # Get jobs list
        async with session.get('http://0.0.0.0:8080/jobs')as response:
            LOG.info("Status: {}".format(response.status))
            html = await response.text()
            LOG.info("Body: {}".format(html))

        # Update subscriber list
        async with session.post(
        'http://0.0.0.0:8080/subscribers', json={'rep1': 'R1'}) as resp:
            LOG.info("Status: {}".format(response.status))
            html = await response.text()
            LOG.info("Body: {}".format(html))

        # Update Job's attributes
        async with session.put(
        'http://0.0.0.0:8080/jobs/' + sys.argv[1], json={"K2": "V2"}) as resp:
            LOG.info("Status: {}".format(response.status))
            html = await response.text()
            LOG.info("Body: {}".format(html))

loop = asyncio.get_event_loop()
loop.run_until_complete(main())
