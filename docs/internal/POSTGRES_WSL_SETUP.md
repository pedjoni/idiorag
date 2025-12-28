# PostgreSQL and pgvector Installation on WSL

This guide walks through installing PostgreSQL and the pgvector extension on Windows Subsystem for Linux (WSL/Ubuntu).

## Prerequisites

- WSL2 with Ubuntu installed
- Basic command line familiarity

## Step 1: Update System Packages

Open your WSL terminal and update the package list:

```bash
sudo apt update
sudo apt upgrade -y
```

## Step 2: Remove Old PostgreSQL (if installed)

If you previously installed PostgreSQL from Ubuntu's default repository, remove it first:

```bash
# Check what PostgreSQL packages are installed
dpkg -l | grep postgresql

# Remove all PostgreSQL packages (adjust version number if needed)
sudo apt remove --purge postgresql-* -y
sudo apt autoremove -y

# Clean up configuration and data (optional - this deletes all databases!)
sudo rm -rf /var/lib/postgresql
sudo rm -rf /etc/postgresql

# Verify removal
psql --version  # Should show "command not found"
```

## Step 3: Install PostgreSQL

Add the official PostgreSQL repository to get the latest version:

```bash
# Install required packages
sudo apt install -y wget gnupg2

# Add PostgreSQL GPG key
wget -qO - https://www.postgresql.org/media/keys/ACCC4CF8.asc | sudo apt-key add -

# Add PostgreSQL repository
echo "deb http://apt.postgresql.org/pub/repos/apt $(lsb_release -cs)-pgdg main" | sudo tee /etc/apt/sources.list.d/pgdg.list

# Update package list
sudo apt update
```

Install PostgreSQL 17 and contrib packages:

```bash
sudo apt install postgresql-17 postgresql-contrib-17 -y
```

Check PostgreSQL version:

```bash
psql --version
```

## Step 4: Configure PostgreSQL Port

Since your Windows PostgreSQL is using port 5432, configure WSL PostgreSQL to use port 5433:

```bash
# Edit the PostgreSQL configuration
sudo nano /etc/postgresql/17/main/postgresql.conf
```

Find the line with `port = 5432` and change it to:

```
port = 5433
```

Save and exit (Ctrl+X, then Y, then Enter).

## Step 5: Start PostgreSQL Service

Start the PostgreSQL service:

```bash
sudo service postgresql start
```

Verify it's running on port 5433:

```bash
# Check service status
sudo service postgresql status

# Check if port 5433 is listening
sudo ss -tlnp | grep 5433
# or use lsof
sudo lsof -i :5433
```

**Note**: WSL doesn't use systemd by default, so you need to start the service manually each time you restart WSL, or add it to your `.bashrc` or `.zshrc`:

```bash
echo "sudo service postgresql start" >> ~/.bashrc
```

## Step 6: Configure PostgreSQL User

Switch to the postgres user and access the PostgreSQL prompt:

```bash
sudo -u postgres psql
```

Set a password for the postgres user:

```sql
ALTER USER postgres PASSWORD 'your_secure_password';
```

Create a new database for your project (optional):

```sql
CREATE DATABASE idiorag;
```

Exit the PostgreSQL prompt:

```sql
\q
```

## Step 7: Install pgvector Extension

Install the required build dependencies:

```bash
sudo apt install -y build-essential git postgresql-server-dev-17
```

Clone the pgvector repository:

```bash
cd /tmp
git clone --branch v0.7.4 https://github.com/pgvector/pgvector.git
cd pgvector
```

Build and install pgvector:

```bash
make
sudo make install
```

## Step 8: Enable pgvector in Your Database

Connect to your database:

```bash
sudo -u postgres psql -d idiorag
```

Enable the pgvector extension:

```sql
CREATE EXTENSION vector;
```

Verify the extension is installed:

```sql
\dx
```

You should see `vector` in the list of installed extensions.

Exit the PostgreSQL prompt:

```sql
\q
```



## Step 9: Connection Strings for Your Application

### From within WSL (Python, Node.js apps running in WSL):

**PostgreSQL URL format:**
```
DATABASE_URL=postgresql://postgres:your_secure_password@localhost:5433/idiorag
```

**Connection string format (ADO.NET/Entity Framework style):**
```
User ID=postgres;Password=your_secure_password;Host=localhost;Port=5433;Database=idiorag;Pooling=true;
```

### From Windows (web apps, other Windows applications):

**Good news**: WSL2 automatically forwards localhost, so you can use `localhost` from Windows!

**PostgreSQL URL format:**
```
DATABASE_URL=postgresql://postgres:your_secure_password@localhost:5433/idiorag
```

**Connection string format (ADO.NET/Entity Framework style):**
```
User ID=postgres;Password=your_secure_password;Host=localhost;Port=5433;Database=idiorag;Pooling=true;
```

Example:
```
User ID=postgres;Password=123qwe;Host=localhost;Port=5433;Database=idiorag;Pooling=true;
```

**If localhost doesn't work** (older WSL versions or network issues), use the WSL IP instead:
```bash
# Get WSL IP from within WSL terminal
hostname -I | awk '{print $1}'
```

Then replace `localhost` with the IP (e.g., `172.18.208.1`):
```
User ID=postgres;Password=123qwe;Host=172.18.208.1;Port=5433;Database=idiorag;Pooling=true;
```

## Migrating Data from Windows PostgreSQL to WSL

If you have an existing database on Windows PostgreSQL that you want to migrate to WSL PostgreSQL:

**Step 1: Dump the database from Windows (PowerShell):**

