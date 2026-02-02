from typing import Optional, Any, Tuple, List

import aiosqlite


class Database:
    """Database wrapper with auto-commit"""

    def __init__(self, db_path: str):
        self.db_path = db_path
        self._conn: Optional[aiosqlite.Connection] = None

    async def connect(self):
        """Establish database connection"""
        if self._conn is None:
            self._conn = await aiosqlite.connect(self.db_path)

    async def execute(self, query: str, params: Tuple = ()) -> aiosqlite.Cursor:
        """Execute a query and auto-commit"""
        await self.connect()
        cursor = await self._conn.execute(query, params)
        await self._conn.commit()
        return cursor

    async def fetchone(self, query: str, params: Tuple = ()) -> Optional[Any]:
        """Execute a query and fetch one result"""
        await self.connect()
        async with self._conn.execute(query, params) as cursor:
            return await cursor.fetchone()

    async def fetchall(self, query: str, params: Tuple = ()) -> List[Any]:
        """Execute a query and fetch all results"""
        await self.connect()
        async with self._conn.execute(query, params) as cursor:
            return await cursor.fetchall()

    async def fetchrows(self, query: str, params: Tuple = ()) -> aiosqlite.Cursor:
        """Execute a query and return the cursor for row iteration"""
        await self.connect()
        cursor = await self._conn.execute(query, params)
        return cursor

    async def executemany(self, query: str, params: List[Tuple]) -> aiosqlite.Cursor:
        """Execute many queries and auto-commit"""
        await self.connect()
        cursor = await self._conn.executemany(query, params)
        await self._conn.commit()
        return cursor

    async def commit(self):
        """Manual commit if needed"""
        if self._conn:
            await self._conn.commit()

    async def close(self):
        """Close the connection"""
        if self._conn:
            await self._conn.close()
            self._conn = None
