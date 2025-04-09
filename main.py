import asyncio
import logging

from parser.spimex_parser import main as spimex_main
from parser.async_processor import main as processor_main

from parser.common_log import configure_logging


configure_logging(level=logging.INFO)
log = logging.getLogger(__name__)


async def main():
    try:
        await spimex_main()
        await processor_main()
    except Exception as e:
        log.error(f"Ошибка при выполнении: {e}")


if __name__ == "__main__":
    asyncio.run(main())
