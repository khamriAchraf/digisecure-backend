from datetime import datetime, timezone
from typing import Any, Dict, List

from sqlalchemy.orm import Session

from app.core.logger import logger
from app.core.security import has_permission
from app.db.models.user import User
from app.schemas.group import GroupCreate
from app.schemas.role import RoleCreate
from app.schemas.user import UserCreate


class PermissionError(Exception):
    pass


class SchemaService:
    def __init__(self, db: Session, current_user: User):
        self.db = db
        self.current_user = current_user

    def get_resource_schema(self, resource_type: str) -> Dict[str, Any]:
        """
        Get JSON schema for a specific resource type.
        Requires 'create' permission on the resource.
        """
        logger.info(
            f"User {self.current_user.id} attempts to GET schema for {resource_type} at {datetime.now(timezone.utc).isoformat()}"
        )

        if not has_permission(self.current_user, "create", resource_type):
            logger.warning(
                f"User {self.current_user.id} denied schema access for {resource_type}"
            )
            raise PermissionError(f"Not allowed to access schema for {resource_type}.")

        # Get the schema based on resource type
        schema = self._generate_schema_for_resource(resource_type)

        logger.info(
            f"User {self.current_user.id} successfully got schema for {resource_type}"
        )
        return schema

    def get_resource_edit_schema(self, resource_type: str) -> Dict[str, Any]:
        """
        Get JSON edit schema for a specific resource type.
        Requires 'update' permission on the resource.
        """
        logger.info(
            f"User {self.current_user.id} attempts to GET edit schema for {resource_type} at {datetime.now(timezone.utc).isoformat()}"
        )

        if not has_permission(self.current_user, "read", resource_type):
            logger.warning(
                f"User {self.current_user.id} denied edit schema access for {resource_type}"
            )
            raise PermissionError(
                f"Not allowed to access edit schema for {resource_type}."
            )

        schema = self._generate_edit_schema_for_resource(resource_type)

        logger.info(
            f"User {self.current_user.id} successfully got edit schema for {resource_type}"
        )
        return schema

    def _generate_schema_for_resource(self, resource_type: str) -> Dict[str, Any]:
        """
        Generate JSON schema for the specified resource type.
        """
        schemas = {
            "group": self._get_group_schema(),
            "user": self._get_user_schema(),
            "role": self._get_role_schema(),
            "computer": self._get_computer_schema(),
            # Add other resource types here as they're implemented
        }

        if resource_type not in schemas:
            raise ValueError(f"Unknown resource type: {resource_type}")

        return schemas[resource_type]

    def _generate_edit_schema_for_resource(self, resource_type: str) -> Dict[str, Any]:
        """
        Generate JSON edit schema for the specified resource type.
        """
        schemas = {
            "user": self._get_user_edit_schema(),
            "group": self._get_group_edit_schema(),
            "computer": self._get_computer_edit_schema(),
        }

        if resource_type not in schemas:
            raise ValueError(f"Unknown resource type: {resource_type}")

        return schemas[resource_type]

    def _get_group_schema(self) -> Dict[str, Any]:
        """
        Generate JSON schema for group resource.
        """
        # Get the base schema from Pydantic
        base_schema = GroupCreate.model_json_schema()

        # Get available parent groups for the select dropdown
        parent_groups = self._get_parent_group_options()

        # Enhance the schema with additional metadata
        enhanced_schema = {
            "version": "1.0.0",
            "resource_type": "group",
            "schema": base_schema,
            "ui": {
                "title_key": "forms.group.create.title",
                "description_key": "forms.group.create.description",
                "fields": {
                    "name": {
                        "widget": "text",
                        "placeholder_key": "forms.group.fields.name.placeholder",
                        "help_text_key": "forms.group.fields.name.help_text",
                        "label_key": "forms.group.fields.name.label",
                        "order": 1,
                        "validation": {
                            "required": True,
                            "min_length": 1,
                            "max_length": 100,
                            "error_messages": {
                                "required": "forms.group.fields.name.errors.required",
                                "min_length": "forms.group.fields.name.errors.min_length",
                                "max_length": "forms.group.fields.name.errors.max_length",
                            },
                        },
                    },
                    "description": {
                        "widget": "textarea",
                        "placeholder_key": "forms.group.fields.description.placeholder",
                        "help_text_key": "forms.group.fields.description.help_text",
                        "label_key": "forms.group.fields.description.label",
                        "order": 4,
                        "validation": {
                            "required": False,
                            "max_length": 500,
                            "error_messages": {
                                "max_length": "forms.group.fields.description.errors.max_length"
                            },
                        },
                    },
                    "type": {
                        "widget": "select",
                        "options": [
                            {
                                "value": "skill",
                                "label_key": "forms.group.fields.type.options.skill",
                            },
                            {
                                "value": "org",
                                "label_key": "forms.group.fields.type.options.org",
                            },
                            {
                                "value": "notification",
                                "label_key": "forms.group.fields.type.options.notification",
                            },
                        ],
                        "placeholder_key": "forms.group.fields.type.placeholder",
                        "help_text_key": "forms.group.fields.type.help_text",
                        "label_key": "forms.group.fields.type.label",
                        "order": 3,
                        "validation": {"required": False},
                    },
                    "contain_users": {
                        "widget": "checkbox",
                        "label_key": "forms.group.fields.contain_users.label",
                        "help_text_key": "forms.group.fields.contain_users.help_text",
                        "order": 5,
                        "validation": {"required": False, "default": True},
                    },
                    "contain_items": {
                        "widget": "checkbox",
                        "label_key": "forms.group.fields.contain_items.label",
                        "help_text_key": "forms.group.fields.contain_items.help_text",
                        "order": 3,
                        "validation": {"required": False, "default": True},
                    },
                    "comment": {
                        "widget": "textarea",
                        "placeholder_key": "forms.group.fields.comment.placeholder",
                        "help_text_key": "forms.group.fields.comment.help_text",
                        "label_key": "forms.group.fields.comment.label",
                        "order": 6,
                        "validation": {
                            "required": False,
                            "max_length": 1000,
                            "error_messages": {
                                "max_length": "forms.group.fields.comment.errors.max_length"
                            },
                        },
                    },
                    "parent_id": {
                        "widget": "select",
                        "quick_create_resource": "group",
                        "options": parent_groups,
                        "placeholder_key": "forms.group.fields.parent_id.placeholder",
                        "help_text_key": "forms.group.fields.parent_id.help_text",
                        "label_key": "forms.group.fields.parent_id.label",
                        "order": 7,
                        "validation": {"required": False},
                    },
                },
            },
        }

        return enhanced_schema

    def _get_user_schema(self) -> Dict[str, Any]:
        """
        Generate JSON schema for user resource.
        """
        # Get the base schema from Pydantic
        base_schema = UserCreate.model_json_schema()

        # Enhance the schema with additional metadata
        enhanced_schema = {
            "version": "1.0.0",
            "resource_type": "user",
            "schema": base_schema,
            "ui": {
                "title_key": "forms.user.create.title",
                "description_key": "forms.user.create.description",
                "fields": {
                    "email": {
                        "widget": "email",
                        "placeholder_key": "forms.user.fields.email.placeholder",
                        "help_text_key": "forms.user.fields.email.help_text",
                        "label_key": "forms.user.fields.email.label",
                        "order": 1,
                        "validation": {
                            "required": True,
                            "error_messages": {
                                "required": "forms.user.fields.email.errors.required",
                                "invalid": "forms.user.fields.email.errors.invalid",
                            },
                        },
                    },
                    "username": {
                        "widget": "text",
                        "placeholder_key": "forms.user.fields.username.placeholder",
                        "help_text_key": "forms.user.fields.username.help_text",
                        "label_key": "forms.user.fields.username.label",
                        "order": 2,
                        "validation": {
                            "required": True,
                            "error_messages": {
                                "required": "forms.user.fields.username.errors.required"
                            },
                        },
                    },
                    "password": {
                        "widget": "password",
                        "placeholder_key": "forms.user.fields.password.placeholder",
                        "help_text_key": "forms.user.fields.password.help_text",
                        "label_key": "forms.user.fields.password.label",
                        "order": 3,
                        "validation": {
                            "required": True,
                            "error_messages": {
                                "required": "forms.user.fields.password.errors.required"
                            },
                        },
                    },
                    "full_name": {
                        "widget": "text",
                        "placeholder_key": "forms.user.fields.full_name.placeholder",
                        "help_text_key": "forms.user.fields.full_name.help_text",
                        "label_key": "forms.user.fields.full_name.label",
                        "order": 4,
                        "validation": {"required": False},
                    },
                    "status": {
                        "widget": "select",
                        "options": [
                            {
                                "value": "active",
                                "label_key": "forms.user.fields.status.options.active",
                            },
                            {
                                "value": "inactive",
                                "label_key": "forms.user.fields.status.options.inactive",
                            },
                            {
                                "value": "deleted",
                                "label_key": "forms.user.fields.status.options.deleted",
                            },
                        ],
                        "placeholder_key": "forms.user.fields.status.placeholder",
                        "help_text_key": "forms.user.fields.status.help_text",
                        "label_key": "forms.user.fields.status.label",
                        "order": 5,
                        "validation": {"required": False, "default": "active"},
                    },
                    "language": {
                        "widget": "select",
                        "options": [
                            {
                                "value": "en",
                                "label_key": "forms.user.fields.language.options.en",
                            },
                            {
                                "value": "fr",
                                "label_key": "forms.user.fields.language.options.fr",
                            },
                            {
                                "value": "es",
                                "label_key": "forms.user.fields.language.options.es",
                            },
                            {
                                "value": "de",
                                "label_key": "forms.user.fields.language.options.de",
                            },
                        ],
                        "placeholder_key": "forms.user.fields.language.placeholder",
                        "help_text_key": "forms.user.fields.language.help_text",
                        "label_key": "forms.user.fields.language.label",
                        "order": 6,
                        "validation": {"required": False, "default": "en"},
                    },
                    "theme": {
                        "widget": "select",
                        "options": [
                            {
                                "value": "light",
                                "label_key": "forms.user.fields.theme.options.light",
                            },
                            {
                                "value": "dark",
                                "label_key": "forms.user.fields.theme.options.dark",
                            },
                        ],
                        "placeholder_key": "forms.user.fields.theme.placeholder",
                        "help_text_key": "forms.user.fields.theme.help_text",
                        "label_key": "forms.user.fields.theme.label",
                        "order": 7,
                        "validation": {"required": False, "default": "light"},
                    },
                    "location": {
                        "widget": "text",
                        "placeholder_key": "forms.user.fields.location.placeholder",
                        "help_text_key": "forms.user.fields.location.help_text",
                        "label_key": "forms.user.fields.location.label",
                        "order": 8,
                        "validation": {"required": False},
                    },
                    "phone": {
                        "widget": "tel",
                        "placeholder_key": "forms.user.fields.phone.placeholder",
                        "help_text_key": "forms.user.fields.phone.help_text",
                        "label_key": "forms.user.fields.phone.label",
                        "order": 9,
                        "validation": {"required": False},
                    },
                    "secondary_phone": {
                        "widget": "tel",
                        "placeholder_key": "forms.user.fields.secondary_phone.placeholder",
                        "help_text_key": "forms.user.fields.secondary_phone.help_text",
                        "label_key": "forms.user.fields.secondary_phone.label",
                        "order": 10,
                        "validation": {"required": False},
                    },
                    "timezone": {
                        "widget": "select",
                        "options": [
                            {
                                "value": "UTC",
                                "label_key": "forms.user.fields.timezone.options.utc",
                            },
                            {
                                "value": "America/New_York",
                                "label_key": "forms.user.fields.timezone.options.america_new_york",
                            },
                            {
                                "value": "Europe/London",
                                "label_key": "forms.user.fields.timezone.options.europe_london",
                            },
                            {
                                "value": "Europe/Paris",
                                "label_key": "forms.user.fields.timezone.options.europe_paris",
                            },
                            {
                                "value": "Asia/Tokyo",
                                "label_key": "forms.user.fields.timezone.options.asia_tokyo",
                            },
                        ],
                        "placeholder_key": "forms.user.fields.timezone.placeholder",
                        "help_text_key": "forms.user.fields.timezone.help_text",
                        "label_key": "forms.user.fields.timezone.label",
                        "order": 11,
                        "validation": {"required": False},
                    },
                    "valid_from": {
                        "widget": "datetime-local",
                        "placeholder_key": "forms.user.fields.valid_from.placeholder",
                        "help_text_key": "forms.user.fields.valid_from.help_text",
                        "label_key": "forms.user.fields.valid_from.label",
                        "order": 12,
                        "validation": {"required": False},
                    },
                    "valid_until": {
                        "widget": "datetime-local",
                        "placeholder_key": "forms.user.fields.valid_until.placeholder",
                        "help_text_key": "forms.user.fields.valid_until.help_text",
                        "label_key": "forms.user.fields.valid_until.label",
                        "order": 13,
                        "validation": {"required": False},
                    },
                    "administartive_number": {
                        "widget": "text",
                        "placeholder_key": "forms.user.fields.administartive_number.placeholder",
                        "help_text_key": "forms.user.fields.administartive_number.help_text",
                        "label_key": "forms.user.fields.administartive_number.label",
                        "order": 14,
                        "validation": {"required": False},
                    },
                    "role_id": {
                        "widget": "select",
                        "quick_create_resource": "role",
                        "placeholder_key": "forms.user.fields.role_id.placeholder",
                        "help_text_key": "forms.user.fields.role_id.help_text",
                        "label_key": "forms.user.fields.role_id.label",
                        "order": 15,
                        "validation": {"required": False},
                    },
                },
            },
        }

        return enhanced_schema

    def _get_role_schema(self) -> Dict[str, Any]:
        """
        Generate JSON schema for role resource.
        """
        # Get the base schema from Pydantic
        base_schema = RoleCreate.model_json_schema()

        # Enhance the schema with additional metadata
        enhanced_schema = {
            "version": "1.0.0",
            "resource_type": "role",
            "schema": base_schema,
            "ui": {
                "title_key": "forms.role.create.title",
                "description_key": "forms.role.create.description",
                "fields": {
                    "name": {
                        "widget": "text",
                        "placeholder_key": "forms.role.fields.name.placeholder",
                        "help_text_key": "forms.role.fields.name.help_text",
                        "label_key": "forms.role.fields.name.label",
                        "order": 1,
                        "validation": {
                            "required": True,
                            "min_length": 1,
                            "max_length": 100,
                            "error_messages": {
                                "required": "forms.role.fields.name.errors.required",
                                "min_length": "forms.role.fields.name.errors.min_length",
                                "max_length": "forms.role.fields.name.errors.max_length",
                            },
                        },
                    },
                    "description": {
                        "widget": "textarea",
                        "placeholder_key": "forms.role.fields.description.placeholder",
                        "help_text_key": "forms.role.fields.description.help_text",
                        "label_key": "forms.role.fields.description.label",
                        "order": 2,
                        "validation": {
                            "required": False,
                            "max_length": 500,
                            "error_messages": {
                                "max_length": "forms.role.fields.description.errors.max_length"
                            },
                        },
                    },
                },
            },
        }

        return enhanced_schema

    def _get_computer_schema(self) -> Dict[str, Any]:
        """
        Generate JSON schema for computer resource creation.
        """
        from app.schemas.asset import \
            ComputerCreate  # Local import to avoid circular

        # Get the base schema from Pydantic
        base_schema = ComputerCreate.model_json_schema()
        available_manufacturers = self._get_manufacturer_options()
        available_locations = self._get_location_options()

        # Enhance the schema with additional metadata
        enhanced_schema = {
            "version": "1.0.0",
            "resource_type": "computer",
            "schema": base_schema,
            "ui": {
                "title_key": "forms.computer.create.title",
                "description_key": "forms.computer.create.description",
                "fields": {
                    "name": {
                        "widget": "text",
                        "placeholder_key": "forms.computer.fields.name.placeholder",
                        "help_text_key": "forms.computer.fields.name.help_text",
                        "label_key": "forms.computer.fields.name.label",
                        "order": 1,
                        "validation": {
                            "required": True,
                            "error_messages": {
                                "required": "forms.computer.fields.name.errors.required"
                            },
                        },
                    },
                    "serial_number": {
                        "widget": "text",
                        "placeholder_key": "forms.computer.fields.serial_number.placeholder",
                        "help_text_key": "forms.computer.fields.serial_number.help_text",
                        "label_key": "forms.computer.fields.serial_number.label",
                        "order": 2,
                        "validation": {"required": False},
                    },
                    "inventory_number": {
                        "widget": "text",
                        "placeholder_key": "forms.computer.fields.inventory_number.placeholder",
                        "help_text_key": "forms.computer.fields.inventory_number.help_text",
                        "label_key": "forms.computer.fields.inventory_number.label",
                        "order": 3,
                        "validation": {"required": False},
                    },
                    "status": {
                        "widget": "select",
                        "options": [
                            {
                                "value": "active",
                                "label_key": "forms.computer.fields.status.options.active",
                            },
                            {
                                "value": "inactive",
                                "label_key": "forms.computer.fields.status.options.inactive",
                            },
                            {
                                "value": "maintenance",
                                "label_key": "forms.computer.fields.status.options.maintenance",
                            },
                            {
                                "value": "retired",
                                "label_key": "forms.computer.fields.status.options.retired",
                            },
                        ],
                        "placeholder_key": "forms.computer.fields.status.placeholder",
                        "help_text_key": "forms.computer.fields.status.help_text",
                        "label_key": "forms.computer.fields.status.label",
                        "order": 4,
                        "validation": {"required": True, "default": "active"},
                    },
                    "purchase_date": {
                        "widget": "date",
                        "placeholder_key": "forms.computer.fields.purchase_date.placeholder",
                        "help_text_key": "forms.computer.fields.purchase_date.help_text",
                        "label_key": "forms.computer.fields.purchase_date.label",
                        "order": 5,
                        "validation": {"required": False},
                    },
                    "warranty_expiry": {
                        "widget": "date",
                        "placeholder_key": "forms.computer.fields.warranty_expiry.placeholder",
                        "help_text_key": "forms.computer.fields.warranty_expiry.help_text",
                        "label_key": "forms.computer.fields.warranty_expiry.label",
                        "order": 6,
                        "validation": {"required": False},
                    },
                    "model": {
                        "widget": "text",
                        "placeholder_key": "forms.computer.fields.model.placeholder",
                        "help_text_key": "forms.computer.fields.model.help_text",
                        "label_key": "forms.computer.fields.model.label",
                        "order": 7,
                        "validation": {"required": False},
                    },
                    "cpu": {
                        "widget": "text",
                        "placeholder_key": "forms.computer.fields.cpu.placeholder",
                        "help_text_key": "forms.computer.fields.cpu.help_text",
                        "label_key": "forms.computer.fields.cpu.label",
                        "order": 8,
                        "validation": {"required": False},
                    },
                    "ram": {
                        "widget": "text",
                        "placeholder_key": "forms.computer.fields.ram.placeholder",
                        "help_text_key": "forms.computer.fields.ram.help_text",
                        "label_key": "forms.computer.fields.ram.label",
                        "order": 9,
                        "validation": {"required": False},
                    },
                    "storage": {
                        "widget": "text",
                        "placeholder_key": "forms.computer.fields.storage.placeholder",
                        "help_text_key": "forms.computer.fields.storage.help_text",
                        "label_key": "forms.computer.fields.storage.label",
                        "order": 10,
                        "validation": {"required": False},
                    },
                    "os": {
                        "widget": "text",
                        "placeholder_key": "forms.computer.fields.os.placeholder",
                        "help_text_key": "forms.computer.fields.os.help_text",
                        "label_key": "forms.computer.fields.os.label",
                        "order": 11,
                        "validation": {"required": False},
                    },
                    "hostname": {
                        "widget": "text",
                        "placeholder_key": "forms.computer.fields.hostname.placeholder",
                        "help_text_key": "forms.computer.fields.hostname.help_text",
                        "label_key": "forms.computer.fields.hostname.label",
                        "order": 12,
                        "validation": {"required": False},
                    },
                    "ip_address": {
                        "widget": "text",
                        "placeholder_key": "forms.computer.fields.ip_address.placeholder",
                        "help_text_key": "forms.computer.fields.ip_address.help_text",
                        "label_key": "forms.computer.fields.ip_address.label",
                        "order": 13,
                        "validation": {"required": False},
                    },
                    "mac_address": {
                        "widget": "text",
                        "placeholder_key": "forms.computer.fields.mac_address.placeholder",
                        "help_text_key": "forms.computer.fields.mac_address.help_text",
                        "label_key": "forms.computer.fields.mac_address.label",
                        "order": 14,
                        "validation": {"required": False},
                    },
                    "manufacturer_id": {
                        "widget": "select",
                        "options": available_manufacturers,
                        "quick_create_resource": "manufacturer",
                        "placeholder_key": "forms.computer.fields.manufacturer_id.placeholder",
                        "help_text_key": "forms.computer.fields.manufacturer_id.help_text",
                        "label_key": "forms.computer.fields.manufacturer_id.label",
                        "order": 15,
                        "validation": {"required": False},
                    },
                    "location_id": {
                        "widget": "select",
                        "options": available_locations,
                        "quick_create_resource": "location",
                        "placeholder_key": "forms.computer.fields.location_id.placeholder",
                        "help_text_key": "forms.computer.fields.location_id.help_text",
                        "label_key": "forms.computer.fields.location_id.label",
                        "order": 16,
                        "validation": {"required": False},
                    },
                },
            },
        }

        return enhanced_schema

    def _get_user_edit_schema(self) -> Dict[str, Any]:
        """
        Generate JSON edit schema for user resource.
        This schema contains additional UI metadata for editing, including relationships and tab grouping.
        """
        from app.schemas.user import \
            UserUpdate  # Local import to avoid circular

        # Base schema allows partial updates
        base_schema = UserUpdate.model_json_schema()

        # Options for relationships
        available_roles = self._get_role_options()

        # Define tab definitions so that the frontend can render tabbed forms
        tabs = [
            {"id": "general", "label_key": "forms.tabs.general"},
            {"id": "preferences", "label_key": "forms.tabs.preferences"},
            {"id": "groups", "label_key": "forms.tabs.groups"},
        ]

        enhanced_schema = {
            "version": "1.0.0",
            "resource_type": "user",
            "schema_type": "edit",
            "schema": base_schema,
            "ui": {
                "title_key": "forms.user.edit.title",
                "description_key": "forms.user.edit.description",
                "tabs": tabs,
                "fields": {
                    # General tab
                    "email": {
                        "widget": "email",
                        "placeholder_key": "forms.user.fields.email.placeholder",
                        "help_text_key": "forms.user.fields.email.help_text",
                        "label_key": "forms.user.fields.email.label",
                        "order": 1,
                        "tab_id": "general",
                        "validation": {"required": False},
                    },
                    "username": {
                        "widget": "text",
                        "placeholder_key": "forms.user.fields.username.placeholder",
                        "help_text_key": "forms.user.fields.username.help_text",
                        "label_key": "forms.user.fields.username.label",
                        "order": 2,
                        "tab_id": "general",
                        "validation": {"required": False},
                    },
                    "full_name": {
                        "widget": "text",
                        "placeholder_key": "forms.user.fields.full_name.placeholder",
                        "help_text_key": "forms.user.fields.full_name.help_text",
                        "label_key": "forms.user.fields.full_name.label",
                        "order": 3,
                        "tab_id": "general",
                        "validation": {"required": False},
                    },
                    # Preferences tab
                    "status": {
                        "widget": "select",
                        "options": [
                            {
                                "value": "active",
                                "label_key": "forms.user.fields.status.options.active",
                            },
                            {
                                "value": "inactive",
                                "label_key": "forms.user.fields.status.options.inactive",
                            },
                            {
                                "value": "deleted",
                                "label_key": "forms.user.fields.status.options.deleted",
                            },
                        ],
                        "placeholder_key": "forms.user.fields.status.placeholder",
                        "help_text_key": "forms.user.fields.status.help_text",
                        "label_key": "forms.user.fields.status.label",
                        "order": 4,
                        "tab_id": "preferences",
                        "validation": {"required": False},
                    },
                    "language": {
                        "widget": "select",
                        "options": [
                            {
                                "value": "en",
                                "label_key": "forms.user.fields.language.options.en",
                            },
                            {
                                "value": "fr",
                                "label_key": "forms.user.fields.language.options.fr",
                            },
                            {
                                "value": "es",
                                "label_key": "forms.user.fields.language.options.es",
                            },
                            {
                                "value": "de",
                                "label_key": "forms.user.fields.language.options.de",
                            },
                        ],
                        "placeholder_key": "forms.user.fields.language.placeholder",
                        "help_text_key": "forms.user.fields.language.help_text",
                        "label_key": "forms.user.fields.language.label",
                        "order": 5,
                        "tab_id": "preferences",
                        "validation": {"required": False},
                    },
                    "theme": {
                        "widget": "select",
                        "options": [
                            {
                                "value": "light",
                                "label_key": "forms.user.fields.theme.options.light",
                            },
                            {
                                "value": "dark",
                                "label_key": "forms.user.fields.theme.options.dark",
                            },
                        ],
                        "placeholder_key": "forms.user.fields.theme.placeholder",
                        "help_text_key": "forms.user.fields.theme.help_text",
                        "label_key": "forms.user.fields.theme.label",
                        "order": 6,
                        "tab_id": "preferences",
                        "validation": {"required": False},
                    },
                    # Relationships tab
                    "role_id": {
                        "widget": "select",
                        "options": available_roles,
                        "quick_create_resource": "role",
                        "placeholder_key": "forms.user.fields.role_id.placeholder",
                        "help_text_key": "forms.user.fields.role_id.help_text",
                        "label_key": "forms.user.fields.role_id.label",
                        "order": 7,
                        "tab_id": "general",
                        "validation": {"required": False},
                        "relationship": {"target": "role", "type": "one-to-one"},
                    },
                    "groups": {
                        "widget": "relationship",
                        "multiple": True,
                        "quick_create_resource": "group",
                        "placeholder_key": "forms.user.fields.groups.placeholder",
                        "help_text_key": "forms.user.fields.groups.help_text",
                        "label_key": "forms.user.fields.groups.label",
                        "order": 8,
                        "tab_id": "groups",
                        "validation": {"required": False},
                    },
                },
            },
        }

        return enhanced_schema

    def _get_group_edit_schema(self) -> Dict[str, Any]:
        """
        Generate JSON edit schema for group resource.
        """
        from app.schemas.group import \
            GroupUpdate  # Local import to avoid circular

        base_schema = GroupUpdate.model_json_schema()

        # Options for parent groups (excluding current group can be handled in frontend or future enhancement)
        parent_group_options = self._get_parent_group_options()

        # Define tabs
        tabs = [
            {"id": "general", "label_key": "forms.tabs.general"},
            {"id": "users", "label_key": "forms.tabs.users"},
            {"id": "assets", "label_key": "forms.tabs.assets"},
        ]

        enhanced_schema = {
            "version": "1.0.0",
            "resource_type": "group",
            "schema_type": "edit",
            "schema": base_schema,
            "ui": {
                "title_key": "forms.group.edit.title",
                "description_key": "forms.group.edit.description",
                "tabs": tabs,
                "fields": {
                    # General tab
                    "name": {
                        "widget": "text",
                        "placeholder_key": "forms.group.fields.name.placeholder",
                        "help_text_key": "forms.group.fields.name.help_text",
                        "label_key": "forms.group.fields.name.label",
                        "order": 1,
                        "tab_id": "general",
                        "validation": {"required": False},
                    },
                    "description": {
                        "widget": "textarea",
                        "placeholder_key": "forms.group.fields.description.placeholder",
                        "help_text_key": "forms.group.fields.description.help_text",
                        "label_key": "forms.group.fields.description.label",
                        "order": 2,
                        "tab_id": "general",
                        "validation": {"required": False},
                    },
                    "type": {
                        "widget": "select",
                        "options": [
                            {
                                "value": "skill",
                                "label_key": "forms.group.fields.type.options.skill",
                            },
                            {
                                "value": "org",
                                "label_key": "forms.group.fields.type.options.org",
                            },
                            {
                                "value": "notification",
                                "label_key": "forms.group.fields.type.options.notification",
                            },
                        ],
                        "placeholder_key": "forms.group.fields.type.placeholder",
                        "help_text_key": "forms.group.fields.type.help_text",
                        "label_key": "forms.group.fields.type.label",
                        "order": 3,
                        "tab_id": "general",
                        "validation": {"required": False},
                    },
                    "contain_users": {
                        "widget": "checkbox",
                        "label_key": "forms.group.fields.contain_users.label",
                        "help_text_key": "forms.group.fields.contain_users.help_text",
                        "order": 4,
                        "tab_id": "general",
                        "validation": {"required": False},
                    },
                    "contain_items": {
                        "widget": "checkbox",
                        "label_key": "forms.group.fields.contain_items.label",
                        "help_text_key": "forms.group.fields.contain_items.help_text",
                        "order": 5,
                        "tab_id": "general",
                        "validation": {"required": False},
                    },
                    "comment": {
                        "widget": "textarea",
                        "placeholder_key": "forms.group.fields.comment.placeholder",
                        "help_text_key": "forms.group.fields.comment.help_text",
                        "label_key": "forms.group.fields.comment.label",
                        "order": 6,
                        "tab_id": "general",
                        "validation": {"required": False},
                    },
                    "parent_id": {
                        "widget": "select",
                        "options": parent_group_options,
                        "quick_create_resource": "group",
                        "placeholder_key": "forms.group.fields.parent_id.placeholder",
                        "help_text_key": "forms.group.fields.parent_id.help_text",
                        "label_key": "forms.group.fields.parent_id.label",
                        "order": 7,
                        "tab_id": "general",
                        "validation": {"required": False},
                    },
                    # Users tab
                    "users": {
                        "widget": "relationship",
                        "multiple": True,
                        "quick_create_resource": "user",
                        "placeholder_key": "forms.group.fields.users.placeholder",
                        "help_text_key": "forms.group.fields.users.help_text",
                        "label_key": "forms.group.fields.users.label",
                        "order": 1,
                        "tab_id": "users",
                        "validation": {"required": False},
                    },
                    # Assets tab
                    "assets": {
                        "widget": "relationship",
                        "multiple": True,
                        "placeholder_key": "forms.group.fields.assets.placeholder",
                        "help_text_key": "forms.group.fields.assets.help_text",
                        "label_key": "forms.group.fields.assets.label",
                        "order": 1,
                        "tab_id": "assets",
                        "validation": {"required": False},
                    },
                },
            },
        }

        return enhanced_schema

    def _get_computer_edit_schema(self) -> Dict[str, Any]:
        """
        Generate JSON edit schema for computer asset resource.
        """
        from app.schemas.asset import \
            ComputerUpdate  # Local import to avoid circular

        base_schema = ComputerUpdate.model_json_schema()

        # Define tabs
        tabs = [
            {"id": "general", "label_key": "forms.tabs.general"},
            {"id": "security", "label_key": "forms.tabs.security"},
            {"id": "specifications", "label_key": "forms.tabs.specifications"},
            {"id": "network", "label_key": "forms.tabs.network"},
            {"id": "groups", "label_key": "forms.tabs.groups"},
        ]

        enhanced_schema = {
            "version": "1.0.0",
            "resource_type": "computer",
            "schema_type": "edit",
            "schema": base_schema,
            "ui": {
                "title_key": "forms.computer.edit.title",
                "description_key": "forms.computer.edit.description",
                "tabs": tabs,
                "fields": {
                    # General tab
                    "name": {
                        "widget": "text",
                        "placeholder_key": "forms.computer.fields.name.placeholder",
                        "help_text_key": "forms.computer.fields.name.help_text",
                        "label_key": "forms.computer.fields.name.label",
                        "order": 1,
                        "tab_id": "general",
                        "validation": {"required": False},
                    },
                    "serial_number": {
                        "widget": "text",
                        "placeholder_key": "forms.computer.fields.serial_number.placeholder",
                        "help_text_key": "forms.computer.fields.serial_number.help_text",
                        "label_key": "forms.computer.fields.serial_number.label",
                        "order": 2,
                        "tab_id": "general",
                        "validation": {"required": False},
                    },
                    "inventory_number": {
                        "widget": "text",
                        "placeholder_key": "forms.computer.fields.inventory_number.placeholder",
                        "help_text_key": "forms.computer.fields.inventory_number.help_text",
                        "label_key": "forms.computer.fields.inventory_number.label",
                        "order": 3,
                        "tab_id": "general",
                        "validation": {"required": False},
                    },
                    "assigned_to": {
                        "widget": "select",
                        "quick_create_resource": "user",
                        "placeholder_key": "forms.computer.fields.assigned_to.placeholder",
                        "help_text_key": "forms.computer.fields.assigned_to.help_text",
                        "label_key": "forms.computer.fields.assigned_to.label",
                        "order": 4,
                        "tab_id": "general",
                        "validation": {"required": False},
                    },
                    "status": {
                        "widget": "select",
                        "options": [
                            {
                                "value": "active",
                                "label_key": "forms.computer.fields.status.options.active",
                            },
                            {
                                "value": "inactive",
                                "label_key": "forms.computer.fields.status.options.inactive",
                            },
                            {
                                "value": "maintenance",
                                "label_key": "forms.computer.fields.status.options.maintenance",
                            },
                            {
                                "value": "retired",
                                "label_key": "forms.computer.fields.status.options.retired",
                            },
                        ],
                        "placeholder_key": "forms.computer.fields.status.placeholder",
                        "help_text_key": "forms.computer.fields.status.help_text",
                        "label_key": "forms.computer.fields.status.label",
                        "order": 5,
                        "tab_id": "general",
                        "validation": {"required": False},
                    },
                    "purchase_date": {
                        "widget": "date",
                        "placeholder_key": "forms.computer.fields.purchase_date.placeholder",
                        "help_text_key": "forms.computer.fields.purchase_date.help_text",
                        "label_key": "forms.computer.fields.purchase_date.label",
                        "order": 6,
                        "tab_id": "general",
                        "validation": {"required": False},
                    },
                    "warranty_expiry": {
                        "widget": "date",
                        "placeholder_key": "forms.computer.fields.warranty_expiry.placeholder",
                        "help_text_key": "forms.computer.fields.warranty_expiry.help_text",
                        "label_key": "forms.computer.fields.warranty_expiry.label",
                        "order": 7,
                        "tab_id": "general",
                        "validation": {"required": False},
                    },
                    "manufacturer_id": {
                        "widget": "select",
                        "quick_create_resource": "manufacturer",
                        "placeholder_key": "forms.computer.fields.manufacturer_id.placeholder",
                        "help_text_key": "forms.computer.fields.manufacturer_id.help_text",
                        "label_key": "forms.computer.fields.manufacturer_id.label",
                        "order": 8,
                        "tab_id": "general",
                        "validation": {"required": False},
                    },
                    "location_id": {
                        "widget": "select",
                        "quick_create_resource": "location",
                        "placeholder_key": "forms.computer.fields.location_id.placeholder",
                        "help_text_key": "forms.computer.fields.location_id.help_text",
                        "label_key": "forms.computer.fields.location_id.label",
                        "order": 9,
                        "tab_id": "general",
                        "validation": {"required": False},
                    },
                    # Security tab
                    "confidentiality_level": {
                        "widget": "select",
                        "options": [
                            {
                                "value": "Public",
                                "label_key": "forms.computer.fields.confidentiality_level.options.Public",
                            },
                            {
                                "value": "Internal",
                                "label_key": "forms.computer.fields.confidentiality_level.options.Internal",
                            },
                            {
                                "value": "Confidential",
                                "label_key": "forms.computer.fields.confidentiality_level.options.Confidential",
                            },
                            {
                                "value": "Secret",
                                "label_key": "forms.computer.fields.confidentiality_level.options.Secret",
                            },
                        ],
                        "placeholder_key": "forms.computer.fields.confidentiality_level.placeholder",
                        "help_text_key": "forms.computer.fields.confidentiality_level.help_text",
                        "label_key": "forms.computer.fields.confidentiality_level.label",
                        "order": 1,
                        "tab_id": "security",
                        "validation": {"required": False},
                    },
                    "integrity_level": {
                        "widget": "select",
                        "options": [
                            {
                                "value": "High",
                                "label_key": "forms.computer.fields.integrity_level.options.High",
                            },
                            {
                                "value": "Medium",
                                "label_key": "forms.computer.fields.integrity_level.options.Medium",
                            },
                            {
                                "value": "Low",
                                "label_key": "forms.computer.fields.integrity_level.options.Low",
                            },
                        ],
                        "placeholder_key": "forms.computer.fields.integrity_level.placeholder",
                        "help_text_key": "forms.computer.fields.integrity_level.help_text",
                        "label_key": "forms.computer.fields.integrity_level.label",
                        "order": 2,
                        "tab_id": "security",
                        "validation": {"required": False},
                    },
                    "availability_level": {
                        "widget": "select",
                        "options": [
                            {
                                "value": "High",
                                "label_key": "forms.computer.fields.availability_level.options.High",
                            },
                            {
                                "value": "Medium",
                                "label_key": "forms.computer.fields.availability_level.options.Medium",
                            },
                            {
                                "value": "Low",
                                "label_key": "forms.computer.fields.availability_level.options.Low",
                            },
                        ],
                        "placeholder_key": "forms.computer.fields.availability_level.placeholder",
                        "help_text_key": "forms.computer.fields.availability_level.help_text",
                        "label_key": "forms.computer.fields.availability_level.label",
                        "order": 3,
                        "tab_id": "security",
                        "validation": {"required": False},
                    },
                    # Specifications tab
                    "model": {
                        "widget": "text",
                        "placeholder_key": "forms.computer.fields.model.placeholder",
                        "help_text_key": "forms.computer.fields.model.help_text",
                        "label_key": "forms.computer.fields.model.label",
                        "order": 1,
                        "tab_id": "specifications",
                        "validation": {"required": False},
                    },
                    "cpu": {
                        "widget": "text",
                        "placeholder_key": "forms.computer.fields.cpu.placeholder",
                        "help_text_key": "forms.computer.fields.cpu.help_text",
                        "label_key": "forms.computer.fields.cpu.label",
                        "order": 2,
                        "tab_id": "specifications",
                        "validation": {"required": False},
                    },
                    "ram": {
                        "widget": "text",
                        "placeholder_key": "forms.computer.fields.ram.placeholder",
                        "help_text_key": "forms.computer.fields.ram.help_text",
                        "label_key": "forms.computer.fields.ram.label",
                        "order": 3,
                        "tab_id": "specifications",
                        "validation": {"required": False},
                    },
                    "storage": {
                        "widget": "text",
                        "placeholder_key": "forms.computer.fields.storage.placeholder",
                        "help_text_key": "forms.computer.fields.storage.help_text",
                        "label_key": "forms.computer.fields.storage.label",
                        "order": 4,
                        "tab_id": "specifications",
                        "validation": {"required": False},
                    },
                    "os": {
                        "widget": "text",
                        "placeholder_key": "forms.computer.fields.os.placeholder",
                        "help_text_key": "forms.computer.fields.os.help_text",
                        "label_key": "forms.computer.fields.os.label",
                        "order": 5,
                        "tab_id": "specifications",
                        "validation": {"required": False},
                    },
                    # Network tab
                    "hostname": {
                        "widget": "text",
                        "placeholder_key": "forms.computer.fields.hostname.placeholder",
                        "help_text_key": "forms.computer.fields.hostname.help_text",
                        "label_key": "forms.computer.fields.hostname.label",
                        "order": 1,
                        "tab_id": "network",
                        "validation": {"required": False},
                    },
                    "ip_address": {
                        "widget": "text",
                        "placeholder_key": "forms.computer.fields.ip_address.placeholder",
                        "help_text_key": "forms.computer.fields.ip_address.help_text",
                        "label_key": "forms.computer.fields.ip_address.label",
                        "order": 2,
                        "tab_id": "network",
                        "validation": {"required": False},
                    },
                    "mac_address": {
                        "widget": "text",
                        "placeholder_key": "forms.computer.fields.mac_address.placeholder",
                        "help_text_key": "forms.computer.fields.mac_address.help_text",
                        "label_key": "forms.computer.fields.mac_address.label",
                        "order": 3,
                        "tab_id": "network",
                        "validation": {"required": False},
                    },
                    # Relationships tab
                    "groups": {
                        "widget": "relationship",
                        "quick_create_resource": "group",
                        "placeholder_key": "forms.computer.fields.group_id.placeholder",
                        "help_text_key": "forms.computer.fields.group_id.help_text",
                        "label_key": "forms.computer.fields.group_id.label",
                        "order": 1,
                        "tab_id": "groups",
                        "validation": {"required": False},
                    },
                },
            },
        }

        return enhanced_schema

    def get_available_resources(self) -> Dict[str, Any]:
        """
        Get list of available resource types that the user has create permission for.
        """
        logger.info(
            f"User {self.current_user.id} attempts to GET available resources at {datetime.now(timezone.utc).isoformat()}"
        )

        available_resources = []

        # Check each resource type for create permission
        resource_types = ["group", "user", "role", "asset", "reference_data"]

        for resource_type in resource_types:
            if has_permission(self.current_user, "create", resource_type):
                available_resources.append(
                    {
                        "type": resource_type,
                        "name_key": f"resources.{resource_type}.name",
                        "description_key": f"resources.{resource_type}.description",
                    }
                )

        logger.info(f"User {self.current_user.id} successfully got available resources")

        return {"version": "1.0.0", "available_resources": available_resources}

    def _get_parent_group_options(self) -> List[Dict[str, Any]]:
        """
        Get available parent groups for the select dropdown.
        """
        try:
            from app.db.crud.group import list_groups

            groups = list_groups(self.db, skip=0, limit=1000)
            options: List[Dict[str, Any]] = [
                {
                    "value": "",
                    "label_key": "forms.group.fields.parent_id.options.no_parent",
                }
            ]

            for group in groups:
                group_type = group.type or "no_type"
                options.append(
                    {
                        "value": str(group.id),
                        "label_key": "forms.group.fields.parent_id.options.group_with_type",
                        "label_params": {"name": group.name, "type": group_type},
                    }
                )

            return options
        except Exception as e:
            logger.warning(f"Failed to fetch parent group options: {e}")
            return [
                {
                    "value": "",
                    "label_key": "forms.group.fields.parent_id.options.no_parent",
                }
            ]

    def _get_group_options(self) -> List[Dict[str, Any]]:
        """
        Get available groups for the multi-select relationship field.
        """
        try:
            from app.db.crud.group import list_groups

            groups = list_groups(self.db, skip=0, limit=1000)
            options: List[Dict[str, Any]] = []

            for group in groups:
                options.append(
                    {
                        "value": str(group.id),
                        "label_key": "forms.user.fields.groups.options.group_name",
                        "label_params": {"name": group.name},
                    }
                )

            return options
        except Exception as e:
            logger.warning(f"Failed to fetch group options: {e}")
            return []

    def _get_manufacturer_options(self) -> List[Dict[str, Any]]:
        """
        Get available manufacturers for the single manufacturer select dropdown.
        """
        try:
            from app.services.reference_data_service import \
                ReferenceDataService

            reference_data_service = ReferenceDataService(self.db, self.current_user)
            manufacturers = reference_data_service.list_manufacturers(limit=1000)
            options = []

            for manufacturer in manufacturers:
                options.append(
                    {
                        "value": str(manufacturer.id),
                        "label_key": "forms.user.fields.manufacturer_id.options.manufacturer_name",
                        "label_params": {
                            "name": manufacturer.name,
                            "description": getattr(manufacturer, "description", "")
                            or "",
                        },
                    }
                )

            return options
        except Exception as e:
            logger.warning(f"Failed to fetch manufacturer options: {e}")
            return []

    def _get_location_options(self) -> List[Dict[str, Any]]:
        """
        Get available locations for the single location select dropdown.
        """
        try:
            from app.services.reference_data_service import \
                ReferenceDataService

            reference_data_service = ReferenceDataService(self.db, self.current_user)
            locations = reference_data_service.list_locations(limit=1000)
            options = []

            for location in locations:
                options.append(
                    {
                        "value": str(location.id),
                        "label_key": "forms.user.fields.location_id.options.location_name",
                        "label_params": {
                            "name": location.name,
                            "description": getattr(location, "description", "") or "",
                        },
                    }
                )

            return options
        except Exception as e:
            logger.warning(f"Failed to fetch location options: {e}")
            return []

    def _get_role_options(self) -> List[Dict[str, Any]]:
        """
        Get available roles for the single role select dropdown.
        """
        try:
            from app.db.crud.role import list_roles

            roles = list_roles(self.db, skip=0, limit=1000)
            options = []

            for role in roles:
                options.append(
                    {
                        "value": str(role.id),
                        "label_key": "forms.user.fields.role_id.options.role_name",
                        "label_params": {
                            "name": role.name,
                            "description": role.description or "",
                        },
                    }
                )

            return options
        except Exception as e:
            logger.warning(f"Failed to fetch role options: {e}")
            return []
