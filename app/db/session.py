from sqlalchemy import create_engine, event
from sqlalchemy.orm import Query, sessionmaker, with_loader_criteria

from app.core.config import settings
from app.db.base import SoftDeleteMixin

DATABASE_URL = (
    f"postgresql+psycopg2://{settings.DB_USER}:{settings.DB_PASSWORD}"
    f"@{settings.DB_HOST}:{settings.DB_PORT}/{settings.DB_NAME}"
)


class SoftDeleteQuery(Query):
    _with_deleted = False
    _only_deleted = False

    def with_deleted(self):
        """Include deleted rows in query results."""
        self._with_deleted = True
        return self

    def only_deleted(self):
        """Only include deleted rows in query results."""
        self._only_deleted = True
        self._with_deleted = True
        return self

    def _iter(self):
        if self._only_deleted:
            for desc in self.column_descriptions:
                entity = desc.get("entity", None)
                if entity and hasattr(entity, "is_deleted"):
                    self = self.enable_assertions(False).filter(
                        entity.is_deleted == True
                    )
        elif not self._with_deleted:
            for desc in self.column_descriptions:
                entity = desc.get("entity", None)
                if entity is not None and hasattr(entity, "is_deleted"):
                    self = self.enable_assertions(False).filter(
                        entity.is_deleted == False
                    )
        return super()._iter()


engine = create_engine(DATABASE_URL, pool_size=10, max_overflow=20, pool_pre_ping=True)

SessionLocal = sessionmaker(
    autocommit=False, autoflush=False, bind=engine, query_cls=SoftDeleteQuery
)


@event.listens_for(SessionLocal, "do_orm_execute")
def _add_soft_delete_criteria(execute_state):
    if not execute_state.is_select:
        return

    # If query explicitly asked for deleted rows, skip filter
    if getattr(execute_state.statement, "_with_deleted", False) or getattr(
        execute_state.statement, "_only_deleted", False
    ):
        return

    execute_state.statement = execute_state.statement.options(
        with_loader_criteria(
            SoftDeleteMixin, lambda cls: cls.is_deleted == False, include_aliases=True
        )
    )


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
