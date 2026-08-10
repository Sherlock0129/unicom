from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

import cv2
import numpy as np

from app.core.config import project_path
from app.detection.association import PersonObservation


class AlarmManager:
    def __init__(self, output_dir: str, event_file: str) -> None:
        self.output_dir = project_path(output_dir)
        self.event_file = project_path(event_file)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.event_file.parent.mkdir(parents=True, exist_ok=True)

    def create_alarm(
        self,
        frame: np.ndarray,
        observation: PersonObservation,
        camera_id: str,
    ) -> dict[str, object]:
        now = datetime.now().astimezone()
        timestamp = now.strftime("%Y%m%d_%H%M%S_%f")
        track_id = observation.person.track_id
        filename = f"{camera_id}_track-{track_id}_{timestamp}.jpg"
        image_path = self.output_dir / filename

        cv2.imwrite(str(image_path), frame)

        event: dict[str, object] = {
            "event": "no_helmet",
            "camera_id": camera_id,
            "track_id": track_id,
            "occurred_at": now.isoformat(),
            "confidence": (
                observation.ppe_detection.confidence
                if observation.ppe_detection is not None
                else None
            ),
            "person_box": list(observation.person.box),
            "image": str(Path("runtime/alarms") / filename),
        }

        with self.event_file.open("a", encoding="utf-8") as file:
            file.write(json.dumps(event, ensure_ascii=False) + "\n")

        return event

