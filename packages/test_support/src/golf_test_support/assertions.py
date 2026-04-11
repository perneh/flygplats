"""Reusable assertions for HTTP responses, domain shots, and Qt widgets."""

from __future__ import annotations

from typing import Any, Mapping


def assert_status_ok(response: Any, expected: int = 200) -> None:
    """Assert an httpx or Starlette response has the expected status code."""
    code = getattr(response, "status_code", None)
    if code is None:
        raise AssertionError("response has no status_code")
    assert code == expected, f"expected status {expected}, got {code}: {getattr(response, 'text', '')}"


def assert_shot_equals(
    actual: Mapping[str, Any] | Any,
    expected: Mapping[str, Any],
    *,
    float_tol: float = 1e-5,
) -> None:
    """Compare shot-like dicts or objects (x, y, club, distance, hole_id, round_id)."""
    keys = ("x", "y", "club", "distance", "hole_id", "round_id")

    def get_val(obj: Mapping[str, Any] | Any, key: str) -> Any:
        if isinstance(obj, Mapping):
            return obj.get(key)
        return getattr(obj, key, None)

    for key in keys:
        if key not in expected:
            continue
        av = get_val(actual, key)
        ev = expected[key]
        if key in ("x", "y", "distance") and av is not None and ev is not None:
            assert float(av) == float(ev) or abs(float(av) - float(ev)) < float_tol, (
                f"{key}: expected {ev}, got {av}"
            )
        else:
            assert av == ev, f"{key}: expected {ev!r}, got {av!r}"


def assert_ui_element_exists(widget: Any, name: str) -> Any:
    """Find a QWidget by QObject.objectName() on self or a descendant (PySide6/PyQt6)."""
    from PySide6.QtWidgets import QWidget

    if hasattr(widget, "objectName") and widget.objectName() == name:
        return widget
    found = widget.findChild(QWidget, name)
    assert found is not None, f"no QWidget with objectName={name!r} on self or under {widget!r}"
    return found
