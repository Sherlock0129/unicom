from __future__ import annotations

import shutil
from pathlib import Path

import yaml

from app.core.config import project_path


CLASSES = ["person", "helmet", "no_helmet", "hook"]
OUTPUT_ROOT = project_path("data/datasets/helmet_light_v2")


def copy_range(
    source_images: Path,
    source_labels: Path,
    split: str,
    prefix: str,
    start: int,
    end: int,
) -> int:
    image_output = OUTPUT_ROOT / "images" / split
    label_output = OUTPUT_ROOT / "labels" / split
    image_output.mkdir(parents=True, exist_ok=True)
    label_output.mkdir(parents=True, exist_ok=True)

    for index in range(start, end + 1):
        stem = f"{prefix}{index:06d}"
        source_image = source_images / f"{stem}.jpg"
        source_label = source_labels / f"{stem}.txt"
        if not source_image.exists():
            raise FileNotFoundError(f"缺少图片: {source_image}")
        if not source_label.exists():
            raise FileNotFoundError(f"缺少标签: {source_label}")
        shutil.copy2(source_image, image_output / source_image.name)
        shutil.copy2(source_label, label_output / source_label.name)

    return end - start + 1


def audit_split(split: str) -> tuple[int, dict[str, int]]:
    image_dir = OUTPUT_ROOT / "images" / split
    label_dir = OUTPUT_ROOT / "labels" / split
    image_names = {path.stem for path in image_dir.glob("*.jpg")}
    label_names = {path.stem for path in label_dir.glob("*.txt")}
    if image_names != label_names:
        raise ValueError(
            f"{split} 图片标签不匹配: "
            f"缺标签 {sorted(image_names - label_names)[:5]}，"
            f"缺图片 {sorted(label_names - image_names)[:5]}"
        )

    counts = {index: 0 for index in range(len(CLASSES))}
    for path in label_dir.glob("*.txt"):
        for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
            fields = line.split()
            if len(fields) != 5:
                raise ValueError(f"标签字段数错误: {path}:{line_number}")
            class_id = int(fields[0])
            coordinates = [float(value) for value in fields[1:]]
            if class_id not in counts or any(value < 0 or value > 1 for value in coordinates):
                raise ValueError(f"标签值错误: {path}:{line_number}")
            counts[class_id] += 1

    return len(image_names), {CLASSES[index]: value for index, value in counts.items()}


def write_yaml() -> Path:
    destination = OUTPUT_ROOT / "helmet.yaml"
    content = {
        "path": OUTPUT_ROOT.resolve().as_posix(),
        "train": "images/train",
        "val": "images/val",
        "test": "images/test",
        "names": {index: name for index, name in enumerate(CLASSES)},
    }
    with destination.open("w", encoding="utf-8") as file:
        yaml.safe_dump(content, file, allow_unicode=True, sort_keys=False)
    return destination


def main() -> None:
    val_images = project_path("data/datasets/helmet/images/val")
    train_images = project_path("data/datasets/helmet/images/train")

    copy_range(
        val_images,
        project_path("data/labels/train"),
        "train",
        "val_val_4min_",
        0,
        75,
    )
    copy_range(
        val_images,
        project_path("data/labels/validate"),
        "val",
        "val_val_4min_",
        76,
        90,
    )
    copy_range(
        val_images,
        project_path("data/labels/test"),
        "test",
        "val_val_4min_",
        91,
        105,
    )
    copy_range(
        train_images,
        project_path("data/labels_additional/train"),
        "train",
        "train_train_13min_",
        230,
        309,
    )

    for split in ("train", "val", "test"):
        image_count, class_counts = audit_split(split)
        print(f"{split}: {image_count} 张，标注框 {class_counts}")

    print(f"扩展数据集配置: {write_yaml()}")


if __name__ == "__main__":
    main()

