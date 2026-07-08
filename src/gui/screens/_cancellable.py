"""
Cancellable screen mixin.

Several screens kick off a background worker thread that streams progress
back to the UI with ``self.after(...)``. If the user navigates away while
that thread is still running, the widget is destroyed and every remaining
``after`` call raises (``main thread is not in main loop`` /
``invalid command name``).

Mix this in *before* ``ctk.CTkFrame`` and use ``self._safe_after(...)``
instead of ``self.after(...)`` inside worker threads, checking its return
value to stop early once the screen is gone::

    class MyScreen(CancellableScreenMixin, ctk.CTkFrame):
        def _worker(self):
            for item in items:
                if not self._safe_after(0, self._update, item):
                    return
"""
from __future__ import annotations


class CancellableScreenMixin:
    """Adds cancellation-aware scheduling to a CTk screen."""

    #: Set True once the screen has been navigated away from / destroyed.
    _cancelled: bool = False

    def destroy(self):  # type: ignore[override]
        self._cancelled = True
        super().destroy()

    def _safe_after(self, *args) -> bool:
        """Schedule a UI callback unless the screen is gone.

        Returns True if the callback was scheduled, False if the screen has
        been cancelled/destroyed (so the caller should stop working).
        """
        if self._cancelled:
            return False
        try:
            if not self.winfo_exists():  # type: ignore[attr-defined]
                self._cancelled = True
                return False
            self.after(*args)  # type: ignore[attr-defined]
            return True
        except Exception:
            # Widget torn down between the check and the call.
            self._cancelled = True
            return False
