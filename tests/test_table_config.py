from sqlalchemy.orm import Session

from app.db.crud import table_config as table_config_crud
from app.db.models.user import User
from app.services.table_config_service import TableConfigService


class TestTableConfigCRUD:
    def test_create_table_config(self, db: Session, test_user: User):
        """Test creating a table config."""
        columns = ["id", "name", "description"]
        table_config = table_config_crud.create_table_config(
            db, test_user.id, "groups", columns
        )

        assert table_config.user_id == test_user.id
        assert table_config.table_key == "groups"
        assert table_config.columns == columns
        assert table_config.id is not None

    def test_get_table_config(self, db: Session, test_user: User):
        """Test getting a table config."""
        columns = ["id", "name", "description"]
        created_config = table_config_crud.create_table_config(
            db, test_user.id, "groups", columns
        )

        retrieved_config = table_config_crud.get_table_config(
            db, test_user.id, "groups"
        )

        assert retrieved_config is not None
        assert retrieved_config.id == created_config.id
        assert retrieved_config.columns == columns

    def test_update_table_config(self, db: Session, test_user: User):
        """Test updating a table config."""
        original_columns = ["id", "name"]
        table_config = table_config_crud.create_table_config(
            db, test_user.id, "groups", original_columns
        )

        new_columns = ["id", "name", "description", "type"]
        updated_config = table_config_crud.update_table_config(
            db, test_user.id, "groups", new_columns
        )

        assert updated_config.columns == new_columns
        assert updated_config.id == table_config.id

    def test_create_or_update_table_config(self, db: Session, test_user: User):
        """Test create or update (upsert) functionality."""
        # First call should create
        columns1 = ["id", "name"]
        config1 = table_config_crud.create_or_update_table_config(
            db, test_user.id, "groups", columns1
        )

        # Second call should update
        columns2 = ["id", "name", "description"]
        config2 = table_config_crud.create_or_update_table_config(
            db, test_user.id, "groups", columns2
        )

        assert config1.id == config2.id
        assert config2.columns == columns2

    def test_delete_table_config(self, db: Session, test_user: User):
        """Test deleting a table config."""
        table_config_crud.create_table_config(
            db, test_user.id, "groups", ["id", "name"]
        )

        deleted = table_config_crud.delete_table_config(db, test_user.id, "groups")

        assert deleted is True

        # Verify it's gone
        retrieved = table_config_crud.get_table_config(db, test_user.id, "groups")
        assert retrieved is None

    def test_get_user_table_configs(self, db: Session, test_user: User):
        """Test getting all table configs for a user."""
        table_config_crud.create_table_config(
            db, test_user.id, "groups", ["id", "name"]
        )
        table_config_crud.create_table_config(
            db, test_user.id, "users", ["id", "email", "username"]
        )

        configs = table_config_crud.get_user_table_configs(db, test_user.id)

        assert len(configs) == 2
        table_keys = [config.table_key for config in configs]
        assert "groups" in table_keys
        assert "users" in table_keys


class TestTableConfigService:
    def test_get_table_config(self, db: Session, test_user: User):
        """Test service get_table_config method."""
        service = TableConfigService(db, test_user)

        # Should return None if no config exists
        config = service.get_table_config("groups")
        assert config is None

        # Create a config and retrieve it
        columns = ["id", "name", "description"]
        created_config = table_config_crud.create_table_config(
            db, test_user.id, "groups", columns
        )

        retrieved_config = service.get_table_config("groups")
        assert retrieved_config is not None
        assert retrieved_config.id == created_config.id

    def test_create_or_update_table_config(self, db: Session, test_user: User):
        """Test service create_or_update_table_config method."""
        service = TableConfigService(db, test_user)

        columns = ["id", "name", "description"]
        config = service.create_or_update_table_config("groups", columns)

        assert config.user_id == test_user.id
        assert config.table_key == "groups"
        assert config.columns == columns

    def test_delete_table_config(self, db: Session, test_user: User):
        """Test service delete_table_config method."""
        service = TableConfigService(db, test_user)

        # Create a config first
        table_config_crud.create_table_config(
            db, test_user.id, "groups", ["id", "name"]
        )

        # Delete it
        deleted = service.delete_table_config("groups")
        assert deleted is True

        # Try to delete non-existent config
        deleted = service.delete_table_config("non_existent")
        assert deleted is False
