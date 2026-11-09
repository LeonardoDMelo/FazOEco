"""Dedicated scheduler process. The API stays free to scale without duplicating jobs.

Run with: python -m app.worker
"""

from __future__ import annotations

import asyncio
import logging
import signal

from app.scheduler.manager import get_scheduler_manager

logger = logging.getLogger(__name__)


async def _run() -> None:
    logging.basicConfig(level=logging.INFO)
    manager = get_scheduler_manager()
    manager.start()
    stop = asyncio.Event()
    loop = asyncio.get_running_loop()
    for sig in (signal.SIGINT, signal.SIGTERM):
        try:
            loop.add_signal_handler(sig, stop.set)
        except NotImplementedError:
            signal.signal(sig, lambda *_: stop.set())
    logger.info("FazOEco worker waiting for scheduled jobs")
    await stop.wait()
    manager.shutdown()


def main() -> None:
    asyncio.run(_run())


if __name__ == "__main__":
    main()
