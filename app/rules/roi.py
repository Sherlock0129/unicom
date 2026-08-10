from __future__ import annotations

import cv2
import numpy as np

from app.detection.detector import Detection


class RegionOfInterest:
    def __init__(self, points: list[list[int]]) -> None:
        if len(points) < 3:
            raise ValueError("检测区域至少需要 3 个顶点")
        self.contour = np.asarray(points, dtype=np.int32)

    def contains(self, x: float, y: float) -> bool:
        return cv2.pointPolygonTest(
            self.contour,
            (float(x), float(y)),
            False,
        ) >= 0

    def contains_person(self, person: Detection) -> bool:
        foot_x = (person.x1 + person.x2) / 2
        foot_y = person.y2
        return self.contains(foot_x, foot_y)

    def draw(self, frame: np.ndarray) -> None:
        overlay = frame.copy()
        cv2.fillPoly(overlay, [self.contour], color=(0, 180, 255))
        cv2.addWeighted(overlay, 0.12, frame, 0.88, 0, dst=frame)
        cv2.polylines(
            frame,
            [self.contour],
            isClosed=True,
            color=(0, 220, 255),
            thickness=2,
        )

