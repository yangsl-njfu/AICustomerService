"""Backfill uploaded knowledge documents into the FAISS knowledge base."""
from __future__ import annotations

import asyncio
import json

from services.knowledge_service import knowledge_service


async def main():
    result = await knowledge_service.reindex_documents(force=False)
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    asyncio.run(main())
