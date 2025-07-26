# Access Filters Function Documentation

## Overview

The `access_filters(user, resource_model)` function builds SQLAlchemy filter expressions that implement the same access control rules as the `can_access(user, resource)` function. This allows you to apply user-specific access controls directly to database queries, ensuring that users only see resources they have permission to access.

## 🎯 Purpose

Instead of fetching all resources and then filtering them in application code, `access_filters` generates SQLAlchemy conditions that can be applied at the database level. This approach is:

- **More efficient**: Filters are applied in the database, reducing data transfer
- **More secure**: Access control is enforced at the query level
- **More scalable**: Works well with large datasets and pagination
- **Consistent**: Uses the same logic as the `can_access` function

## 📋 Function Signature

```python
def access_filters(user: User, resource_model) -> Optional[List[SQLAlchemyFilter]]:
    """
    Build SQLAlchemy filters for querying resources based on user access rules.
    
    Args:
        user: User object with id, groups, and role attributes
        resource_model: SQLAlchemy model class (e.g., Asset) to build filters for
        
    Returns:
        list: List of SQLAlchemy filter expressions, or None if no filters needed (Super-Admin)
    """
```

## 🔧 How It Works

The function implements the same access control logic as `can_access`:

### 1. Super-Admin Override
- **Condition**: `user.role.name == "Super-Admin"`
- **Result**: Returns `None` (no filters applied)
- **Effect**: Super-Admins can see all resources

### 2. Direct Assignment Access
- **Condition**: `resource.assigned_to == user.id`
- **SQLAlchemy Filter**: `resource_model.assigned_to == user.id`
- **Effect**: Users can see resources directly assigned to them

### 3. Group Membership Access
- **Condition**: User and resource share the same group
- **SQLAlchemy Filter**: `resource_model.group_id.in_(user_group_ids)`
- **Effect**: Users can see resources in their groups

### 4. Hierarchical Group Access
- **Condition**: User's group is a parent of the resource's group
- **SQLAlchemy Filter**: `resource_model.group_id.in_(accessible_group_ids)`
- **Effect**: Parent groups can access child group resources

## 📝 Usage Examples

### Basic Usage

```python
from app.core.security import access_filters
from app.db.models.asset import Asset

# Get access filters for the current user
access_conditions = access_filters(current_user, Asset)

if access_conditions is None:
    # Super-Admin: no restrictions
    assets = db.query(Asset).all()
else:
    # Apply access filters
    query = db.query(Asset)
    for condition in access_conditions:
        query = query.filter(condition)
    assets = query.all()
```

### With Pagination and Search

```python
def get_user_accessible_assets(db, user, page=1, per_page=20, search=None):
    access_conditions = access_filters(user, Asset)
    
    query = db.query(Asset)
    
    # Apply access filters first
    if access_conditions:
        for condition in access_conditions:
            query = query.filter(condition)
    
    # Apply search
    if search:
        search_term = f"%{search}%"
        query = query.filter(
            or_(
                Asset.name.ilike(search_term),
                Asset.serial_number.ilike(search_term),
            )
        )
    
    # Apply pagination
    total = query.count()
    assets = query.offset((page - 1) * per_page).limit(per_page).all()
    
    return assets, total
```

### In Service Layer

```python
class AssetService:
    def get_paginated_assets(self, page, per_page, search=None):
        # Get access filters
        access_conditions = access_filters(self.current_user, Asset)
        
        # Build query
        query = self.db.query(Asset)
        
        # Apply access filters
        if access_conditions:
            for condition in access_conditions:
                query = query.filter(condition)
        
        # Apply additional filters, search, sorting, pagination...
        # ... (implementation details)
        
        return assets, total
```

## 🔍 Generated Filter Examples

### Regular User with Group Membership

```python
# User belongs to groups [1, 2, 3]
# User ID: 123

access_conditions = access_filters(user, Asset)

# Generated filters:
[
    or_(
        Asset.assigned_to == 123,           # Direct assignment
        Asset.group_id.in_([1, 2, 3])      # Group membership
    )
]
```

### User with Hierarchical Groups

