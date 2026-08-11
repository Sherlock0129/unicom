from __future__ import annotations

import argparse
import shutil
from pathlib import Path

import yaml

from app.core.config import load_yaml, project_path


FILE_PREFIX = "val_val_4min_"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="构建轻量安全帽训练数据集")
    parser.add_argument("--config", default="configs/light_dataset.yaml")
    return parser.parse_args()


def copy_split(
    source_images: Path,
    source_labels: Path,
    output_root: Path,
    split: str,
    start: int,
    end: int,
) -> int:
    image_output = output_root / "images" / split
    label_output = output_root / "labels" / split
    image_output.mkdir(parents=True, exist_ok=True)
    label_output.mkdir(parents=True, exist_ok=True)

    copied = 0
    for index in range(start, end + 1):
        stem = f"{FILE_PREFIX}{index:06d}"
        source_image = source_images / f"{stem}.jpg"
        source_label = source_labels / f"{stem}.txt"
        if not source_image.exists():
            raise FileNotFoundError(f"缺少原图片: {source_image}")
        if not source_label.exists():
            raise FileNotFoundError(f"缺少标签: {source_label}")

        shutil.copy2(source_image, image_output / source_image.name)
        shutil.copy2(source_label, label_output / source_label.name)
        copied += 1

    return copied


def validate_label(path: Path, class_count: int) -> dict[int, int]:
    counts = {index: 0 for index in range(class_count)}
    for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        fields = line.split()
        if len(fields) != 5:
            raise ValueError(f"标签字段数不是 5: {path}:{line_number}")
        class_id = int(fields[0])
        coordinates = [float(value) for value in fields[1:]]
        if class_id not in counts:
            raise ValueError(f"类别 ID 超出范围: {path}:{line_number}")
        if any(value < 0 or value > 1 for value in coordinates):
            raise ValueError(f"归一化坐标超出 [0, 1]: {path}:{line_number}")
        counts[class_id] += 1
    return counts


def write_dataset_yaml(output_root: Path, classes: list[str]) -> Path:
    dataset_yaml = output_root / "helmet.yaml"
    content = {
        "path": output_root.resolve().as_posix(),
        "train": "images/train",
        "val": "images/val",
        "test": "images/test",
        "names": {index: name for index, name in enumerate(classes)},
    }
    with dataset_yaml.open("w", encoding="utf-8") as file:
        yaml.safe_dump(content, file, allow_unicode=True, sort_keys=False)
    return dataset_yaml


def main() -> None:
    args = parse_args()
    config = load_yaml(args.config)
    source_images = project_path(config["source_images"])
    output_root = project_path(config["output"])
    classes = [str(name) for name in config["classes"]]

    total = 0
    for split, split_config in config["splits"].items():
        count = copy_split(
            source_images=source_images,
            source_labels=project_path(split_config["labels"]),
            output_root=output_root,
            split=str(split),
            start=int(split_config["start"]),
            end=int(split_config["end"]),
        )
        total += count

        class_counts = {index: 0 for index in range(len(classes))}
        for label_path in (output_root / "labels" / str(split)).glob("*.txt"):
            for class_id, value in validate_label(label_path, len(classes)).items():
                class_counts[class_id] += value
        readable_counts = {
            classes[class_id]: value for class_id, value in class_counts.items()
        }
        print(f"{split}: {count} 张，标注框 {readable_counts}")

    dataset_yaml = write_dataset_yaml(output_root, classes)
    print(f"数据集准备完成，共 {total} 张图片")
    print(f"训练配置: {dataset_yaml}")


if __name__ == "__main__":
    main()

