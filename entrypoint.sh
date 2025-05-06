#!/bin/bash
set -ex

export PYTHONUNBUFFERED=1

# Wait for PostgreSQL
echo "⏳ Waiting for PostgreSQL..."
while ! pg_isready -h db -U test -d subnotifier -t 1; do
    sleep 2
done
echo "✅ PostgreSQL ready!"

# Ensure required variables are set
: "${HOSTNAME:?Need to set HOSTNAME}"
: "${SSL_CONTACT_EMAIL:?Need to set SSL_CONTACT_EMAIL}"

CERT_PATH="/etc/letsencrypt/live/${HOSTNAME}"

# SSL Certificate Setup
if [ ! -f "${CERT_PATH}/fullchain.pem" ]; then
    echo "🔐 Attempting to set up SSL certificate with Certbot..."
    if certbot certonly --standalone -d "${HOSTNAME}" --non-interactive --agree-tos --email "${SSL_CONTACT_EMAIL}" -v; then
        echo "✅ Certbot succeeded."
    else
        echo "⚠️ Certbot failed — generating self-signed certificate as fallback..."
        mkdir -p "${CERT_PATH}"
        openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
            -keyout "${CERT_PATH}/privkey.pem" \
            -out "${CERT_PATH}/fullchain.pem" \
            -subj "/CN=${HOSTNAME}"
    fi
else
    echo "✅ SSL certificate already exists."
fi

# Configure nginx with envsubst
echo "📝 Configuring nginx..."
envsubst '${HOSTNAME}' < /app/nginx.conf > /etc/nginx/nginx.conf

# Test nginx config
nginx -t || exit 1

# Start Uvicorn in background
echo "🚀 Starting Uvicorn..."
uvicorn app.main:app \
    --host 0.0.0.0 \
    --port 8000 \
    --log-level info \
    --no-access-log &

# Start nginx in foreground
echo "🌐 Starting Nginx..."
exec nginx -g "daemon off;"