from prisma import Prisma

db = Prisma()


async def connect() -> None:
    await db.connect()


async def disconnect() -> None:
    await db.disconnect()
