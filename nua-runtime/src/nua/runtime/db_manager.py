"""
Common interface for databases managers (WIP).

This could make it more uniform to use different databases (and easier to add additional databases).

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

    def __init__(self, host: str, port: str, user: str, password: str):
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

    def db_create(self, dbname: str, user: str):
        ...

    def db_exist(self, dbname: str) -> bool:
        ...

    def db_table_exist(self, dbname: str, user: str, password: str, table: str) -> bool:
        ...

    # # Additional from mariadb_utils
    # def pwd(self) -> str:
    #     pass
    #
    # # Additional from postgres:
    # def run_environment(_unused: dict) -> dict:
    #     pass
    #
    # def check_installed() -> bool:
    #     pass
    #
    # def check_listening(gateway: str) -> bool:
    #     pass
    #
    # def restart_service():
    #     pass
    #
    # # "Port" variants. Probably can be refactored somehow.
    # def setup_db_user_port(host: str, port: str, dbname: str, user: str, password: str):
    #     pass
    #
    # def remove_db_user_port(host: str, port: str, dbname: str, user: str):
    #     pass
    #
    # def db_drop_port(host: str, port: str, dbname: str):
    #     pass
    #
    # def user_drop_port(host: str, port: str, user: str) -> bool:
    #     pass
    #
    # def user_exist_port(host: str, port: str, user: str) -> bool:
    #     pass
    #
    # def user_create_port(host: str, port: str, user: str, password: str):
    #     pass
    #
    # def db_create_port(host: str, port: str, dbname: str, user: str):
    #     pass
    #
    # def db_exist_port(host: str, port: str, dbname: str) -> bool:
    #     pass
    #
    # def pg_db_table_exist_port(
    #     host: str, port: str, dbname: str, user: str, password: str, table: str
    # ) -> bool:
    #     """Check if the named database exists (for host, connecting as user), assuming
    #     DB exists."""
