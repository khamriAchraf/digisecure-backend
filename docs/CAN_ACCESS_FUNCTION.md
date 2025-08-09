# Can Access Function Documentation

## Overview

The `can_access(user, resource)` function determines whether a given user has the right to view or interact with a specific resource instance. This is **not** about permissions (what the user can do), but about **object-level access control** (which objects the user is allowed to see or reference).

## 🧠 Logic Breakdown

The function implements a hierarchical access control system with the following checks in order:

### 1. Direct Assignment Check
- **Condition**: `resource.assigned_to == user.id`
- **Access**: ✅ **ALLOWED**
- **Example**: A laptop directly assigned to the user
- **Use Case**: Personal equipment, individually assigned assets

### 2. Group Membership Check
- **Condition**: User and resource share the same group
- **Access**: ✅ **ALLOWED**
- **Example**: A computer shared by the IT department group
- **Use Case**: Team equipment, shared resources

### 3. Hierarchical Group Check
- **Condition**: User's group is a parent of the resource's group
- **Access**: ✅ **ALLOWED**
- **Example**: IT Manager (parent group) can access Network Team (child group) resources
- **Use Case**: Organizational hierarchy, management oversight

### 4. Location Affiliation Check (Optional)
- **Condition**: User and resource belong to the same location
- **Status**: 🔄 **Not implemented** (requires location model enhancement)
- **Future Use**: Department-based access, geographic scoping

### 5. Fallback
- **Condition**: None of the above conditions are met
- **Access**: ❌ **DENIED**
- **Example**: User trying to access another department's equipment

## 📥 Inputs

### User Object
```python
user: User
# Required attributes:
- id: int                    # Primary key
- groups: List[Group]        # Groups the user belongs to
# Optional attributes:
- location: str              # User's location (string field)
```

### Resource Object
```python
resource: Any
# Required attributes (checked in order):
- assigned_to: Optional[int] # User ID this resource is assigned to
- group_id: Optional[int]    # Group ID this resource belongs to
- location_id: Optional[int] # Location ID this resource belongs to
```

## 📤 Output

```python
bool: True if access is allowed, False otherwise
```

## 🔧 Usage Examples

### Basic Usage

```python
from app.core.security import can_access
from app.db.crud.user import get_user
from app.db.crud.asset import get_asset

# Get user and resource
user = get_user(db, user_id=123)
asset = get_asset(db, asset_id=456)

# Check access
if can_access(user, asset):
    print(f"User {user.username} can access {asset.name}")
else:
    print(f"Access denied to {asset.name}")
```

### In API Endpoints

```python
from fastapi import HTTPException
from app.core.security import can_access

@router.get("/assets/{asset_id}")
def get_asset(asset_id: int, current_user: User = Depends(get_current_user)):
    asset = get_asset(db, asset_id)
    if not asset:
        raise HTTPException(status_code=404, detail="Asset not found")
    
    if not can_access(current_user, asset):
        raise HTTPException(status_code=403, detail="Access denied")
    
    return asset
```

### In Service Layer

```python
class AssetService:
    def get_user_accessible_assets(self, user: User) -> List[Asset]:
        """Get all assets the user can access"""
        all_assets = self.db.query(Asset).all()
        return [asset for asset in all_assets if can_access(user, asset)]
    
    def filter_assets_by_access(self, user: User, assets: List[Asset]) -> List[Asset]:
        """Filter a list of assets based on user access"""
        return [asset for asset in assets if can_access(user, asset)]
```

## 🧪 Testing

### Unit Tests

```python
import pytest
from unittest.mock import Mock
from app.core.security import can_access

def test_direct_assignment_access():
    # Create user
    user = Mock()
    user.id = 1
    user.groups = []
    
    # Create resource assigned to user
    resource = Mock()
    resource.assigned_to = 1
    resource.group_id = None
    
    assert can_access(user, resource) is True

def test_group_membership_access():
    # Create group
    group = Mock()
    group.id = 10
    group.children = []
    
    # Create user with group
    user = Mock()
    user.id = 1
    user.groups = [group]
    
    # Create resource in same group
    resource = Mock()
    resource.assigned_to = None
    resource.group_id = 10
    
    assert can_access(user, resource) is True
```

