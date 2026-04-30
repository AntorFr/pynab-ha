import asyncio

from asgiref.sync import sync_to_async
from django.db import close_old_connections


async def close_old_async_connections_async():
    await sync_to_async(close_old_connections, thread_sensitive=True)()


def close_old_async_connections():
    try:
        asyncio.get_running_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        try:
            loop.run_until_complete(close_old_async_connections_async())
        finally:
            loop.close()
    else:
        raise RuntimeError(
            "close_old_async_connections() cannot be called from a running "
            "event loop; use close_old_async_connections_async() instead."
        )
