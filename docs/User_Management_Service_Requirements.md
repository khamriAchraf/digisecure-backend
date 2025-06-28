
# User Management Service Requirements (GLPI-style)

## 📋 Functional Requirements

### 1. User Accounts
- Create, view, update, and delete users
- Support bulk import/export (CSV)
- Password hashing and reset flow
- Email verification and optional 2FA

### 2. User Types
- Internal users
- External users
- LDAP users (optional later)
- User status: active, inactive, deleted

### 3. Attributes
- Full name
- Email
- Username
- Password
- Phone (optional)
- Department (optional)
- Location (optional)
- Profile (role)
- Entity (organization context)
- Language
- Theme (UI preference)

### 4. Roles / Profiles
- Create/manage profiles with permission sets
- Assign users to profiles (e.g., admin, tech, self-service)
- Each profile defines:
  - Module access (assets, tickets, etc.)
  - Allowed actions (read, create, update, delete)
  - Visibility scope (own org vs all)

### 5. Entities / Multi-org Support
- Support multi-entity mode:
  - Users belong to one or more entities
  - Can have different roles per entity
- Entity-level visibility and access rules

### 6. Authentication
- JWT-based login
- Login history (IP, timestamp, device info)
- Failed login attempt tracking
- Lockout after N failed attempts
- Support session expiration and token refresh

### 7. User Delegation & Supervision
- Ability to define supervisors
- Delegation for time-off or absence
- Users can be assigned to groups or teams

### 8. Search & Filters
- Filter users by entity, profile, status, department
- Full-text search on name, email, username

### 9. Audit Trail
- Log creation, update, deletion of users
- Who changed what and when

### 10. Notifications
- Email notification for:
  - New account created
  - Password reset
  - Profile changes
- Optional: webhook support

## 🧱 Non-Functional Requirements

### ✅ Security
- Passwords must be hashed (e.g., bcrypt)
- Input sanitization
- Per-schema (tenant) isolation
- Role/attribute-based access control (ABAC)

### 📈 Scalability
- Must work across multiple tenants (via schema or subdomain)
- Support bulk operations efficiently

### 🧪 Testability
- Unit + e2e tests
- Mock LDAP and SMTP

 Permission Matrix Verified:
Role	Read	Create	Update	Delete	Search
Super-Admin	✅	✅	✅	✅	✅
Admin	✅	✅	✅	✅	✅
Supervisor	✅	✅	✅	❌	✅
Technician	✅	❌	✅	❌	✅
Hotliner	✅	❌	❌	❌	✅
Observer	✅	❌	❌	❌	✅
Self-Service	Own only	❌	❌	❌	❌