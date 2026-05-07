# Image Compressor

A FastAPI service that compresses images to 144p using Celery background workers, Redis as the message broker, and Flower for task monitoring.

## Stack

- **FastAPI** — REST API
- **Celery** — background task queue
- **Redis** — message broker & result backend
- **Flower** — Celery task monitoring UI
- **Pillow** — image processing

## Requirements

- Docker & Docker Compose

## Getting Started

```bash
# Create required directories (first time only)
mkdir -p uploads compressed

# Build and start all services
docker compose up -d --build
```

| Service | URL |
|---------|-----|
| FastAPI | http://localhost:8000 |
| API Docs | http://localhost:8000/docs |
| Flower | http://localhost:5555 |

## API Endpoints

### Upload an image
```
POST /upload
Content-Type: multipart/form-data
```
Accepts: `.jpg`, `.jpeg`, `.png`, `.bmp`, `.webp`, `.tiff`

**Response:**
```json
{
  "task_id": "abc123",
  "compressed_filename": "compressed_abc123.jpg",
  "original_filename": "photo.jpg",
  "status": "queued"
}
```

### Check task status
```
GET /status/{task_id}
```

**Response:**
```json
{
  "task_id": "abc123",
  "status": "SUCCESS",
  "result": {
    "original_size": 1500000,
    "compressed_size": 10000
  }
}
```

Possible statuses: `PENDING`, `PROGRESS`, `SUCCESS`, `FAILURE`

### Download compressed image
```
GET /download/{compressed_filename}
```

### Delete original upload
```
DELETE /files/{filename}
```

## Project Structure

```
.
├── main.py           # FastAPI app & endpoints
├── celery_app.py     # Celery configuration
├── tasks.py          # compress_image task
├── requirements.txt
├── Dockerfile
├── docker-compose.yml
├── uploads/          # uploaded originals
└── compressed/       # processed output
```

## Configuration

| Environment Variable | Default | Description |
|---|---|---|
| `REDIS_URL` | `redis://localhost:6379` | Redis connection URL |

## Stopping

```bash
docker compose down
```
