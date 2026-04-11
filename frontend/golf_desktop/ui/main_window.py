from __future__ import annotations

from datetime import datetime

from PySide6.QtCore import QTimer
from PySide6.QtWidgets import (
    QComboBox,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from golf_desktop.api_client import GolfApiClient
from golf_desktop.domain.models import HoleView, RoundSummary, ShotPoint
from golf_desktop.ui.course_canvas import CourseCanvas


class MainWindow(QMainWindow):
    def __init__(self, api: GolfApiClient, parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Golf Desktop")
        self._api = api
        self._rounds: list[RoundSummary] = []
        self._holes: list[HoleView] = []

        central = QWidget()
        central.setObjectName("centralWidget")
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)

        row = QHBoxLayout()
        self._round_combo = QComboBox()
        self._round_combo.setObjectName("roundCombo")
        self._hole_combo = QComboBox()
        self._hole_combo.setObjectName("holeCombo")
        refresh = QPushButton("Refresh")
        refresh.setObjectName("refreshButton")
        refresh.clicked.connect(self._schedule_refresh)
        row.addWidget(QLabel("Round"))
        row.addWidget(self._round_combo, stretch=1)
        row.addWidget(QLabel("Hole"))
        row.addWidget(self._hole_combo, stretch=1)
        row.addWidget(refresh)
        layout.addLayout(row)

        self._canvas = CourseCanvas()
        layout.addWidget(self._canvas, stretch=1)

        self._round_combo.currentIndexChanged.connect(self._on_round_changed)
        self._hole_combo.currentIndexChanged.connect(self._on_hole_changed)

        self._timer = QTimer(self)
        self._timer.setSingleShot(True)
        self._timer.timeout.connect(self._load_data)

        self._schedule_refresh()

    def _schedule_refresh(self) -> None:
        self._timer.start(0)

    async def refresh_async(self) -> None:
        """Public for tests — load rounds and current selection."""
        await self._load_data_async()

    def _load_data(self) -> None:
        import asyncio

        asyncio.ensure_future(self._load_data_async())

    async def _load_data_async(self) -> None:
        try:
            raw_rounds = await self._api.get_rounds()
        except Exception as e:  # noqa: BLE001
            QMessageBox.warning(self, "API error", str(e))
            return

        self._rounds = [
            RoundSummary(
                id=r["id"],
                player_id=r["player_id"],
                course_id=r["course_id"],
                started_at=datetime.fromisoformat(r["started_at"].replace("Z", "+00:00")),
                finished_at=(
                    datetime.fromisoformat(r["finished_at"].replace("Z", "+00:00"))
                    if r.get("finished_at")
                    else None
                ),
            )
            for r in raw_rounds
        ]

        self._round_combo.blockSignals(True)
        self._round_combo.clear()
        for rnd in self._rounds:
            label = f"Round #{rnd.id} (course {rnd.course_id})"
            self._round_combo.addItem(label, rnd.id)
        self._round_combo.blockSignals(False)

        if self._round_combo.count() == 0:
            self._canvas.set_hole_and_shots(None, [])
            return

        self._round_combo.setCurrentIndex(0)
        await self._load_holes_for_current_round()
        await self._load_shots_for_selection()

    def _on_round_changed(self) -> None:
        import asyncio

        asyncio.ensure_future(self._load_holes_for_current_round())
        asyncio.ensure_future(self._load_shots_for_selection())

    def _on_hole_changed(self) -> None:
        import asyncio

        asyncio.ensure_future(self._load_shots_for_selection())

    async def _load_holes_for_current_round(self) -> None:
        rid = self._current_round_id()
        if rid is None:
            self._hole_combo.blockSignals(True)
            self._hole_combo.clear()
            self._hole_combo.blockSignals(False)
            self._holes = []
            return

        course_id = next((r.course_id for r in self._rounds if r.id == rid), None)
        if course_id is None:
            return
        try:
            raw = await self._api.get_holes(course_id=course_id)
        except Exception as e:  # noqa: BLE001
            QMessageBox.warning(self, "API error", str(e))
            return

        self._holes = [
            HoleView(
                id=h["id"],
                course_id=h["course_id"],
                number=h["number"],
                par=h["par"],
                tee_x=h["tee_x"],
                tee_y=h["tee_y"],
                green_x=h["green_x"],
                green_y=h["green_y"],
            )
            for h in raw
        ]
        self._holes.sort(key=lambda x: x.number)

        self._hole_combo.blockSignals(True)
        self._hole_combo.clear()
        for h in self._holes:
            self._hole_combo.addItem(f"Hole {h.number} (par {h.par})", h.id)
        self._hole_combo.blockSignals(False)
        if self._hole_combo.count() > 0:
            self._hole_combo.setCurrentIndex(0)

    async def _load_shots_for_selection(self) -> None:
        rid = self._current_round_id()
        hid = self._current_hole_id()
        hole = next((h for h in self._holes if h.id == hid), None) if hid else None
        if rid is None or hid is None:
            self._canvas.set_hole_and_shots(hole, [])
            return
        try:
            raw = await self._api.get_shots(rid, hole_id=hid)
        except Exception as e:  # noqa: BLE001
            QMessageBox.warning(self, "API error", str(e))
            return

        shots = [
            ShotPoint(
                id=s["id"],
                round_id=s["round_id"],
                hole_id=s["hole_id"],
                x=s["x"],
                y=s["y"],
                club=s.get("club", ""),
                distance=s.get("distance"),
                shot_at=datetime.fromisoformat(s["shot_at"].replace("Z", "+00:00")),
            )
            for s in raw
        ]
        shots.sort(key=lambda s: (s.shot_at, s.id))
        self._canvas.set_hole_and_shots(hole, shots)

    def _current_round_id(self) -> int | None:
        i = self._round_combo.currentIndex()
        if i < 0:
            return None
        return int(self._round_combo.currentData())

    def _current_hole_id(self) -> int | None:
        i = self._hole_combo.currentIndex()
        if i < 0:
            return None
        return int(self._hole_combo.currentData())
