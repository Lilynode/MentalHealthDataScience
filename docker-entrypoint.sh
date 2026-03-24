#!/bin/bash
set -e

echo "=========================================="
echo "MHRAS Docker Entry Point"
echo "=========================================="

# Wait for database to be ready
echo "Waiting for PostgreSQL to be ready..."
until PGPASSWORD=$DB_PASSWORD psql -h "$DB_HOST" -U "$DB_USER" -d "$DB_NAME" -c '\q' 2>/dev/null; do
    echo "PostgreSQL is unavailable - sleeping"
    sleep 2
done
echo "PostgreSQL is ready!"

# Wait for Redis to be ready
echo "Waiting for Redis to be ready..."
until redis-cli -h redis -p 6379 ping 2>/dev/null | grep -q PONG; do
    echo "Redis is unavailable - sleeping"
    sleep 2
done
echo "Redis is ready!"

# Initialize database if needed
echo "Checking if database needs initialization..."
python -c "
import sys
sys.path.insert(0, '/app')
from scripts.init_database import create_database, run_migrations, seed_consent_records, seed_resource_catalog

# Create database if needed
print('Creating database if needed...')
# Note: This requires postgres user access

# Run migrations
print('Running migrations...')
run_migrations(
    host='$DB_HOST',
    port=5432,
    database='$DB_NAME',
    user='$DB_USER',
    password='$DB_PASSWORD'
)

# Seed consent records
print('Seeding consent records...')
try:
    seed_consent_records(
        host='$DB_HOST',
        port=5432,
        database='$DB_NAME',
        user='$DB_USER',
        password='$DB_PASSWORD'
    )
except Exception as e:
    print(f'Warning: Consent seeding issue: {e}')

# Seed resources
print('Seeding resource catalog...')
try:
    seed_resource_catalog(
        host='$DB_HOST',
        port=5432,
        database='$DB_NAME',
        user='$DB_USER',
        password='$DB_PASSWORD'
    )
except Exception as e:
    print(f'Warning: Resource catalog seeding issue: {e}')

print('Database initialization complete!')
"

# Check if models need to be trained
echo "Checking if models need training..."
MODEL_COUNT=$(ls -1 /app/models/registry/*.json 2>/dev/null | wc -l)
if [ "$MODEL_COUNT" -eq 0 ]; then
    echo "No trained models found. Training models now..."
    python -c "
import sys
sys.path.insert(0, '/app')
from scripts.train_models import train_and_register_models

train_and_register_models(
    n_samples=5000,
    model_dir='/app/models',
    registry_dir='/app/models/registry',
    random_state=42
)
print('Model training complete!')
"
else
    echo "Found $MODEL_COUNT existing model(s) in registry"
fi

echo "=========================================="
echo "Startup complete! Starting MHRAS API..."
echo "=========================================="

# Execute the main command
exec "$@"
