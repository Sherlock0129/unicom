from __future__ import annotations

import cv2
import numpy as np

from app.detection.association import HelmetState
from app.rules.helmet_rule import RuleResult


COLORS = {
    HelmetState.HELMET: (40, 200, 40),
    HelmetState.NO_HELMET: (0, 165, 255),
    HelmetState.UNKNOWN: (160, 160, 160),
}


def draw_rule_result(frame: np.ndarray, result: RuleResult) -> None:
    observation = result.observation
    person = observation.person
    color = (0, 0, 255) if result.alarm_active else COLORS[observation.helmet_state]

    cv2.rectangle(frame, (person.x1, person.y1), (person.x2, person.y2), color, 2)

    track = f"ID {person.track_id}" if person.track_id is not None else "ID -"
    region = "IN" if observation.in_region else "OUT"
    status = "ALARM" if result.alarm_active else observation.helmet_state.value.upper()
    label = f"{track} | {region} | {status}"

    cv2.putText(
        frame,
        label,
        (person.x1, max(24, person.y1 - 8)),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.55,
        color,
        2,
        cv2.LINE_AA,
    )

