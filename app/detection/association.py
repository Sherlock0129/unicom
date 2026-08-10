from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from app.core.config import ClassNames
from app.detection.detector import Detection


class HelmetState(str, Enum):
    HELMET = "helmet"
    NO_HELMET = "no_helmet"
    UNKNOWN = "unknown"


@dataclass(frozen=True)
class PersonObservation:
    person: Detection
    helmet_state: HelmetState
    ppe_detection: Detection | None
    in_region: bool = False


def _point_in_box(
    point: tuple[float, float],
    box: tuple[float, float, float, float],
) -> bool:
    x, y = point
    x1, y1, x2, y2 = box
    return x1 <= x <= x2 and y1 <= y <= y2


def associate_ppe_to_people(
    detections: list[Detection],
    class_names: ClassNames,
    head_ratio: float,
) -> list[PersonObservation]:
    """Match helmet/no-helmet detections to a person's upper body area."""
    people = [d for d in detections if d.class_name == class_names.person]
    ppe = [
        d
        for d in detections
        if d.class_name in {class_names.helmet, class_names.no_helmet}
    ]

    observations: list[PersonObservation] = []
    for person in people:
        head_bottom = person.y1 + (person.y2 - person.y1) * head_ratio
        head_box = (person.x1, person.y1, person.x2, head_bottom)
        candidates = [item for item in ppe if _point_in_box(item.center, head_box)]

        match = max(candidates, key=lambda item: item.confidence, default=None)
        if match is None:
            state = HelmetState.UNKNOWN
        elif match.class_name == class_names.no_helmet:
            state = HelmetState.NO_HELMET
        else:
            state = HelmetState.HELMET

        observations.append(
            PersonObservation(
                person=person,
                helmet_state=state,
                ppe_detection=match,
            )
        )

    return observations

