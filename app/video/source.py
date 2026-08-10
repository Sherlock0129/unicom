from __future__ import annotations

import cv2
import numpy as np


class VideoSource:
    def __init__(self, source: str | int) -> None:
        if isinstance(source, str) and source.isdigit():
            source = int(source)
        self.source = source
        self.capture: cv2.VideoCapture | None = None

    def open(self) -> None:
        self.capture = cv2.VideoCapture(self.source)
        if not self.capture.isOpened():
            raise RuntimeError(f"无法打开视频源: {self.source}")

    def read(self) -> tuple[bool, np.ndarray | None]:
        if self.capture is None:
            self.open()
        assert self.capture is not None
        return self.capture.read()

    @property
    def fps(self) -> float:
        if self.capture is None:
            return 25.0
        value = self.capture.get(cv2.CAP_PROP_FPS)
        return value if value and value > 0 else 25.0

    def release(self) -> None:
        if self.capture is not None:
            self.capture.release()
            self.capture = None

