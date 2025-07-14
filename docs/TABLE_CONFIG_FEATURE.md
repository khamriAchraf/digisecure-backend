# Table Configuration Feature

This document describes the table configuration feature that allows users to customize which columns are displayed in their DataTable components.

## Overview

The table configuration feature enables users to:
- Save their preferred column configurations for different tables
- Have these preferences persist across sessions
- Fall back to default configurations when no custom config exists

## Database Schema

### TableConfig Model

```sql
CREATE TABLE user_table_configs (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    table_key VARCHAR(64) NOT NULL,  -- e.g., 'groups', 'users', 'tickets'
    columns JSONB NOT NULL,          -- Array of column keys to display
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    UNIQUE(user_id, table_key)
);
```

## API Endpoints

### Get Table Config
```
GET /api/v1/table-configs/{table_key}
```
Returns the table configuration for a specific table key for the current user.
- Returns `404` if no configuration exists
- Returns `200` with the configuration if found

### List All Table Configs
```
GET /api/v1/table-configs/
```
Returns all table configurations for the current user.

### Create or Update Table Config
```
PUT /api/v1/table-configs/{table_key}
```
Creates or updates a table configuration for the current user (upsert operation).

**Request Body:**
```json
{
  "columns": ["id", "name", "description", "type"]
}
```

### Delete Table Config
```
DELETE /api/v1/table-configs/{table_key}
```
Deletes a table configuration for the current user.
- Returns `204` on successful deletion
- Returns `404` if the configuration doesn't exist

## Frontend Integration

### SWR Fetcher Pattern

```typescript
// Example SWR fetcher for table config
const useTableConfig = (tableKey: string) => {
  const { data, error, mutate } = useSWR(
    `/api/v1/table-configs/${tableKey}`,
    async (url) => {
      const response = await fetch(url);
      if (response.status === 404) {
        // No custom config exists, return null to use defaults
        return null;
      }
      if (!response.ok) {
        throw new Error('Failed to fetch table config');
      }
      return response.json();
    }
  );

  return {
    columns: data?.columns || defaultColumns, // Fall back to defaults
    error,
    mutate
  };
};
```

### Usage in DataTable Component

```typescript
// In your DataTable component
const DataTable = ({ tableKey, defaultConfig }) => {
  const { columns, mutate } = useTableConfig(tableKey);
  
  // Use columns from API or fall back to default config
  const displayColumns = columns || defaultConfig.columns;
  
  // When user changes column visibility
  const updateColumns = async (newColumns) => {
    await fetch(`/api/v1/table-configs/${tableKey}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ columns: newColumns })
    });
    mutate(); // Refresh the SWR cache
  };
  
  return (
    <table>
      {/* Render table with displayColumns */}
    </table>
  );
};
```

## Database Migration

To add the table to an existing database, run:

```bash
poetry run python app/utils/add_table_config_table.py
```

This script will:
1. Create the `user_table_configs` table
2. Add the unique constraint
3. Create indexes for performance
4. Add a trigger to automatically update the `updated_at` column

## Security

- Users can only access their own table configurations
- No permission checks are required since users only access their own data
- The `user_id` is automatically set from the authenticated user's session

## Testing

Run the table config tests:

```bash
poetry run pytest tests/test_table_config.py -v
```

## Example Usage

### Creating a Table Config
```bash
curl -X PUT "http://localhost:8000/api/v1/table-configs/groups" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"columns": ["id", "name", "description", "contain_users"]}'
```

### Getting a Table Config
```bash
curl -X GET "http://localhost:8000/api/v1/table-configs/groups" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### Deleting a Table Config
```bash
curl -X DELETE "http://localhost:8000/api/v1/table-configs/groups" \
  -H "Authorization: Bearer YOUR_TOKEN"
``` 