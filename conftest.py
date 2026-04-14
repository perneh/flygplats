"""Root pytest hooks: CLI options available for any test path (backend-only or full suite)."""


def pytest_addoption(parser) -> None:
    parser.addoption(
        "--xdotool",
        action="store",
        choices=("auto", "off", "require"),
        default="auto",
        help=(
            "xdotool GUI E2E (frontend test_02_*): "
            "auto=skip if DISPLAY/xdotool missing; "
            "off=always skip those tests; "
            "require=fail collection if xdotool tests are selected but environment is incomplete."
        ),
    )
