from __future__ import annotations

from PySide6.QtCore import QPointF, Qt, Signal
from PySide6.QtGui import QColor, QPainter, QPen
from PySide6.QtWidgets import QWidget

from golf_desktop.domain.models import HoleView, ShotPoint


class CourseCanvas(QWidget):
    """Draws a simple fairway, tee, green, and shot trail for one hole."""

    MARGIN = 24
    MAX_X = 250.0
    MIN_Y = -60.0
    SPAN_Y = 200.0

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

    def course_to_widget(self, x: float, y: float) -> QPointF:
        w, h = self.width(), self.height()
        margin = self.MARGIN
        inner_w = max(1, w - 2 * margin)
        inner_h = max(1, h - 2 * margin)
        nx = x / self.MAX_X
        ny = (y - self.MIN_Y) / self.SPAN_Y
        nx = max(0.0, min(1.0, nx))
        ny = max(0.0, min(1.0, ny))
        return QPointF(margin + nx * inner_w, margin + (1.0 - ny) * inner_h)

    def widget_to_course(self, pos: QPointF) -> tuple[float, float]:
        margin = self.MARGIN
        w, h = self.width(), self.height()
        inner_w = max(1, w - 2 * margin)
        inner_h = max(1, h - 2 * margin)
        nx = (pos.x() - margin) / inner_w
        ny = 1.0 - (pos.y() - margin) / inner_h
        nx = max(0.0, min(1.0, nx))
        ny = max(0.0, min(1.0, ny))
        cx = nx * self.MAX_X
        cy = self.MIN_Y + ny * self.SPAN_Y
        return cx, cy

    def paintEvent(self, event) -> None:  # noqa: ARG002
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        w, h = self.width(), self.height()
        painter.fillRect(0, 0, w, h, QColor(34, 85, 51))

        if self._hole:
            tee = self.course_to_widget(self._hole.tee_x, self._hole.tee_y)
            green = self.course_to_widget(self._hole.green_x, self._hole.green_y)
            painter.setPen(QPen(QColor(200, 230, 200), 14, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
            painter.drawLine(tee, green)

            painter.setBrush(QColor(180, 140, 90))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawEllipse(tee, 8, 8)

            painter.setBrush(QColor(80, 160, 80))
            painter.drawEllipse(green, 12, 12)

        if self._hole and self._shots:
            ordered = sorted(self._shots, key=lambda sp: sp.shot_at)
            painter.setPen(QPen(QColor(255, 220, 80), 2))
            tee_pt = self.course_to_widget(self._hole.tee_x, self._hole.tee_y)
            prev = tee_pt
            for s in ordered:
                p = self.course_to_widget(s.x, s.y)
                painter.drawLine(prev, p)
                prev = p

        painter.setPen(QPen(QColor(255, 255, 255), 1))
        painter.setBrush(QColor(255, 80, 80))
        for s in self._shots:
            p = self.course_to_widget(s.x, s.y)
            painter.drawEllipse(p, 4, 4)


class InteractiveHoleCanvas(CourseCanvas):
    """Same map as CourseCanvas; left-click emits course coordinates for a new shot."""

    shot_clicked = Signal(float, float)

    def mousePressEvent(self, event) -> None:
        if event.button() == Qt.LeftButton:
            pos = event.position().toPointF()
            cx, cy = self.widget_to_course(pos)
            self.shot_clicked.emit(cx, cy)
        super().mousePressEvent(event)
