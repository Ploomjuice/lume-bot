
import mysql.connector.aio
import pandas as pd


class DBUtils:

    def __init__(self):
        """ Future work: Implement connection pooling """
        self.con = None

    async def connect(self, user, password, database, host="localhost"):

        self.con = await mysql.connector.aio.connect(
            host=host,
            user=user,
            password=password,
            database=database
        )

    async def close(self):
        """ Close or release a connection back to the connection pool """
        if self.con:
            await self.con.close()
            self.con = None

    async def getdf(self, query, params=()):
        """ Execute a select query and returns the result as a dataframe """

        """Execute a query asynchronously."""
        if not self.con:
            raise ConnectionError("Database connection is not established.")

        cursor = await self.con.cursor()

        try:
            await cursor.execute(query, params or ())

            rows = await cursor.fetchall()
            cols = [desc[0] for desc in cursor.description]

            return pd.DataFrame(rows, columns=cols)

        finally:
            await cursor.close()

    async def execute_query(self, query, params=()):
        if not self.con:
            raise ConnectionError("Database connection is not established.")

        cursor = await self.con.cursor()

        try:
            await cursor.execute(query, params or ())

        finally:
            await cursor.close()

    async def insert_one(self, sql, val):
        """ Insert a single row """
        if not self.con:
            raise ConnectionError("Database connection is not established.")

        cursor = await self.con.cursor()

        try:
            await cursor.execute(sql, val or ())
            await self.con.commit()

        finally:
            await cursor.close()


async def insert_many(self, sql, vals):
        """ Insert multiple rows """
        if not self.con:
            raise ConnectionError("Database connection is not established.")

        async with self.con.cursor() as cursor:
            cursor.execute(sql, vals)
            self.con.commit()