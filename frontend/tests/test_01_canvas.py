"""GUI smoke tests (pytest-qt, offscreen)."""

from datetime import datetime, timezone

from golf_test_support import assert_ui_element_exists

from golf_desktop.domain.models import HoleView, ShotPoint
from golf_desktop.ui.course_canvas import CourseCanvas


def test_course_canvas_renders_shots(qtbot):
    canvas = CourseCanvas()
    qtbot.addWidget(canvas)
    hole = HoleView(
        id=1,
        course_id=1,
        number=1,
        par=4,
        tee_x=0.0,
        tee_y=0.0,
        green_x=200.0,
        green_y=0.0,
    )
    t = datetime.now(timezone.utc)
    shots = [
        ShotPoint(
            id=1,
            round_id=1,
            hole_id=1,
            x=20.0,
            y=0.0,
            club="D",
            distance=100.0,
            shot_at=t,
        ),
        ShotPoint(
            id=2,
            round_id=1,
            hole_id=1,
            x=100.0,
            y=5.0,
            club="I",
            distance=90.0,
            shot_at=t,
        ),
    ]
    canvas.set_hole_and_shots(hole, shots)
    canvas.show()
    qtbot.waitExposed(canvas)
    assert_ui_element_exists(canvas, "courseCanvas")
