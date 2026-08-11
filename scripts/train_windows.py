from __future__ import annotations

import argparse
import shutil
from pathlib import Path

from ultralytics import YOLO

from app.core.config import project_path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="在 Windows CUDA 环境训练轻量四类别模型")
    parser.add_argument("--model", default="yolo11n.pt")
    parser.add_argument("--data", default="data/datasets/helmet_light/helmet.yaml")
    parser.add_argument("--epochs", type=int, default=60)
    parser.add_argument("--imgsz", type=int, default=640)
    parser.add_argument("--batch", type=int, default=4)
    parser.add_argument("--device", default="0")
    parser.add_argument("--name", default="light_v1")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    dataset_yaml = project_path(args.data)
    if not dataset_yaml.exists():
        raise FileNotFoundError(
            f"未找到数据集配置: {dataset_yaml}\n"
            "请先运行 python -m scripts.prepare_light_dataset"
        )

    model = YOLO(args.model)
    model.train(
        data=str(dataset_yaml),
        epochs=args.epochs,
        imgsz=args.imgsz,
        batch=args.batch,
        device=args.device,
        workers=0,
        patience=12,
        cache="disk",
        deterministic=False,
        project=str(project_path("runs/helmet")),
        name=args.name,
        exist_ok=True,
        plots=True,
    )

    if model.trainer is None:
        raise RuntimeError("训练器未返回结果")
    best_weight = Path(model.trainer.best)
    if not best_weight.exists():
        raise FileNotFoundError(f"训练完成但未找到最佳权重: {best_weight}")

    destination = project_path("models/best.pt")
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(best_weight, destination)
    print(f"最佳模型已复制到: {destination}")


if __name__ == "__main__":
    main()

