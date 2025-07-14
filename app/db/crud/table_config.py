from typing import List, Optional

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.db.models.table_config import TableConfig


def get_table_config(
    db: Session, user_id: int, table_key: str
) -> Optional[TableConfig]:
    """Get a specific table config for a user."""
    return (
        db.query(TableConfig)
        .filter(TableConfig.user_id == user_id, TableConfig.table_key == table_key)
        .first()
    )


def get_user_table_configs(db: Session, user_id: int) -> List[TableConfig]:
    """Get all table configs for a user."""
    return db.query(TableConfig).filter(TableConfig.user_id == user_id).all()


def create_table_config(
    db: Session, user_id: int, table_key: str, columns: List[str]
) -> TableConfig:
    """Create a new table config for a user."""
    table_config = TableConfig(
        user_id=user_id,
        table_key=table_key,
        columns=columns,
    )
    db.add(table_config)
    try:
        db.commit()
        db.refresh(table_config)
    except IntegrityError as e:
        db.rollback()
        msg = str(e.orig).lower()
        if "unique constraint" in msg and "uq_user_table_config" in msg:
            raise ValueError(
                f"Table config for user {user_id} and table '{table_key}' already exists."
            )
        raise
    return table_config


def update_table_config(
    db: Session, user_id: int, table_key: str, columns: List[str]
) -> TableConfig:
    """Update an existing table config for a user."""
    table_config = get_table_config(db, user_id, table_key)
    if not table_config:
        raise ValueError(
            f"Table config for user {user_id} and table '{table_key}' not found."
        )

    table_config.columns = columns
    db.commit()
    db.refresh(table_config)
    return table_config


def create_or_update_table_config(
    db: Session, user_id: int, table_key: str, columns: List[str]
) -> TableConfig:
    """Create or update a table config for a user (upsert operation)."""
    table_config = get_table_config(db, user_id, table_key)
    if table_config:
        return update_table_config(db, user_id, table_key, columns)
    else:
        return create_table_config(db, user_id, table_key, columns)


def delete_table_config(db: Session, user_id: int, table_key: str) -> bool:
    """Delete a table config for a user."""
    table_config = get_table_config(db, user_id, table_key)
    if not table_config:
        return False

    db.delete(table_config)
    db.commit()
    return True


def delete_user_table_configs(db: Session, user_id: int) -> int:
    """Delete all table configs for a user."""
    result = db.query(TableConfig).filter(TableConfig.user_id == user_id).delete()
    db.commit()
    return result
