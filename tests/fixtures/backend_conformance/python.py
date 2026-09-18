from __future__ import annotations

import asyncio
from typing import Generic, TypeVar
from support import Service

T = TypeVar("T")


class BaseWorker:
    pass


class Worker(BaseWorker, Generic[T]):
    def run(self, item: T) -> T:
        helper(item)
        helper(item)
        return item

    def helper(self, item: T) -> T:
        return item

    async def async_probe(self, item: T) -> T:
        await asyncio.sleep(0)
        return item

    def nested_probe(self, item: T) -> T:
        def nested(value: T) -> T:
            return value

        return nested(item)
