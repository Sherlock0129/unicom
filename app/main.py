from __future__ import annotations

from app.alarm.manager import AlarmManager
from app.core.config import AppConfig, load_json, project_path
from app.detection.detector import HelmetDetector
from app.rules.helmet_rule import HelmetRuleEngine
from app.rules.roi import RegionOfInterest
from app.video.processor import VideoProcessor
from app.video.source import VideoSource


def build_processor(config: AppConfig) -> VideoProcessor:
    raw = config.raw
    model = raw["model"]
    tracking = raw["tracking"]
    video = raw["video"]
    region_config = raw["region"]
    rule = raw["rule"]
    alarm = raw["alarm"]

    model_path = project_path(model["path"])
    if not model_path.exists():
        raise FileNotFoundError(
            f"未找到模型文件: {model_path}\n"
            "请将训练好的 best.pt 放入 models 目录，或修改 configs/app.yaml。"
        )

    regions = load_json(region_config["file"])
    camera_id = str(region_config["camera_id"])
    if camera_id not in regions:
        raise KeyError(f"区域配置中不存在摄像头: {camera_id}")

    source_value = video["source"]
    if isinstance(source_value, str) and not source_value.startswith(
        ("rtsp://", "http://", "https://")
    ):
        source_value = str(project_path(source_value))

    detector = HelmetDetector(
        model_path=str(model_path),
        confidence=float(model["confidence"]),
        iou=float(model["iou"]),
        image_size=int(model["image_size"]),
        device=str(model["device"]),
        tracking_enabled=bool(tracking["enabled"]),
        tracker=str(tracking["tracker"]),
    )

    return VideoProcessor(
        detector=detector,
        source=VideoSource(source_value),
        roi=RegionOfInterest(regions[camera_id]["polygon"]),
        rule_engine=HelmetRuleEngine(
            alarm_after=float(rule["alarm_after_seconds"]),
            clear_after=float(rule["clear_after_seconds"]),
        ),
        alarm_manager=AlarmManager(
            output_dir=str(alarm["output_dir"]),
            event_file=str(alarm["event_file"]),
        ),
        class_names=config.classes,
        camera_id=camera_id,
        head_ratio=float(rule["head_ratio"]),
        display=bool(video["display"]),
        save_output=bool(video["save_output"]),
        output_path=str(video["output_path"]),
    )


def main() -> None:
    config = AppConfig.from_file()
    processor = build_processor(config)
    processor.run()


if __name__ == "__main__":
    main()

