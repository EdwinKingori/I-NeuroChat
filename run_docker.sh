#!/usr/bin/env bash

set -e

# Colors
GREEN='\033[0;32m'
CYAN='\033[0;36m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${CYAN}"
echo "      🚀 INeuroChat API - Docker Stack"
echo -e "${NC}"

# Verifying Docker Exists
if ! command -v docker &> /dev/null
then
    echo -e "${RED}❌ Docker is not installed or not in PATH.${NC}"
    exit 1
fi 

echo -e "${GREEN}✅ Docker detected${NC}"

# Start Stack
echo -e "${GREEN}🐳 Starting IneuroChat services...${NC}"
docker compose up -d

echo -e "${GREEN}✅ Containers running.${NC}"

# Show Container status
echo -e "\n${CYAN}📦 Active Containers:${NC}"
docker compose ps

# Useful URLS
echo -e "\n${CYAN}🌍 Application URLs:${NC}"
echo -e "API:        ${GREEN}http://localhost:8000${NC}"
echo -e "Docs:       ${GREEN}http://localhost:8000/docs${NC}"
echo -e "Health:     ${GREEN}http://localhost:8000/health${NC}"

# Log streaming behavior
# ------------------------------
# Usage:
#   ./run_docker.sh            -> just start + show status
#   ./run_docker.sh api        -> follow only api logs
#   ./run_docker.sh all        -> follow logs for all services
# ------------------------------
if [ "${1:-}" = "api" ]; then
  echo -e "\n${YELLOW}📜 Following LIVE logs for: api (Ctrl+C to stop viewing logs)${NC}"
  docker compose logs -f api
elif [ "${1:-}" = "all" ]; then
  echo -e "\n${YELLOW}📜 Following LIVE logs for: ALL services (Ctrl+C to stop viewing logs)${NC}"
  docker compose logs -f
else
echo -e "${CYAN}Tip: run '${YELLOW}./run.sh api${CYAN}' to watch live API logs.${NC}"
echo -e "\n${CYAN}✅ Container Stack Ready. HAVE FUN! :).${NC}"
fi 

