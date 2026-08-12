from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from pathlib import Path

import cv2
from ultralytics import YOLO

from app.core.config import project_path


@dataclass
class OpenEvent:
    start: float
    last_seen: float
    confidence: float
    hook_confidence: float


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="分析吊钩危险区安全帽违规事件")
    parser.add_argument("--model", default="models/best.pt")
    parser.add_argument("--source", default="data/raw_videos/demo_video.mp4")
    parser.add_argument("--output", default="web-demo/public/events.json")
    parser.add_argument("--conf", type=float, default=0.20)
    parser.add_argument("--imgsz", type=int, default=960)
    parser.add_argument("--device", default="0")
    parser.add_argument("--stride", type=int, default=5)
    parser.add_argument("--horizontal", type=float, default=420.0)
    parser.add_argument("--vertical", type=float, default=780.0)
    parser.add_argument("--min-duration", type=float, default=0.8)
    parser.add_argument("--merge-gap", type=float, default=0.8)
    return parser.parse_args()


def center(box: list[float]) -> tuple[float, float]:
    return (box[0] + box[2]) / 2, (box[1] + box[3]) / 2


def main() -> None:
    args = parse_args()
    model = YOLO(str(project_path(args.model)))
    capture = cv2.VideoCapture(str(project_path(args.source)))
    if not capture.isOpened():
        raise RuntimeError("无法打开演示视频")

    fps = capture.get(cv2.CAP_PROP_FPS) or 25.0
    total_frames = int(capture.get(cv2.CAP_PROP_FRAME_COUNT))
    events: list[dict[str, object]] = []
    active: OpenEvent | None = None
    frame_index = 0

    while True:
        success, frame = capture.read()
        if not success or frame is None:
            break
        if frame_index % args.stride != 0:
            frame_index += 1
            continue

        result = model.predict(
            frame,
            conf=args.conf,
            imgsz=args.imgsz,
            device=args.device,
            verbose=False,
        )[0]
        hooks: list[tuple[list[float], float]] = []
        no_helmets: list[tuple[list[float], float]] = []
        helmets: list[tuple[list[float], float]] = []

        if result.boxes is not None:
            for box in result.boxes:
                class_name = str(model.names[int(box.cls.item())])
                xyxy = box.xyxy[0].cpu().tolist()
                confidence = float(box.conf.item())
                if class_name == "hook":
                    hooks.append((xyxy, confidence))
                elif class_name == "no_helmet":
                    no_helmets.append((xyxy, confidence))
                elif class_name == "helmet":
                    helmets.append((xyxy, confidence))

        violation: tuple[float, float] | None = None
        for hook_box, hook_confidence in hooks:
            hx, hy = center(hook_box)
            for head_box, head_confidence in no_helmets:
                px, py = center(head_box)
                if abs(px - hx) <= args.horizontal and -80 <= py - hy <= args.vertical:
                    candidate = (head_confidence, hook_confidence)
                    if violation is None or candidate[0] > violation[0]:
                        violation = candidate

        timestamp = frame_index / fps
        if violation is not None:
            if active is None:
                active = OpenEvent(timestamp, timestamp, violation[0], violation[1])
            else:
                active.last_seen = timestamp
                active.confidence = max(active.confidence, violation[0])
                active.hook_confidence = max(active.hook_confidence, violation[1])
        elif active is not None and timestamp - active.last_seen > args.merge_gap:
            if active.last_seen - active.start >= args.min_duration:
                events.append(
                    {
                        "id": f"ALM-{len(events) + 1:03d}",
                        "start": round(active.start, 2),
                        "end": round(active.last_seen, 2),
                        "level": "high",
                        "title": "吊钩作业区未佩戴安全帽",
                        "location": "一号吊装作业区",
                        "confidence": round(active.confidence, 2),
                        "hookConfidence": round(active.hook_confidence, 2),
                    }
                )
            active = None

        frame_index += 1
        if frame_index % 250 == 0:
            print(f"分析进度 {frame_index}/{total_frames}", flush=True)

    capture.release()
    if active is not None and active.last_seen - active.start >= args.min_duration:
        events.append(
            {
                "id": f"ALM-{len(events) + 1:03d}",
                "start": round(active.start, 2),
                "end": round(active.last_seen, 2),
                "level": "high",
                "title": "吊钩作业区未佩戴安全帽",
                "location": "一号吊装作业区",
                "confidence": round(active.confidence, 2),
                "hookConfidence": round(active.hook_confidence, 2),
            }
        )

    destination = project_path(args.output)
    destination.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "camera": "CAM-01",
        "duration": round(total_frames / fps, 2),
        "rule": {
            "name": "吊钩下方安全帽规则",
            "horizontalPixels": args.horizontal,
            "verticalPixels": args.vertical,
            "minDurationSeconds": args.min_duration,
        },
        "events": events,
    }
    destination.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"生成 {len(events)} 个告警事件: {destination}")


if __name__ == "__main__":
    main()

