from sqlalchemy import create_engine, inspect

from .. import config


def table_exists(table_name: str) -> bool:
    engine = create_engine(config.read("nua", "db", "url"))
    insp = inspect(engine)
    return insp.has_table(table_name)


def column_exists(table_name: str, column_name: str) -> bool:
    engine = create_engine(config.read("nua", "db", "url"))
    insp = inspect(engine)
    columns = insp.get_columns(table_name)
    return any(col["name"] == column_name for col in columns)


def execute_cmd(cmd: str):
    """Execute some command on the DB.

    Ex: 'alter table table_name add column column_name VARCHAR(160)
    """
    engine = create_engine(config.read("nua", "db", "url"))
    engine.execute(cmd)
