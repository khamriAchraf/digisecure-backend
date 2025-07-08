# Role-Based Permissions

This document outlines the permission structure for each role in the system. Permissions are defined by a combination of a **resource** (e.g., `user`, `role`, `group`) and an **action** (e.g., `read`, `create`, `update`, `delete`, `purge`).

## Permission Matrix

The following table details the permissions assigned to each role for the available resources.

| Role           | User Management                        | Role Management                        | Group Management                       |
| :------------- | :------------------------------------- | :------------------------------------- | :------------------------------------- |
| **Super-Admin**| `read`, `create`, `update`, `delete`, `purge` | `read`, `create`, `update`, `delete`, `purge` | `read`, 'create', `update`, `delete`, `purge` |
| **Admin**      | `read`, `create`, `update`, `delete`       | -                                      | -                                      |
| **Supervisor** | `read`, `create`, `update`             | -                                      | -                                      |
| **Technician** | `read`, `update`                       | -                                      | -                                      |
| **Hotliner**   | `read`                                 | -                                      | -                                      |
| **Observer**   | `read`                                 | -                                      | -                                      |
| **Self-Service**| -                                      | -                                      | -                                      |

## Permission Details

### Resources

-   **User**: Represents user accounts in the system.
-   **Role**: Represents user roles and their associated permissions.
-   **Group**: Represents user groups for organization or skill-based assignments.

#### Configuration Resource

Supporting entities such as **assetTypes**, **statuses**, **locations**, **manufacturers**, and similar types are all managed under a single resource type called **configuration**. Instead of assigning separate permissions for each of these entities, permissions are controlled collectively through the **configuration** resource. This simplifies permission management for all system configuration data.

### Actions

-   **read**: View existing resources.
-   **create**: Create new resources.
-   **update**: Modify existing resources.
-   **delete**: Soft-delete or deactivate resources.
-   **purge**: Permanently remove resources from the system. 