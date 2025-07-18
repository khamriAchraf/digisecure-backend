# Translation Keys for Schema-Driven Forms

This document outlines all the translation keys used in the schema service for the dynamic form system.

## Group Resource Translation Keys

### Form Title and Description
- `forms.group.create.title` - "Create Group"
- `forms.group.create.description` - "Create a new group in the system"

### Field Labels
- `forms.group.fields.name.label` - "Group Name"
- `forms.group.fields.description.label` - "Description"
- `forms.group.fields.type.label` - "Group Type"
- `forms.group.fields.contain_users.label` - "Can contain users"
- `forms.group.fields.contain_items.label` - "Can contain items"
- `forms.group.fields.comment.label` - "Comments"
- `forms.group.fields.parent_id.label` - "Parent Group"

### Field Placeholders
- `forms.group.fields.name.placeholder` - "Enter group name"
- `forms.group.fields.description.placeholder` - "Enter group description"
- `forms.group.fields.type.placeholder` - "Select group type"
- `forms.group.fields.comment.placeholder` - "Enter any additional comments"
- `forms.group.fields.parent_id.placeholder` - "Select parent group (optional)"

### Field Help Text
- `forms.group.fields.name.help_text` - "Group name must be unique and between 1-100 characters"
- `forms.group.fields.description.help_text` - "Optional description of the group (max 500 characters)"
- `forms.group.fields.type.help_text` - "Type of group (optional)"
- `forms.group.fields.contain_users.help_text` - "Whether this group can contain user members"
- `forms.group.fields.contain_items.help_text` - "Whether this group can contain asset items"
- `forms.group.fields.comment.help_text` - "Optional comments about the group (max 1000 characters)"
- `forms.group.fields.parent_id.help_text` - "Parent group if this is a subgroup"

### Field Options
- `forms.group.fields.type.options.skill` - "Skill Group"
- `forms.group.fields.type.options.org` - "Organization Group"
- `forms.group.fields.type.options.notification` - "Notification Group"
- `forms.group.fields.parent_id.options.no_parent` - "No parent group"
- `forms.group.fields.parent_id.options.group_with_type` - "{name} ({type})" (with parameters)

### Validation Error Messages
- `forms.group.fields.name.errors.required` - "Group name is required"
- `forms.group.fields.name.errors.min_length` - "Group name must be at least 1 character"
- `forms.group.fields.name.errors.max_length` - "Group name cannot exceed 100 characters"
- `forms.group.fields.description.errors.max_length` - "Description cannot exceed 500 characters"
- `forms.group.fields.comment.errors.max_length` - "Comments cannot exceed 1000 characters"

## User Resource Translation Keys

### Form Title and Description
- `forms.user.create.title` - "Create User"
- `forms.user.create.description` - "Create a new user in the system"

### Field Labels
- `forms.user.fields.email.label` - "Email Address"
- `forms.user.fields.username.label` - "Username"
- `forms.user.fields.password.label` - "Password"
- `forms.user.fields.full_name.label` - "Full Name"
- `forms.user.fields.status.label` - "Status"
- `forms.user.fields.language.label` - "Language"
- `forms.user.fields.theme.label` - "Theme"
- `forms.user.fields.location.label` - "Location"
- `forms.user.fields.phone.label` - "Phone Number"
- `forms.user.fields.secondary_phone.label` - "Secondary Phone"
- `forms.user.fields.timezone.label` - "Timezone"
- `forms.user.fields.valid_from.label` - "Valid From"
- `forms.user.fields.valid_until.label` - "Valid Until"
- `forms.user.fields.administartive_number.label` - "Administrative Number"
- `forms.user.fields.roles.label` - "Roles"

### Field Placeholders
- `forms.user.fields.email.placeholder` - "Enter email address"
- `forms.user.fields.username.placeholder` - "Enter username"
- `forms.user.fields.password.placeholder` - "Enter password"
- `forms.user.fields.full_name.placeholder` - "Enter full name"
- `forms.user.fields.status.placeholder` - "Select status"
- `forms.user.fields.language.placeholder` - "Select language"
- `forms.user.fields.theme.placeholder` - "Select theme"
- `forms.user.fields.location.placeholder` - "Enter location"
- `forms.user.fields.phone.placeholder` - "Enter phone number"
- `forms.user.fields.secondary_phone.placeholder` - "Enter secondary phone number"
- `forms.user.fields.timezone.placeholder` - "Select timezone"
- `forms.user.fields.valid_from.placeholder` - "Select valid from date"
- `forms.user.fields.valid_until.placeholder` - "Select valid until date"
- `forms.user.fields.administartive_number.placeholder` - "Enter administrative number"
- `forms.user.fields.roles.placeholder` - "Select roles"

### Field Help Text
- `forms.user.fields.email.help_text` - "User's email address (must be unique)"
- `forms.user.fields.username.help_text` - "Unique username for login"
- `forms.user.fields.password.help_text` - "Secure password for the account"
- `forms.user.fields.full_name.help_text` - "User's full name (optional)"
- `forms.user.fields.status.help_text` - "User account status"
- `forms.user.fields.language.help_text` - "User's preferred language"
- `forms.user.fields.theme.help_text` - "User's preferred theme"
- `forms.user.fields.location.help_text` - "User's physical location (optional)"
- `forms.user.fields.phone.help_text` - "Primary phone number (optional)"
- `forms.user.fields.secondary_phone.help_text` - "Secondary phone number (optional)"
- `forms.user.fields.timezone.help_text` - "User's timezone"
- `forms.user.fields.valid_from.help_text` - "Account validity start date (optional)"
- `forms.user.fields.valid_until.help_text` - "Account validity end date (optional)"
- `forms.user.fields.administartive_number.help_text` - "Administrative reference number (optional)"
- `forms.user.fields.roles.help_text` - "User roles and permissions"

