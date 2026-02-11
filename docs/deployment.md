# Deployment

## Local

Run `docker-compose up --build`.

## Production

1. Build Docker images.
2. Push to Container Registry (GCR/GAR).
3. Deploy to Cloud Run or GKE.
4. Update environment variables for real GCP Pub/Sub and Cloud SQL.
