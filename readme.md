demo:



https://github.com/user-attachments/assets/665d5aef-33cd-4593-81ac-d84070fd94b1



A robust, scalable webhook delivery service that reliably processes and delivers webhook notifications with signature verification, exponential backoff retries, and comprehensive monitoring.

## Table of Contents

1. Overview
2. Features
3. Architecture
4. Local Setup
5. API Endpoints
6. Using the Service
7. Webhook Verification
8. Monitoring and Logs
9. Cost Estimation
10. Development and Production

## Overview

This Webhook Delivery System (WDS) allows applications to:
- Create webhook subscriptions with optional signature verification
- Receive webhooks and immediately acknowledge reception
- Process webhook deliveries asynchronously
- Implement intelligent retry logic with exponential backoff
- Track delivery status and performance metrics

## Features

- **Subscription Management**: Create, retrieve, and delete webhook subscriptions
- **Signature Verification**: SHA-256 HMAC signature verification for secure webhook processing
- **Asynchronous Processing**: Quick acknowledgment and background processing
- **Retry Logic**: Exponential backoff retry mechanism for failed deliveries
- **Delivery Tracking**: Comprehensive logging of delivery attempts and status
- **Monitoring**: Status endpoints for metrics and performance analysis
- **API Documentation**: Interactive Swagger UI documentation
- **Containerization**: Docker-based deployment for easy scaling

## Architecture

The system consists of the following components:

- **Flask Web Application**: Handles HTTP requests and responses
- **PostgreSQL Database**: Stores subscription, webhook, and delivery attempt data
- **Redis**: Acts as message broker and result backend for Celery
- **Celery Workers**: Process webhook deliveries asynchronously
- **Docker Containers**: Isolate and package the entire system
- **Swagger UI**: for the UI of the application

## Local Setup

### Prerequisites

- Docker and Docker Compose
- Git

### Installation Steps

1. **Clone the repository**:
   ```bash
   git clone git@github.com:Chandan-CV/segwiseAssignment.git
   cd segwiseAssignment
   ```

2. **Build and start the containers**:
   ```bash
   docker-compose build
   docker-compose up
   ```

   This will start:
   - Web service on port 5000
   - Redis on port 6380
   - PostgreSQL on port 5432
   - Celery workers for background processing


3. **Access the application**:
   - API: http://localhost:5000/
   - Swagger UI: http://localhost:5000/api/docs/

### Verifying Setup

To verify your setup is working correctly:

```bash
curl http://localhost:5000/ping
```

You should receive a response with status 200 and basic system information.

## API Endpoints

### Subscription Management

#### Create a Subscription
```
POST /subscriptions/createsubscription
```
**Request Body**:
```json
{
  "url": "https://example.com/callback",
  "secret": "your_secret_key" // Optional
}
```
**Response**:
```json
{
  "id": 1,
  "url": "https://example.com/callback",
  "created_at": "2025-04-27T10:30:00Z",
  "has_secret": true
}
```

#### List All Subscriptions
```
GET /subscriptions/getsubscriptions
```
**Response**:
```json
[
  {
    "id": 1,
    "url": "https://example.com/callback",
    "has_secret": true,
    "created_at": "2025-04-27T10:30:00Z"
  }
]
```

#### Delete a Subscription
```
DELETE /subscriptions/deletesubscription
```
**Request Body**:
```json
{
  "id": 1
}
```
**Response**:
```json
{
  "message": "Subscription deleted successfully"
}
```

### Webhook Ingestion

#### Ingest a Webhook
```
POST /ingest/{subscription_id}
```
**Headers** (if subscription has secret):
```
X-Hub-Signature-256: sha256=<signature>
```
**Request Body** (any valid JSON):
```json
{
  "event": "test_event",
  "data": {
    "hello": "world"
  }
}
```
**Response**:
```json
{
  "status": "accepted",
  "webhook_id": "123e4567-e89b-12d3-a456-426614174000",
  "subscription_id": 1
}
```

### Status and Monitoring

#### Get Delivery Logs
```
GET /logs/deliverylogs
```
**Response**:
```json
[
  {
    "id": 1,
    "webhook_id": "123e4567-e89b-12d3-a456-426614174000",
    "attempt_number": 1,
    "status": "success",
    "response_code": 200,
    "timestamp": "2025-04-27T10:30:05Z"
  }
]
```

