from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path

import cv2


PROJECT_ROOT = Path(__file__).resolve().parents[1]


@dataclass(frozen=True)
class ExtractionTask:
    source: Path
    split: str
    interval_seconds: float


DEFAULT_TASKS = (
    ExtractionTask(
        source=PROJECT_ROOT / "data/raw_videos/train_13min.mp4",
        split="train",
        interval_seconds=2.0,
    ),
    ExtractionTask(
        source=PROJECT_ROOT / "data/raw_videos/val_4min.mp4",
        split="val",
        interval_seconds=2.0,
    ),
    ExtractionTask(
        source=PROJECT_ROOT / "data/raw_videos/test_1min.mp4",
        split="test",
        interval_seconds=1.0,
    ),
)


def extract_frames(task: ExtractionTask, overwrite: bool = False) -> int:
    if not task.source.exists():
        raise FileNotFoundError(f"未找到视频文件: {task.source}")

    output_dir = PROJECT_ROOT / "data/datasets/helmet/images" / task.split
    output_dir.mkdir(parents=True, exist_ok=True)

    capture = cv2.VideoCapture(str(task.source))
    if not capture.isOpened():
        raise RuntimeError(f"OpenCV 无法打开视频: {task.source}")

    fps = capture.get(cv2.CAP_PROP_FPS)
    total_frames = int(capture.get(cv2.CAP_PROP_FRAME_COUNT))
    if fps <= 0:
        capture.release()
        raise RuntimeError(f"无法读取视频帧率: {task.source}")

    sample_step = max(1, round(fps * task.interval_seconds))
    prefix = f"{task.split}_{task.source.stem}"
    frame_index = 0
    saved_count = 0

    while True:
        success, frame = capture.read()
        if not success or frame is None:
            break

        if frame_index % sample_step == 0:
            destination = output_dir / f"{prefix}_{saved_count:06d}.jpg"
            if overwrite or not destination.exists():
                if not cv2.imwrite(str(destination), frame):
                    capture.release()
                    raise RuntimeError(f"图片写入失败: {destination}")
            saved_count += 1

        frame_index += 1
        if total_frames > 0 and frame_index % max(1, sample_step * 50) == 0:
            progress = min(100.0, frame_index / total_frames * 100)
            print(f"  {task.split}: {progress:5.1f}%", end="\r")

    capture.release()
    print(
        f"  {task.split}: 完成，{saved_count} 张，"
        f"原视频 {fps:.2f} FPS，抽帧间隔 {task.interval_seconds:.1f} 秒"
    )
    return saved_count


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="从单视角安全帽视频数据中抽帧")
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="覆盖已经存在的同名图片",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    total = 0
    for task in DEFAULT_TASKS:
        print(f"处理 {task.source.name} -> {task.split}")
        total += extract_frames(task, overwrite=args.overwrite)

    print(f"全部完成，共生成或确认 {total} 张图片。")
    print("演示视频 demo_1min.mp4 保持完整，不参与训练或抽帧。")


if __name__ == "__main__":
    main()

