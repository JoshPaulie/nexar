import asyncio
import logging
import os
import sys

from nexar.client import NexarClient
from nexar.enums import Region

# Get API key from environment
api_key = os.getenv("RIOT_API_KEY")
if api_key is None:
    sys.exit("Please set RIOT_API_KEY environment variable")


async def main() -> None:
    # --8<-- [start:basic-logging]
    # Enable logging for nexar
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger("nexar")
    logger.setLevel(logging.INFO)

    client = NexarClient(
        riot_api_key=api_key,
        default_region=Region.NA1,
    )

    async with client:
        account = await client.get_riot_account("bexli", "bex")
    # --8<-- [end:basic-logging]

    # --8<-- [start:verbose-logging]
    # Enable debug-level logging for detailed output
    logging.basicConfig(
        level=logging.DEBUG,
        format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
    )
    logger = logging.getLogger("nexar")
    logger.setLevel(logging.DEBUG)

    client = NexarClient(
        riot_api_key=api_key,
        default_region=Region.NA1,
    )

    async with client:
        account = await client.get_riot_account("bexli", "bex")
    # --8<-- [end:verbose-logging]

    # --8<-- [start:suppress-logging]
    # Suppress nexar logging entirely
    logger = logging.getLogger("nexar")
    logger.setLevel(logging.CRITICAL + 1)

    client = NexarClient(
        riot_api_key=api_key,
        default_region=Region.NA1,
    )

    async with client:
        account = await client.get_riot_account("bexli", "bex")
    # --8<-- [end:suppress-logging]

    # --8<-- [start:custom-handler]
    # Route nexar logs to a file
    logger = logging.getLogger("nexar")
    logger.setLevel(logging.DEBUG)

    file_handler = logging.FileHandler("nexar.log")
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(logging.Formatter("%(asctime)s [%(name)s] %(levelname)s: %(message)s"))
    logger.addHandler(file_handler)

    client = NexarClient(
        riot_api_key=api_key,
        default_region=Region.NA1,
    )

    async with client:
        account = await client.get_riot_account("bexli", "bex")
    # --8<-- [end:custom-handler]


if __name__ == "__main__":
    asyncio.run(main())
