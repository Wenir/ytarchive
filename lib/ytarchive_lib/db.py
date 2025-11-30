import psycopg


class DB:
    @classmethod
    async def create(cls, connection_string: str):
        self = cls()

        self.connection_string = connection_string
        self.connection = await psycopg.AsyncConnection.connect(self.connection_string)

        return self

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_value, traceback):
        await self.connection.close()
        return False
