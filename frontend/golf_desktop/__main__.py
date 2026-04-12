"""Application entry: Qt event loop + asyncio via qasync."""

from __future__ import annotations

import asyncio
import os
import sys

import qasync
from PySide6.QtWidgets import QApplication

from golf_desktop.api_client import GolfApiClient
from golf_desktop.ui import MainWindow


def main() -> None:
    qapp = QApplication(sys.argv)
    loop = qasync.QEventLoop(qapp)
    asyncio.set_event_loop(loop)

    stop = asyncio.Event()
    qapp.aboutToQuit.connect(stop.set)

    async def _run() -> None:
        api_base = os.environ.get("API_BASE_URL", "http://localhost:8000")
        api = GolfApiClient(api_base)
        win = MainWindow(api)
        win.show()
        # X11 over TCP/Docker: window may open behind other apps or on the XQuartz desktop.
        win.raise_()
        win.activateWindow()
        await stop.wait()
        await api.aclose()

    task = asyncio.ensure_future(_run())

    def _raise(fut):
        exc = fut.exception()
        if exc:
            loop.stop()
            raise exc

    task.add_done_callback(_raise)

    with loop:
        loop.run_forever()


if __name__ == "__main__":
    main()
