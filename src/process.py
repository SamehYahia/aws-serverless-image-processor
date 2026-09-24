import io
import logging
import os
import time
from pathlib import PurePosixPath
from urllib.parse import quote

import boto3
from PIL import Image, ImageDraw, ImageFont, ImageOps, UnidentifiedImageError

logger = logging.getLogger()
logger.setLevel(logging.INFO)

s3 = boto3.client("s3")
SOURCE_BUCKET = os.environ["SOURCE_BUCKET"]
PROCESSED_BUCKET = os.environ["PROCESSED_BUCKET"]
MAX_IMAGE_BYTES = int(os.environ.get("MAX_IMAGE_BYTES", "10485760"))
MAX_IMAGE_DIMENSION = int(os.environ.get("MAX_IMAGE_DIMENSION", "1200"))
THUMBNAIL_DIMENSION = int(os.environ.get("THUMBNAIL_DIMENSION", "320"))
MAX_IMAGE_PIXELS = 40_000_000
WATERMARK_TEXT = os.environ.get("WATERMARK_TEXT", "AWS SAA Graduation Project")[:64]
CLOUDFRONT_DOMAIN = os.environ["CLOUDFRONT_DOMAIN"]
ALLOWED_FORMATS = {"JPEG": "image/jpeg", "PNG": "image/png"}


def handler(event, _context):
    bucket = event["sourceBucket"]
    key = event["sourceKey"]
    if bucket != SOURCE_BUCKET or not key.startswith("uploads/"):
        raise ValueError("Workflow input does not reference an allowed source object.")

    response = s3.get_object(Bucket=bucket, Key=key)
    image_bytes = response["Body"].read(MAX_IMAGE_BYTES + 1)
    if len(image_bytes) > MAX_IMAGE_BYTES:
        raise ValueError(f"Image exceeds the {MAX_IMAGE_BYTES}-byte limit.")

    try:
        with Image.open(io.BytesIO(image_bytes)) as image:
            image_format = image.format
            if image_format not in ALLOWED_FORMATS:
                raise ValueError(f"Unsupported image format: {image_format}")
            if image.width * image.height > MAX_IMAGE_PIXELS:
                raise ValueError("Image dimensions exceed the pixel limit.")
            image.verify()

        with Image.open(io.BytesIO(image_bytes)) as source:
            image = ImageOps.exif_transpose(source)
            original_width, original_height = image.size
            image.thumbnail(
                (MAX_IMAGE_DIMENSION, MAX_IMAGE_DIMENSION),
                Image.Resampling.LANCZOS,
            )
            watermarked = _add_watermark(image)
            thumbnail = watermarked.copy()
            thumbnail.thumbnail(
                (THUMBNAIL_DIMENSION, THUMBNAIL_DIMENSION),
                Image.Resampling.LANCZOS,
            )
            processed_bytes = _encode(watermarked, image_format)
            thumbnail_bytes = _encode(thumbnail, image_format)
            width, height = watermarked.size
    except (UnidentifiedImageError, OSError) as exc:
        raise ValueError("The uploaded object is not a supported image.") from exc

    relative_key = str(PurePosixPath(key).relative_to("uploads"))
    processed_key = f"processed/{relative_key}"
    thumbnail_key = f"thumbnails/{relative_key}"
    _put_image(processed_key, processed_bytes, image_format)
    _put_image(thumbnail_key, thumbnail_bytes, image_format)

    result = {
        "imageId": event["imageId"],
        "sourceBucket": bucket,
        "sourceKey": key,
        "processedKey": processed_key,
        "thumbnailKey": thumbnail_key,
        "imageUrl": _image_url(processed_key),
        "thumbnailUrl": _image_url(thumbnail_key),
        "width": width,
        "height": height,
        "originalWidth": original_width,
        "originalHeight": original_height,
        "createdAt": event.get("createdAt") or "",
        "expiresAt": int(time.time()) + 90 * 24 * 60 * 60,
    }
    logger.info("Processed s3://%s/%s into %s and %s", bucket, key, processed_key, thumbnail_key)
    return result


def _add_watermark(image):
    watermarked = image.convert("RGBA")
    overlay = Image.new("RGBA", watermarked.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)
    font = ImageFont.load_default()
    left, top, right, bottom = draw.textbbox((0, 0), WATERMARK_TEXT, font=font)
    text_width = right - left
    text_height = bottom - top
    margin = max(8, min(watermarked.size) // 40)
    x = max(margin, watermarked.width - text_width - margin)
    y = max(margin, watermarked.height - text_height - margin)
    draw.rounded_rectangle(
        (x - 5, y - 4, x + text_width + 5, y + text_height + 4),
        radius=4,
        fill=(0, 0, 0, 145),
    )
    draw.text((x, y), WATERMARK_TEXT, font=font, fill=(255, 255, 255, 235))
    return Image.alpha_composite(watermarked, overlay)


def _encode(image, image_format):
    output = io.BytesIO()
    if image_format == "JPEG":
        image = image.convert("RGB")
        image.save(output, format="JPEG", quality=85, optimize=True)
    else:
        image.save(output, format="PNG", optimize=True)
    return output.getvalue()


def _put_image(key, data, image_format):
    s3.put_object(
        Bucket=PROCESSED_BUCKET,
        Key=key,
        Body=data,
        ContentType=ALLOWED_FORMATS[image_format],
    )


def _image_url(key):
    return f"https://{CLOUDFRONT_DOMAIN}/{quote(key, safe='/')}"
