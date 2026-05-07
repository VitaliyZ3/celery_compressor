import uuid
from pathlib import Path

from celery.result import AsyncResult
from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.responses import FileResponse

from celery_app import celery
from tasks import OUTPUT_DIR, UPLOAD_DIR, compress_image

ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".bmp", ".webp", ".tiff"}

app = FastAPI(title="Image Compressor", description="Compress images to 144p using Celery workers")

# Cache terminal task results so repeated polls work after amqp backend consumes the message
_result_cache: dict = {}


@app.post("/upload", summary="Upload an image for compression")
async def upload_image(file: UploadFile = File(...)):
    ext = Path(file.filename).suffix.lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=400, detail=f"Unsupported file type: {ext}")

    unique_filename = f"{uuid.uuid4().hex}{ext}"
    dest = UPLOAD_DIR / unique_filename

    content = await file.read()
    dest.write_bytes(content)

    task = compress_image.delay(unique_filename)

    return {
        "task_id": task.id,
        "compressed_filename": f"compressed_{unique_filename}",
        "original_filename": file.filename,
        "status": "queued",
    }


@app.get("/status/{task_id}", summary="Get compression task status")
def get_task_status(task_id: str):
    result = AsyncResult(task_id, app=celery)

    # Return cached terminal state if already consumed from amqp queue
    if task_id in _result_cache:
        return _result_cache[task_id]

    response = {"task_id": task_id, "status": result.status}

    if result.successful():
        response["result"] = result.result
        _result_cache[task_id] = response
    elif result.failed():
        response["error"] = str(result.result)
        _result_cache[task_id] = response
    elif result.status == "PROGRESS":
        response["progress"] = result.info

    return response


@app.get("/download/{compressed_filename}", summary="Download compressed image")
def download_image(compressed_filename: str):
    file_path = OUTPUT_DIR / compressed_filename
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Compressed file not found")
    return FileResponse(path=file_path, filename=compressed_filename)


@app.delete("/files/{filename}", summary="Delete original uploaded file")
def delete_file(filename: str):
    file_path = UPLOAD_DIR / filename
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="File not found")
    file_path.unlink()
    return {"deleted": filename}
