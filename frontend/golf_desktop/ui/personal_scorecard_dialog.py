"""Personal scorecard: one player at a time — tournament gross or training round with GPS shots."""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Any, Literal

from PySide6.QtWidgets import (
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QDoubleSpinBox,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QSpinBox,
    QVBoxLayout,
)

from golf_desktop.api_client import GolfApiClient, GolfApiError
from golf_desktop.domain.models import HoleView, ShotPoint
from golf_desktop.ui.course_canvas import CourseCanvas, InteractiveHoleCanvas

log = logging.getLogger(__name__)

# Course coordinate ranges (same mapping as CourseCanvas).
_MAX_X = CourseCanvas.MAX_X
_MIN_Y = CourseCanvas.MIN_Y
_SPAN_Y = CourseCanvas.SPAN_Y

_CLUB_PRESETS: list[tuple[str, str]] = [
    ("— (optional)", ""),
    ("Driver", "Driver"),
    ("3-wood", "3W"),
    ("5-wood", "5W"),
    ("Hybrid", "Hybrid"),
    ("4-iron", "4i"),
    ("5-iron", "5i"),
    ("6-iron", "6i"),
    ("7-iron", "7i"),
    ("8-iron", "8i"),
    ("9-iron", "9i"),
    ("Pitching wedge", "PW"),
    ("Gap wedge", "GW"),
    ("Sand wedge", "SW"),
    ("Lob wedge", "LW"),
    ("Putter", "Putter"),
]


def _hole_number(h: dict[str, Any]) -> int:
    return int(h.get("hole") if h.get("hole") is not None else h.get("number", 0))


def _hole_dict_to_view(h: dict[str, Any]) -> HoleView:
    return HoleView(
        id=int(h["id"]),
        course_id=int(h["course_id"]),
        number=_hole_number(h),
        par=int(h.get("par", 4)),
        tee_x=float(h["tee_x"]),
        tee_y=float(h["tee_y"]),
        green_x=float(h["green_x"]),
        green_y=float(h["green_y"]),
    )


def _shot_dict_to_point(d: dict[str, Any]) -> ShotPoint:
    return ShotPoint(
        id=int(d["id"]),
        round_id=int(d["round_id"]),
        hole_id=int(d["hole_id"]),
        x=float(d["x"]),
        y=float(d["y"]),
        club=str(d.get("club") or ""),
        distance=float(d["distance"]) if d.get("distance") is not None else None,
        shot_at=datetime.fromisoformat(str(d["shot_at"]).replace("Z", "+00:00")),
    )


class PersonalScorecardRequestDialog(QDialog):
    """Pick player + scorecard context (started tournament or training round)."""

    def __init__(
        self,
        players: list[dict[str, Any]],
        started_tournaments: list[dict[str, Any]],
        courses: list[dict[str, Any]],
        parent=None,
    ) -> None:
        super().__init__(parent)
        self.setWindowTitle("Personal scorecard")
        self.resize(520, 220)
        layout = QFormLayout(self)

        self._player = QComboBox()
        self._player.setObjectName("personalScorecardPlayer")
        for p in players:
            self._player.addItem(f"{p.get('name', '')} (#{p['id']})", int(p["id"]))
        layout.addRow("Player", self._player)

        self._mode = QComboBox()
        self._mode.setObjectName("personalScorecardMode")
        self._mode.addItem("Started tournament", "tournament")
        self._mode.addItem("Training round", "training")
        self._mode.currentIndexChanged.connect(self._on_mode_changed)
        layout.addRow("Type", self._mode)

        self._tournament = QComboBox()
        self._tournament.setObjectName("personalScorecardTournament")
        for t in started_tournaments:
            tid = int(t["id"])
            name = str(t.get("name") or "")
            play_date = str(t.get("play_date") or "")
            self._tournament.addItem(f"{name} (#{tid}) - {play_date}", tid)
        layout.addRow("Started tournament", self._tournament)

        self._course = QComboBox()
        self._course.setObjectName("personalScorecardCourse")
        for c in courses:
            self._course.addItem(f"{c.get('name', '')} (#{c['id']})", int(c["id"]))
        layout.addRow("Course", self._course)

        self._holes = QComboBox()
        self._holes.setObjectName("personalScorecardHoles")
        self._holes.addItem("9 holes", 9)
        self._holes.addItem("18 holes", 18)
        layout.addRow("Layout", self._holes)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addRow(buttons)

        self._on_mode_changed()

    def _on_mode_changed(self) -> None:
        mode = str(self._mode.currentData())
        tournament_mode = mode == "tournament"
        self._tournament.setEnabled(tournament_mode)
        self._course.setEnabled(not tournament_mode)
        self._holes.setEnabled(not tournament_mode)

    def values(self) -> dict[str, int | str | None]:
        return {
            "player_id": int(self._player.currentData()),
            "mode": str(self._mode.currentData()),
            "tournament_id": (
                int(self._tournament.currentData())
                if self._tournament.currentIndex() >= 0
                else None
            ),
            "course_id": int(self._course.currentData()) if self._course.currentIndex() >= 0 else None,
            "hole_count": int(self._holes.currentData()),
        }


