#!/usr/bin/env python3

# s3 replicator client
#
# This file contains replicator client
# with various REST requests.

import sys
import aiohttp
import asyncio
import logging
from log import setup_logging

LOG = logging.getLogger('multisite')

async def main():
    """
    main main function

    Main function for calling various REST requests.
    """
    setup_logging()

    async with aiohttp.ClientSession() as session:

        # Get inprogress list
        async with session.get('http://0.0.0.0:8080/jobs')as response:
            LOG.info("Status: {}".format(response.status))
            html = await response.text()
            LOG.info("Body: {}".format(html))

        # Get job attributes
        async with session.get(
        'http://0.0.0.0:8080/jobs/' + sys.argv[1]) as response:
            LOG.info("Status: {}".format(response.status))
            html = await response.text()
            LOG.info("Body: {}".format(html))

        # Add job and attributes
        async with session.put(
        'http://0.0.0.0:8080/jobs', json={"job2": "bar"}) as resp:
            LOG.info("Status: {}".format(response.status))
            html = await resp.text()
            LOG.info("Body: {}".format(html))

        # Abort job with given job_id
        async with session.post(
        'http://0.0.0.0:8080/jobs/' + sys.argv[1]) as resp:
            LOG.info("Status: {}".format(response.status))
            html = await resp.text()
            LOG.info("Body: {}".format(html))

loop = asyncio.get_event_loop()
loop.run_until_complete(main())
