import hashlib
import json
import logging
import os
import urllib.parse

import boto3
from botocore.exceptions import ClientError

logger = logging.getLogger()
logger.setLevel(logging.INFO)

stepfunctions = boto3.client("stepfunctions")
STATE_MACHINE_ARN = os.environ["STATE_MACHINE_ARN"]


def handler(event, _context):
    failures = []
    for message in event.get("Records", []):
        try:
            notification = json.loads(message["body"])
            for record in notification.get("Records", []):
                _start_workflow(record)
        except Exception:
            logger.exception("Could not dispatch SQS message %s", message.get("messageId", "unknown"))
            failures.append({"itemIdentifier": message["messageId"]})

    return {"batchItemFailures": failures}


def _start_workflow(record):
    bucket = record["s3"]["bucket"]["name"]
    object_info = record["s3"]["object"]
    key = urllib.parse.unquote_plus(object_info["key"])
    if not key.startswith("uploads/"):
        return

    sequencer = object_info.get("sequencer", "")
    event_id = hashlib.sha256(f"{bucket}:{key}:{sequencer}".encode()).hexdigest()[:64]
    payload = {
        "imageId": f"{bucket}/{key}",
        "sourceBucket": bucket,
        "sourceKey": key,
        "createdAt": record.get("eventTime", ""),
    }
    try:
        stepfunctions.start_execution(
            stateMachineArn=STATE_MACHINE_ARN,
            name=event_id,
            input=json.dumps(payload),
        )
    except ClientError as exc:
        if exc.response.get("Error", {}).get("Code") == "ExecutionAlreadyExists":
            logger.info("Duplicate object event ignored: %s", event_id)
            return
        raise
    logger.info("Started image workflow %s for s3://%s/%s", event_id, bucket, key)
