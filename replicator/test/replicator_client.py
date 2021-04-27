#!/usr/bin/env python3

# s3 replicator client
#
# This file contains replicator client
# with various REST requests.

import sys
import aiohttp
import asyncio

async def main():
    """
    main main function

    Main function for calling various REST requests.
    """
    async with aiohttp.ClientSession() as session:

        # Get inprogress list
        async with session.get('http://0.0.0.0:8080/jobs')as response:
            print("Status:", response.status)
            html = await response.text()
            print("Body1:", html)

        # Get job attributes
        async with session.get(
        'http://0.0.0.0:8080/jobs/' + sys.argv[1]) as response:
            print("Status:", response.status)
            html = await response.text()
            print("Body2:", html)

        # Add job and attributes
        async with session.put(
        'http://0.0.0.0:8080/jobs', json={"job2": "bar"}) as resp:
            print("Status:", response.status)
            print(str(resp.url))
            html = await resp.text()
            print("Body3:", html)

        # Abort job with given job_id
        async with session.post(
        'http://0.0.0.0:8080/jobs/' + sys.argv[1]) as resp:
            print("Status:", response.status)
            print(str(resp.url))
            html = await resp.text()
            print("Body4:", html)

loop = asyncio.get_event_loop()
loop.run_until_complete(main())
