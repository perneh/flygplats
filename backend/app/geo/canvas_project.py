"""Project WGS84 lat/lng into the rough 2D range expected by the desktop canvas (see ``course_canvas.py``)."""


def bounds_from_latlng_pairs(pairs: list[tuple[float, float]]) -> tuple[float, float, float, float]:
    """Return (min_lat, max_lat, min_lng, max_lng)."""
    lats = [p[0] for p in pairs]
    lngs = [p[1] for p in pairs]
    return min(lats), max(lats), min(lngs), max(lngs)


def project_latlng_to_canvas(
    lat: float,
    lng: float,
    bounds: tuple[float, float, float, float],
) -> tuple[float, float]:
    """
    Map (lat, lng) into x in [0, 250], y roughly in [-60, 140] for a course bounding box.
    """
    min_lat, max_lat, min_lng, max_lng = bounds
    lat_span = max(max_lat - min_lat, 1e-9)
    lng_span = max(max_lng - min_lng, 1e-9)
    x = (lng - min_lng) / lng_span * 250.0
    y = (lat - min_lat) / lat_span * 200.0 - 60.0
    return x, y
