import json
import logging
import os
import re
from pathlib import Path
from uuid import uuid4

import boto3

s3 = boto3.client("s3")
logger = logging.getLogger()
logger.setLevel(logging.INFO)
UPLOADS_BUCKET = os.environ["UPLOADS_BUCKET"]
MAX_IMAGE_BYTES = int(os.environ.get("MAX_IMAGE_BYTES", "10485760"))
UPLOAD_TYPES = {
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".png": "image/png",
}


def handler(event, _context):
    try:
        body = json.loads(event.get("body") or "{}")
        filename = Path(str(body.get("filename", ""))).name
        content_type = str(body.get("contentType", "")).lower()
        extension = Path(filename).suffix.lower()
        if not filename or content_type != UPLOAD_TYPES.get(extension):
            return _response(400, {"message": "Provide a .jpg, .jpeg, or .png filename with its matching contentType."})

        safe_name = re.sub(r"[^A-Za-z0-9._-]+", "-", filename).strip(".-_")
        if not safe_name:
            return _response(400, {"message": "The filename is not valid."})

        key = f"uploads/{uuid4().hex}-{safe_name}"
        form = s3.generate_presigned_post(
            Bucket=UPLOADS_BUCKET,
            Key=key,
            Fields={"Content-Type": content_type},
            Conditions=[
                {"Content-Type": content_type},
                ["content-length-range", 1, MAX_IMAGE_BYTES],
            ],
            ExpiresIn=300,
        )
        return _response(200, {"key": key, "expiresInSeconds": 300, "upload": form})
    except (TypeError, ValueError):
        return _response(400, {"message": "Request body must be valid JSON."})
    except Exception:
        logger.exception("Could not prepare an upload form")
        return _response(500, {"message": "Could not prepare an upload. Check the function logs."})


def _response(status_code, body):
    return {
        "statusCode": status_code,
        "headers": {"content-type": "application/json"},
        "body": json.dumps(body),
    }