#### System Health Check
```
GET /ping
```
**Response**:
```json
{
  "message": "API is up and running",
  "database": {
    "tables": ["subscriptions", "webhook_payloads", "delivery_attempts"]
  }
}
```

## Using the Service

### Creating a Test Subscription

1. Create a subscription that points to your target URL:
   ```bash
   curl -X POST http://localhost:5000/subscriptions/createsubscription \
     -H "Content-Type: application/json" \
     -d '{"url": "https://webhook.site/your-unique-id", "secret": "helloworld"}'
   ```

2. Note the subscription ID from the response.

### Sending a Test Webhook

Use the provided bash script to send a webhook with proper signature:

```bash
# First, make the script executable
chmod +x sendReq.bash

# Edit the script if needed to change the payload or secret
nano sendReq.bash

# Run the script to send the webhook
./sendReq.bash
```

Here's what the sendReq.bash script contains:

```bash
#!/bin/bash
PAYLOAD='{"event":"test_event","data":{"hello":"world"}}'
SECRET="helloworld"

# Calculate signature first and display it
SIGNATURE=$(echo -n "$PAYLOAD" | openssl sha256 -hmac "$SECRET" | awk '{print $2}')
echo "Calculated signature: $SIGNATURE"

# Send the request with the signature
curl -X POST http://localhost:5000/ingest/1 \
  -H "Content-Type: application/json" \
  -H "X-Hub-Signature-256: sha256=$SIGNATURE" \
  -d "$PAYLOAD" \
  -v  # Verbose output for debugging
```

You can modify this script to:
- Change the payload content
- Update the secret key (must match the subscription secret)
- Change the subscription ID (the number at the end of the URL)

### Customizing the Test Request

To modify the webhook payload:

1. Edit the PAYLOAD variable in the script:
   ```bash
   PAYLOAD='{"event":"order_created","data":{"order_id":"12345","total":"99.99"}}'
   ```

2. Make sure the SECRET matches what you set when creating the subscription.

3. Run the script again to send the new webhook.

## Webhook Verification

The system verifies webhooks using HMAC SHA-256 signatures. Here's how it works:

1. The sender calculates a signature by:
   - Taking the raw JSON payload
   - Creating an HMAC signature using SHA-256 and the shared secret
   - Adding the signature in an HTTP header: `X-Hub-Signature-256: sha256=<signature>`

2. The receiver (this service):
   - Extracts the signature from the header
   - Calculates its own signature using the received payload and stored secret
   - Compares the signatures to verify the payload is authentic

For testing, you can manually calculate a signature with:

```bash
echo -n '{"event":"test_event","data":{"hello":"world"}}' | \
  openssl sha256 -hmac "your_secret" | \
  awk '{print $2}'
```

## Monitoring and Logs

### Viewing Delivery Attempts

To see all delivery attempts for webhooks:

```bash
curl http://localhost:5000/logs/deliverylogs
```

### Checking Delivery Status

You can check the delivery status of specific webhooks or view system metrics through the API endpoints.

### Container Logs

To view logs from the containers:

```bash
# View web service logs
docker-compose logs web

# View worker logs
docker-compose logs worker

# Follow logs in real-time
docker-compose logs -f
```

## Cost Estimation

For a production deployment, estimated monthly costs would be:

| Resource | Specification | Monthly Cost |
|----------|---------------|--------------|
| EC2 instance | t2.micro (1 vCPU, 1GB RAM) | $8.50 |
| RDS PostgreSQL | db.t3.micro, 20GB storage | $15.00 |
| ElastiCache Redis | cache.t2.micro | $13.00 |
| Data Transfer | 100GB | $9.00 |
| **Total** | | **$45.50** |

For higher volumes, costs would scale linearly with increased instance sizes and data transfer.

## Development and Production

### Development Mode

The default Docker Compose configuration sets up a development environment with:

- Debug mode enabled
- Volume mounting for live code changes
- Local database and Redis instances

### Production Deployment

For production, consider:

1. Using managed database and Redis services
2. Setting up proper monitoring and alerting
3. Implementing a CI/CD pipeline
4. Configuring proper load balancing for high availability

To switch to production mode, update the environment variables in Docker Compose:

```yaml
environment:
  - FLASK_ENV=production
  - FLASK_DEBUG=0
```

---

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details.

---

Built with ❤️ as part of a technical assignment for Segwise.
