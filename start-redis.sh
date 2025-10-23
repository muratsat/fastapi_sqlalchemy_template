#!/usr/bin/env bash

set -a
source .env

REDIS_PASSWORD=$(echo "$REDIS_URL" | awk -F':' '{print $3}' | awk -F'@' '{print $1}')
REDIS_PORT=$(echo "$REDIS_URL" | awk -F':' '{print $4}' | awk -F'\/' '{print $1}')
# generate container name from current working directory basename, safe for Docker
PWD_BASENAME=$(basename "$PWD")
REDIS_CONTAINER_NAME=$(echo "$PWD_BASENAME" | tr '[:upper:]' '[:lower:]' | sed 's/[^a-z0-9_.-]/-/g')_redis
[ -z "$REDIS_CONTAINER_NAME" ] && REDIS_CONTAINER_NAME="redis"

if ! [ -x "$(command -v docker)" ] && ! [ -x "$(command -v podman)" ]; then
  echo -e "Docker or Podman is not installed. Please install docker or podman and try again.\nDocker install guide: https://docs.docker.com/engine/install/\nPodman install guide: https://podman.io/getting-started/installation"
  exit 1
fi

if [ -x "$(command -v docker)" ]; then
  DOCKER_CMD="docker"
elif [ -x "$(command -v podman)" ]; then
  DOCKER_CMD="podman"
fi

if ! $DOCKER_CMD info > /dev/null 2>&1; then
  echo "$DOCKER_CMD daemon is not running. Please start $DOCKER_CMD and try again."
  exit 1
fi

if command -v nc >/dev/null 2>&1; then
  if nc -z localhost "$REDIS_PORT" 2>/dev/null; then
    echo "Port $REDIS_PORT is already in use."
    exit 1
  fi
else
  echo "Warning: Unable to check if port $REDIS_PORT is already in use (netcat not installed)"
  read -p "Do you want to continue anyway? [y/N]: " -r REPLY
  if ! [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "Aborting."
    exit 1
  fi
fi

if [ "$($DOCKER_CMD ps -q -f name=$REDIS_CONTAINER_NAME)" ]; then
  echo "Redis container '$REDIS_CONTAINER_NAME' already running"
  exit 0
fi

if [ "$($DOCKER_CMD ps -q -a -f name=$REDIS_CONTAINER_NAME)" ]; then
  $DOCKER_CMD start "$REDIS_CONTAINER_NAME"
  echo "Existing redis container '$REDIS_CONTAINER_NAME' started"
  exit 0
fi

if [ -z "$REDIS_PASSWORD" ] || [ "$REDIS_PASSWORD" = "password" ]; then
  echo "You are using the default redis password"
  read -p "Should we generate a random password for you? [y/N]: " -r REPLY
  if ! [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "Please change the default password in the .env file and try again"
    exit 1
  fi
  REDIS_PASSWORD=$(openssl rand -base64 12 | tr '+/' '-_')
  sed -i '' "s#:password@#:$REDIS_PASSWORD@#" .env
fi

$DOCKER_CMD run -d \
  --name $REDIS_CONTAINER_NAME \
  -p "$REDIS_PORT":6379 \
  docker.io/redis:7-alpine \
  redis-server --requirepass "$REDIS_PASSWORD" && echo "Redis container '$REDIS_CONTAINER_NAME' was successfully created"