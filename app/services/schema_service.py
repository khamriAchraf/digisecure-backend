from datetime import datetime
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
            f"User {self.current_user.id} attempts to GET schema for {resource_type} at {datetime.utcnow().isoformat()}"
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

    def _generate_schema_for_resource(self, resource_type: str) -> Dict[str, Any]:
        """
        Generate JSON schema for the specified resource type.
        """
        schemas = {
            "group": self._get_group_schema(),
            "user": self._get_user_schema(),
            "role": self._get_role_schema(),
            # Add other resource types here as they're implemented
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

    def _get_user_schema(self) -> Dict[str, Any]:
        """
        Generate JSON schema for user resource.
        """
        # Get the base schema from Pydantic
        base_schema = UserCreate.model_json_schema()

        # Get available roles for the select dropdown
        available_roles = self._get_role_options()

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
                        "options": available_roles,
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

    def get_available_resources(self) -> Dict[str, Any]:
        """
        Get list of available resource types that the user has create permission for.
        """
        logger.info(
            f"User {self.current_user.id} attempts to GET available resources at {datetime.utcnow().isoformat()}"
        )

        available_resources = []

        # Check each resource type for create permission
        resource_types = ["group", "user", "role", "asset", "configuration"]

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
