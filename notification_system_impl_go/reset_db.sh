#!/bin/bash

# Script to reset the PostgreSQL database schema
# This will drop all tables and let GORM recreate them fresh

DB_HOST="${DB_HOST:-localhost}"
DB_PORT="${DB_PORT:-5432}"
DB_USER="${DB_USER:-postgres}"
DB_NAME="${DB_NAME:-notification_system_go}"
DB_PASSWORD="${DB_PASSWORD:-root}"

echo "========================================================================"
echo "Database Reset Script"
echo "========================================================================"
echo ""
echo "This will DROP ALL TABLES in database: $DB_NAME"
echo "Host: $DB_HOST:$DB_PORT"
echo "User: $DB_USER"
echo ""
read -p "Are you sure? (yes/no): " -r
echo ""

if [[ ! $REPLY =~ ^[Yy][Ee][Ss]$ ]]; then
    echo "Cancelled."
    exit 0
fi

echo "Connecting to database and dropping all tables..."

# Use docker exec if PostgreSQL is running in Docker
if docker ps | grep -q postgres; then
    CONTAINER=$(docker ps --format '{{.Names}}' | grep postgres | head -1)
    echo "Found PostgreSQL container: $CONTAINER"

    docker exec -i "$CONTAINER" psql -U "$DB_USER" -d "$DB_NAME" <<-EOSQL
        DO \$\$ DECLARE
            r RECORD;
        BEGIN
            -- Drop all tables
            FOR r IN (SELECT tablename FROM pg_tables WHERE schemaname = 'public') LOOP
                EXECUTE 'DROP TABLE IF EXISTS public.' || quote_ident(r.tablename) || ' CASCADE';
            END LOOP;

            -- Drop all types (enums)
            FOR r IN (SELECT typname FROM pg_type WHERE typtype = 'e') LOOP
                EXECUTE 'DROP TYPE IF EXISTS ' || quote_ident(r.typname) || ' CASCADE';
            END LOOP;
        END \$\$;
EOSQL
else
    # Try direct PostgreSQL connection
    PGPASSWORD="$DB_PASSWORD" psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" <<-EOSQL
        DO \$\$ DECLARE
            r RECORD;
        BEGIN
            -- Drop all tables
            FOR r IN (SELECT tablename FROM pg_tables WHERE schemaname = 'public') LOOP
                EXECUTE 'DROP TABLE IF EXISTS public.' || quote_ident(r.tablename) || ' CASCADE';
            END LOOP;

            -- Drop all types (enums)
            FOR r IN (SELECT typname FROM pg_type WHERE typtype = 'e') LOOP
                EXECUTE 'DROP TYPE IF EXISTS ' || quote_ident(r.typname) || ' CASCADE';
            END LOOP;
        END \$\$;
EOSQL
fi

if [ $? -eq 0 ]; then
    echo ""
    echo "✓ Database reset complete!"
    echo ""
    echo "Next steps:"
    echo "1. Restart the API server (it will run migrations on startup)"
    echo "2. Restart the workers"
    echo "3. Run the test script"
else
    echo ""
    echo "✗ Database reset failed!"
    echo ""
    echo "If PostgreSQL is not accessible via docker or psql, you can manually connect"
    echo "to your database and run the DROP TABLE and DROP TYPE commands."
fi
