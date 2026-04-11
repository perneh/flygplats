from __future__ import annotations

from PySide6.QtCore import QPointF, Qt
from PySide6.QtGui import QColor, QPainter, QPen
from PySide6.QtWidgets import QWidget

from golf_desktop.domain.models import HoleView, ShotPoint


class CourseCanvas(QWidget):
    """Draws a simple fairway, tee, green, and shot trail for one hole."""

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setMinimumSize(400, 320)
        self.setObjectName("courseCanvas")
        self._hole: HoleView | None = None
        self._shots: list[ShotPoint] = []

    def set_hole_and_shots(self, hole: HoleView | None, shots: list[ShotPoint]) -> None:
        self._hole = hole
        self._shots = list(shots)
        self.update()

    def paintEvent(self, event) -> None:  # noqa: ARG002
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        w, h = self.width(), self.height()
        painter.fillRect(0, 0, w, h, QColor(34, 85, 51))

        margin = 24
        inner_w = max(1, w - 2 * margin)
        inner_h = max(1, h - 2 * margin)

        def to_screen(x: float, y: float) -> QPointF:
            # Map course coords into a bounded box (assume rough 0..250 x, -50..150 y)
            max_x, min_y, span_y = 250.0, -60.0, 200.0
            nx = x / max_x
            ny = (y - min_y) / span_y
            nx = max(0.0, min(1.0, nx))
            ny = max(0.0, min(1.0, ny))
            return QPointF(margin + nx * inner_w, margin + (1.0 - ny) * inner_h)

        if self._hole:
            tee = to_screen(self._hole.tee_x, self._hole.tee_y)
            green = to_screen(self._hole.green_x, self._hole.green_y)
            painter.setPen(QPen(QColor(200, 230, 200), 14, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
            painter.drawLine(tee, green)

            painter.setBrush(QColor(180, 140, 90))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawEllipse(tee, 8, 8)

            painter.setBrush(QColor(80, 160, 80))
            painter.drawEllipse(green, 12, 12)

        if len(self._shots) >= 2:
            painter.setPen(QPen(QColor(255, 220, 80), 2))
            pts = [to_screen(s.x, s.y) for s in self._shots]
            for i in range(len(pts) - 1):
                painter.drawLine(pts[i], pts[i + 1])

        painter.setPen(QPen(QColor(255, 255, 255), 1))
        painter.setBrush(QColor(255, 80, 80))
        for s in self._shots:
            p = to_screen(s.x, s.y)
            painter.drawEllipse(p, 4, 4)