class PersonalScorecardSessionDialog(QDialog):
    """
    One player — map shows tee + green from course data.

    **Training:** optional GPS (map click or coordinates), optional club and distance; shots saved via
    ``POST /shots`` and drawn on the map.

    **Tournament:** gross strokes per hole via ``POST /scorecards/hole``; optional GPS/club/distance
    for the same round (a companion ``Round`` is created for shot storage).
    """

    def __init__(
        self,
        api: GolfApiClient,
        run_async,
        *,
        mode: Literal["training", "tournament"],
        player_id: int,
        player_name: str,
        holes_raw: list[dict[str, Any]],
        round_id: int,
        initial_shots: list[dict[str, Any]] | None = None,
        tournament_name: str = "",
        scorecard: dict[str, Any] | None = None,
        parent=None,
    ) -> None:
        super().__init__(parent)
        self._api = api
        self._run_async = run_async
        self._mode = mode
        self._player_id = player_id
        self._player_name = player_name
        self._holes_raw = sorted(holes_raw, key=_hole_number)
        self._hole_views = [_hole_dict_to_view(h) for h in self._holes_raw]
        self._round_id = round_id
        self._tournament_name = tournament_name
        self._scorecard = dict(scorecard) if scorecard else {}

        self._shots_by_hole_id: dict[int, list[ShotPoint]] = {}
        for s in initial_shots or []:
            hid = int(s["hole_id"])
            self._shots_by_hole_id.setdefault(hid, []).append(_shot_dict_to_point(s))

        title = (
            f"Personal scorecard — {player_name} (training)"
            if mode == "training"
            else f"Personal scorecard — {player_name} (tournament)"
        )
        self.setWindowTitle(title)
        self.resize(920, 680)

        root = QVBoxLayout(self)
        hint = (
            "One player at a time. Map uses tee/green from course data. "
            "Optional: club and distance for the next shot. "
            "Add GPS by clicking the fairway or by entering course X/Y below. "
            "Shots are drawn in order from the tee."
        )
        if mode == "tournament":
            hint += " Save gross strokes for the tournament scorecard separately."
        root.addWidget(QLabel(hint))

        top = QHBoxLayout()
        self._hole_combo = QComboBox()
        self._hole_combo.setObjectName("personalScorecardHoleSelect")
        for h in self._holes_raw:
            n = _hole_number(h)
            par = int(h.get("par", 0))
            self._hole_combo.addItem(f"Hole {n} (par {par})", int(h["id"]))
        self._hole_combo.currentIndexChanged.connect(self._on_hole_changed)
        top.addWidget(QLabel("Hole"))
        top.addWidget(self._hole_combo, stretch=1)
        root.addLayout(top)

        self._canvas = InteractiveHoleCanvas()
        self._canvas.setObjectName(
            "personalScorecardCanvasTraining"
            if mode == "training"
            else "personalScorecardCanvasTournament"
        )
        self._canvas.shot_clicked.connect(self._on_shot_click)
        root.addWidget(self._canvas, stretch=1)

        form = QFormLayout()
        self._club = QComboBox()
        self._club.setObjectName("personalScorecardClub")
        self._club.setEditable(True)
        for label, value in _CLUB_PRESETS:
            self._club.addItem(label, value)
        form.addRow("Club (next shot, optional)", self._club)

        self._distance = QDoubleSpinBox()
        self._distance.setObjectName("personalScorecardDistance")
        self._distance.setRange(0.0, 500.0)
        self._distance.setDecimals(1)
        self._distance.setSpecialValueText("—")
        self._distance.setValue(0.0)
        form.addRow("Distance m (optional)", self._distance)

        coord_row = QHBoxLayout()
        self._coord_x = QDoubleSpinBox()
        self._coord_x.setRange(0.0, float(_MAX_X))
        self._coord_x.setDecimals(1)
        self._coord_y = QDoubleSpinBox()
        self._coord_y.setRange(float(_MIN_Y), float(_MIN_Y + _SPAN_Y))
        self._coord_y.setDecimals(1)
        self._coord_x.setValue(0.0)
        self._coord_y.setValue(0.0)
        coord_row.addWidget(QLabel("Course X"))
        coord_row.addWidget(self._coord_x)
        coord_row.addWidget(QLabel("Y"))
        coord_row.addWidget(self._coord_y)
        add_coord_btn = QPushButton("Add shot at coordinates")
        add_coord_btn.setObjectName("personalScorecardAddCoordShot")
        add_coord_btn.clicked.connect(self._on_add_coord_shot)
        coord_row.addWidget(add_coord_btn)
        form.addRow("GPS (optional)", coord_row)

        clear_btn = QPushButton("Clear shots on this hole")
        clear_btn.setObjectName("personalScorecardClearHoleShots")
        clear_btn.clicked.connect(self._on_clear_hole_shots)
        form.addRow(clear_btn)

        if mode == "tournament":
            self._strokes = QSpinBox()
            self._strokes.setObjectName("personalScorecardStrokes")
            self._strokes.setRange(1, 40)
            self._strokes.setValue(4)
            form.addRow("Strokes (gross)", self._strokes)
            save_btn = QPushButton("Save strokes for this hole")
            save_btn.setObjectName("personalScorecardSaveTournamentHole")
            save_btn.clicked.connect(self._on_save_tournament_hole)
            form.addRow(save_btn)

        root.addLayout(form)

        self._status = QLabel("")
        self._status.setWordWrap(True)
        root.addWidget(self._status)

        close_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        close_box.rejected.connect(self.reject)
        root.addWidget(close_box)

        if self._hole_combo.count() > 0:
            self._hole_combo.setCurrentIndex(0)
        if mode == "tournament":
            self._sync_strokes_spin_from_scorecard()
        self._sync_coord_spin_defaults()
        self._refresh_canvas()

    def _club_for_next_shot(self) -> str:
        text = self._club.currentText().strip()
        if not text or text.startswith("—"):
            return ""
        return text

    def _current_hole_raw(self) -> dict[str, Any]:
        idx = self._hole_combo.currentIndex()
        return self._holes_raw[idx]

    def _current_hole_view(self) -> HoleView:
        idx = self._hole_combo.currentIndex()
        return self._hole_views[idx]

    def _on_hole_changed(self) -> None:
        self._sync_coord_spin_defaults()
        self._refresh_canvas()
        if self._mode == "tournament":
            self._sync_strokes_spin_from_scorecard()

    def _sync_coord_spin_defaults(self) -> None:
        """Mid-fairway defaults for optional manual GPS entry."""
        hv = self._current_hole_view()
        self._coord_x.setValue(round((hv.tee_x + hv.green_x) / 2.0, 1))
        self._coord_y.setValue(round((hv.tee_y + hv.green_y) / 2.0, 1))

    def _sync_strokes_spin_from_scorecard(self) -> None:
        h = self._current_hole_raw()
        n = _hole_number(h)
        holes = self._scorecard.get("holes") or []
        row = next((x for x in holes if int(x.get("hole_number", -1)) == n), None)
        if row and row.get("strokes") is not None:
            self._strokes.setValue(int(row["strokes"]))
        else:
            self._strokes.setValue(int(h.get("par", 4)))

    def _shots_for_canvas(self, hole_id: int) -> list[ShotPoint]:
        pts = list(self._shots_by_hole_id.get(hole_id, []))
        return sorted(pts, key=lambda sp: sp.shot_at)

    def _refresh_canvas(self) -> None:
        hv = self._current_hole_view()
        hid = int(hv.id)
        shots = self._shots_for_canvas(hid)
        self._canvas.set_hole_and_shots(hv, shots)
        if self._mode == "training":
            self._status.setText(
                f"Hole {hv.number}: {len(shots)} shot(s) on map. Click the map or use coordinates."
            )
        else:
            self._status.setText(
                f"Hole {hv.number} (par {hv.par}). "
                f"{len(shots)} optional GPS shot(s). Save strokes for the tournament below."
            )

    def _distance_optional(self) -> float | None:
        if self._distance.value() > 0:
            return float(self._distance.value())
        return None

    def _on_shot_click(self, cx: float, cy: float) -> None:
        self._submit_shot_at(cx, cy)

    def _on_add_coord_shot(self) -> None:
        cx = float(self._coord_x.value())
        cy = float(self._coord_y.value())
        self._submit_shot_at(cx, cy)

    def _submit_shot_at(self, cx: float, cy: float) -> None:
        async def _go() -> None:
            hole = self._current_hole_raw()
            hole_id = int(hole["id"])
            try:
                body = await self._api.create_shot(
                    round_id=self._round_id,
                    hole_id=hole_id,
                    x=cx,
                    y=cy,
                    club=self._club_for_next_shot(),
                    distance=self._distance_optional(),
                )
            except GolfApiError as e:
                QMessageBox.warning(self, "Shot", str(e))
                return
            pt = _shot_dict_to_point(body)
            self._shots_by_hole_id.setdefault(hole_id, []).append(pt)
            self._refresh_canvas()

        self._run_async(_go())

    def _on_clear_hole_shots(self) -> None:
        async def _go() -> None:
            hole_id = int(self._current_hole_raw()["id"])
            shots = list(self._shots_by_hole_id.get(hole_id, []))
            for s in shots:
                try:
                    await self._api.delete_shot(s.id)
                except GolfApiError as e:
                    QMessageBox.warning(self, "Shot", str(e))
                    return
            self._shots_by_hole_id[hole_id] = []
            self._refresh_canvas()

        self._run_async(_go())

    def _on_save_tournament_hole(self) -> None:
        if self._mode != "tournament":
            return

        async def _go() -> None:
            sc_id = int(self._scorecard["id"])
            h = self._current_hole_raw()
            n = _hole_number(h)
            strokes = int(self._strokes.value())
            try:
                updated = await self._api.post_scorecard_hole(
                    scorecard_id=sc_id,
                    hole_number=n,
                    strokes=strokes,
                    player_id=self._player_id,
                )
            except GolfApiError as e:
                QMessageBox.warning(self, "Scorecard", str(e))
                return
            self._scorecard = updated
            self._status.setText(f"Saved hole {n}: {strokes} gross strokes (tournament).")
            self._refresh_canvas()

        self._run_async(_go())
