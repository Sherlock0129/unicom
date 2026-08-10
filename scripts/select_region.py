from __future__ import annotations

import argparse
import json
from pathlib import Path

import cv2

from app.core.config import project_path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="在视频首帧中选择检测区域")
    parser.add_argument("--source", required=True, help="视频路径、摄像头编号或 RTSP URL")
    parser.add_argument("--camera-id", default="camera_01")
    parser.add_argument("--name", default="生产作业区")
    parser.add_argument("--output", default="configs/regions.json")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    source: str | int = args.source
    if source.isdigit():
        source = int(source)
    elif not source.startswith(("rtsp://", "http://", "https://")):
        source = str(project_path(source))

    capture = cv2.VideoCapture(source)
    success, frame = capture.read()
    capture.release()
    if not success or frame is None:
        raise RuntimeError(f"无法读取视频源: {args.source}")

    points: list[list[int]] = []
    window = "Select ROI | Left click: add | S: save | R: reset | Q: quit"

    def on_mouse(event, x, y, _flags, _param) -> None:
        if event == cv2.EVENT_LBUTTONDOWN:
            points.append([x, y])

    cv2.namedWindow(window)
    cv2.setMouseCallback(window, on_mouse)

    while True:
        canvas = frame.copy()
        for point in points:
            cv2.circle(canvas, tuple(point), 5, (0, 255, 255), -1)
        if len(points) >= 2:
            cv2.polylines(
                canvas,
                [__import__("numpy").asarray(points, dtype="int32")],
                len(points) >= 3,
                (0, 255, 255),
                2,
            )
        cv2.imshow(window, canvas)
        key = cv2.waitKey(20) & 0xFF

        if key == ord("r"):
            points.clear()
        elif key == ord("q"):
            break
        elif key == ord("s"):
            if len(points) < 3:
                print("区域至少需要 3 个顶点")
                continue
            save_region(args.output, args.camera_id, args.name, points)
            print(f"区域已保存到 {project_path(args.output)}")
            break

    cv2.destroyAllWindows()


def save_region(output: str, camera_id: str, name: str, points: list[list[int]]) -> None:
    path = project_path(output)
    path.parent.mkdir(parents=True, exist_ok=True)
    existing = {}
    if path.exists():
        with path.open("r", encoding="utf-8") as file:
            existing = json.load(file)
    existing[camera_id] = {"name": name, "polygon": points}
    with path.open("w", encoding="utf-8") as file:
        json.dump(existing, file, ensure_ascii=False, indent=2)


if __name__ == "__main__":
    main()

