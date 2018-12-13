"""
Module of asyncio extensions.

Functions:
    wait_with_optional - Waits for multiple coroutines, with specific time outs
"""

import asyncio
from time import perf_counter


async def wait_with_optional(required, requiredTimeout, optional, optionalTimeout, auto_cancel=True):
    """
    Wait for all required tasks, and all optional tasks, with specific time outs.

    Finishes when:
     - All required tasks complete (with a result or exception), or timeout
     - All optional tasks complete, or the optionalTimeout exprires

    Optional tasks are given the longer of the time it takes the required
    tasks to complete, and the optionalTimeout.

    If auto_cancel is True, any tasks not done will be canceled before returning.

    Returns a tuple made up of the required tasks, and the optional tasks.
    """
    if optionalTimeout >= requiredTimeout:
        raise ValueError('requiredTimeout must be less than optionalTimeout')

    if len(required) == 0 and len(optional) == 0:
        raise ValueError('No awaitables!')

    # keep track of time so we can properly compute the optional timeout
    startTime = perf_counter()

    # wrap the passed coroutines into Futures (Tasks) if needed
    required = [asyncio.ensure_future(coro) for coro in required]
    optional = [asyncio.ensure_future(coro) for coro in optional]

    # wait for/finish all of the required tasks, timing them out as needed
    if len(required) > 0:
        await asyncio.wait(required, timeout=requiredTimeout)

    remainingTime = optionalTimeout - (perf_counter() - startTime)
    if remainingTime > 0 and len(optional) > 0:
        # some time is remaining, so give the optional tasks time to complete
        await asyncio.wait(optional, timeout=remainingTime)

    # cancel anything that hasn't completed (if desired)
    if auto_cancel:
        for future in required:
            if not future.done():
                future.cancel()
        for future in optional:
            if not future.done():
                future.cancel()

    return required, optional
