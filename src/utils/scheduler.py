"""Simple scheduler to run agent tasks on an interval.

This is intentionally minimal: it runs functions at fixed intervals in a
background thread and writes reports to disk. For production use consider
APScheduler or system services.
"""
from __future__ import annotations

import threading
import time
from typing import Callable


class SimpleScheduler:
    def __init__(self):
        self._jobs: list[tuple[Callable, int]] = []
        self._stop = False

    def add_job(self, func: Callable, interval_seconds: int) -> None:
        self._jobs.append((func, interval_seconds))

    def start(self):
        def _runner():
            last_run = [0.0] * len(self._jobs)
            while not self._stop:
                now = time.time()
                for i, (f, interval) in enumerate(self._jobs):
                    if now - last_run[i] >= interval:
                        try:
                            f()
                        except Exception:
                            pass
                        last_run[i] = now
                time.sleep(1)

        t = threading.Thread(target=_runner, daemon=True)
        t.start()

    def stop(self):
        self._stop = True