### Field Options
- `forms.user.fields.status.options.active` - "Active"
- `forms.user.fields.status.options.inactive` - "Inactive"
- `forms.user.fields.status.options.deleted` - "Deleted"
- `forms.user.fields.language.options.en` - "English"
- `forms.user.fields.language.options.fr` - "French"
- `forms.user.fields.language.options.es` - "Spanish"
- `forms.user.fields.language.options.de` - "German"
- `forms.user.fields.theme.options.light` - "Light"
- `forms.user.fields.theme.options.dark` - "Dark"
- `forms.user.fields.timezone.options.utc` - "UTC"
- `forms.user.fields.timezone.options.america_new_york` - "America/New York"
- `forms.user.fields.timezone.options.europe_london` - "Europe/London"
- `forms.user.fields.timezone.options.europe_paris` - "Europe/Paris"
- `forms.user.fields.timezone.options.asia_tokyo` - "Asia/Tokyo"
- `forms.user.fields.roles.options.role_name` - "{name} - {description}" (with parameters)

### Validation Error Messages
- `forms.user.fields.email.errors.required` - "Email address is required"
- `forms.user.fields.email.errors.invalid` - "Please enter a valid email address"
- `forms.user.fields.username.errors.required` - "Username is required"
- `forms.user.fields.password.errors.required` - "Password is required"

## Resource Type Translation Keys

### Resource Names
- `resources.group.name` - "Group"
- `resources.user.name` - "User"
- `resources.role.name` - "Role"
- `resources.asset.name` - "Asset"
- `resources.configuration.name` - "Configuration"

### Resource Descriptions
- `resources.group.description` - "Create and manage groups"
- `resources.user.description` - "Create and manage users"
- `resources.role.description` - "Create and manage roles"
- `resources.asset.description` - "Create and manage assets"
- `resources.configuration.description` - "Create and manage configuration items"

## Frontend Implementation Notes

### Translation Function
The frontend should implement a translation function that:
1. Takes a translation key and optional parameters
2. Returns the translated text
3. Falls back to the key if translation is not found

Example:
```typescript
const t = (key: string, params?: Record<string, string>) => {
  const translation = translations[key] || key;
  if (params) {
    return translation.replace(/\{(\w+)\}/g, (_, param) => params[param] || '');
  }
  return translation;
};
```

### Usage Examples
```typescript
// Simple translation
t('forms.group.create.title') // "Create Group"

// Translation with parameters
t('forms.group.fields.parent_id.options.group_with_type', {
  name: 'IT Department',
  type: 'org'
}) // "IT Department (org)"

// Field label
t('forms.group.fields.name.label') // "Group Name"

// Error message
t('forms.group.fields.name.errors.required') // "Group name is required"
```

### Translation File Structure
The frontend should maintain translation files like:
```json
{
  "forms": {
    "group": {
      "create": {
        "title": "Create Group",
        "description": "Create a new group in the system"
      },
      "fields": {
        "name": {
          "label": "Group Name",
          "placeholder": "Enter group name",
          "help_text": "Group name must be unique and between 1-100 characters",
          "errors": {
            "required": "Group name is required",
            "min_length": "Group name must be at least 1 character",
            "max_length": "Group name cannot exceed 100 characters"
          }
        }
      }
    },
    "user": {
      "create": {
        "title": "Create User",
        "description": "Create a new user in the system"
      },
      "fields": {
        "email": {
          "label": "Email Address",
          "placeholder": "Enter email address",
          "help_text": "User's email address (must be unique)",
          "errors": {
            "required": "Email address is required",
            "invalid": "Please enter a valid email address"
          }
        },
        "username": {
          "label": "Username",
          "placeholder": "Enter username",
          "help_text": "Unique username for login",
          "errors": {
            "required": "Username is required"
          }
        },
        "password": {
          "label": "Password",
          "placeholder": "Enter password",
          "help_text": "Secure password for the account",
          "errors": {
            "required": "Password is required"
          }
        },
        "status": {
          "label": "Status",
          "placeholder": "Select status",
          "help_text": "User account status",
          "options": {
            "active": "Active",
            "inactive": "Inactive",
            "deleted": "Deleted"
          }
        },
        "roles": {
          "label": "Roles",
          "placeholder": "Select roles",
          "help_text": "User roles and permissions",
          "options": {
            "role_name": "{name} - {description}"
          }
        }
      }
    }
  },
  "resources": {
    "group": {
      "name": "Group",
      "description": "Create and manage groups"
    },
    "user": {
      "name": "User",
      "description": "Create and manage users"
    }
  }
}
```

### Dynamic Form Component Integration
The dynamic form component should:
1. Use the translation keys from the schema response
2. Apply translations to all UI elements (labels, placeholders, help text, error messages)
3. Handle parameterized translations for dynamic content (like parent group options)
4. Provide fallback text if translations are missing 