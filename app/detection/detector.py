from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from ultralytics import YOLO


@dataclass(frozen=True)
class Detection:
    x1: int
    y1: int
    x2: int
    y2: int
    confidence: float
    class_id: int
    class_name: str
    track_id: int | None = None

    @property
    def box(self) -> tuple[int, int, int, int]:
        return self.x1, self.y1, self.x2, self.y2

    @property
    def center(self) -> tuple[float, float]:
        return (self.x1 + self.x2) / 2, (self.y1 + self.y2) / 2


class HelmetDetector:
    def __init__(
        self,
        model_path: str,
        confidence: float = 0.45,
        iou: float = 0.50,
        image_size: int = 640,
        device: str = "cpu",
        tracking_enabled: bool = True,
        tracker: str = "bytetrack.yaml",
    ) -> None:
        self.model = YOLO(model_path)
        self.confidence = confidence
        self.iou = iou
        self.image_size = image_size
        self.device = device
        self.tracking_enabled = tracking_enabled
        self.tracker = tracker

    def detect(self, frame: np.ndarray) -> list[Detection]:
        common_args = {
            "source": frame,
            "conf": self.confidence,
            "iou": self.iou,
            "imgsz": self.image_size,
            "device": self.device,
            "verbose": False,
        }

        if self.tracking_enabled:
            results = self.model.track(
                **common_args,
                persist=True,
                tracker=self.tracker,
            )
        else:
            results = self.model.predict(**common_args)

        result = results[0]
        if result.boxes is None:
            return []

        detections: list[Detection] = []
        boxes = result.boxes

        for index, box in enumerate(boxes):
            x1, y1, x2, y2 = box.xyxy[0].cpu().tolist()
            class_id = int(box.cls[0].item())
            track_id = None
            if boxes.id is not None:
                track_id = int(boxes.id[index].item())

            detections.append(
                Detection(
                    x1=int(x1),
                    y1=int(y1),
                    x2=int(x2),
                    y2=int(y2),
                    confidence=float(box.conf[0].item()),
                    class_id=class_id,
                    class_name=str(self.model.names[class_id]),
                    track_id=track_id,
                )
            )

        return detections

