#!/usr/bin/env python3
"""Render the project architecture using official AWS architecture icons."""

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


ROOT = Path(__file__).resolve().parents[1]
ICONS = ROOT / "assets" / "aws-icons"
OUTPUT = ROOT / "docs" / "architecture.png"
WIDTH, HEIGHT = 1800, 1120
NAVY = "#182B49"
INK = "#243247"
MUTED = "#65758B"
GREEN = "#1E8E5A"
BLUE = "#2875B9"
LINE = "#A8B5C4"
PALE = "#F4F7FA"
FONT_PATH = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"

canvas = Image.new("RGB", (WIDTH, HEIGHT), "#FFFFFF")
draw = ImageDraw.Draw(canvas)


def font(size, bold=False):
    path = FONT_PATH.replace("DejaVuSans.ttf", "DejaVuSans-Bold.ttf") if bold else FONT_PATH
    return ImageFont.truetype(path, size)


def center_text(text, x, y, f, fill=INK):
    draw.text((x, y), text, font=f, fill=fill, anchor="mt")


def rounded_box(box, fill, outline="#D6DEE8", radius=14, width=2):
    draw.rounded_rectangle(box, radius=radius, fill=fill, outline=outline, width=width)


def service_card(x, y, title, detail, icon_file, width=190, height=174):
    rounded_box((x, y, x + width, y + height), "#FFFFFF", "#D5DEE8", 14, 2)
    icon = Image.open(ICONS / icon_file).convert("RGBA")
    icon.thumbnail((82, 82), Image.Resampling.LANCZOS)
    canvas.paste(icon, (x + (width - icon.width) // 2, y + 14), icon)
    center_text(title, x + width // 2, y + 106, font(19, True))
    for i, line in enumerate(detail.split("\n")):
        center_text(line, x + width // 2, y + 134 + i * 21, font(15), MUTED)


def arrow(points, color=GREEN, width=5, dashed=False, head=13):
    if dashed:
        for start, end in zip(points, points[1:]):
            x1, y1 = start
            x2, y2 = end
            if x1 == x2:
                direction = 1 if y2 > y1 else -1
                pos = y1
                while (pos < y2 if direction > 0 else pos > y2):
                    nxt = pos + direction * 13
                    end_y = min(nxt, y2) if direction > 0 else max(nxt, y2)
                    draw.line((x1, pos, x2, end_y), fill=color, width=width)
                    pos += direction * 23
            elif y1 == y2:
                direction = 1 if x2 > x1 else -1
                pos = x1
                while (pos < x2 if direction > 0 else pos > x2):
                    nxt = pos + direction * 13
                    end_x = min(nxt, x2) if direction > 0 else max(nxt, x2)
                    draw.line((pos, y1, end_x, y2), fill=color, width=width)
                    pos += direction * 23
    else:
        draw.line(points, fill=color, width=width, joint="curve")
    x1, y1 = points[-2]
    x2, y2 = points[-1]
    if x2 > x1:
        triangle = [(x2, y2), (x2 - head, y2 - head // 2), (x2 - head, y2 + head // 2)]
    elif x2 < x1:
        triangle = [(x2, y2), (x2 + head, y2 - head // 2), (x2 + head, y2 + head // 2)]
    elif y2 > y1:
        triangle = [(x2, y2), (x2 - head // 2, y2 - head), (x2 + head // 2, y2 - head)]
    else:
        triangle = [(x2, y2), (x2 - head // 2, y2 + head), (x2 + head // 2, y2 + head)]
    draw.polygon(triangle, fill=color)


# Page heading
center_text("SERVERLESS IMAGE PROCESSING PIPELINE", WIDTH // 2, 36, font(36, True), NAVY)
center_text("Secure uploads  |  Event-driven processing  |  Global image delivery", WIDTH // 2, 88, font(19), MUTED)

# AWS account boundary and stage bands
rounded_box((255, 165, 1750, 1008), "#FFFFFF", "#687A90", 20, 3)
draw.rounded_rectangle((275, 180, 495, 222), radius=10, fill=NAVY)
draw.text((294, 189), "AWS ACCOUNT", font=font(19, True), fill="#FFFFFF")

for box, fill in [((285, 245, 1720, 465), "#F5F9FD"), ((285, 500, 1720, 730), "#F5FBF8"), ((285, 770, 1720, 975), "#FBF8F3")]:
    rounded_box(box, fill, "#E0E7EF", 16, 1)

draw.text((310, 254), "1  UPLOAD & QUEUE", font=font(16, True), fill="#47627E")
draw.text((310, 509), "2  ORCHESTRATED PROCESSING", font=font(16, True), fill="#367354")
draw.text((310, 779), "3  RESULTS, DELIVERY & OPERATIONS", font=font(16, True), fill="#9A6330")

# User outside the AWS account
rounded_box((28, 375, 220, 550), "#FFFFFF", "#D5DEE8", 14, 2)
draw.ellipse((96, 395, 150, 449), outline=BLUE, width=5)
draw.arc((75, 435, 170, 515), start=180, end=360, fill=BLUE, width=6)
center_text("USER / CLIENT", 124, 505, font(18, True))
center_text("Upload and view", 124, 529, font(15), MUTED)

# Stage 1 nodes
service_card(320, 286, "API Gateway", "POST /uploads", "Arch_Amazon-API-Gateway_64.png")
service_card(570, 286, "Presign Lambda", "Returns 5-min form", "Arch_AWS-Lambda_64.png")
service_card(820, 286, "Source S3", "Private • uploads/", "Arch_Amazon-Simple-Storage-Service_64.png")
service_card(1070, 286, "SQS Queue", "Buffers S3 events", "Arch_Amazon-Simple-Queue-Service_64.png")
service_card(1320, 286, "SQS DLQ", "Retry failures", "Arch_Amazon-Simple-Queue-Service_64.png")

# Stage 2 nodes
service_card(320, 545, "Starter Lambda", "Starts workflow", "Arch_AWS-Lambda_64.png")
service_card(570, 545, "Step Functions", "Retry • coordinate", "Arch_AWS-Step-Functions_64.png")
service_card(820, 545, "Processor Lambda", "Resize • watermark", "Arch_AWS-Lambda_64.png")
service_card(1070, 545, "Processed S3", "Private output\nImages + thumbnails", "Arch_Amazon-Simple-Storage-Service_64.png")
service_card(1320, 545, "CloudFront", "CDN • OAC", "Arch_Amazon-CloudFront_64.png")

# Stage 3 supporting services
service_card(510, 812, "DynamoDB", "Image metadata • TTL", "Arch_Amazon-DynamoDB_64.png", 205, 160)
service_card(797, 812, "Amazon SNS", "Success / failure", "Arch_Amazon-Simple-Notification-Service_64.png", 205, 160)
service_card(1084, 812, "CloudWatch", "Logs • DLQ alarm", "Arch_Amazon-CloudWatch_64.png", 205, 160)
rounded_box((1380, 812, 1660, 957), "#FFFFFF", "#D5DEE8", 14, 2)
center_text("BUCKET PROTECTION", 1520, 835, font(17, True))
center_text("Block public access", 1520, 871, font(15), MUTED)
center_text("Encryption at rest", 1520, 899, font(15), MUTED)
center_text("90-day lifecycle", 1520, 927, font(15), MUTED)

# Upload / event flow
arrow([(220, 418), (320, 418)], BLUE)
center_text("Request URL", 269, 389, font(13), BLUE)
arrow([(510, 368), (570, 368)], GREEN)
arrow([(665, 460), (665, 482), (240, 482), (240, 430), (220, 430)], BLUE, dashed=True)
center_text("Presigned form", 440, 487, font(13), BLUE)
arrow([(124, 375), (124, 278), (920, 278), (920, 286)], GREEN)
center_text("Upload image", 650, 253, font(13), GREEN)
arrow([(1010, 368), (1070, 368)], GREEN)
center_text("S3 event", 1040, 340, font(13), GREEN)
arrow([(1260, 368), (1320, 368)], color="#C75B45")
center_text("After 5 receives", 1290, 340, font(13), "#A94C3A")

# Queue to workflow and processing data flow
arrow([(1165, 460), (1165, 535), (415, 535), (415, 545)], GREEN)
center_text("SQS event source mapping", 800, 488, font(14, True), GREEN)
arrow([(1010, 420), (1035, 420), (1035, 480), (915, 480), (915, 545)], GREEN)
center_text("Read source", 1000, 487, font(13), GREEN)
arrow([(510, 632), (570, 632)], GREEN)
arrow([(760, 632), (820, 632)], GREEN)
arrow([(1010, 632), (1070, 632)], GREEN)
arrow([(1260, 632), (1320, 632)], GREEN)

# Supporting workflow outputs and viewer delivery
arrow([(665, 719), (665, 755), (612, 755), (612, 812)], BLUE)
arrow([(665, 719), (665, 755), (900, 755), (900, 812)], BLUE)
center_text("Metadata + status", 780, 735, font(13), BLUE)
arrow([(1510, 632), (1770, 632), (1770, 150), (124, 150), (124, 375)], BLUE)
center_text("Processed image URL", 1450, 128, font(13), BLUE)
arrow([(1510, 368), (1690, 368), (1690, 755), (1186, 755), (1186, 812)], color="#C75B45")
center_text("DLQ alarm", 1500, 735, font(13), "#A94C3A")

# Footer note and legend
draw.line((40, 1040, 1760, 1040), fill="#E0E6ED", width=2)
draw.line((72, 1070, 132, 1070), fill=GREEN, width=5)
draw.polygon([(132, 1070), (120, 1063), (120, 1077)], fill=GREEN)
draw.text((145, 1058), "Data / event flow", font=font(15), fill=INK)
draw.line((360, 1070, 420, 1070), fill=BLUE, width=4)
for px in (360, 383, 406):
    draw.line((px, 1070, px + 12, 1070), fill="#FFFFFF", width=1)
draw.polygon([(420, 1070), (408, 1063), (408, 1077)], fill=BLUE)
draw.text((435, 1058), "Response / result", font=font(15), fill=INK)
draw.line((660, 1070, 720, 1070), fill="#C75B45", width=5)
draw.polygon([(720, 1070), (708, 1063), (708, 1077)], fill="#C75B45")
draw.text((735, 1058), "Retry exhaustion", font=font(15), fill=INK)
draw.text((1760, 1058), "Official AWS architecture icons", font=font(14), fill=MUTED, anchor="rt")

OUTPUT.parent.mkdir(parents=True, exist_ok=True)
canvas.save(OUTPUT, format="PNG", optimize=True)
print(f"Rendered {OUTPUT} ({WIDTH}x{HEIGHT})")
