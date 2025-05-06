# Use newer Go version just for SubFinder build
FROM golang:1.24 AS subfinder-builder
# Install SubFinder with controlled output
RUN echo "Installing SubFinder v2.7.1..." && \
    go install -v github.com/projectdiscovery/subfinder/v2/cmd/subfinder@v2.7.1 > /dev/null 2>&1 && \
    echo "SubFinder installed successfully"

FROM python:3.9-slim

# Install system dependencies (drop apt-based certbot)
# Replace certbot system install with pip version
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        nginx \
        postgresql-client \
        gettext-base \
        curl && \
    rm -rf /var/lib/apt/lists/* && \
    pip install certbot==2.6.0 josepy==1.13.0

# Install Certbot with pip to avoid AttributeError issues
RUN pip install certbot==2.10.0

# Copy SubFinder from builder
COPY --from=subfinder-builder /go/bin/subfinder /usr/local/bin/

# Everything below remains identical to your original
WORKDIR /app
COPY . .

RUN pip install --no-cache-dir -r requirements.txt uvicorn

COPY nginx.conf /etc/nginx/nginx.conf
RUN mkdir -p /var/www/certbot /app/ssldata /app/data /app/payload-fire-images

COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

EXPOSE 80 443
ENTRYPOINT ["/entrypoint.sh"]