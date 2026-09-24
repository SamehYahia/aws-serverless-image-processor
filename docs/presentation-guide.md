# Project Presentation Guide

## Short overview

This project turns an image upload into an asynchronous AWS workflow. API Gateway issues a restricted, short-lived S3 form. S3 stores the original and sends an event to SQS, so uploads remain decoupled from processing. A Lambda consumer starts Step Functions, which coordinates image transformation, metadata storage, and status notification. CloudFront serves the completed image while the S3 output bucket remains private.

## Walkthrough

1. Show the architecture diagram in the repository README.
2. Explain why SQS sits between S3 and the workflow: it buffers bursts and gives failed dispatch messages a retry path to the DLQ.
3. Request a temporary upload form through the API and upload a sample JPEG or PNG with `scripts/upload_image.py`.
4. Follow the SQS message into the Step Functions execution and show the processor's resize and watermark outputs.
5. Show the DynamoDB metadata record and open the CloudFront image URL.
6. Point out that the source and processed buckets stay private, failed queue jobs are observable, and stored objects expire after 90 days.

## Demo checklist

- Deploy the SAM stack and keep its outputs available.
- Use a disposable sample image with no personal or sensitive content.
- Confirm the source object appears under `uploads/`.
- Confirm the workflow completes and writes both `processed/` and `thumbnails/` objects.
- Show the DynamoDB metadata and test both CloudFront URLs.
- If demonstrating recovery, send a malformed SQS message in a test account and show how repeated failures reach the DLQ. Do not do this in a production queue.
- Delete the stack and empty both S3 buckets after the demo to avoid ongoing charges.

## Questions to prepare for

- **Why SQS?** It separates upload traffic from compute, buffers bursts, and supports retries with a DLQ.
- **Why Step Functions?** It makes image processing, metadata persistence, and notifications visible as separate workflow stages.
- **How is the upload restricted?** The API issues a five-minute form for one JPEG or PNG object, limited to the upload prefix and 10 MiB.
- **Are the buckets public?** No. CloudFront uses Origin Access Control for the output; originals are never served through the CDN.
- **What happens when processing fails?** Step Functions retries transient Lambda failures and sends workflow errors to SNS. The DLQ catches messages that repeatedly fail before a workflow starts.
- **What is the project limitation?** The upload API has rate limiting but no user sign-in. Processed images are viewable by anyone with their CloudFront URL, so use demo images only.
