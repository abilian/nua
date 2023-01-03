"""Common interface for databases managers (WIP).

This could make it more uniform to use different databases
(and easier to add additional databases).

Ex:

```python

pg_manager = PostgresManager("localhost", "5432", "postgres", "postgres")
if not pg_manager.db_exists("mydb"):
    pg_manager.db_create("my_db")
...

# Where PostgresManager is a subclass of DbManager
```

TODO: refactor the existing modules to implement the API.
"""

from typing import Protocol


class DbManager(Protocol):
    """Database manager."""

    def __init__(
        self,
        host: str = "",
        port: str | int = "",
        user: str = "",
        password: str | None = None,
    ):
        ...

    # Common methods (between PostgreSQL and MariaDB)
    def setup_db_user(self, dbname: str, user: str, password: str):
        ...

    def remove_db_user(self, dbname: str, user: str):
        ...

    def db_drop(self, dbname: str):
        ...

    def db_dump(self, dbname: str, **kwargs: str):
        ...

    def user_drop(self, user: str) -> bool:
        ...

    def user_exist(self, user: str) -> bool:
        ...

    def user_create(self, user: str, password: str):
        ...

    def db_create(self, dbname: str, user: str, password: str | None = None):
        ...

    def db_exist(self, dbname: str) -> bool:
        ...

    def db_table_exist(self, dbname: str, user: str, password: str, table: str) -> bool:
        ...
