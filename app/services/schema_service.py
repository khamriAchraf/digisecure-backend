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
            "virtual_machine": self._get_virtual_machine_schema(),
            "network_device": self._get_network_device_schema(),
            "software": self._get_software_schema(),
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
            "virtual_machine": self._get_virtual_machine_edit_schema(),
            "network_device": self._get_network_device_edit_schema(),
            "software": self._get_software_edit_schema(),
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
                        "label_key": "forms.group.fields.type.label",
                        "order": 3,
                        "validation": {"required": False},
                    },
                    "contain_users": {
                        "widget": "checkbox",
                        "label_key": "forms.group.fields.contain_users.label",
                        "order": 5,
                        "validation": {"required": False, "default": True},
                    },
                    "contain_items": {
                        "widget": "checkbox",
                        "label_key": "forms.group.fields.contain_items.label",
                        "order": 3,
                        "validation": {"required": False, "default": True},
                    },
                    "comment": {
                        "widget": "textarea",
                        "placeholder_key": "forms.group.fields.comment.placeholder",
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
                        "label_key": "forms.user.fields.theme.label",
                        "order": 7,
                        "validation": {"required": False, "default": "light"},
                    },
                    "location": {
                        "widget": "text",
                        "placeholder_key": "forms.user.fields.location.placeholder",
                        "label_key": "forms.user.fields.location.label",
                        "order": 8,
                        "validation": {"required": False},
                    },
                    "phone": {
                        "widget": "tel",
                        "placeholder_key": "forms.user.fields.phone.placeholder",
                        "label_key": "forms.user.fields.phone.label",
                        "order": 9,
                        "validation": {"required": False},
                    },
                    "secondary_phone": {
                        "widget": "tel",
                        "placeholder_key": "forms.user.fields.secondary_phone.placeholder",
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
                        "label_key": "forms.user.fields.timezone.label",
                        "order": 11,
                        "validation": {"required": False},
                    },
                    "valid_from": {
                        "widget": "datetime-local",
                        "placeholder_key": "forms.user.fields.valid_from.placeholder",
                        "label_key": "forms.user.fields.valid_from.label",
                        "order": 12,
                        "validation": {"required": False},
                    },
                    "valid_until": {
                        "widget": "datetime-local",
                        "placeholder_key": "forms.user.fields.valid_until.placeholder",
                        "label_key": "forms.user.fields.valid_until.label",
                        "order": 13,
                        "validation": {"required": False},
                    },
                    "administartive_number": {
                        "widget": "text",
                        "placeholder_key": "forms.user.fields.administartive_number.placeholder",
                        "label_key": "forms.user.fields.administartive_number.label",
                        "order": 14,
                        "validation": {"required": False},
                    },
                    "role_id": {
                        "widget": "select",
                        "quick_create_resource": "role",
                        "placeholder_key": "forms.user.fields.role_id.placeholder",
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
                        "label_key": "forms.computer.fields.serial_number.label",
                        "order": 2,
                        "validation": {"required": False},
                    },
                    "inventory_number": {
                        "widget": "text",
                        "placeholder_key": "forms.computer.fields.inventory_number.placeholder",
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
                        "label_key": "forms.computer.fields.status.label",
                        "order": 4,
                        "validation": {"required": True, "default": "active"},
                    },
                    "purchase_date": {
                        "widget": "date",
                        "placeholder_key": "forms.computer.fields.purchase_date.placeholder",
                        "label_key": "forms.computer.fields.purchase_date.label",
                        "order": 5,
                        "validation": {"required": False},
                    },
                    "warranty_expiry": {
                        "widget": "date",
                        "placeholder_key": "forms.computer.fields.warranty_expiry.placeholder",
                        "label_key": "forms.computer.fields.warranty_expiry.label",
                        "order": 6,
                        "validation": {"required": False},
                    },
                    "model": {
                        "widget": "text",
                        "placeholder_key": "forms.computer.fields.model.placeholder",
                        "label_key": "forms.computer.fields.model.label",
                        "order": 7,
                        "validation": {"required": False},
                    },
                    "cpu": {
                        "widget": "text",
                        "placeholder_key": "forms.computer.fields.cpu.placeholder",
                        "label_key": "forms.computer.fields.cpu.label",
                        "order": 8,
                        "validation": {"required": False},
                    },
                    "ram": {
                        "widget": "text",
                        "placeholder_key": "forms.computer.fields.ram.placeholder",
                        "label_key": "forms.computer.fields.ram.label",
                        "order": 9,
                        "validation": {"required": False},
                    },
                    "storage": {
                        "widget": "text",
                        "placeholder_key": "forms.computer.fields.storage.placeholder",
                        "label_key": "forms.computer.fields.storage.label",
                        "order": 10,
                        "validation": {"required": False},
                    },
                    "os": {
                        "widget": "text",
                        "placeholder_key": "forms.computer.fields.os.placeholder",
                        "label_key": "forms.computer.fields.os.label",
                        "order": 11,
                        "validation": {"required": False},
                    },
                    "hostname": {
                        "widget": "text",
                        "placeholder_key": "forms.computer.fields.hostname.placeholder",
                        "label_key": "forms.computer.fields.hostname.label",
                        "order": 12,
                        "validation": {"required": False},
                    },
                    "ip_address": {
                        "widget": "text",
                        "placeholder_key": "forms.computer.fields.ip_address.placeholder",
                        "label_key": "forms.computer.fields.ip_address.label",
                        "order": 13,
                        "validation": {"required": False},
                    },
                    "mac_address": {
                        "widget": "text",
                        "placeholder_key": "forms.computer.fields.mac_address.placeholder",
                        "label_key": "forms.computer.fields.mac_address.label",
                        "order": 14,
                        "validation": {"required": False},
                    },
                    "manufacturer_id": {
                        "widget": "select",
                        "options": available_manufacturers,
                        "quick_create_resource": "manufacturer",
                        "placeholder_key": "forms.computer.fields.manufacturer_id.placeholder",
                        "label_key": "forms.computer.fields.manufacturer_id.label",
                        "order": 15,
                        "validation": {"required": False},
                    },
                    "location_id": {
                        "widget": "select",
                        "options": available_locations,
                        "quick_create_resource": "location",
                        "placeholder_key": "forms.computer.fields.location_id.placeholder",
                        "label_key": "forms.computer.fields.location_id.label",
                        "order": 16,
                        "validation": {"required": False},
                    },
                },
            },
        }
        return enhanced_schema

    def _get_virtual_machine_schema(self) -> Dict[str, Any]:
        """
        Generate JSON schema for virtual machine resource creation.
        """
        from app.schemas.asset import \
            VirtualMachineCreate  # Local import to avoid circular

        # Get the base schema from Pydantic
        base_schema = VirtualMachineCreate.model_json_schema()
        available_manufacturers = self._get_manufacturer_options()
        available_locations = self._get_location_options()
        # Enhance the schema with additional metadata
        enhanced_schema = {
            "version": "1.0.0",
            "resource_type": "virtual_machine",
            "schema": base_schema,
            "ui": {
                "title_key": "forms.virtual_machine.create.title",
                "description_key": "forms.virtual_machine.create.description",
                "fields": {
                    "name": {
                        "widget": "text",
                        "placeholder_key": "forms.virtual_machine.fields.name.placeholder",
                        "label_key": "forms.virtual_machine.fields.name.label",
                        "order": 1,
                        "validation": {
                            "required": True,
                            "error_messages": {
                                "required": "forms.virtual_machine.fields.name.errors.required"
                            },
                        },
                    },
                    "serial_number": {
                        "widget": "text",
                        "placeholder_key": "forms.virtual_machine.fields.serial_number.placeholder",
                        "label_key": "forms.virtual_machine.fields.serial_number.label",
                        "order": 2,
                        "validation": {"required": False},
                    },
                    "inventory_number": {
                        "widget": "text",
                        "placeholder_key": "forms.virtual_machine.fields.inventory_number.placeholder",
                        "label_key": "forms.virtual_machine.fields.inventory_number.label",
                        "order": 3,
                        "validation": {"required": False},
                    },
                    "status": {
                        "widget": "select",
                        "options": [
                            {
                                "value": "active",
                                "label_key": "forms.virtual_machine.fields.status.options.active",
                            },
                            {
                                "value": "inactive",
                                "label_key": "forms.virtual_machine.fields.status.options.inactive",
                            },
                            {
                                "value": "maintenance",
                                "label_key": "forms.virtual_machine.fields.status.options.maintenance",
                            },
                            {
                                "value": "retired",
                                "label_key": "forms.virtual_machine.fields.status.options.retired",
                            },
                        ],
                        "placeholder_key": "forms.virtual_machine.fields.status.placeholder",
                        "label_key": "forms.virtual_machine.fields.status.label",
                        "order": 4,
                        "validation": {"required": True, "default": "active"},
                    },
                    "purchase_date": {
                        "widget": "date",
                        "placeholder_key": "forms.virtual_machine.fields.purchase_date.placeholder",
                        "label_key": "forms.virtual_machine.fields.purchase_date.label",
                        "order": 5,
                        "validation": {"required": False},
                    },
                    "warranty_expiry": {
                        "widget": "date",
                        "placeholder_key": "forms.virtual_machine.fields.warranty_expiry.placeholder",
                        "label_key": "forms.virtual_machine.fields.warranty_expiry.label",
                        "order": 6,
                        "validation": {"required": False},
                    },
                    "model": {
                        "widget": "text",
                        "placeholder_key": "forms.virtual_machine.fields.model.placeholder",
                        "label_key": "forms.virtual_machine.fields.model.label",
                        "order": 7,
                        "validation": {"required": False},
                    },
                    "cpu": {
                        "widget": "text",
                        "placeholder_key": "forms.virtual_machine.fields.cpu.placeholder",
                        "label_key": "forms.virtual_machine.fields.cpu.label",
                        "order": 8,
                        "validation": {"required": False},
                    },
                    "ram": {
                        "widget": "text",
                        "placeholder_key": "forms.virtual_machine.fields.ram.placeholder",
                        "label_key": "forms.virtual_machine.fields.ram.label",
                        "order": 9,
                        "validation": {"required": False},
                    },
                    "storage": {
                        "widget": "text",
                        "placeholder_key": "forms.virtual_machine.fields.storage.placeholder",
                        "label_key": "forms.virtual_machine.fields.storage.label",
                        "order": 10,
                        "validation": {"required": False},
                    },
                    "os": {
                        "widget": "text",
                        "placeholder_key": "forms.virtual_machine.fields.os.placeholder",
                        "label_key": "forms.virtual_machine.fields.os.label",
                        "order": 11,
                        "validation": {"required": False},
                    },
                    "hostname": {
                        "widget": "text",
                        "placeholder_key": "forms.virtual_machine.fields.hostname.placeholder",
                        "label_key": "forms.virtual_machine.fields.hostname.label",
                        "order": 12,
                        "validation": {"required": False},
                    },
                    "ip_address": {
                        "widget": "text",
                        "placeholder_key": "forms.virtual_machine.fields.ip_address.placeholder",
                        "label_key": "forms.virtual_machine.fields.ip_address.label",
                        "order": 13,
                        "validation": {"required": False},
                    },
                    "mac_address": {
                        "widget": "text",
                        "placeholder_key": "forms.virtual_machine.fields.mac_address.placeholder",
                        "label_key": "forms.virtual_machine.fields.mac_address.label",
                        "order": 14,
                        "validation": {"required": False},
                    },
                    "manufacturer_id": {
                        "widget": "select",
                        "options": available_manufacturers,
                        "quick_create_resource": "manufacturer",
                        "placeholder_key": "forms.virtual_machine.fields.manufacturer_id.placeholder",
                        "label_key": "forms.virtual_machine.fields.manufacturer_id.label",
                        "order": 15,
                        "validation": {"required": False},
                    },
                    "location_id": {
                        "widget": "select",
                        "options": available_locations,
                        "quick_create_resource": "location",
                        "placeholder_key": "forms.virtual_machine.fields.location_id.placeholder",
                        "label_key": "forms.virtual_machine.fields.location_id.label",
                        "order": 16,
                        "validation": {"required": False},
                    },
                },
            },
        }
        return enhanced_schema

    def _get_network_device_schema(self) -> Dict[str, Any]:
        """
        Generate JSON schema for network device resource creation.
        """
        from app.schemas.asset import \
            NetworkDeviceCreate  # Local import to avoid circular

        # Get the base schema from Pydantic
        base_schema = NetworkDeviceCreate.model_json_schema()
        available_manufacturers = self._get_manufacturer_options()
        available_locations = self._get_location_options()
        # Enhance the schema with additional metadata
        enhanced_schema = {
            "version": "1.0.0",
            "resource_type": "network_device",
            "schema": base_schema,
            "ui": {
                "title_key": "forms.network_device.create.title",
                "description_key": "forms.network_device.create.description",
                "fields": {
                    "name": {
                        "widget": "text",
                        "placeholder_key": "forms.network_device.fields.name.placeholder",
                        "label_key": "forms.network_device.fields.name.label",
                        "order": 1,
                        "validation": {
                            "required": True,
                            "error_messages": {
                                "required": "forms.network_device.fields.name.errors.required"
                            },
                        },
                    },
                    "serial_number": {
                        "widget": "text",
                        "placeholder_key": "forms.network_device.fields.serial_number.placeholder",
                        "label_key": "forms.network_device.fields.serial_number.label",
                        "order": 2,
                        "validation": {"required": False},
                    },
                    "inventory_number": {
                        "widget": "text",
                        "placeholder_key": "forms.network_device.fields.inventory_number.placeholder",
                        "label_key": "forms.network_device.fields.inventory_number.label",
                        "order": 3,
                        "validation": {"required": False},
                    },
                    "status": {
                        "widget": "select",
                        "options": [
                            {
                                "value": "active",
                                "label_key": "forms.network_device.fields.status.options.active",
                            },
                            {
                                "value": "inactive",
                                "label_key": "forms.network_device.fields.status.options.inactive",
                            },
                            {
                                "value": "maintenance",
                                "label_key": "forms.network_device.fields.status.options.maintenance",
                            },
                            {
                                "value": "retired",
                                "label_key": "forms.network_device.fields.status.options.retired",
                            },
                        ],
                        "placeholder_key": "forms.network_device.fields.status.placeholder",
                        "label_key": "forms.network_device.fields.status.label",
                        "order": 4,
                        "validation": {"required": True, "default": "active"},
                    },
                    "device_type": {
                        "widget": "select",
                        "options": [
                            {
                                "value": "Switch",
                                "label_key": "forms.network_device.fields.device_type.options.switch",
                            },
                            {
                                "value": "Router",
                                "label_key": "forms.network_device.fields.device_type.options.router",
                            },
                            {
                                "value": "Access Point",
                                "label_key": "forms.network_device.fields.device_type.options.access_point",
                            },
                            {
                                "value": "Firewall",
                                "label_key": "forms.network_device.fields.device_type.options.firewall",
                            },
                        ],
                        "placeholder_key": "forms.network_device.fields.device_type.placeholder",
                        "label_key": "forms.network_device.fields.device_type.label",
                        "order": 5,
                        "validation": {"required": False},
                    },
                    "model": {
                        "widget": "text",
                        "placeholder_key": "forms.network_device.fields.model.placeholder",
                        "label_key": "forms.network_device.fields.model.label",
                        "order": 6,
                        "validation": {"required": False},
                    },
                    "manufacturer_id": {
                        "widget": "select",
                        "options": available_manufacturers,
                        "quick_create_resource": "manufacturer",
                        "placeholder_key": "forms.network_device.fields.manufacturer_id.placeholder",
                        "label_key": "forms.network_device.fields.manufacturer_id.label",
                        "order": 7,
                        "validation": {"required": False},
                    },
                    "location_id": {
                        "widget": "select",
                        "options": available_locations,
                        "quick_create_resource": "location",
                        "placeholder_key": "forms.network_device.fields.location_id.placeholder",
                        "label_key": "forms.network_device.fields.location_id.label",
                        "order": 8,
                        "validation": {"required": False},
                    },
                    "purchase_date": {
                        "widget": "date",
                        "placeholder_key": "forms.network_device.fields.purchase_date.placeholder",
                        "label_key": "forms.network_device.fields.purchase_date.label",
                        "order": 9,
                        "validation": {"required": False},
                    },
                    "warranty_expiry": {
                        "widget": "date",
                        "placeholder_key": "forms.network_device.fields.warranty_expiry.placeholder",
                        "label_key": "forms.network_device.fields.warranty_expiry.label",
                        "order": 10,
                        "validation": {"required": False},
                    },
                    "ip_address": {
                        "widget": "text",
                        "placeholder_key": "forms.network_device.fields.ip_address.placeholder",
                        "label_key": "forms.network_device.fields.ip_address.label",
                        "order": 11,
                        "validation": {"required": False},
                    },
                    "management_ip": {
                        "widget": "text",
                        "placeholder_key": "forms.network_device.fields.management_ip.placeholder",
                        "label_key": "forms.network_device.fields.management_ip.label",
                        "order": 12,
                        "validation": {"required": False},
                    },
                    "mac_address": {
                        "widget": "text",
                        "placeholder_key": "forms.network_device.fields.mac_address.placeholder",
                        "label_key": "forms.network_device.fields.mac_address.label",
                        "order": 13,
                        "validation": {"required": False},
                    },
                    "port_count": {
                        "widget": "number",
                        "placeholder_key": "forms.network_device.fields.port_count.placeholder",
                        "label_key": "forms.network_device.fields.port_count.label",
                        "order": 14,
                        "validation": {"required": False},
                    },
                    "connection_type": {
                        "widget": "select",
                        "options": [
                            {
                                "value": "Ethernet",
                                "label_key": "forms.network_device.fields.connection_type.options.ethernet",
                            },
                            {
                                "value": "WiFi",
                                "label_key": "forms.network_device.fields.connection_type.options.wifi",
                            },
                            {
                                "value": "Fiber",
                                "label_key": "forms.network_device.fields.connection_type.options.fiber",
                            },
                        ],
                        "placeholder_key": "forms.network_device.fields.connection_type.placeholder",
                        "label_key": "forms.network_device.fields.connection_type.label",
                        "order": 15,
                        "validation": {"required": False},
                    },
                    "firmware_version": {
                        "widget": "text",
                        "placeholder_key": "forms.network_device.fields.firmware_version.placeholder",
                        "label_key": "forms.network_device.fields.firmware_version.label",
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
                        "label_key": "forms.user.fields.email.label",
                        "order": 1,
                        "tab_id": "general",
                        "validation": {"required": False},
                    },
                    "username": {
                        "widget": "text",
                        "placeholder_key": "forms.user.fields.username.placeholder",
                        "label_key": "forms.user.fields.username.label",
                        "order": 2,
                        "tab_id": "general",
                        "validation": {"required": False},
                    },
                    "full_name": {
                        "widget": "text",
                        "placeholder_key": "forms.user.fields.full_name.placeholder",
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
                        "label_key": "forms.group.fields.name.label",
                        "order": 1,
                        "tab_id": "general",
                        "validation": {"required": False},
                    },
                    "description": {
                        "widget": "textarea",
                        "placeholder_key": "forms.group.fields.description.placeholder",
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
                        "label_key": "forms.group.fields.type.label",
                        "order": 3,
                        "tab_id": "general",
                        "validation": {"required": False},
                    },
                    "contain_users": {
                        "widget": "checkbox",
                        "label_key": "forms.group.fields.contain_users.label",
                        "order": 4,
                        "tab_id": "general",
                        "validation": {"required": False},
                    },
                    "contain_items": {
                        "widget": "checkbox",
                        "label_key": "forms.group.fields.contain_items.label",
                        "order": 5,
                        "tab_id": "general",
                        "validation": {"required": False},
                    },
                    "comment": {
                        "widget": "textarea",
                        "placeholder_key": "forms.group.fields.comment.placeholder",
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
            {"id": "compliance", "label_key": "forms.tabs.compliance"},
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
                        "label_key": "forms.computer.fields.name.label",
                        "order": 1,
                        "tab_id": "general",
                        "validation": {"required": False},
                    },
                    "serial_number": {
                        "widget": "text",
                        "placeholder_key": "forms.computer.fields.serial_number.placeholder",
                        "label_key": "forms.computer.fields.serial_number.label",
                        "order": 2,
                        "tab_id": "general",
                        "validation": {"required": False},
                    },
                    "inventory_number": {
                        "widget": "text",
                        "placeholder_key": "forms.computer.fields.inventory_number.placeholder",
                        "label_key": "forms.computer.fields.inventory_number.label",
                        "order": 3,
                        "tab_id": "general",
                        "validation": {"required": False},
                    },
                    "assigned_to": {
                        "widget": "select",
                        "quick_create_resource": "user",
                        "placeholder_key": "forms.computer.fields.assigned_to.placeholder",
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
                        "label_key": "forms.computer.fields.status.label",
                        "order": 5,
                        "tab_id": "general",
                        "validation": {"required": False},
                    },
                    "purchase_date": {
                        "widget": "date",
                        "placeholder_key": "forms.computer.fields.purchase_date.placeholder",
                        "label_key": "forms.computer.fields.purchase_date.label",
                        "order": 6,
                        "tab_id": "general",
                        "validation": {"required": False},
                    },
                    "warranty_expiry": {
                        "widget": "date",
                        "placeholder_key": "forms.computer.fields.warranty_expiry.placeholder",
                        "label_key": "forms.computer.fields.warranty_expiry.label",
                        "order": 7,
                        "tab_id": "general",
                        "validation": {"required": False},
                    },
                    "manufacturer_id": {
                        "widget": "select",
                        "quick_create_resource": "manufacturer",
                        "placeholder_key": "forms.computer.fields.manufacturer_id.placeholder",
                        "label_key": "forms.computer.fields.manufacturer_id.label",
                        "order": 8,
                        "tab_id": "general",
                        "validation": {"required": False},
                    },
                    "location_id": {
                        "widget": "select",
                        "quick_create_resource": "location",
                        "placeholder_key": "forms.computer.fields.location_id.placeholder",
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
                        "label_key": "forms.computer.fields.availability_level.label",
                        "order": 3,
                        "tab_id": "security",
                        "validation": {"required": False},
                    },
                    # Specifications tab
                    "model": {
                        "widget": "text",
                        "placeholder_key": "forms.computer.fields.model.placeholder",
                        "label_key": "forms.computer.fields.model.label",
                        "order": 1,
                        "tab_id": "specifications",
                        "validation": {"required": False},
                    },
                    "cpu": {
                        "widget": "text",
                        "placeholder_key": "forms.computer.fields.cpu.placeholder",
                        "label_key": "forms.computer.fields.cpu.label",
                        "order": 2,
                        "tab_id": "specifications",
                        "validation": {"required": False},
                    },
                    "ram": {
                        "widget": "text",
                        "placeholder_key": "forms.computer.fields.ram.placeholder",
                        "label_key": "forms.computer.fields.ram.label",
                        "order": 3,
                        "tab_id": "specifications",
                        "validation": {"required": False},
                    },
                    "storage": {
                        "widget": "text",
                        "placeholder_key": "forms.computer.fields.storage.placeholder",
                        "label_key": "forms.computer.fields.storage.label",
                        "order": 4,
                        "tab_id": "specifications",
                        "validation": {"required": False},
                    },
                    "os": {
                        "widget": "text",
                        "placeholder_key": "forms.computer.fields.os.placeholder",
                        "label_key": "forms.computer.fields.os.label",
                        "order": 5,
                        "tab_id": "specifications",
                        "validation": {"required": False},
                    },
                    # Network tab
                    "hostname": {
                        "widget": "text",
                        "placeholder_key": "forms.computer.fields.hostname.placeholder",
                        "label_key": "forms.computer.fields.hostname.label",
                        "order": 1,
                        "tab_id": "network",
                        "validation": {"required": False},
                    },
                    "ip_address": {
                        "widget": "text",
                        "placeholder_key": "forms.computer.fields.ip_address.placeholder",
                        "label_key": "forms.computer.fields.ip_address.label",
                        "order": 2,
                        "tab_id": "network",
                        "validation": {"required": False},
                    },
                    "mac_address": {
                        "widget": "text",
                        "placeholder_key": "forms.computer.fields.mac_address.placeholder",
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
                        "label_key": "forms.computer.fields.group_id.label",
                        "order": 1,
                        "tab_id": "groups",
                        "validation": {"required": False},
                    },
                },
            },
        }
        return enhanced_schema

    def _get_virtual_machine_edit_schema(self) -> Dict[str, Any]:
        """
        Generate JSON edit schema for virtual machine resource.
        """
        from app.schemas.asset import \
            VirtualMachineUpdate  # Local import to avoid circular

        base_schema = VirtualMachineUpdate.model_json_schema()
        # Define tabs
        tabs = [
            {"id": "general", "label_key": "forms.tabs.general"},
            {"id": "virtualization", "label_key": "forms.tabs.virtualization"},
            {"id": "specifications", "label_key": "forms.tabs.specifications"},
            {"id": "network", "label_key": "forms.tabs.network"},
            {"id": "security", "label_key": "forms.tabs.security"},
            {"id": "compliance", "label_key": "forms.tabs.compliance"},
            {"id": "backup", "label_key": "forms.tabs.backup"},
            {"id": "groups", "label_key": "forms.tabs.groups"},
            {"id": "compliance", "label_key": "forms.tabs.compliance"},
        ]
        enhanced_schema = {
            "version": "1.0.0",
            "resource_type": "virtual_machine",
            "schema_type": "edit",
            "schema": base_schema,
            "ui": {
                "title_key": "forms.virtual_machine.edit.title",
                "description_key": "forms.virtual_machine.edit.description",
                "tabs": tabs,
                "fields": {
                    # General tab
                    "name": {
                        "widget": "text",
                        "placeholder_key": "forms.virtual_machine.fields.name.placeholder",
                        "label_key": "forms.virtual_machine.fields.name.label",
                        "order": 1,
                        "tab_id": "general",
                        "validation": {"required": False},
                    },
                    "serial_number": {
                        "widget": "text",
                        "placeholder_key": "forms.virtual_machine.fields.serial_number.placeholder",
                        "label_key": "forms.virtual_machine.fields.serial_number.label",
                        "order": 2,
                        "tab_id": "general",
                        "validation": {"required": False},
                    },
                    "inventory_number": {
                        "widget": "text",
                        "placeholder_key": "forms.virtual_machine.fields.inventory_number.placeholder",
                        "label_key": "forms.virtual_machine.fields.inventory_number.label",
                        "order": 3,
                        "tab_id": "general",
                        "validation": {"required": False},
                    },
                    "assigned_to": {
                        "widget": "select",
                        "quick_create_resource": "user",
                        "placeholder_key": "forms.virtual_machine.fields.assigned_to.placeholder",
                        "label_key": "forms.virtual_machine.fields.assigned_to.label",
                        "order": 4,
                        "tab_id": "general",
                        "validation": {"required": False},
                    },
                    "status": {
                        "widget": "select",
                        "options": [
                            {
                                "value": "active",
                                "label_key": "forms.virtual_machine.fields.status.options.active",
                            },
                            {
                                "value": "inactive",
                                "label_key": "forms.virtual_machine.fields.status.options.inactive",
                            },
                            {
                                "value": "maintenance",
                                "label_key": "forms.virtual_machine.fields.status.options.maintenance",
                            },
                            {
                                "value": "retired",
                                "label_key": "forms.virtual_machine.fields.status.options.retired",
                            },
                        ],
                        "placeholder_key": "forms.virtual_machine.fields.status.placeholder",
                        "label_key": "forms.virtual_machine.fields.status.label",
                        "order": 5,
                        "tab_id": "general",
                        "validation": {"required": False},
                    },
                    "purchase_date": {
                        "widget": "date",
                        "placeholder_key": "forms.virtual_machine.fields.purchase_date.placeholder",
                        "label_key": "forms.virtual_machine.fields.purchase_date.label",
                        "order": 6,
                        "tab_id": "general",
                        "validation": {"required": False},
                    },
                    "warranty_expiry": {
                        "widget": "date",
                        "placeholder_key": "forms.virtual_machine.fields.warranty_expiry.placeholder",
                        "label_key": "forms.virtual_machine.fields.warranty_expiry.label",
                        "order": 7,
                        "tab_id": "general",
                        "validation": {"required": False},
                    },
                    "manufacturer_id": {
                        "widget": "select",
                        "quick_create_resource": "manufacturer",
                        "placeholder_key": "forms.virtual_machine.fields.manufacturer_id.placeholder",
                        "label_key": "forms.virtual_machine.fields.manufacturer_id.label",
                        "order": 8,
                        "tab_id": "general",
                        "validation": {"required": False},
                    },
                    "location_id": {
                        "widget": "select",
                        "quick_create_resource": "location",
                        "placeholder_key": "forms.virtual_machine.fields.location_id.placeholder",
                        "label_key": "forms.virtual_machine.fields.location_id.label",
                        "order": 9,
                        "tab_id": "general",
                        "validation": {"required": False},
                    },
                    # Virtualization tab
                    "hypervisor_type": {
                        "widget": "select",
                        "options": [
                            {
                                "value": "VMware",
                                "label_key": "forms.virtual_machine.fields.hypervisor_type.options.vmware",
                            },
                            {
                                "value": "Hyper-V",
                                "label_key": "forms.virtual_machine.fields.hypervisor_type.options.hyperv",
                            },
                            {
                                "value": "KVM",
                                "label_key": "forms.virtual_machine.fields.hypervisor_type.options.kvm",
                            },
                            {
                                "value": "Xen",
                                "label_key": "forms.virtual_machine.fields.hypervisor_type.options.xen",
                            },
                            {
                                "value": "VirtualBox",
                                "label_key": "forms.virtual_machine.fields.hypervisor_type.options.virtualbox",
                            },
                        ],
                        "placeholder_key": "forms.virtual_machine.fields.hypervisor_type.placeholder",
                        "label_key": "forms.virtual_machine.fields.hypervisor_type.label",
                        "order": 1,
                        "tab_id": "virtualization",
                        "validation": {"required": False},
                    },
                    "hypervisor_version": {
                        "widget": "text",
                        "placeholder_key": "forms.virtual_machine.fields.hypervisor_version.placeholder",
                        "label_key": "forms.virtual_machine.fields.hypervisor_version.label",
                        "order": 2,
                        "tab_id": "virtualization",
                        "validation": {"required": False},
                    },
                    "vm_platform": {
                        "widget": "text",
                        "placeholder_key": "forms.virtual_machine.fields.vm_platform.placeholder",
                        "label_key": "forms.virtual_machine.fields.vm_platform.label",
                        "order": 3,
                        "tab_id": "virtualization",
                        "validation": {"required": False},
                    },
                    "power_state": {
                        "widget": "select",
                        "options": [
                            {
                                "value": "Running",
                                "label_key": "forms.virtual_machine.fields.power_state.options.running",
                            },
                            {
                                "value": "Stopped",
                                "label_key": "forms.virtual_machine.fields.power_state.options.stopped",
                            },
                            {
                                "value": "Suspended",
                                "label_key": "forms.virtual_machine.fields.power_state.options.suspended",
                            },
                        ],
                        "placeholder_key": "forms.virtual_machine.fields.power_state.placeholder",
                        "label_key": "forms.virtual_machine.fields.power_state.label",
                        "order": 4,
                        "tab_id": "virtualization",
                        "validation": {"required": False},
                    },
                    "creation_date": {
                        "widget": "date",
                        "placeholder_key": "forms.virtual_machine.fields.creation_date.placeholder",
                        "label_key": "forms.virtual_machine.fields.creation_date.label",
                        "order": 5,
                        "tab_id": "virtualization",
                        "validation": {"required": False},
                    },
                    "scheduled_decommission_date": {
                        "widget": "date",
                        "placeholder_key": "forms.virtual_machine.fields.scheduled_decommission_date.placeholder",
                        "label_key": "forms.virtual_machine.fields.scheduled_decommission_date.label",
                        "order": 6,
                        "tab_id": "virtualization",
                        "validation": {"required": False},
                    },
                    "ha_enabled": {
                        "widget": "select",
                        "options": [
                            {
                                "value": "Yes",
                                "label_key": "forms.virtual_machine.fields.ha_enabled.options.yes",
                            },
                            {
                                "value": "No",
                                "label_key": "forms.virtual_machine.fields.ha_enabled.options.no",
                            },
                        ],
                        "placeholder_key": "forms.virtual_machine.fields.ha_enabled.placeholder",
                        "label_key": "forms.virtual_machine.fields.ha_enabled.label",
                        "order": 7,
                        "tab_id": "virtualization",
                        "validation": {"required": False},
                    },
                    "redundancy_level": {
                        "widget": "select",
                        "options": [
                            {
                                "value": "None",
                                "label_key": "forms.virtual_machine.fields.redundancy_level.options.none",
                            },
                            {
                                "value": "N+1",
                                "label_key": "forms.virtual_machine.fields.redundancy_level.options.n_plus_1",
                            },
                            {
                                "value": "N+2",
                                "label_key": "forms.virtual_machine.fields.redundancy_level.options.n_plus_2",
                            },
                        ],
                        "placeholder_key": "forms.virtual_machine.fields.redundancy_level.placeholder",
                        "label_key": "forms.virtual_machine.fields.redundancy_level.label",
                        "order": 8,
                        "tab_id": "virtualization",
                        "validation": {"required": False},
                    },
                    "failover_capability": {
                        "widget": "select",
                        "options": [
                            {
                                "value": "Yes",
                                "label_key": "forms.virtual_machine.fields.failover_capability.options.yes",
                            },
                            {
                                "value": "No",
                                "label_key": "forms.virtual_machine.fields.failover_capability.options.no",
                            },
                        ],
                        "placeholder_key": "forms.virtual_machine.fields.failover_capability.placeholder",
                        "label_key": "forms.virtual_machine.fields.failover_capability.label",
                        "order": 9,
                        "tab_id": "virtualization",
                        "validation": {"required": False},
                    },
                    # Security tab
                    "confidentiality_level": {
                        "widget": "select",
                        "options": [
                            {
                                "value": "Public",
                                "label_key": "forms.virtual_machine.fields.confidentiality_level.options.Public",
                            },
                            {
                                "value": "Internal",
                                "label_key": "forms.virtual_machine.fields.confidentiality_level.options.Internal",
                            },
                            {
                                "value": "Confidential",
                                "label_key": "forms.virtual_machine.fields.confidentiality_level.options.Confidential",
                            },
                            {
                                "value": "Secret",
                                "label_key": "forms.virtual_machine.fields.confidentiality_level.options.Secret",
                            },
                        ],
                        "placeholder_key": "forms.virtual_machine.fields.confidentiality_level.placeholder",
                        "label_key": "forms.virtual_machine.fields.confidentiality_level.label",
                        "order": 1,
                        "tab_id": "security",
                        "validation": {"required": False},
                    },
                    "integrity_level": {
                        "widget": "select",
                        "options": [
                            {
                                "value": "High",
                                "label_key": "forms.virtual_machine.fields.integrity_level.options.High",
                            },
                            {
                                "value": "Medium",
                                "label_key": "forms.virtual_machine.fields.integrity_level.options.Medium",
                            },
                            {
                                "value": "Low",
                                "label_key": "forms.virtual_machine.fields.integrity_level.options.Low",
                            },
                        ],
                        "placeholder_key": "forms.virtual_machine.fields.integrity_level.placeholder",
                        "label_key": "forms.virtual_machine.fields.integrity_level.label",
                        "order": 2,
                        "tab_id": "security",
                        "validation": {"required": False},
                    },
                    "availability_level": {
                        "widget": "select",
                        "options": [
                            {
                                "value": "High",
                                "label_key": "forms.virtual_machine.fields.availability_level.options.High",
                            },
                            {
                                "value": "Medium",
                                "label_key": "forms.virtual_machine.fields.availability_level.options.Medium",
                            },
                            {
                                "value": "Low",
                                "label_key": "forms.virtual_machine.fields.availability_level.options.Low",
                            },
                        ],
                        "placeholder_key": "forms.virtual_machine.fields.availability_level.placeholder",
                        "label_key": "forms.virtual_machine.fields.availability_level.label",
                        "order": 3,
                        "tab_id": "security",
                        "validation": {"required": False},
                    },
                    "encryption_status": {
                        "widget": "select",
                        "options": [
                            {
                                "value": "Encrypted",
                                "label_key": "forms.virtual_machine.fields.encryption_status.options.encrypted",
                            },
                            {
                                "value": "Not Encrypted",
                                "label_key": "forms.virtual_machine.fields.encryption_status.options.not_encrypted",
                            },
                            {
                                "value": "Partial",
                                "label_key": "forms.virtual_machine.fields.encryption_status.options.partial",
                            },
                        ],
                        "placeholder_key": "forms.virtual_machine.fields.encryption_status.placeholder",
                        "label_key": "forms.virtual_machine.fields.encryption_status.label",
                        "order": 4,
                        "tab_id": "security",
                        "validation": {"required": False},
                    },
                    "encryption_type": {
                        "widget": "text",
                        "placeholder_key": "forms.virtual_machine.fields.encryption_type.placeholder",
                        "label_key": "forms.virtual_machine.fields.encryption_type.label",
                        "order": 5,
                        "tab_id": "security",
                        "validation": {"required": False},
                    },
                    "admin_access_restricted": {
                        "widget": "select",
                        "options": [
                            {
                                "value": "Yes",
                                "label_key": "forms.virtual_machine.fields.admin_access_restricted.options.yes",
                            },
                            {
                                "value": "No",
                                "label_key": "forms.virtual_machine.fields.admin_access_restricted.options.no",
                            },
                        ],
                        "placeholder_key": "forms.virtual_machine.fields.admin_access_restricted.placeholder",
                        "label_key": "forms.virtual_machine.fields.admin_access_restricted.label",
                        "order": 6,
                        "tab_id": "security",
                        "validation": {"required": False},
                    },
                    "multi_factor_auth_enabled": {
                        "widget": "select",
                        "options": [
                            {
                                "value": "Yes",
                                "label_key": "forms.virtual_machine.fields.multi_factor_auth_enabled.options.yes",
                            },
                            {
                                "value": "No",
                                "label_key": "forms.virtual_machine.fields.multi_factor_auth_enabled.options.no",
                            },
                        ],
                        "placeholder_key": "forms.virtual_machine.fields.multi_factor_auth_enabled.placeholder",
                        "label_key": "forms.virtual_machine.fields.multi_factor_auth_enabled.label",
                        "order": 7,
                        "tab_id": "security",
                        "validation": {"required": False},
                    },
                    "logging_enabled": {
                        "widget": "select",
                        "options": [
                            {
                                "value": "Yes",
                                "label_key": "forms.virtual_machine.fields.logging_enabled.options.yes",
                            },
                            {
                                "value": "No",
                                "label_key": "forms.virtual_machine.fields.logging_enabled.options.no",
                            },
                        ],
                        "placeholder_key": "forms.virtual_machine.fields.logging_enabled.placeholder",
                        "label_key": "forms.virtual_machine.fields.logging_enabled.label",
                        "order": 8,
                        "tab_id": "security",
                        "validation": {"required": False},
                    },
                    "monitoring_tool": {
                        "widget": "text",
                        "placeholder_key": "forms.virtual_machine.fields.monitoring_tool.placeholder",
                        "label_key": "forms.virtual_machine.fields.monitoring_tool.label",
                        "order": 9,
                        "tab_id": "security",
                        "validation": {"required": False},
                    },
                    "isolation_level": {
                        "widget": "select",
                        "options": [
                            {
                                "value": "High",
                                "label_key": "forms.virtual_machine.fields.isolation_level.options.high",
                            },
                            {
                                "value": "Medium",
                                "label_key": "forms.virtual_machine.fields.isolation_level.options.medium",
                            },
                            {
                                "value": "Low",
                                "label_key": "forms.virtual_machine.fields.isolation_level.options.low",
                            },
                        ],
                        "placeholder_key": "forms.virtual_machine.fields.isolation_level.placeholder",
                        "label_key": "forms.virtual_machine.fields.isolation_level.label",
                        "order": 10,
                        "tab_id": "security",
                        "validation": {"required": False},
                    },
                    "resource_isolation": {
                        "widget": "select",
                        "options": [
                            {
                                "value": "Yes",
                                "label_key": "forms.virtual_machine.fields.resource_isolation.options.yes",
                            },
                            {
                                "value": "No",
                                "label_key": "forms.virtual_machine.fields.resource_isolation.options.no",
                            },
                        ],
                        "placeholder_key": "forms.virtual_machine.fields.resource_isolation.placeholder",
                        "label_key": "forms.virtual_machine.fields.resource_isolation.label",
                        "order": 11,
                        "tab_id": "security",
                        "validation": {"required": False},
                    },
                    "network_isolation": {
                        "widget": "select",
                        "options": [
                            {
                                "value": "Yes",
                                "label_key": "forms.virtual_machine.fields.network_isolation.options.yes",
                            },
                            {
                                "value": "No",
                                "label_key": "forms.virtual_machine.fields.network_isolation.options.no",
                            },
                        ],
                        "placeholder_key": "forms.virtual_machine.fields.network_isolation.placeholder",
                        "label_key": "forms.virtual_machine.fields.network_isolation.label",
                        "order": 12,
                        "tab_id": "security",
                        "validation": {"required": False},
                    },
                    "storage_isolation": {
                        "widget": "select",
                        "options": [
                            {
                                "value": "Yes",
                                "label_key": "forms.virtual_machine.fields.storage_isolation.options.yes",
                            },
                            {
                                "value": "No",
                                "label_key": "forms.virtual_machine.fields.storage_isolation.options.no",
                            },
                        ],
                        "placeholder_key": "forms.virtual_machine.fields.storage_isolation.placeholder",
                        "label_key": "forms.virtual_machine.fields.storage_isolation.label",
                        "order": 13,
                        "tab_id": "security",
                        "validation": {"required": False},
                    },
                    # Specifications tab
                    "cpu_cores": {
                        "widget": "number",
                        "placeholder_key": "forms.virtual_machine.fields.cpu_cores.placeholder",
                        "label_key": "forms.virtual_machine.fields.cpu_cores.label",
                        "order": 1,
                        "tab_id": "specifications",
                        "validation": {"required": False},
                    },
                    "memory_mb": {
                        "widget": "number",
                        "placeholder_key": "forms.virtual_machine.fields.memory_mb.placeholder",
                        "label_key": "forms.virtual_machine.fields.memory_mb.label",
                        "order": 2,
                        "tab_id": "specifications",
                        "validation": {"required": False},
                    },
                    "storage_gb": {
                        "widget": "number",
                        "placeholder_key": "forms.virtual_machine.fields.storage_gb.placeholder",
                        "label_key": "forms.virtual_machine.fields.storage_gb.label",
                        "order": 3,
                        "tab_id": "specifications",
                        "validation": {"required": False},
                    },
                    "os_type": {
                        "widget": "select",
                        "options": [
                            {
                                "value": "Windows",
                                "label_key": "forms.virtual_machine.fields.os_type.options.windows",
                            },
                            {
                                "value": "Linux",
                                "label_key": "forms.virtual_machine.fields.os_type.options.linux",
                            },
                            {
                                "value": "macOS",
                                "label_key": "forms.virtual_machine.fields.os_type.options.macos",
                            },
                        ],
                        "placeholder_key": "forms.virtual_machine.fields.os_type.placeholder",
                        "label_key": "forms.virtual_machine.fields.os_type.label",
                        "order": 4,
                        "tab_id": "specifications",
                        "validation": {"required": False},
                    },
                    "os_version": {
                        "widget": "text",
                        "placeholder_key": "forms.virtual_machine.fields.os_version.placeholder",
                        "label_key": "forms.virtual_machine.fields.os_version.label",
                        "order": 5,
                        "tab_id": "specifications",
                        "validation": {"required": False},
                    },
                    "os_architecture": {
                        "widget": "select",
                        "options": [
                            {
                                "value": "x86_64",
                                "label_key": "forms.virtual_machine.fields.os_architecture.options.x86_64",
                            },
                            {
                                "value": "ARM64",
                                "label_key": "forms.virtual_machine.fields.os_architecture.options.arm64",
                            },
                            {
                                "value": "i386",
                                "label_key": "forms.virtual_machine.fields.os_architecture.options.i386",
                            },
                        ],
                        "placeholder_key": "forms.virtual_machine.fields.os_architecture.placeholder",
                        "label_key": "forms.virtual_machine.fields.os_architecture.label",
                        "order": 6,
                        "tab_id": "specifications",
                        "validation": {"required": False},
                    },
                    "cpu_allocation_percent": {
                        "widget": "number",
                        "placeholder_key": "forms.virtual_machine.fields.cpu_allocation_percent.placeholder",
                        "label_key": "forms.virtual_machine.fields.cpu_allocation_percent.label",
                        "order": 7,
                        "tab_id": "specifications",
                        "validation": {"required": False},
                    },
                    "memory_allocation_percent": {
                        "widget": "number",
                        "placeholder_key": "forms.virtual_machine.fields.memory_allocation_percent.placeholder",
                        "label_key": "forms.virtual_machine.fields.memory_allocation_percent.label",
                        "order": 8,
                        "tab_id": "specifications",
                        "validation": {"required": False},
                    },
                    "storage_allocation_percent": {
                        "widget": "number",
                        "placeholder_key": "forms.virtual_machine.fields.storage_allocation_percent.placeholder",
                        "label_key": "forms.virtual_machine.fields.storage_allocation_percent.label",
                        "order": 9,
                        "tab_id": "specifications",
                        "validation": {"required": False},
                    },
                    # Network tab
                    "network_segment": {
                        "widget": "select",
                        "options": [
                            {
                                "value": "DMZ",
                                "label_key": "forms.virtual_machine.fields.network_segment.options.dmz",
                            },
                            {
                                "value": "Internal",
                                "label_key": "forms.virtual_machine.fields.network_segment.options.internal",
                            },
                            {
                                "value": "PCI",
                                "label_key": "forms.virtual_machine.fields.network_segment.options.pci",
                            },
                            {
                                "value": "Management",
                                "label_key": "forms.virtual_machine.fields.network_segment.options.management",
                            },
                        ],
                        "placeholder_key": "forms.virtual_machine.fields.network_segment.placeholder",
                        "label_key": "forms.virtual_machine.fields.network_segment.label",
                        "order": 1,
                        "tab_id": "network",
                        "validation": {"required": False},
                    },
                    "vlan_id": {
                        "widget": "text",
                        "placeholder_key": "forms.virtual_machine.fields.vlan_id.placeholder",
                        "label_key": "forms.virtual_machine.fields.vlan_id.label",
                        "order": 2,
                        "tab_id": "network",
                        "validation": {"required": False},
                    },
                    "ip_address": {
                        "widget": "text",
                        "placeholder_key": "forms.virtual_machine.fields.ip_address.placeholder",
                        "label_key": "forms.virtual_machine.fields.ip_address.label",
                        "order": 3,
                        "tab_id": "network",
                        "validation": {"required": False},
                    },
                    "mac_address": {
                        "widget": "text",
                        "placeholder_key": "forms.virtual_machine.fields.mac_address.placeholder",
                        "label_key": "forms.virtual_machine.fields.mac_address.label",
                        "order": 4,
                        "tab_id": "network",
                        "validation": {"required": False},
                    },
                    # Compliance tab
                    "pci_scope": {
                        "widget": "select",
                        "options": [
                            {
                                "value": "In Scope",
                                "label_key": "forms.virtual_machine.fields.pci_scope.options.in_scope",
                            },
                            {
                                "value": "Out of Scope",
                                "label_key": "forms.virtual_machine.fields.pci_scope.options.out_of_scope",
                            },
                        ],
                        "placeholder_key": "forms.virtual_machine.fields.pci_scope.placeholder",
                        "label_key": "forms.virtual_machine.fields.pci_scope.label",
                        "order": 1,
                        "tab_id": "compliance",
                        "validation": {"required": False},
                    },
                    "cardholder_data_environment": {
                        "widget": "select",
                        "options": [
                            {
                                "value": "CDE",
                                "label_key": "forms.virtual_machine.fields.cardholder_data_environment.options.cde",
                            },
                            {
                                "value": "Connected-to",
                                "label_key": "forms.virtual_machine.fields.cardholder_data_environment.options.connected_to",
                            },
                            {
                                "value": "Out-of-Scope",
                                "label_key": "forms.virtual_machine.fields.cardholder_data_environment.options.out_of_scope",
                            },
                        ],
                        "placeholder_key": "forms.virtual_machine.fields.cardholder_data_environment.placeholder",
                        "label_key": "forms.virtual_machine.fields.cardholder_data_environment.label",
                        "order": 2,
                        "tab_id": "compliance",
                        "validation": {"required": False},
                    },
                    "pci_assessment_date": {
                        "widget": "date",
                        "placeholder_key": "forms.virtual_machine.fields.pci_assessment_date.placeholder",
                        "label_key": "forms.virtual_machine.fields.pci_assessment_date.label",
                        "order": 3,
                        "tab_id": "compliance",
                        "validation": {"required": False},
                    },
                    "pci_compliance_status": {
                        "widget": "select",
                        "options": [
                            {
                                "value": "Compliant",
                                "label_key": "forms.virtual_machine.fields.pci_compliance_status.options.compliant",
                            },
                            {
                                "value": "Non-Compliant",
                                "label_key": "forms.virtual_machine.fields.pci_compliance_status.options.non_compliant",
                            },
                            {
                                "value": "In Progress",
                                "label_key": "forms.virtual_machine.fields.pci_compliance_status.options.in_progress",
                            },
                        ],
                        "placeholder_key": "forms.virtual_machine.fields.pci_compliance_status.placeholder",
                        "label_key": "forms.virtual_machine.fields.pci_compliance_status.label",
                        "order": 4,
                        "tab_id": "compliance",
                        "validation": {"required": False},
                    },
                    "next_assessment_date": {
                        "widget": "date",
                        "placeholder_key": "forms.virtual_machine.fields.next_assessment_date.placeholder",
                        "label_key": "forms.virtual_machine.fields.next_assessment_date.label",
                        "order": 5,
                        "tab_id": "compliance",
                        "validation": {"required": False},
                    },
                    "compliance_notes": {
                        "widget": "textarea",
                        "placeholder_key": "forms.virtual_machine.fields.compliance_notes.placeholder",
                        "label_key": "forms.virtual_machine.fields.compliance_notes.label",
                        "order": 6,
                        "tab_id": "compliance",
                        "validation": {"required": False},
                    },
                    "last_patch_date": {
                        "widget": "date",
                        "placeholder_key": "forms.virtual_machine.fields.last_patch_date.placeholder",
                        "label_key": "forms.virtual_machine.fields.last_patch_date.label",
                        "order": 7,
                        "tab_id": "compliance",
                        "validation": {"required": False},
                    },
                    "patch_level": {
                        "widget": "text",
                        "placeholder_key": "forms.virtual_machine.fields.patch_level.placeholder",
                        "label_key": "forms.virtual_machine.fields.patch_level.label",
                        "order": 8,
                        "tab_id": "compliance",
                        "validation": {"required": False},
                    },
                    "vulnerability_scan_date": {
                        "widget": "date",
                        "placeholder_key": "forms.virtual_machine.fields.vulnerability_scan_date.placeholder",
                        "label_key": "forms.virtual_machine.fields.vulnerability_scan_date.label",
                        "order": 9,
                        "tab_id": "compliance",
                        "validation": {"required": False},
                    },
                    "vulnerability_status": {
                        "widget": "select",
                        "options": [
                            {
                                "value": "Compliant",
                                "label_key": "forms.virtual_machine.fields.vulnerability_status.options.compliant",
                            },
                            {
                                "value": "Non-Compliant",
                                "label_key": "forms.virtual_machine.fields.vulnerability_status.options.non_compliant",
                            },
                            {
                                "value": "Pending",
                                "label_key": "forms.virtual_machine.fields.vulnerability_status.options.pending",
                            },
                        ],
                        "placeholder_key": "forms.virtual_machine.fields.vulnerability_status.placeholder",
                        "label_key": "forms.virtual_machine.fields.vulnerability_status.label",
                        "order": 10,
                        "tab_id": "compliance",
                        "validation": {"required": False},
                    },
                    # Backup tab
                    "backup_frequency": {
                        "widget": "select",
                        "options": [
                            {
                                "value": "Daily",
                                "label_key": "forms.virtual_machine.fields.backup_frequency.options.daily",
                            },
                            {
                                "value": "Weekly",
                                "label_key": "forms.virtual_machine.fields.backup_frequency.options.weekly",
                            },
                            {
                                "value": "Monthly",
                                "label_key": "forms.virtual_machine.fields.backup_frequency.options.monthly",
                            },
                        ],
                        "placeholder_key": "forms.virtual_machine.fields.backup_frequency.placeholder",
                        "label_key": "forms.virtual_machine.fields.backup_frequency.label",
                        "order": 1,
                        "tab_id": "backup",
                        "validation": {"required": False},
                    },
                    "last_backup_date": {
                        "widget": "date",
                        "placeholder_key": "forms.virtual_machine.fields.last_backup_date.placeholder",
                        "label_key": "forms.virtual_machine.fields.last_backup_date.label",
                        "order": 2,
                        "tab_id": "backup",
                        "validation": {"required": False},
                    },
                    "backup_retention_days": {
                        "widget": "number",
                        "placeholder_key": "forms.virtual_machine.fields.backup_retention_days.placeholder",
                        "label_key": "forms.virtual_machine.fields.backup_retention_days.label",
                        "order": 3,
                        "tab_id": "backup",
                        "validation": {"required": False},
                    },
                    "backup_encryption": {
                        "widget": "select",
                        "options": [
                            {
                                "value": "Yes",
                                "label_key": "forms.virtual_machine.fields.backup_encryption.options.yes",
                            },
                            {
                                "value": "No",
                                "label_key": "forms.virtual_machine.fields.backup_encryption.options.no",
                            },
                            {
                                "value": "N/A",
                                "label_key": "forms.virtual_machine.fields.backup_encryption.options.na",
                            },
                        ],
                        "placeholder_key": "forms.virtual_machine.fields.backup_encryption.placeholder",
                        "label_key": "forms.virtual_machine.fields.backup_encryption.label",
                        "order": 4,
                        "tab_id": "backup",
                        "validation": {"required": False},
                    },
                    "disaster_recovery_plan": {
                        "widget": "select",
                        "options": [
                            {
                                "value": "Yes",
                                "label_key": "forms.virtual_machine.fields.disaster_recovery_plan.options.yes",
                            },
                            {
                                "value": "No",
                                "label_key": "forms.virtual_machine.fields.disaster_recovery_plan.options.no",
                            },
                            {
                                "value": "N/A",
                                "label_key": "forms.virtual_machine.fields.disaster_recovery_plan.options.na",
                            },
                        ],
                        "placeholder_key": "forms.virtual_machine.fields.disaster_recovery_plan.placeholder",
                        "label_key": "forms.virtual_machine.fields.disaster_recovery_plan.label",
                        "order": 5,
                        "tab_id": "backup",
                        "validation": {"required": False},
                    },
                    # Relationships tab
                    "groups": {
                        "widget": "relationship",
                        "quick_create_resource": "group",
                        "placeholder_key": "forms.virtual_machine.fields.group_id.placeholder",
                        "label_key": "forms.virtual_machine.fields.group_id.label",
                        "order": 1,
                        "tab_id": "groups",
                        "validation": {"required": False},
                    },
                },
            },
        }
        return enhanced_schema

    def _get_network_device_edit_schema(self) -> Dict[str, Any]:
        """
        Generate JSON edit schema for network device resource.
        """
        from app.schemas.asset import \
            NetworkDeviceUpdate  # Local import to avoid circular

        base_schema = NetworkDeviceUpdate.model_json_schema()
        # Define tabs
        tabs = [
            {"id": "general", "label_key": "forms.tabs.general"},
            {"id": "network", "label_key": "forms.tabs.network"},
            {"id": "security", "label_key": "forms.tabs.security"},
            {"id": "authentication", "label_key": "forms.tabs.authentication"},
            {"id": "monitoring", "label_key": "forms.tabs.monitoring"},
            {"id": "lifecycle", "label_key": "forms.tabs.lifecycle"},
            {"id": "groups", "label_key": "forms.tabs.groups"},
            {"id": "compliance", "label_key": "forms.tabs.compliance"},
        ]
        enhanced_schema = {
            "version": "1.0.0",
            "resource_type": "network_device",
            "schema_type": "edit",
            "schema": base_schema,
            "ui": {
                "title_key": "forms.network_device.edit.title",
                "description_key": "forms.network_device.edit.description",
                "tabs": tabs,
                "fields": {
                    # General tab
                    "name": {
                        "widget": "text",
                        "placeholder_key": "forms.network_device.fields.name.placeholder",
                        "label_key": "forms.network_device.fields.name.label",
                        "order": 1,
                        "tab_id": "general",
                        "validation": {"required": False},
                    },
                    "serial_number": {
                        "widget": "text",
                        "placeholder_key": "forms.network_device.fields.serial_number.placeholder",
                        "label_key": "forms.network_device.fields.serial_number.label",
                        "order": 2,
                        "tab_id": "general",
                        "validation": {"required": False},
                    },
                    "inventory_number": {
                        "widget": "text",
                        "placeholder_key": "forms.network_device.fields.inventory_number.placeholder",
                        "label_key": "forms.network_device.fields.inventory_number.label",
                        "order": 3,
                        "tab_id": "general",
                        "validation": {"required": False},
                    },
                    "assigned_to": {
                        "widget": "select",
                        "quick_create_resource": "user",
                        "placeholder_key": "forms.network_device.fields.assigned_to.placeholder",
                        "label_key": "forms.network_device.fields.assigned_to.label",
                        "order": 4,
                        "tab_id": "general",
                        "validation": {"required": False},
                    },
                    "status": {
                        "widget": "select",
                        "options": [
                            {
                                "value": "active",
                                "label_key": "forms.network_device.fields.status.options.active",
                            },
                            {
                                "value": "inactive",
                                "label_key": "forms.network_device.fields.status.options.inactive",
                            },
                            {
                                "value": "maintenance",
                                "label_key": "forms.network_device.fields.status.options.maintenance",
                            },
                            {
                                "value": "retired",
                                "label_key": "forms.network_device.fields.status.options.retired",
                            },
                        ],
                        "placeholder_key": "forms.network_device.fields.status.placeholder",
                        "label_key": "forms.network_device.fields.status.label",
                        "order": 5,
                        "tab_id": "general",
                        "validation": {"required": False},
                    },
                    "purchase_date": {
                        "widget": "date",
                        "placeholder_key": "forms.network_device.fields.purchase_date.placeholder",
                        "label_key": "forms.network_device.fields.purchase_date.label",
                        "order": 6,
                        "tab_id": "general",
                        "validation": {"required": False},
                    },
                    "warranty_expiry": {
                        "widget": "date",
                        "placeholder_key": "forms.network_device.fields.warranty_expiry.placeholder",
                        "label_key": "forms.network_device.fields.warranty_expiry.label",
                        "order": 7,
                        "tab_id": "general",
                        "validation": {"required": False},
                    },
                    "manufacturer_id": {
                        "widget": "select",
                        "quick_create_resource": "manufacturer",
                        "placeholder_key": "forms.network_device.fields.manufacturer_id.placeholder",
                        "label_key": "forms.network_device.fields.manufacturer_id.label",
                        "order": 8,
                        "tab_id": "general",
                        "validation": {"required": False},
                    },
                    "location_id": {
                        "widget": "select",
                        "quick_create_resource": "location",
                        "placeholder_key": "forms.network_device.fields.location_id.placeholder",
                        "label_key": "forms.network_device.fields.location_id.label",
                        "order": 9,
                        "tab_id": "general",
                        "validation": {"required": False},
                    },
                    "device_type": {
                        "widget": "select",
                        "options": [
                            {
                                "value": "Switch",
                                "label_key": "forms.network_device.fields.device_type.options.switch",
                            },
                            {
                                "value": "Router",
                                "label_key": "forms.network_device.fields.device_type.options.router",
                            },
                            {
                                "value": "Access Point",
                                "label_key": "forms.network_device.fields.device_type.options.access_point",
                            },
                            {
                                "value": "Firewall",
                                "label_key": "forms.network_device.fields.device_type.options.firewall",
                            },
                        ],
                        "placeholder_key": "forms.network_device.fields.device_type.placeholder",
                        "label_key": "forms.network_device.fields.device_type.label",
                        "order": 10,
                        "tab_id": "general",
                        "validation": {"required": False},
                    },
                    "model": {
                        "widget": "text",
                        "placeholder_key": "forms.network_device.fields.model.placeholder",
                        "label_key": "forms.network_device.fields.model.label",
                        "order": 11,
                        "tab_id": "general",
                        "validation": {"required": False},
                    },
                    "firmware_version": {
                        "widget": "text",
                        "placeholder_key": "forms.network_device.fields.firmware_version.placeholder",
                        "label_key": "forms.network_device.fields.firmware_version.label",
                        "order": 12,
                        "tab_id": "general",
                        "validation": {"required": False},
                    },
                    # Network tab
                    "ip_address": {
                        "widget": "text",
                        "placeholder_key": "forms.network_device.fields.ip_address.placeholder",
                        "label_key": "forms.network_device.fields.ip_address.label",
                        "order": 1,
                        "tab_id": "network",
                        "validation": {"required": False},
                    },
                    "management_ip": {
                        "widget": "text",
                        "placeholder_key": "forms.network_device.fields.management_ip.placeholder",
                        "label_key": "forms.network_device.fields.management_ip.label",
                        "order": 2,
                        "tab_id": "network",
                        "validation": {"required": False},
                    },
                    "mac_address": {
                        "widget": "text",
                        "placeholder_key": "forms.network_device.fields.mac_address.placeholder",
                        "label_key": "forms.network_device.fields.mac_address.label",
                        "order": 3,
                        "tab_id": "network",
                        "validation": {"required": False},
                    },
                    "port_count": {
                        "widget": "number",
                        "placeholder_key": "forms.network_device.fields.port_count.placeholder",
                        "label_key": "forms.network_device.fields.port_count.label",
                        "order": 4,
                        "tab_id": "network",
                        "validation": {"required": False},
                    },
                    "connection_type": {
                        "widget": "select",
                        "options": [
                            {
                                "value": "Ethernet",
                                "label_key": "forms.network_device.fields.connection_type.options.ethernet",
                            },
                            {
                                "value": "WiFi",
                                "label_key": "forms.network_device.fields.connection_type.options.wifi",
                            },
                            {
                                "value": "Fiber",
                                "label_key": "forms.network_device.fields.connection_type.options.fiber",
                            },
                        ],
                        "placeholder_key": "forms.network_device.fields.connection_type.placeholder",
                        "label_key": "forms.network_device.fields.connection_type.label",
                        "order": 5,
                        "tab_id": "network",
                        "validation": {"required": False},
                    },
                    "vlan": {
                        "widget": "text",
                        "placeholder_key": "forms.network_device.fields.vlan.placeholder",
                        "label_key": "forms.network_device.fields.vlan.label",
                        "order": 6,
                        "tab_id": "network",
                        "validation": {"required": False},
                    },
                    "segmentation": {
                        "widget": "select",
                        "options": [
                            {
                                "value": "PCI",
                                "label_key": "forms.network_device.fields.segmentation.options.pci",
                            },
                            {
                                "value": "Guest",
                                "label_key": "forms.network_device.fields.segmentation.options.guest",
                            },
                            {
                                "value": "Internal",
                                "label_key": "forms.network_device.fields.segmentation.options.internal",
                            },
                            {
                                "value": "DMZ",
                                "label_key": "forms.network_device.fields.segmentation.options.dmz",
                            },
                        ],
                        "placeholder_key": "forms.network_device.fields.segmentation.placeholder",
                        "label_key": "forms.network_device.fields.segmentation.label",
                        "order": 7,
                        "tab_id": "network",
                        "validation": {"required": False},
                    },
                    # Security tab
                    "confidentiality_level": {
                        "widget": "select",
                        "options": [
                            {
                                "value": "Public",
                                "label_key": "forms.network_device.fields.confidentiality_level.options.Public",
                            },
                            {
                                "value": "Internal",
                                "label_key": "forms.network_device.fields.confidentiality_level.options.Internal",
                            },
                            {
                                "value": "Confidential",
                                "label_key": "forms.network_device.fields.confidentiality_level.options.Confidential",
                            },
                            {
                                "value": "Secret",
                                "label_key": "forms.network_device.fields.confidentiality_level.options.Secret",
                            },
                        ],
                        "placeholder_key": "forms.network_device.fields.confidentiality_level.placeholder",
                        "label_key": "forms.network_device.fields.confidentiality_level.label",
                        "order": 1,
                        "tab_id": "security",
                        "validation": {"required": False},
                    },
                    "integrity_level": {
                        "widget": "select",
                        "options": [
                            {
                                "value": "High",
                                "label_key": "forms.network_device.fields.integrity_level.options.High",
                            },
                            {
                                "value": "Medium",
                                "label_key": "forms.network_device.fields.integrity_level.options.Medium",
                            },
                            {
                                "value": "Low",
                                "label_key": "forms.network_device.fields.integrity_level.options.Low",
                            },
                        ],
                        "placeholder_key": "forms.network_device.fields.integrity_level.placeholder",
                        "label_key": "forms.network_device.fields.integrity_level.label",
                        "order": 2,
                        "tab_id": "security",
                        "validation": {"required": False},
                    },
                    "availability_level": {
                        "widget": "select",
                        "options": [
                            {
                                "value": "High",
                                "label_key": "forms.network_device.fields.availability_level.options.High",
                            },
                            {
                                "value": "Medium",
                                "label_key": "forms.network_device.fields.availability_level.options.Medium",
                            },
                            {
                                "value": "Low",
                                "label_key": "forms.network_device.fields.availability_level.options.Low",
                            },
                        ],
                        "placeholder_key": "forms.network_device.fields.availability_level.placeholder",
                        "label_key": "forms.network_device.fields.availability_level.label",
                        "order": 3,
                        "tab_id": "security",
                        "validation": {"required": False},
                    },
                    "rack_location": {
                        "widget": "text",
                        "placeholder_key": "forms.network_device.fields.rack_location.placeholder",
                        "label_key": "forms.network_device.fields.rack_location.label",
                        "order": 4,
                        "tab_id": "security",
                        "validation": {"required": False},
                    },
                    "physical_lock": {
                        "widget": "select",
                        "options": [
                            {
                                "value": "Yes",
                                "label_key": "forms.network_device.fields.physical_lock.options.yes",
                            },
                            {
                                "value": "No",
                                "label_key": "forms.network_device.fields.physical_lock.options.no",
                            },
                        ],
                        "placeholder_key": "forms.network_device.fields.physical_lock.placeholder",
                        "label_key": "forms.network_device.fields.physical_lock.label",
                        "order": 5,
                        "tab_id": "security",
                        "validation": {"required": False},
                    },
                    "tamper_evident": {
                        "widget": "select",
                        "options": [
                            {
                                "value": "Yes",
                                "label_key": "forms.network_device.fields.tamper_evident.options.yes",
                            },
                            {
                                "value": "No",
                                "label_key": "forms.network_device.fields.tamper_evident.options.no",
                            },
                        ],
                        "placeholder_key": "forms.network_device.fields.tamper_evident.placeholder",
                        "label_key": "forms.network_device.fields.tamper_evident.label",
                        "order": 6,
                        "tab_id": "security",
                        "validation": {"required": False},
                    },
                    "firewall_enabled": {
                        "widget": "checkbox",
                        "placeholder_key": "forms.network_device.fields.firewall_enabled.placeholder",
                        "label_key": "forms.network_device.fields.firewall_enabled.label",
                        "order": 7,
                        "tab_id": "security",
                        "validation": {"required": False},
                    },
                    "ids_ips_enabled": {
                        "widget": "checkbox",
                        "placeholder_key": "forms.network_device.fields.ids_ips_enabled.placeholder",
                        "label_key": "forms.network_device.fields.ids_ips_enabled.label",
                        "order": 8,
                        "tab_id": "security",
                        "validation": {"required": False},
                    },
                    "remote_access_enabled": {
                        "widget": "checkbox",
                        "placeholder_key": "forms.network_device.fields.remote_access_enabled.placeholder",
                        "label_key": "forms.network_device.fields.remote_access_enabled.label",
                        "order": 9,
                        "tab_id": "security",
                        "validation": {"required": False},
                    },
                    "remote_access_method": {
                        "widget": "select",
                        "options": [
                            {
                                "value": "SSH",
                                "label_key": "forms.network_device.fields.remote_access_method.options.ssh",
                            },
                            {
                                "value": "Telnet",
                                "label_key": "forms.network_device.fields.remote_access_method.options.telnet",
                            },
                            {
                                "value": "HTTPS",
                                "label_key": "forms.network_device.fields.remote_access_method.options.https",
                            },
                            {
                                "value": "HTTP",
                                "label_key": "forms.network_device.fields.remote_access_method.options.http",
                            },
                        ],
                        "placeholder_key": "forms.network_device.fields.remote_access_method.placeholder",
                        "label_key": "forms.network_device.fields.remote_access_method.label",
                        "order": 10,
                        "tab_id": "security",
                        "validation": {"required": False},
                    },
                    "remote_access_restriction": {
                        "widget": "text",
                        "placeholder_key": "forms.network_device.fields.remote_access_restriction.placeholder",
                        "label_key": "forms.network_device.fields.remote_access_restriction.label",
                        "order": 11,
                        "tab_id": "security",
                        "validation": {"required": False},
                    },
                    "management_encryption": {
                        "widget": "checkbox",
                        "placeholder_key": "forms.network_device.fields.management_encryption.placeholder",
                        "label_key": "forms.network_device.fields.management_encryption.label",
                        "order": 12,
                        "tab_id": "security",
                        "validation": {"required": False},
                    },
                    "encryption_type": {
                        "widget": "text",
                        "placeholder_key": "forms.network_device.fields.encryption_type.placeholder",
                        "label_key": "forms.network_device.fields.encryption_type.label",
                        "order": 13,
                        "tab_id": "security",
                        "validation": {"required": False},
                    },
                    "data_in_transit_encryption": {
                        "widget": "checkbox",
                        "placeholder_key": "forms.network_device.fields.data_in_transit_encryption.placeholder",
                        "label_key": "forms.network_device.fields.data_in_transit_encryption.label",
                        "order": 14,
                        "tab_id": "security",
                        "validation": {"required": False},
                    },
                    # Authentication tab
                    "admin_username": {
                        "widget": "text",
                        "placeholder_key": "forms.network_device.fields.admin_username.placeholder",
                        "label_key": "forms.network_device.fields.admin_username.label",
                        "order": 1,
                        "tab_id": "authentication",
                        "validation": {"required": False},
                    },
                    "admin_password_set": {
                        "widget": "checkbox",
                        "placeholder_key": "forms.network_device.fields.admin_password_set.placeholder",
                        "label_key": "forms.network_device.fields.admin_password_set.label",
                        "order": 2,
                        "tab_id": "authentication",
                        "validation": {"required": False},
                    },
                    "password_last_changed": {
                        "widget": "date",
                        "placeholder_key": "forms.network_device.fields.password_last_changed.placeholder",
                        "label_key": "forms.network_device.fields.password_last_changed.label",
                        "order": 3,
                        "tab_id": "authentication",
                        "validation": {"required": False},
                    },
                    "multi_factor_auth_enabled": {
                        "widget": "checkbox",
                        "placeholder_key": "forms.network_device.fields.multi_factor_auth_enabled.placeholder",
                        "label_key": "forms.network_device.fields.multi_factor_auth_enabled.label",
                        "order": 4,
                        "tab_id": "authentication",
                        "validation": {"required": False},
                    },
                    "default_accounts_disabled": {
                        "widget": "checkbox",
                        "placeholder_key": "forms.network_device.fields.default_accounts_disabled.placeholder",
                        "label_key": "forms.network_device.fields.default_accounts_disabled.label",
                        "order": 5,
                        "tab_id": "authentication",
                        "validation": {"required": False},
                    },
                    # Monitoring tab
                    "logging_enabled": {
                        "widget": "checkbox",
                        "placeholder_key": "forms.network_device.fields.logging_enabled.placeholder",
                        "label_key": "forms.network_device.fields.logging_enabled.label",
                        "order": 1,
                        "tab_id": "monitoring",
                        "validation": {"required": False},
                    },
                    "log_retention_days": {
                        "widget": "number",
                        "placeholder_key": "forms.network_device.fields.log_retention_days.placeholder",
                        "label_key": "forms.network_device.fields.log_retention_days.label",
                        "order": 2,
                        "tab_id": "monitoring",
                        "validation": {"required": False},
                    },
                    "syslog_server": {
                        "widget": "text",
                        "placeholder_key": "forms.network_device.fields.syslog_server.placeholder",
                        "label_key": "forms.network_device.fields.syslog_server.label",
                        "order": 3,
                        "tab_id": "monitoring",
                        "validation": {"required": False},
                    },
                    "snmp_enabled": {
                        "widget": "checkbox",
                        "placeholder_key": "forms.network_device.fields.snmp_enabled.placeholder",
                        "label_key": "forms.network_device.fields.snmp_enabled.label",
                        "order": 4,
                        "tab_id": "monitoring",
                        "validation": {"required": False},
                    },
                    "snmp_version": {
                        "widget": "select",
                        "options": [
                            {
                                "value": "v1",
                                "label_key": "forms.network_device.fields.snmp_version.options.v1",
                            },
                            {
                                "value": "v2c",
                                "label_key": "forms.network_device.fields.snmp_version.options.v2c",
                            },
                            {
                                "value": "v3",
                                "label_key": "forms.network_device.fields.snmp_version.options.v3",
                            },
                        ],
                        "placeholder_key": "forms.network_device.fields.snmp_version.placeholder",
                        "label_key": "forms.network_device.fields.snmp_version.label",
                        "order": 5,
                        "tab_id": "monitoring",
                        "validation": {"required": False},
                    },
                    "monitoring_tool": {
                        "widget": "text",
                        "placeholder_key": "forms.network_device.fields.monitoring_tool.placeholder",
                        "label_key": "forms.network_device.fields.monitoring_tool.label",
                        "order": 6,
                        "tab_id": "monitoring",
                        "validation": {"required": False},
                    },
                    # Compliance tab
                    "pci_assessment_date": {
                        "widget": "date",
                        "placeholder_key": "forms.network_device.fields.pci_assessment_date.placeholder",
                        "label_key": "forms.network_device.fields.pci_assessment_date.label",
                        "order": 1,
                        "tab_id": "compliance",
                        "validation": {"required": False},
                    },
                    "pci_compliance_status": {
                        "widget": "select",
                        "options": [
                            {
                                "value": "Compliant",
                                "label_key": "forms.network_device.fields.pci_compliance_status.options.compliant",
                            },
                            {
                                "value": "Non-Compliant",
                                "label_key": "forms.network_device.fields.pci_compliance_status.options.non_compliant",
                            },
                            {
                                "value": "In Progress",
                                "label_key": "forms.network_device.fields.pci_compliance_status.options.in_progress",
                            },
                        ],
                        "placeholder_key": "forms.network_device.fields.pci_compliance_status.placeholder",
                        "label_key": "forms.network_device.fields.pci_compliance_status.label",
                        "order": 2,
                        "tab_id": "compliance",
                        "validation": {"required": False},
                    },
                    "next_assessment_date": {
                        "widget": "date",
                        "placeholder_key": "forms.network_device.fields.next_assessment_date.placeholder",
                        "label_key": "forms.network_device.fields.next_assessment_date.label",
                        "order": 3,
                        "tab_id": "compliance",
                        "validation": {"required": False},
                    },
                    "compliance_notes": {
                        "widget": "textarea",
                        "placeholder_key": "forms.network_device.fields.compliance_notes.placeholder",
                        "label_key": "forms.network_device.fields.compliance_notes.label",
                        "order": 4,
                        "tab_id": "compliance",
                        "validation": {"required": False},
                    },
                    "last_patch_date": {
                        "widget": "date",
                        "placeholder_key": "forms.network_device.fields.last_patch_date.placeholder",
                        "label_key": "forms.network_device.fields.last_patch_date.label",
                        "order": 5,
                        "tab_id": "compliance",
                        "validation": {"required": False},
                    },
                    "patch_level": {
                        "widget": "text",
                        "placeholder_key": "forms.network_device.fields.patch_level.placeholder",
                        "label_key": "forms.network_device.fields.patch_level.label",
                        "order": 6,
                        "tab_id": "compliance",
                        "validation": {"required": False},
                    },
                    "vulnerability_scan_date": {
                        "widget": "date",
                        "placeholder_key": "forms.network_device.fields.vulnerability_scan_date.placeholder",
                        "label_key": "forms.network_device.fields.vulnerability_scan_date.label",
                        "order": 7,
                        "tab_id": "compliance",
                        "validation": {"required": False},
                    },
                    "vulnerability_status": {
                        "widget": "select",
                        "options": [
                            {
                                "value": "Compliant",
                                "label_key": "forms.network_device.fields.vulnerability_status.options.compliant",
                            },
                            {
                                "value": "Non-Compliant",
                                "label_key": "forms.network_device.fields.vulnerability_status.options.non_compliant",
                            },
                            {
                                "value": "Pending",
                                "label_key": "forms.network_device.fields.vulnerability_status.options.pending",
                            },
                        ],
                        "placeholder_key": "forms.network_device.fields.vulnerability_status.placeholder",
                        "label_key": "forms.network_device.fields.vulnerability_status.label",
                        "order": 8,
                        "tab_id": "compliance",
                        "validation": {"required": False},
                    },
                    # Lifecycle tab
                    "power_state": {
                        "widget": "select",
                        "options": [
                            {
                                "value": "On",
                                "label_key": "forms.network_device.fields.power_state.options.on",
                            },
                            {
                                "value": "Off",
                                "label_key": "forms.network_device.fields.power_state.options.off",
                            },
                            {
                                "value": "Standby",
                                "label_key": "forms.network_device.fields.power_state.options.standby",
                            },
                        ],
                        "placeholder_key": "forms.network_device.fields.power_state.placeholder",
                        "label_key": "forms.network_device.fields.power_state.label",
                        "order": 1,
                        "tab_id": "lifecycle",
                        "validation": {"required": False},
                    },
                    "creation_date": {
                        "widget": "date",
                        "placeholder_key": "forms.network_device.fields.creation_date.placeholder",
                        "label_key": "forms.network_device.fields.creation_date.label",
                        "order": 2,
                        "tab_id": "lifecycle",
                        "validation": {"required": False},
                    },
                    "scheduled_decommission_date": {
                        "widget": "date",
                        "placeholder_key": "forms.network_device.fields.scheduled_decommission_date.placeholder",
                        "label_key": "forms.network_device.fields.scheduled_decommission_date.label",
                        "order": 3,
                        "tab_id": "lifecycle",
                        "validation": {"required": False},
                    },
                    "ha_enabled": {
                        "widget": "checkbox",
                        "placeholder_key": "forms.network_device.fields.ha_enabled.placeholder",
                        "label_key": "forms.network_device.fields.ha_enabled.label",
                        "order": 4,
                        "tab_id": "lifecycle",
                        "validation": {"required": False},
                    },
                    "redundancy_level": {
                        "widget": "select",
                        "options": [
                            {
                                "value": "None",
                                "label_key": "forms.network_device.fields.redundancy_level.options.none",
                            },
                            {
                                "value": "N+1",
                                "label_key": "forms.network_device.fields.redundancy_level.options.n_plus_1",
                            },
                            {
                                "value": "N+2",
                                "label_key": "forms.network_device.fields.redundancy_level.options.n_plus_2",
                            },
                        ],
                        "placeholder_key": "forms.network_device.fields.redundancy_level.placeholder",
                        "label_key": "forms.network_device.fields.redundancy_level.label",
                        "order": 5,
                        "tab_id": "lifecycle",
                        "validation": {"required": False},
                    },
                    "failover_capability": {
                        "widget": "checkbox",
                        "placeholder_key": "forms.network_device.fields.failover_capability.placeholder",
                        "label_key": "forms.network_device.fields.failover_capability.label",
                        "order": 6,
                        "tab_id": "lifecycle",
                        "validation": {"required": False},
                    },
                    # Relationships tab
                    "groups": {
                        "widget": "relationship",
                        "quick_create_resource": "group",
                        "placeholder_key": "forms.network_device.fields.group_id.placeholder",
                        "label_key": "forms.network_device.fields.group_id.label",
                        "order": 1,
                        "tab_id": "groups",
                        "validation": {"required": False},
                    },
                },
            },
        }
        return enhanced_schema

    def _get_software_schema(self) -> Dict[str, Any]:
        """
        Generate JSON schema for software resource.
        """
        from app.schemas.asset import \
            SoftwareCreate  # Local import to avoid circular

        # Get the base schema from Pydantic
        base_schema = SoftwareCreate.model_json_schema()

        # Enhance the schema with additional metadata
        enhanced_schema = {
            "version": "1.0.0",
            "resource_type": "software",
            "schema": base_schema,
            "ui": {
                "title_key": "forms.software.create.title",
                "description_key": "forms.software.create.description",
                "fields": {
                    "name": {
                        "widget": "text",
                        "placeholder_key": "forms.software.fields.name.placeholder",
                        "label_key": "forms.software.fields.name.label",
                        "order": 1,
                        "validation": {
                            "required": True,
                            "min_length": 1,
                            "max_length": 100,
                            "error_messages": {
                                "required": "forms.software.fields.name.errors.required",
                                "min_length": "forms.software.fields.name.errors.min_length",
                                "max_length": "forms.software.fields.name.errors.max_length",
                            },
                        },
                    },
                    "vendor": {
                        "widget": "text",
                        "placeholder_key": "forms.software.fields.vendor.placeholder",
                        "label_key": "forms.software.fields.vendor.label",
                        "order": 2,
                        "validation": {
                            "required": False,
                            "max_length": 100,
                            "error_messages": {
                                "max_length": "forms.software.fields.vendor.errors.max_length"
                            },
                        },
                    },
                    "description": {
                        "widget": "textarea",
                        "placeholder_key": "forms.software.fields.description.placeholder",
                        "label_key": "forms.software.fields.description.label",
                        "order": 3,
                        "validation": {
                            "required": False,
                            "max_length": 500,
                            "error_messages": {
                                "max_length": "forms.software.fields.description.errors.max_length"
                            },
                        },
                    },
                    "software_type": {
                        "widget": "select",
                        "options": [
                            {
                                "value": "Application",
                                "label_key": "forms.software.fields.software_type.options.application",
                            },
                            {
                                "value": "Operating System",
                                "label_key": "forms.software.fields.software_type.options.operating_system",
                            },
                            {
                                "value": "Utility",
                                "label_key": "forms.software.fields.software_type.options.utility",
                            },
                            {
                                "value": "Security Tool",
                                "label_key": "forms.software.fields.software_type.options.security_tool",
                            },
                        ],
                        "placeholder_key": "forms.software.fields.software_type.placeholder",
                        "label_key": "forms.software.fields.software_type.label",
                        "order": 4,
                        "validation": {"required": False},
                    },
                },
            },
        }
        return enhanced_schema

    def _get_software_edit_schema(self) -> Dict[str, Any]:
        """
        Generate JSON edit schema for software resource.
        This schema contains additional UI metadata for editing, including tab grouping.
        """
        from app.schemas.asset import \
            SoftwareUpdate  # Local import to avoid circular

        # Base schema allows partial updates
        base_schema = SoftwareUpdate.model_json_schema()

        # Define tab definitions so that the frontend can render tabbed forms
        tabs = [
            {"id": "general", "label_key": "forms.tabs.general"},
            {"id": "security", "label_key": "forms.tabs.security"},
            {"id": "lifecycle", "label_key": "forms.tabs.lifecycle"},
            {"id": "groups", "label_key": "forms.tabs.groups"},
            {"id": "compliance", "label_key": "forms.tabs.compliance"},
        ]

        enhanced_schema = {
            "version": "1.0.0",
            "resource_type": "software",
            "schema_type": "edit",
            "schema": base_schema,
            "ui": {
                "title_key": "forms.software.edit.title",
                "description_key": "forms.software.edit.description",
                "tabs": tabs,
                "fields": {
                    # General tab
                    "name": {
                        "widget": "text",
                        "placeholder_key": "forms.software.fields.name.placeholder",
                        "label_key": "forms.software.fields.name.label",
                        "order": 1,
                        "tab_id": "general",
                        "validation": {"required": False},
                    },
                    "vendor": {
                        "widget": "text",
                        "placeholder_key": "forms.software.fields.vendor.placeholder",
                        "label_key": "forms.software.fields.vendor.label",
                        "order": 2,
                        "tab_id": "general",
                        "validation": {"required": False},
                    },
                    "description": {
                        "widget": "textarea",
                        "placeholder_key": "forms.software.fields.description.placeholder",
                        "label_key": "forms.software.fields.description.label",
                        "order": 3,
                        "tab_id": "general",
                        "validation": {"required": False},
                    },
                    "software_type": {
                        "widget": "select",
                        "options": [
                            {
                                "value": "Application",
                                "label_key": "forms.software.fields.software_type.options.application",
                            },
                            {
                                "value": "Operating System",
                                "label_key": "forms.software.fields.software_type.options.operating_system",
                            },
                            {
                                "value": "Utility",
                                "label_key": "forms.software.fields.software_type.options.utility",
                            },
                            {
                                "value": "Security Tool",
                                "label_key": "forms.software.fields.software_type.options.security_tool",
                            },
                        ],
                        "placeholder_key": "forms.software.fields.software_type.placeholder",
                        "label_key": "forms.software.fields.software_type.label",
                        "order": 4,
                        "tab_id": "general",
                        "validation": {"required": False},
                    },
                    
                    # Security tab
                    "encryption_enabled": {
                        "widget": "checkbox",
                        "label_key": "forms.software.fields.encryption_enabled.label",
                        "order": 1,
                        "tab_id": "security",
                        "validation": {"required": False},
                    },
                    "encryption_type": {
                        "widget": "text",
                        "placeholder_key": "forms.software.fields.encryption_type.placeholder",
                        "label_key": "forms.software.fields.encryption_type.label",
                        "order": 2,
                        "tab_id": "security",
                        "validation": {"required": False},
                    },
                    "authentication_required": {
                        "widget": "checkbox",
                        "label_key": "forms.software.fields.authentication_required.label",
                        "order": 3,
                        "tab_id": "security",
                        "validation": {"required": False},
                    },
                    "multi_factor_auth_supported": {
                        "widget": "checkbox",
                        "label_key": "forms.software.fields.multi_factor_auth_supported.label",
                        "order": 4,
                        "tab_id": "security",
                        "validation": {"required": False},
                    },
                    "vulnerability_status": {
                        "widget": "select",
                        "options": [
                            {
                                "value": "Compliant",
                                "label_key": "forms.software.fields.vulnerability_status.options.compliant",
                            },
                            {
                                "value": "Non-Compliant",
                                "label_key": "forms.software.fields.vulnerability_status.options.non_compliant",
                            },
                            {
                                "value": "Pending",
                                "label_key": "forms.software.fields.vulnerability_status.options.pending",
                            },
                        ],
                        "placeholder_key": "forms.software.fields.vulnerability_status.placeholder",
                        "label_key": "forms.software.fields.vulnerability_status.label",
                        "order": 5,
                        "tab_id": "security",
                        "validation": {"required": False},
                    },
                    "data_classification": {
                        "widget": "select",
                        "options": [
                            {
                                "value": "Public",
                                "label_key": "forms.software.fields.data_classification.options.public",
                            },
                            {
                                "value": "Internal",
                                "label_key": "forms.software.fields.data_classification.options.internal",
                            },
                            {
                                "value": "Confidential",
                                "label_key": "forms.software.fields.data_classification.options.confidential",
                            },
                            {
                                "value": "Restricted",
                                "label_key": "forms.software.fields.data_classification.options.restricted",
                            },
                        ],
                        "placeholder_key": "forms.software.fields.data_classification.placeholder",
                        "label_key": "forms.software.fields.data_classification.label",
                        "order": 6,
                        "tab_id": "security",
                        "validation": {"required": False},
                    },
                    # Lifecycle tab
                    "end_of_life_date": {
                        "widget": "date",
                        "placeholder_key": "forms.software.fields.end_of_life_date.placeholder",
                        "label_key": "forms.software.fields.end_of_life_date.label",
                        "order": 1,
                        "tab_id": "lifecycle",
                        "validation": {"required": False},
                    },
                    "end_of_support_date": {
                        "widget": "date",
                        "placeholder_key": "forms.software.fields.end_of_support_date.placeholder",
                        "label_key": "forms.software.fields.end_of_support_date.label",
                        "order": 2,
                        "tab_id": "lifecycle",
                        "validation": {"required": False},
                    },
                    "replacement_planned": {
                        "widget": "checkbox",
                        "label_key": "forms.software.fields.replacement_planned.label",
                        "order": 3,
                        "tab_id": "lifecycle",
                        "validation": {"required": False},
                    },
                    # Groups tab
                    "groups": {
                        "widget": "relationship",
                        "quick_create_resource": "group",
                        "placeholder_key": "forms.software.fields.group_id.placeholder",
                        "label_key": "forms.software.fields.group_id.label",
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
