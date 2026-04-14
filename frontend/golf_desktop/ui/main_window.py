from __future__ import annotations

import logging
from datetime import datetime
from typing import Any

log = logging.getLogger(__name__)

from PySide6.QtCore import QDate, Qt, QTimer
from PySide6.QtGui import QAction
from PySide6.QtWidgets import (
    QComboBox,
    QDateEdit,
    QDoubleSpinBox,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from golf_desktop.api_client import GolfApiClient, GolfApiError
from golf_desktop.domain.models import HoleView, RoundSummary, ShotPoint
from golf_desktop.log_setup import LOG_DIR, flush_log_handlers, get_latest_log_path
from golf_desktop.ui.api_json_dialog import ApiJsonDialog, LogFileViewerDialog
from golf_desktop.ui.course_canvas import CourseCanvas


class TournamentCreateDialog(QDialog):
    """Form: name, play date, course — POST /api/v1/tournaments."""

    def __init__(self, courses: list[dict[str, Any]], parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Create tournament")
        self.resize(420, 160)
        layout = QFormLayout(self)
        self._name = QLineEdit()
        self._name.setPlaceholderText("Tournament name")
        self._name.setObjectName("tournamentCreateName")
        self._date = QDateEdit()
        self._date.setCalendarPopup(True)
        self._date.setDisplayFormat("yyyy-MM-dd")
        self._date.setDate(QDate.currentDate())
        self._date.setObjectName("tournamentCreateDate")
        self._course = QComboBox()
        self._course.setObjectName("tournamentCreateCourse")
        for c in courses:
            self._course.addItem(f"{c['name']} (#{c['id']})", c["id"])
        layout.addRow("Name", self._name)
        layout.addRow("Play date", self._date)
        layout.addRow("Course", self._course)
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addRow(buttons)

    def values(self) -> tuple[str, str, int]:
        return (
            self._name.text().strip(),
            self._date.date().toString("yyyy-MM-dd"),
            int(self._course.currentData()),
        )


class TournamentPickerDialog(QDialog):
    """Choose a tournament from API rows (id, name, play_date, status, …)."""

    def __init__(
        self,
        title: str,
        rows: list[dict[str, Any]],
        *,
        field_label: str = "Tournament",
        parent=None,
    ) -> None:
        super().__init__(parent)
        self.setWindowTitle(title)
        self.resize(480, 120)
        layout = QFormLayout(self)
        self._combo = QComboBox()
        self._combo.setObjectName("tournamentPickerCombo")
        for row in rows:
            tid = int(row["id"])
            name = str(row.get("name", ""))
            play_date = str(row.get("play_date", ""))
            st = row.get("status")
            text = f"{name} (#{tid}) — {play_date}"
            if st:
                text += f" [{st}]"
            self._combo.addItem(text, tid)
        layout.addRow(field_label, self._combo)
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addRow(buttons)

    def selected_id(self) -> int:
        return int(self._combo.currentData())


class PlayerProfileDialog(QDialog):
    """Create/edit a full player profile."""

    def __init__(self, title: str, *, initial: dict[str, Any] | None = None, parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle(title)
        self.resize(440, 320)
        layout = QFormLayout(self)
        initial = initial or {}

        self._name = QLineEdit()
        self._name.setObjectName("playerProfileName")
        self._name.setPlaceholderText("Player name")
        self._name.setText(str(initial.get("name") or ""))
        layout.addRow("Name", self._name)

        self._handicap = QDoubleSpinBox()
        self._handicap.setObjectName("playerProfileHandicap")
        self._handicap.setRange(0.0, 54.0)
        self._handicap.setDecimals(1)
        self._handicap.setSingleStep(0.1)
        self._handicap.setSpecialValueText("Not set")
        self._handicap.setValue(float(initial.get("handicap") or 0.0))
        layout.addRow("Handicap", self._handicap)

        self._age = QSpinBox()
        self._age.setObjectName("playerProfileAge")
        self._age.setRange(0, 120)
        self._age.setSpecialValueText("Not set")
        self._age.setValue(int(initial.get("age") or 0))
        layout.addRow("Age", self._age)

        self._gender = QLineEdit()
        self._gender.setObjectName("playerProfileGender")
        self._gender.setPlaceholderText("e.g. male, female, non-binary")
        self._gender.setText(str(initial.get("gender") or ""))
        layout.addRow("Gender", self._gender)

        self._email = QLineEdit()
        self._email.setObjectName("playerProfileEmail")
        self._email.setPlaceholderText("name@example.com")
        self._email.setText(str(initial.get("email") or ""))
        layout.addRow("Email", self._email)

        self._sponsor = QLineEdit()
        self._sponsor.setObjectName("playerProfileSponsor")
        self._sponsor.setPlaceholderText("Sponsor")
        self._sponsor.setText(str(initial.get("sponsor") or ""))
        layout.addRow("Sponsor", self._sponsor)

        self._phone = QLineEdit()
        self._phone.setObjectName("playerProfilePhone")
        self._phone.setPlaceholderText("+46...")
        self._phone.setText(str(initial.get("phone") or ""))
        layout.addRow("Phone", self._phone)

        self._country = QLineEdit()
        self._country.setObjectName("playerProfileCountry")
        self._country.setPlaceholderText("Country")
        self._country.setText(str(initial.get("country") or ""))
        layout.addRow("Country", self._country)

        self._club = QLineEdit()
        self._club.setObjectName("playerProfileClub")
        self._club.setPlaceholderText("Golf club")
        self._club.setText(str(initial.get("club") or ""))
        layout.addRow("Club", self._club)

        self._rank = QSpinBox()
        self._rank.setObjectName("playerProfileRank")
        self._rank.setRange(0, 9999)
        self._rank.setSpecialValueText("Not set")
        self._rank.setValue(int(initial.get("rank") or 0))
        layout.addRow("Rank", self._rank)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addRow(buttons)

    def payload(self) -> dict[str, Any]:
        return {
            "name": self._name.text().strip(),
            "handicap": None if self._handicap.value() == 0.0 else float(self._handicap.value()),
            "age": None if self._age.value() == 0 else int(self._age.value()),
            "gender": _clean_text(self._gender.text()),
            "email": _clean_text(self._email.text()),
            "sponsor": _clean_text(self._sponsor.text()),
            "phone": _clean_text(self._phone.text()),
            "country": _clean_text(self._country.text()),
            "club": _clean_text(self._club.text()),
            "rank": None if self._rank.value() == 0 else int(self._rank.value()),
        }

class PlayerManageDialog(QDialog):
    """Select a player and choose Edit/Delete."""

    def __init__(self, rows: list[dict[str, Any]], parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Manage players")
        self.resize(520, 160)
        layout = QFormLayout(self)

        self._rows = rows
        self._combo = QComboBox()
        self._combo.setObjectName("playerManageCombo")
        for row in rows:
            pid = int(row["id"])
            name = str(row.get("name", ""))
            self._combo.addItem(f"{name} (#{pid})", pid)
        self._combo.currentIndexChanged.connect(self._on_selection_changed)
        layout.addRow("Player", self._combo)

        buttons_row = QHBoxLayout()
        self._btn_update = QPushButton("Edit")
        self._btn_update.setObjectName("playerManageUpdate")
        self._btn_update.clicked.connect(self._mark_update)
        self._btn_delete = QPushButton("Delete")
        self._btn_delete.setObjectName("playerManageDelete")
        self._btn_delete.clicked.connect(self._mark_delete)
        self._btn_cancel = QPushButton("Cancel")
        self._btn_cancel.setObjectName("playerManageCancel")
        self._btn_cancel.clicked.connect(self.reject)
        buttons_row.addWidget(self._btn_update)
        buttons_row.addWidget(self._btn_delete)
        buttons_row.addStretch(1)
        buttons_row.addWidget(self._btn_cancel)
        layout.addRow(buttons_row)

        self._action: str | None = None
        self._on_selection_changed()

    def _on_selection_changed(self) -> None:
        return

    def _mark_update(self) -> None:
        self._action = "update"
        self.accept()

    def _mark_delete(self) -> None:
        self._action = "delete"
        self.accept()

    def selection(self) -> tuple[str, int]:
        action = self._action or "update"
        player_id = int(self._combo.currentData())
        return action, player_id


def _clean_text(v: str) -> str | None:
    s = v.strip()
    return s or None


class MainWindow(QMainWindow):
    def __init__(self, api: GolfApiClient, parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Golf Desktop")
        self._api = api
        self._rounds: list[RoundSummary] = []
        self._holes: list[HoleView] = []

        self._build_browse_menus()

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

        self._log_viewer: LogFileViewerDialog | None = None

        self._schedule_refresh()
        log.info("MainWindow ready")

    def _build_browse_menus(self) -> None:
        """Top menu bar: one dropdown per API resource (browse JSON from the server)."""
        bar = self.menuBar()
        # In-window menu: on macOS the default is the screen menu bar (easy to miss); Docker/X11 is clearer too.
        bar.setNativeMenuBar(False)
        entries: list[tuple[str, str, str]] = [
            ("Players", "&Players", "list"),
            ("Courses", "&Courses", "list"),
            ("Holes", "&Holes", "list"),
            ("Matches", "&Matches", "info"),
            ("Rounds", "&Rounds", "list"),
            ("Shots", "&Shots", "list"),
        ]
        handlers = {
            "Players": self._browse_players,
            "Courses": self._browse_courses,
            "Holes": self._browse_holes,
            "Matches": self._browse_matches_info,
            "Rounds": self._browse_rounds,
            "Shots": self._browse_shots,
        }
        for key, menu_title, kind in entries:
            menu = bar.addMenu(menu_title)
            if kind == "info":
                act = QAction("About this API…", self)
                act.triggered.connect(handlers[key])
            else:
                act = QAction("List from API…", self)
                act.triggered.connect(handlers[key])
            menu.addAction(act)
            if key == "Players":
                act_add_player = QAction("Add…", self)
                act_add_player.setObjectName("menuPlayersAdd")
                act_add_player.triggered.connect(self._player_add)
                menu.addAction(act_add_player)
                act_manage_player = QAction("Manage…", self)
                act_manage_player.setObjectName("menuPlayersManage")
                act_manage_player.triggered.connect(self._player_manage)
                menu.addAction(act_manage_player)

        tournaments_menu = bar.addMenu("&Tournaments")
        act_t_create = QAction("Create…", self)
        act_t_create.setObjectName("menuTournamentsCreate")
        act_t_create.triggered.connect(self._tournament_create)
        tournaments_menu.addAction(act_t_create)
        act_t_list = QAction("List all…", self)
        act_t_list.setObjectName("menuTournamentsListAll")
        act_t_list.triggered.connect(self._tournament_list_all)
        tournaments_menu.addAction(act_t_list)
        act_t_start = QAction("Start…", self)
        act_t_start.setObjectName("menuTournamentsStart")
        act_t_start.triggered.connect(self._tournament_start)
        tournaments_menu.addAction(act_t_start)
        act_t_stop = QAction("Mark finished…", self)
        act_t_stop.setObjectName("menuTournamentsStop")
        act_t_stop.triggered.connect(self._tournament_stop)
        tournaments_menu.addAction(act_t_stop)
        act_t_cards = QAction("Scorecards…", self)
        act_t_cards.setObjectName("menuTournamentsScorecards")
        act_t_cards.triggered.connect(self._tournament_scorecards)
        tournaments_menu.addAction(act_t_cards)

        view_menu = bar.addMenu("&View")
        act_log = QAction("Show &log file…", self)
        act_log.setObjectName("menuViewShowLog")
        act_log.triggered.connect(self._show_log_file)
        view_menu.addAction(act_log)

    def _show_log_file(self) -> None:
        log.info("Menu: View → show log file")
        if self._log_viewer is not None and self._log_viewer.isVisible():
            self._log_viewer.raise_()
            self._log_viewer.activateWindow()
            return

        flush_log_handlers()
        path = get_latest_log_path()
        if path is None:
            QMessageBox.information(
                self,
                "Log file",
                f"No log file found yet.\nLogs are written to:\n{LOG_DIR}/",
            )
            return

        viewer = LogFileViewerDialog(path, self)
        viewer.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose, True)
        viewer.destroyed.connect(self._on_log_viewer_destroyed)
        self._log_viewer = viewer
        viewer.show()

    def _on_log_viewer_destroyed(self) -> None:
        self._log_viewer = None

    def _run_async(self, coro) -> None:
        import asyncio

        async def _wrap():
            try:
                await coro
            except GolfApiError as e:
                log.warning("API error: %s", e)
                QMessageBox.warning(self, "API error", str(e))
            except Exception as e:  # noqa: BLE001
                log.exception("Async UI task failed")
                QMessageBox.warning(self, "API error", str(e))

        asyncio.ensure_future(_wrap())

    def _browse_players(self) -> None:
        log.info("Menu: Players → list from API")
        self._run_async(self._browse_players_async())

    async def _browse_players_async(self) -> None:
        data = await self._api.get_players()
        dlg = ApiJsonDialog("Players", self)
        dlg.set_payload(data)
        dlg.exec()

    def _player_add(self) -> None:
        log.info("Menu: Players → Add")
        self._run_async(self._player_add_async())

    async def _player_add_async(self) -> None:
        dlg = PlayerProfileDialog("Add player", parent=self)
        if dlg.exec() != QDialog.DialogCode.Accepted:
            log.debug("Player add dialog cancelled")
            return
        payload = dlg.payload()
        if not payload["name"]:
            QMessageBox.warning(self, "Players", "Name is required.")
            return
        data = await self._api.create_player(**payload)
        out = ApiJsonDialog("Player created", self)
        out.set_payload(data)
        out.exec()

    def _player_manage(self) -> None:
        log.info("Menu: Players → Manage")
        self._run_async(self._player_manage_async())

    async def _player_manage_async(self) -> None:
        rows = await self._api.get_players()
        if not rows:
            QMessageBox.information(self, "Players", "No players available yet.")
            return
        dlg = PlayerManageDialog(rows, self)
        if dlg.exec() != QDialog.DialogCode.Accepted:
            log.debug("Player manage dialog cancelled")
            return
        action, player_id = dlg.selection()
        if action == "update":
            current = next((row for row in rows if int(row["id"]) == player_id), None)
            if not current:
                QMessageBox.warning(self, "Players", f"Player #{player_id} not found.")
                return
            profile_dlg = PlayerProfileDialog(
                f"Edit player #{player_id}",
                initial=current,
                parent=self,
            )
            if profile_dlg.exec() != QDialog.DialogCode.Accepted:
                return
            payload = profile_dlg.payload()
            if not payload["name"]:
                QMessageBox.warning(self, "Players", "Name is required to update.")
                return
            data = await self._api.update_player(player_id, **payload)
            out = ApiJsonDialog("Player updated", self)
            out.set_payload(data)
            out.exec()
            return

        if action == "delete":
            confirm = QMessageBox.question(
                self,
                "Delete player",
                f"Delete player #{player_id}?\nThis cannot be undone.",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No,
            )
            if confirm != QMessageBox.StandardButton.Yes:
                return
            await self._api.delete_player(player_id)
            QMessageBox.information(self, "Players", f"Player #{player_id} deleted.")

    def _browse_courses(self) -> None:
        log.info("Menu: Courses → list from API")
        self._run_async(self._browse_courses_async())

    async def _browse_courses_async(self) -> None:
        data = await self._api.get_courses()
        dlg = ApiJsonDialog("Courses", self)
        dlg.set_payload(data)
        dlg.exec()

    def _browse_holes(self) -> None:
        log.info("Menu: Holes → list from API")
        self._run_async(self._browse_holes_async())

    async def _browse_holes_async(self) -> None:
        data = await self._api.get_holes()
        dlg = ApiJsonDialog("Holes", self)
        dlg.set_payload(data)
        dlg.exec()

    def _browse_matches_info(self) -> None:
        log.info("Menu: Matches → info dialog")
        QMessageBox.information(
            self,
            "Matches",
            "The API only exposes POST /api/v1/matches to record a match. "
            "There is no GET list endpoint; use Rounds and Shots to inspect recorded play.",
        )

    def _browse_rounds(self) -> None:
        log.info("Menu: Rounds → list from API")
        self._run_async(self._browse_rounds_async())

    async def _browse_rounds_async(self) -> None:
        data = await self._api.get_rounds()
        dlg = ApiJsonDialog("Rounds", self)
        dlg.set_payload(data)
        dlg.exec()

    def _browse_shots(self) -> None:
        log.info("Menu: Shots → list from API")
        self._run_async(self._browse_shots_async())

    async def _browse_shots_async(self) -> None:
        data = await self._api.list_shots()
        dlg = ApiJsonDialog("Shots", self)
        dlg.set_payload(data)
        dlg.exec()

    def _tournament_create(self) -> None:
        log.info("Menu: Tournaments → Create")
        self._run_async(self._tournament_create_async())

    async def _tournament_create_async(self) -> None:
        courses = await self._api.get_courses()
        if not courses:
            QMessageBox.information(
                self,
                "Tournaments",
                "No courses in the API — create or seed courses first.",
            )
            return
        dlg = TournamentCreateDialog(courses, self)
        if dlg.exec() != QDialog.DialogCode.Accepted:
            log.debug("Tournament create dialog cancelled")
            return
        name, play_date, course_id = dlg.values()
        if not name:
            QMessageBox.warning(self, "Tournaments", "Name is required.")
            return
        log.info("Creating tournament name=%r play_date=%s course_id=%s", name, play_date, course_id)
        data = await self._api.create_tournament(
            name=name, play_date=play_date, course_id=course_id
        )
        out = ApiJsonDialog("Tournament created", self)
        out.set_payload(data)
        out.exec()

    def _tournament_list_all(self) -> None:
        log.info("Menu: Tournaments → List all")
        self._run_async(self._tournament_list_all_async())

    async def _tournament_list_all_async(self) -> None:
        data = await self._api.get_tournaments()
        dlg = ApiJsonDialog("Tournaments", self)
        dlg.set_payload(data)
        dlg.exec()

    def _tournament_start(self) -> None:
        log.info("Menu: Tournaments → Start")
        self._run_async(self._tournament_start_async())

    async def _tournament_start_async(self) -> None:
        try:
            rows = await self._api.get_tournament_drafts()
        except GolfApiError as e:
            QMessageBox.warning(self, "Tournaments", str(e))
            return
        except Exception as e:  # noqa: BLE001
            log.exception("Failed to list draft tournaments")
            QMessageBox.warning(self, "Tournaments", str(e))
            return
        if not rows:
            QMessageBox.information(
                self,
                "Start tournament",
                "There are no draft tournaments. Create one first.",
            )
            return
        picker = TournamentPickerDialog(
            "Start tournament",
            rows,
            field_label="Not yet started",
            parent=self,
        )
        if picker.exec() != QDialog.DialogCode.Accepted:
            log.debug("Start tournament dialog cancelled")
            return
        tid = picker.selected_id()
        log.info("Starting tournament id=%s", tid)
        try:
            data = await self._api.start_tournament(tid)
        except GolfApiError as e:
            QMessageBox.warning(self, "Tournaments", str(e))
            return
        except Exception as e:  # noqa: BLE001
            log.exception("Start tournament failed")
            QMessageBox.warning(self, "Tournaments", str(e))
            return
        dlg = ApiJsonDialog("Tournament started", self)
        dlg.set_payload(data)
        dlg.exec()

    def _tournament_stop(self) -> None:
        log.info("Menu: Tournaments → Mark finished")
        self._run_async(self._tournament_stop_async())

    async def _tournament_stop_async(self) -> None:
        try:
            rows = await self._api.get_tournaments_started()
        except GolfApiError as e:
            QMessageBox.warning(self, "Tournaments", str(e))
            return
        except Exception as e:  # noqa: BLE001
            log.exception("Failed to list started tournaments")
            QMessageBox.warning(self, "Tournaments", str(e))
            return
        if not rows:
            QMessageBox.information(
                self,
                "Mark finished",
                'No tournament is in progress (nothing with status "started").',
            )
            return
        picker = TournamentPickerDialog(
            "Mark tournament finished",
            rows,
            field_label="In progress",
            parent=self,
        )
        if picker.exec() != QDialog.DialogCode.Accepted:
            log.debug("Stop tournament dialog cancelled")
            return
        tid = picker.selected_id()
        log.info("Marking tournament finished id=%s", tid)
        try:
            data = await self._api.stop_tournament(tid)
        except GolfApiError as e:
            QMessageBox.warning(self, "Tournaments", str(e))
            return
        except Exception as e:  # noqa: BLE001
            log.exception("Stop tournament failed")
            QMessageBox.warning(self, "Tournaments", str(e))
            return
        dlg = ApiJsonDialog("Tournament finished", self)
        dlg.set_payload(data)
        dlg.exec()

    def _tournament_scorecards(self) -> None:
        log.info("Menu: Tournaments → Scorecards")
        self._run_async(self._tournament_scorecards_async())

    async def _tournament_scorecards_async(self) -> None:
        try:
            rows = await self._api.get_tournaments_non_draft()
        except GolfApiError as e:
            QMessageBox.warning(self, "Tournaments", str(e))
            return
        except Exception as e:  # noqa: BLE001
            log.exception("Failed to list tournaments with scorecards")
            QMessageBox.warning(self, "Tournaments", str(e))
            return
        if not rows:
            QMessageBox.information(
                self,
                "Tournament scorecards",
                "No started or finished tournaments yet — start a draft tournament first.",
            )
            return
        picker = TournamentPickerDialog(
            "Tournament scorecards",
            rows,
            field_label="Started or finished",
            parent=self,
        )
        if picker.exec() != QDialog.DialogCode.Accepted:
            log.debug("Scorecards dialog cancelled")
            return
        tid = picker.selected_id()
        log.info("Fetching scorecards for tournament id=%s", tid)
        try:
            data = await self._api.get_tournament_scorecards(tid)
        except GolfApiError as e:
            QMessageBox.warning(self, "Tournaments", str(e))
            return
        except Exception as e:  # noqa: BLE001
            log.exception("Fetch scorecards failed")
            QMessageBox.warning(self, "Tournaments", str(e))
            return
        dlg = ApiJsonDialog(f"Tournament #{tid} scorecards", self)
        dlg.set_payload(data)
        dlg.exec()

    def _schedule_refresh(self) -> None:
        log.debug("Schedule refresh (rounds/holes/shots)")
        self._timer.start(0)

    async def refresh_async(self) -> None:
        """Public for tests — load rounds and current selection."""
        await self._load_data_async()

    def _load_data(self) -> None:
        import asyncio

        asyncio.ensure_future(self._load_data_async())

    async def _load_data_async(self) -> None:
        log.info("Loading rounds and canvas data")
        try:
            raw_rounds = await self._api.get_rounds()
        except GolfApiError as e:
            log.warning("Failed to load rounds: %s", e)
            QMessageBox.warning(self, "API error", str(e))
            return
        except Exception as e:  # noqa: BLE001
            log.exception("Failed to load rounds")
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
            log.info("No rounds in API — canvas cleared")
            self._canvas.set_hole_and_shots(None, [])
            return

        self._round_combo.setCurrentIndex(0)
        log.info("Loaded %d round(s) into combo", len(self._rounds))
        await self._load_holes_for_current_round()
        await self._load_shots_for_selection()

    def _on_round_changed(self) -> None:
        import asyncio

        log.debug("Round combo changed → reload holes and shots")
        asyncio.ensure_future(self._load_holes_for_current_round())
        asyncio.ensure_future(self._load_shots_for_selection())

    def _on_hole_changed(self) -> None:
        import asyncio

        log.debug("Hole combo changed → reload shots")
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
        log.debug("Loading holes for round_id=%s course_id=%s", rid, course_id)
        try:
            raw = await self._api.get_holes(course_id=course_id)
        except GolfApiError as e:
            log.warning("Failed to load holes: %s", e)
            QMessageBox.warning(self, "API error", str(e))
            return
        except Exception as e:  # noqa: BLE001
            log.exception("Failed to load holes")
            QMessageBox.warning(self, "API error", str(e))
            return

        self._holes = [
            HoleView(
                id=h["id"],
                course_id=h["course_id"],
                number=int(h["hole"] if "hole" in h else h["number"]),
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
        log.debug("Hole combo has %d hole(s)", len(self._holes))

    async def _load_shots_for_selection(self) -> None:
        rid = self._current_round_id()
        hid = self._current_hole_id()
        hole = next((h for h in self._holes if h.id == hid), None) if hid else None
        if rid is None or hid is None:
            self._canvas.set_hole_and_shots(hole, [])
            return
        try:
            raw = await self._api.get_shots_for_round(rid, hole_id=hid)
        except GolfApiError as e:
            log.warning("Failed to load shots: %s", e)
            QMessageBox.warning(self, "API error", str(e))
            return
        except Exception as e:  # noqa: BLE001
            log.exception("Failed to load shots")
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
        log.debug("Canvas: round_id=%s hole_id=%s → %d shot(s)", rid, hid, len(shots))
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
