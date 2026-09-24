#!/usr/bin/env python3
"""Request a temporary upload form and submit an image to the project API."""

import json
import mimetypes
import sys
import urllib.error
import urllib.request
import uuid
from pathlib import Path


def main():
    if len(sys.argv) != 3:
        raise SystemExit("Usage: python3 scripts/upload_image.py API_URL IMAGE_PATH")

    api_url, image_path = sys.argv[1], Path(sys.argv[2])
    if not image_path.is_file():
        raise SystemExit(f"Image not found: {image_path}")

    content_type = mimetypes.guess_type(image_path.name)[0]
    if content_type not in {"image/jpeg", "image/png"}:
        raise SystemExit("Choose a JPEG or PNG image.")

    request_body = json.dumps({"filename": image_path.name, "contentType": content_type}).encode()
    request = urllib.request.Request(
        api_url,
        data=request_body,
        headers={"content-type": "application/json"},
        method="POST",
    )

    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            upload_request = json.load(response)
        upload = upload_request["upload"]
        source_key = upload_request["key"]
        fields = upload["fields"]
        boundary = f"----ImageUpload{uuid.uuid4().hex}"
        body = bytearray()
        for name, value in fields.items():
            body.extend(f"--{boundary}\r\n".encode())
            body.extend(f'Content-Disposition: form-data; name="{name}"\r\n\r\n'.encode())
            body.extend(str(value).encode())
            body.extend(b"\r\n")

        body.extend(f"--{boundary}\r\n".encode())
        body.extend(
            f'Content-Disposition: form-data; name="file"; filename="{image_path.name}"\r\n'.encode()
        )
        body.extend(f"Content-Type: {content_type}\r\n\r\n".encode())
        body.extend(image_path.read_bytes())
        body.extend(f"\r\n--{boundary}--\r\n".encode())

        s3_request = urllib.request.Request(
            upload["url"],
            data=bytes(body),
            headers={"content-type": f"multipart/form-data; boundary={boundary}"},
            method="POST",
        )
        with urllib.request.urlopen(s3_request, timeout=60) as response:
            if response.status not in (200, 201, 204):
                raise RuntimeError(f"S3 upload returned HTTP {response.status}")
        print(f"Upload accepted. Source object key: {source_key}")
    except (urllib.error.URLError, KeyError, json.JSONDecodeError) as exc:
        raise SystemExit(f"Upload failed: {exc}") from exc


if __name__ == "__main__":
    main()
