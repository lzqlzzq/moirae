import asyncio


class Latch:
    def __init__(self, count):
        if count < 0:
            raise ValueError("count should be >= 0")
        self._count = count
        self._event = asyncio.Event()
        self._lock = asyncio.Lock()

        if self._count == 0:
            self._event.set()

    async def count_down(self):
        async with self._lock:
            self._count -= 1
            if self._count <= 0:
                self._event.set()

    async def wait(self):
        await self._event.wait()

    async def get_count(self):
        async with self._lock:
            return self._count

    def __str__(self):
        return f"<CountDownLatch count={self._count}>"

    def __repr__(self):
        return self.__str__()
