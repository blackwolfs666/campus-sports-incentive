# Local Database Notes

Project root:

```text
D:\my-web\sportsNum
```

Database scripts:

```text
D:\my-web\sportsNum\database
```

Current local MySQL settings are read by the backend from `backend/.env` or terminal environment variables.

```text
Host: localhost
Port: 3306
User: root
Password: 123456
Database: step_counter
```

Initialization order:

```sql
source D:/my-web/sportsNum/database/schema.sql;
source D:/my-web/sportsNum/database/seed.sql;
source D:/my-web/sportsNum/database/checkin_tables.sql;
source D:/my-web/sportsNum/database/admin_tables.sql;
```

Files:

```text
schema.sql          Create database tables
seed.sql            Insert local development data
checkin_tables.sql  Create check-in feed tables
admin_tables.sql    Create activity admin backend tables
```
