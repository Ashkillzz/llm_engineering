# PostgreSQL Database Configuration for The Price is Right

## Setup Instructions

### 1. Install PostgreSQL

**Windows:**
- Download from https://www.postgresql.org/download/windows/
- Run the installer and remember the password you set for the `postgres` user
- During installation, make sure to check "PostgreSQL Server"

**macOS:**
```bash
brew install postgresql
brew services start postgresql
```

**Linux (Ubuntu/Debian):**
```bash
sudo apt-get install postgresql postgresql-contrib
sudo service postgresql start
```

### 2. Create Database and User

Open PostgreSQL command line (`psql`) and run:

```sql
-- Create the database
CREATE DATABASE price_is_right;

-- Create a user (change 'llm_user' and 'secure_password' as needed)
CREATE USER llm_user WITH PASSWORD 'secure_password';

-- Grant privileges
ALTER ROLE llm_user SET client_encoding TO 'utf8';
ALTER ROLE llm_user SET default_transaction_isolation TO 'read committed';
ALTER ROLE llm_user SET default_transaction_deferrable TO on;
ALTER ROLE llm_user SET default_transaction_read_only TO off;
GRANT ALL PRIVILEGES ON DATABASE price_is_right TO llm_user;

-- Connect to the database and grant schema privileges
\c price_is_right
GRANT ALL ON SCHEMA public TO llm_user;
```

### 3. Configure Environment Variables

Create a `.env` file in the project root with:

```
DATABASE_URL=postgresql://llm_user:secure_password@localhost:5432/price_is_right
```

### 4. Install Python Dependencies

```bash
pip install -r requirements.txt
```

### 5. Initialize the Database

The database tables will be created automatically when you first run the application. The `init_db()` function in `database.py` handles this.

## Database Schema

### `deals` table
- `id` (Primary Key): Auto-incrementing integer
- `product_description` (String): Product description
- `price` (Float): Listed price
- `url` (String): Unique deal URL
- `created_at` (DateTime): When the deal was added

### `opportunities` table
- `id` (Primary Key): Auto-incrementing integer
- `deal_id` (Foreign Key): Reference to deals table
- `estimate` (Float): Estimated actual value
- `discount` (Float): Difference between estimate and price
- `created_at` (DateTime): When opportunity was identified

## Performance Features

- **Connection Pooling**: 10 persistent connections with 20 overflow
- **Indexes**: On commonly queried fields (price, url, discount)
- **Foreign Keys**: Cascade delete for data integrity
- **Connection Health**: Pre-ping checks before using connections

## Troubleshooting

### Connection Error
```
postgresql.exceptions.OperationalError: could not connect to server
```
**Solution**: Make sure PostgreSQL is running and DATABASE_URL is correct

### Permission Denied
**Solution**: Verify user permissions were granted correctly

```sql
-- Check current user
SELECT current_user;

-- List databases
\l

-- List tables
\dt
```

### Migration from JSON

The old `memory.json` file is no longer used. Historical data can be migrated manually if needed by reading the JSON and inserting into PostgreSQL.
