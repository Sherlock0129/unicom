from __future__ import annotations

import argparse
from pathlib import Path

import cv2
from ultralytics import YOLO

from app.core.config import project_path


EXPECTED_CLASSES = {
    0: "person",
    1: "helmet",
    2: "no_helmet",
    3: "hook",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="运行轻量四类别视频演示")
    parser.add_argument("--model", default="models/best.pt")
    parser.add_argument("--source", default="data/raw_videos/demo_video.mp4")
    parser.add_argument("--output", default="data/output/demo_result.mp4")
    parser.add_argument("--conf", type=float, default=0.35)
    parser.add_argument("--imgsz", type=int, default=640)
    parser.add_argument("--device", default="0")
    parser.add_argument("--show", action="store_true", help="同时显示实时窗口")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    model_path = project_path(args.model)
    source_path = project_path(args.source)
    output_path = project_path(args.output)

    if not model_path.exists():
        raise FileNotFoundError(
            f"未找到模型: {model_path}\n请先运行 python -m scripts.train"
        )
    if not source_path.exists():
        raise FileNotFoundError(f"未找到演示视频: {source_path}")

    model = YOLO(str(model_path))
    actual_classes = {int(index): str(name) for index, name in model.names.items()}
    if actual_classes != EXPECTED_CLASSES:
        raise ValueError(
            f"模型类别与 Demo 不一致。期望 {EXPECTED_CLASSES}，实际 {actual_classes}"
        )

    capture = cv2.VideoCapture(str(source_path))
    if not capture.isOpened():
        raise RuntimeError(f"无法打开演示视频: {source_path}")

    width = int(capture.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(capture.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fps = capture.get(cv2.CAP_PROP_FPS)
    if fps <= 0:
        fps = 25.0

    output_path.parent.mkdir(parents=True, exist_ok=True)
    writer = cv2.VideoWriter(
        str(output_path),
        cv2.VideoWriter_fourcc(*"mp4v"),
        fps,
        (width, height),
    )
    if not writer.isOpened():
        capture.release()
        raise RuntimeError(f"无法创建结果视频: {output_path}")

    processed = 0
    try:
        while True:
            success, frame = capture.read()
            if not success or frame is None:
                break

            result = model.predict(
                source=frame,
                conf=args.conf,
                imgsz=args.imgsz,
                device=args.device,
                verbose=False,
            )[0]
            annotated = result.plot()
            writer.write(annotated)
            processed += 1

            if args.show:
                cv2.imshow("Helmet Detection Demo", annotated)
                if cv2.waitKey(1) & 0xFF == ord("q"):
                    break

            if processed % 100 == 0:
                print(f"已处理 {processed} 帧", flush=True)
    finally:
        capture.release()
        writer.release()
        cv2.destroyAllWindows()

    print(f"演示完成，共处理 {processed} 帧")
    print(f"结果视频: {output_path}")


if __name__ == "__main__":
    main()