```python
# User belongs to group 1 (parent)
# Group 1 has children: groups 2, 3
# User ID: 123

access_conditions = access_filters(user, Asset)

# Generated filters:
[
    or_(
        Asset.assigned_to == 123,           # Direct assignment
        Asset.group_id.in_([1, 2, 3])      # Group + hierarchical access
    )
]
```

### Super-Admin User

```python
# Super-Admin user

access_conditions = access_filters(user, Asset)

# Result: None (no filters applied)
# Query: db.query(Asset).all()  # Returns all assets
```

## ⚠️ Important Considerations

### 1. Model Requirements

The resource model must have the expected attributes:
- `assigned_to`: Foreign key to users table
- `group_id`: Foreign key to groups table

```python
class Asset(Base):
    __tablename__ = "assets"
    assigned_to = Column(Integer, ForeignKey("users.id"), nullable=True)
    group_id = Column(Integer, ForeignKey("groups.id"), nullable=True)
```

### 2. User Object Requirements

The user object must have:
- `id`: User's primary key
- `groups`: List of Group objects with `id` and `children` attributes
- `role`: Role object with `name` attribute

### 3. Performance Considerations

- **Indexes**: Ensure proper database indexes on `assigned_to` and `group_id` columns
- **Eager Loading**: Consider using `joinedload()` for user groups to avoid N+1 queries
- **Caching**: For frequently accessed users, consider caching their group memberships

### 4. Security

- Always apply access filters before any other query modifications
- Never bypass access filters for "performance" reasons
- Test thoroughly with different user roles and group hierarchies

## 🧪 Testing

### Unit Tests

```python
def test_access_filters_super_admin():
    super_admin = create_super_admin_user()
    conditions = access_filters(super_admin, Asset)
    assert conditions is None

def test_access_filters_regular_user():
    user = create_regular_user_with_groups([1, 2])
    conditions = access_filters(user, Asset)
    assert conditions is not None
    assert len(conditions) == 1  # One OR condition

def test_access_filters_hierarchical_groups():
    parent_group = create_group_with_children([1, 2])
    user = create_user_with_group(parent_group)
    conditions = access_filters(user, Asset)
    # Verify that child group IDs are included in the filter
```

### Integration Tests

```python
def test_asset_query_with_access_filters():
    # Create test data
    user = create_test_user()
    asset1 = create_asset(assigned_to=user.id)
    asset2 = create_asset(group_id=user.groups[0].id)
    asset3 = create_asset(assigned_to=999)  # Other user's asset
    
    # Apply access filters
    conditions = access_filters(user, Asset)
    query = db.query(Asset)
    for condition in conditions:
        query = query.filter(condition)
    
    assets = query.all()
    
    # Verify results
    assert asset1 in assets  # Direct assignment
    assert asset2 in assets  # Group membership
    assert asset3 not in assets  # No access
```

## 🔄 Migration from can_access

If you're currently using `can_access` for filtering in application code:

### Before (Inefficient)
```python
# Fetch all assets, then filter
all_assets = db.query(Asset).all()
user_assets = [asset for asset in all_assets if can_access(user, asset)]
```

### After (Efficient)
```python
# Apply filters at database level
conditions = access_filters(user, Asset)
query = db.query(Asset)
if conditions:
    for condition in conditions:
        query = query.filter(condition)
user_assets = query.all()
```

## 📚 Related Functions

- `can_access(user, resource)`: Check access for a specific resource instance
- `has_permission(user, action, resource)`: Check user permissions
- `_check_group_hierarchy(user_group, resource_group_id)`: Check hierarchical group access

## 🐛 Troubleshooting

### Common Issues

1. **No filters generated for regular user**
   - Check if user has groups loaded: `user.groups`
   - Verify user role is not "Super-Admin"

2. **Filters too restrictive**
   - Check group hierarchy relationships
   - Verify `_add_child_group_ids` function is working correctly

3. **Performance issues**
   - Ensure proper database indexes
   - Consider eager loading user groups
   - Monitor query execution plans

### Debug Mode

```python
# Enable debug logging to see generated filters
import logging
logging.getLogger('app.core.security').setLevel(logging.DEBUG)

conditions = access_filters(user, Asset)
print(f"Generated conditions: {conditions}")
``` 