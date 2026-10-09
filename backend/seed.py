"""Idempotent LeadForge seed entry point."""
import asyncio

from lib.db import ensure_indexes
from lib.demo_seed import seed_demo_data


async def main() -> None:
    await ensure_indexes()
    await seed_demo_data()
    print("LeadForge demo data is ready")


if __name__ == "__main__":
    asyncio.run(main())