from __future__ import annotations

import time
from dataclasses import replace
from pathlib import Path

import cv2

from app.alarm.manager import AlarmManager
from app.core.config import project_path
from app.detection.association import associate_ppe_to_people
from app.detection.detector import HelmetDetector
from app.rules.helmet_rule import HelmetRuleEngine
from app.rules.roi import RegionOfInterest
from app.ui.drawer import draw_rule_result
from app.video.source import VideoSource


class VideoProcessor:
    def __init__(
        self,
        detector: HelmetDetector,
        source: VideoSource,
        roi: RegionOfInterest,
        rule_engine: HelmetRuleEngine,
        alarm_manager: AlarmManager,
        class_names,
        camera_id: str,
        head_ratio: float,
        display: bool,
        save_output: bool,
        output_path: str,
    ) -> None:
        self.detector = detector
        self.source = source
        self.roi = roi
        self.rule_engine = rule_engine
        self.alarm_manager = alarm_manager
        self.class_names = class_names
        self.camera_id = camera_id
        self.head_ratio = head_ratio
        self.display = display
        self.save_output = save_output
        self.output_path = project_path(output_path)

    def run(self) -> None:
        self.source.open()
        writer: cv2.VideoWriter | None = None

        try:
            while True:
                success, frame = self.source.read()
                if not success or frame is None:
                    break

                now = time.monotonic()
                detections = self.detector.detect(frame)
                observations = associate_ppe_to_people(
                    detections,
                    self.class_names,
                    self.head_ratio,
                )

                self.roi.draw(frame)
                for index, observation in enumerate(observations):
                    observation = replace(
                        observation,
                        in_region=self.roi.contains_person(observation.person),
                    )
                    rule_result = self.rule_engine.evaluate(observation, now, index)
                    draw_rule_result(frame, rule_result)

                    if rule_result.alarm_started_now:
                        event = self.alarm_manager.create_alarm(
                            frame,
                            observation,
                            self.camera_id,
                        )
                        print(f"[ALARM] {event}")

                self.rule_engine.remove_stale_tracks(now)

                if self.save_output:
                    if writer is None:
                        writer = self._create_writer(frame.shape[1], frame.shape[0])
                    writer.write(frame)

                if self.display:
                    cv2.imshow("Factory Helmet Detection", frame)
                    if cv2.waitKey(1) & 0xFF == ord("q"):
                        break
        finally:
            self.source.release()
            if writer is not None:
                writer.release()
            cv2.destroyAllWindows()

    def _create_writer(self, width: int, height: int) -> cv2.VideoWriter:
        self.output_path.parent.mkdir(parents=True, exist_ok=True)
        writer = cv2.VideoWriter(
            str(self.output_path),
            cv2.VideoWriter_fourcc(*"mp4v"),
            self.source.fps,
            (width, height),
        )
        if not writer.isOpened():
            raise RuntimeError(f"无法创建输出视频: {self.output_path}")
        return writer

