#!/bin/sh
cat << EOF
POSTGRES_USER=${POSTGRES_USER}
POSTGRES_PASSWORD=${POSTGRES_PASSWORD}
POSTGRES_DB=${POSTGRES_DB}
POSTGRES_HOST=${POSTGRES_HOST}
POSTGRES_PORT=${POSTGRES_PORT}
DEBUG=${DEBUG}
SERVER_NAME="${SERVER_NAME}"
PROJECT_NAME="${PROJECT_NAME}"
EOF