### Integration Tests

```python
@pytest.mark.integration
def test_can_access_with_real_data():
    # Create test data
    user = create_test_user()
    group = create_test_group()
    asset = create_test_asset(assigned_to=user.id)
    
    # Test access
    assert can_access(user, asset) is True
    
    # Test group access
    user.groups.append(group)
    asset.assigned_to = None
    asset.group_id = group.id
    
    assert can_access(user, asset) is True
```

## 📊 Logging

The function automatically logs access checks with detailed information:

```python
# Successful access
logger.info("access_check", extra={
    "log_type": "access",
    "user_id": 123,
    "resource_type": "Computer",
    "resource_id": 456,
    "access_reason": "direct_assignment",
    "success": True
})

# Failed access
logger.warning("access_check", extra={
    "log_type": "access", 
    "user_id": 123,
    "resource_type": "Computer",
    "resource_id": 456,
    "access_reason": "none",
    "success": False
})
```

## 🔄 Performance Considerations

### Database Queries
- The function assumes user groups are already loaded
- Use `joinedload(User.groups)` when fetching users for access checks
- Consider caching group hierarchies for large organizations

### Optimization Tips
```python
# Efficient: Load groups with user
user = db.query(User).options(joinedload(User.groups)).filter(User.id == user_id).first()

# Inefficient: Lazy loading groups
user = db.query(User).filter(User.id == user_id).first()
# This will trigger additional queries when accessing user.groups
```

## 🚀 Advanced Usage

### Custom Resource Types

The function works with any object that has the required attributes:

```python
class Document:
    def __init__(self, assigned_to=None, group_id=None, location_id=None):
        self.assigned_to = assigned_to
        self.group_id = group_id
        self.location_id = location_id

# Can be used with can_access
document = Document(assigned_to=user.id)
assert can_access(user, document) is True
```

### Batch Access Checking

```python
def check_multiple_access(user: User, resources: List[Any]) -> Dict[int, bool]:
    """Check access for multiple resources at once"""
    results = {}
    for resource in resources:
        results[resource.id] = can_access(user, resource)
    return results
```

### Access Reporting

```python
def generate_access_report(user: User, resources: List[Any]) -> Dict[str, Any]:
    """Generate detailed access report for a user"""
    accessible = []
    inaccessible = []
    
    for resource in resources:
        if can_access(user, resource):
            accessible.append(resource)
        else:
            inaccessible.append(resource)
    
    return {
        "user_id": user.id,
        "total_resources": len(resources),
        "accessible_count": len(accessible),
        "inaccessible_count": len(inaccessible),
        "accessible_resources": accessible,
        "inaccessible_resources": inaccessible
    }
```

## 🔧 Configuration

### Super Admin Override

To give super admins access to everything, uncomment this section in the function:

```python
# 4. Super Admin Override (optional)
if user.role and user.role.name == "Super-Admin":
    outcome = True
    access_reason = "super_admin"
```

### Location-Based Access

To implement location-based access, enhance the location check:

```python
# 3. Location Affiliation Check
elif (hasattr(resource, 'location_id') and resource.location_id and 
      hasattr(user, 'location_id') and user.location_id):
    if resource.location_id == user.location_id:
        outcome = True
        access_reason = "location_affiliation"
```

## 🐛 Troubleshooting

### Common Issues

1. **Access always denied**: Check if user has groups loaded
2. **Group hierarchy not working**: Verify parent-child relationships are set up
3. **Performance issues**: Use `joinedload` to preload user groups

### Debug Mode

Enable debug logging to see detailed access decisions:

```python
import logging
logging.getLogger("app.core.security").setLevel(logging.DEBUG)
```

## 📚 Related Documentation

- [User Management](../docs/User_Management_Service_Requirements.md)
- [Group Management](../app/db/models/group.py)
- [Asset Management](../app/db/models/asset.py)
- [Security Module](../app/core/security.py) 