```powershell
# Replace the path with your PostgreSQL installation directory
& "C:\Program Files\PostgreSQL\17\bin\pg_dump.exe" -h localhost -p 5432 -U postgres -d your_database_name -f C:\temp\database_dump.sql
```

**Important**: Use the `-f` flag instead of `>` to avoid PowerShell UTF-16 encoding issues. The dump will be created in UTF-8 format which PostgreSQL expects.

**Step 2: Import into WSL PostgreSQL:**

From your WSL terminal:

```bash
# Import the dump file (replace database name as needed)
psql -h localhost -p 5433 -U postgres -d idiorag < /mnt/c/temp/database_dump.sql
```

If you need to recreate the database first:

```bash
# Drop and recreate database
psql -h localhost -p 5433 -U postgres -c "DROP DATABASE IF EXISTS idiorag;"
psql -h localhost -p 5433 -U postgres -c "CREATE DATABASE idiorag;"

# Then import
psql -h localhost -p 5433 -U postgres -d idiorag < /mnt/c/temp/database_dump.sql
```

**Note**: If your application has already created the schema on the new database, you can dump only the data from Windows:

```powershell
# Data only dump
& "C:\Program Files\PostgreSQL\17\bin\pg_dump.exe" -h localhost -p 5432 -U postgres -d your_database_name --data-only --column-inserts -f C:\temp\data_only_dump.sql
```

## Using pgAdmin with WSL PostgreSQL

pgAdmin (running on Windows) can connect to your WSL PostgreSQL instance:

1. Open pgAdmin
2. Right-click "Servers" → "Register" → "Server"
3. In the "General" tab:
   - Name: `WSL PostgreSQL 17` (or any name you prefer)
4. In the "Connection" tab:
   - Host: `localhost` (or use WSL IP if localhost doesn't work)
   - Port: `5433`
   - Maintenance database: `postgres`
   - Username: `postgres`
   - Password: `your_secure_password`
   - Save password: ✓ (optional)
5. Click "Save"

**Note**: If you get connection errors with `localhost`, you may need to configure PostgreSQL for external connections (Step 9) and use your WSL IP address instead. Get it with: `hostname -I | awk '{print $1}'`

## Testing the Installation

Test the connection using psql (from within WSL):

```bash
psql -h localhost -p 5433 -U postgres -d idiorag
```

Test pgvector functionality:

```sql
-- Create a test table with vector column
CREATE TABLE test_vectors (
    id SERIAL PRIMARY KEY,
    embedding vector(3)
);

-- Insert test data
INSERT INTO test_vectors (embedding) VALUES ('[1,2,3]'), ('[4,5,6]');

-- Query test data
SELECT * FROM test_vectors;

-- Test vector similarity search
SELECT * FROM test_vectors ORDER BY embedding <-> '[3,4,5]' LIMIT 1;

-- Clean up
DROP TABLE test_vectors;
```

## Troubleshooting

### PostgreSQL service shows "active (exited)"
This is normal - it's just the wrapper service. Check the actual cluster status:
```bash
# Check if PostgreSQL is actually running
sudo pg_lsclusters

# Check if port 5432 is in use
sudo ss -tlnp | grep 5432
# or
sudo lsof -i :5432
```

### Port conflict issues
If you didn't configure port 5433 in Step 4, WSL PostgreSQL won't start because Windows is using 5432:
```bash
# Edit the config to use port 5433
sudo nano /etc/postgresql/17/main/postgresql.conf
# Change: port = 5433

# Restart the service
sudo service postgresql restart

# Verify it's listening on 5433
sudo ss -tlnp | grep 5433
```

### PostgreSQL won't start
- Check logs: `sudo tail -f /var/log/postgresql/postgresql-17-main.log`
- Ensure no other PostgreSQL instance is running on port 5432
- Check cluster status: `sudo pg_lsclusters`

### Permission denied errors
- Make sure you're using `sudo` for service commands
- Check file permissions in `/var/lib/postgresql`

### Can't connect from Windows
- Verify WSL IP address hasn't changed
- Check firewall settings
- Ensure PostgreSQL is listening on all interfaces

### pgvector extension not found
- Verify PostgreSQL version compatibility
- Check if the extension was installed: `ls /usr/share/postgresql/*/extension/vector*`
- Try reinstalling with `sudo make install` in the pgvector directory

## Starting PostgreSQL Automatically

To avoid manually starting PostgreSQL each time, add to your `~/.bashrc`:

```bash
# Start PostgreSQL if not running
if ! sudo service postgresql status > /dev/null 2>&1; then
    sudo service postgresql start
fi
```

Or configure passwordless sudo for the PostgreSQL service by adding to `/etc/sudoers` (use `sudo visudo`):

```
%sudo ALL=(ALL) NOPASSWD: /usr/sbin/service postgresql *
```

## Uninstallation (if needed)

To remove PostgreSQL and pgvector:

```bash
# Stop PostgreSQL
sudo service postgresql stop

# Remove PostgreSQL
sudo apt remove --purge postgresql postgresql-contrib -y
sudo apt autoremove -y

# Remove data directory (warning: this deletes all databases)
sudo rm -rf /var/lib/postgresql
sudo rm -rf /etc/postgresql
```

## Next Steps

After installation:
1. Run your project's database migrations
2. Test vector operations with your RAG application
3. Review `PGVECTOR_SETUP.md` for application-specific setup
4. Check `DEVELOPMENT.md` for development workflow

## Additional Resources

- [PostgreSQL Documentation](https://www.postgresql.org/docs/)
- [pgvector GitHub Repository](https://github.com/pgvector/pgvector)
- [WSL Documentation](https://docs.microsoft.com/en-us/windows/wsl/)
