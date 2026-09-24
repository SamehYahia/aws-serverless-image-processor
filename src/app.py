import io
import logging
import os
import urllib.parse

import boto3
from PIL import Image, UnidentifiedImageError

logger = logging.getLogger()
logger.setLevel(logging.INFO)

s3 = boto3.client("s3")
DESTINATION_BUCKET = os.environ["DESTINATION_BUCKET"]
MAX_IMAGE_BYTES = int(os.environ.get("MAX_IMAGE_BYTES", "10485760"))
MAX_IMAGE_DIMENSION = int(os.environ.get("MAX_IMAGE_DIMENSION", "1200"))
ALLOWED_FORMATS = {"JPEG": "image/jpeg", "PNG": "image/png"}


def handler(event, _context):
    for record in event.get("Records", []):
        source_bucket = record["s3"]["bucket"]["name"]
        object_key = urllib.parse.unquote_plus(record["s3"]["object"]["key"])

        if object_key.startswith("processed/"):
            continue

        process_image(source_bucket, object_key)

    return {"statusCode": 200, "body": "Image processing complete"}


def process_image(source_bucket, object_key):
    response = s3.get_object(Bucket=source_bucket, Key=object_key)
    image_bytes = response["Body"].read(MAX_IMAGE_BYTES + 1)
    if len(image_bytes) > MAX_IMAGE_BYTES:
        raise ValueError(f"Image exceeds the {MAX_IMAGE_BYTES}-byte limit: {object_key}")

    try:
        with Image.open(io.BytesIO(image_bytes)) as image:
            image_format = image.format
            if image_format not in ALLOWED_FORMATS:
                raise ValueError(f"Unsupported image format: {image_format}")
            image.verify()

        with Image.open(io.BytesIO(image_bytes)) as image:
            image.thumbnail((MAX_IMAGE_DIMENSION, MAX_IMAGE_DIMENSION))
            output = io.BytesIO()
            save_options = {"format": image_format}
            if image_format == "JPEG":
                if image.mode not in ("RGB", "L"):
                    image = image.convert("RGB")
                save_options["quality"] = 85
                save_options["optimize"] = True
            image.save(output, **save_options)
    except (UnidentifiedImageError, OSError) as exc:
        raise ValueError(f"Invalid image: {object_key}") from exc

    output_key = f"processed/{object_key}"
    s3.put_object(
        Bucket=DESTINATION_BUCKET,
        Key=output_key,
        Body=output.getvalue(),
        ContentType=ALLOWED_FORMATS[image_format],
        Metadata={"source-key": object_key},
    )
    logger.info(
        "Processed s3://%s/%s to s3://%s/%s",
        source_bucket,
        object_key,
        DESTINATION_BUCKET,
        output_key,
    )
