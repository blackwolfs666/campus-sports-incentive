# Local Database Notes

Project root:

```text
<repo-root>
```

Database scripts:

```text
<repo-root>/database
```

Current local MySQL settings are read by the backend from `backend/.env` or terminal environment variables.

```text
Host: localhost
Port: 3306
User: root
Password: your_mysql_password
Database: step_counter
```

Initialization order:

```sql
source database/schema.sql;
source database/seed.sql;
source database/checkin_tables.sql;
source database/admin_tables.sql;
```

Files:

```text
schema.sql          Create database tables
seed.sql            Insert local development data
checkin_tables.sql  Create check-in feed tables
admin_tables.sql    Create activity admin backend tables
```
