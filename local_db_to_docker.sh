#!/usr/bin/env bash 

set -e # stop on error

# Local DB Config
LOCAL_DB_USER=neurochatadmin
LOCAL_DB_NAME=ineurochat
LOCAL_DB_PORT=5432
LOCAL_DB_HOST=localhost

# Docker Container Config
DOCKER_CONTAINER="ineurochat_postgres"
DUMP_FILE="ineurochat_local.dump"

echo "🚀 Starting DB sync: Local → Docker"
echo "📦 Dumping local database as user: $LOCAL_DB_USER"

# 1️⃣ Dumping local database
echo "📦 Dumping local database..."
pg_dump \
  -h "$LOCAL_DB_HOST" \
  -p "$LOCAL_DB_PORT" \
  -U "$LOCAL_DB_USER" \
  -d "$LOCAL_DB_NAME" \
  -Fc \
  -f "$DUMP_FILE"

echo "✅ Local dump created: $DUMP_FILE"

# 2️⃣ Copying dump to container
echo "📤 Copying dump into Docker container..."
docker cp "$DUMP_FILE" "$DOCKER_CONTAINER":/tmp/"$DUMP_FILE"

# 3️⃣ Drop and recreate public schema
echo "🧹 Dropping existing Docker schema..."
docker exec -it "$DOCKER_CONTAINER" bash -lc \
'psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -c "DROP SCHEMA public CASCADE; CREATE SCHEMA public; GRANT ALL ON SCHEMA public TO $POSTGRES_USER;"'

# 4️⃣ Restore into Docker DB
echo "📥 Restoring dump into Docker database..."
docker exec -it "$DOCKER_CONTAINER" bash -lc \
'pg_restore -U "$POSTGRES_USER" -d "$POSTGRES_DB" --no-owner --role="$POSTGRES_USER" /tmp/'"$DUMP_FILE"

# 5️⃣ Cleanup
echo "🧼 Cleaning up..."
rm -f "$DUMP_FILE"
docker exec -it "$DOCKER_CONTAINER" rm -f /tmp/"$DUMP_FILE"

echo "🎉 Database sync completed successfully!"