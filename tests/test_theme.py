"""Testovi za Fluent 2 temu (QSS + Segoe UI + Mica best-effort)."""

import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from mujofix.platform import windows
from mujofix.ui import theme
from PySide6.QtWidgets import QPushButton, QWidget


class TestTokens(unittest.TestCase):
    def tearDown(self):
        os.environ.pop("MUJOFIX_THEME", None)

    def test_qss_uses_segoe_ui_and_is_fluent(self):
        css = theme.qss(False)
        self.assertIn("Segoe UI", css)
        self.assertIn("border-radius", css)
        self.assertIn("QPushButton#primary", css)

    def test_light_and_dark_differ(self):
        self.assertNotEqual(theme.qss(False), theme.qss(True))
        self.assertIn("#f3f3f3", theme.qss(False))   # Fluent base light
        self.assertIn("#202020", theme.qss(True))    # Fluent base dark

    def test_mica_makes_root_transparent(self):
        self.assertIn("background: transparent", theme.qss(True, mica=True))
        self.assertNotIn("QWidget#root { background: transparent",
                         theme.qss(True, mica=False))

    def test_is_dark_env_override_beats_platform(self):
        os.environ["MUJOFIX_THEME"] = "dark"
        self.assertTrue(theme.is_dark())
        os.environ["MUJOFIX_THEME"] = "light"
        self.assertFalse(theme.is_dark())

    def test_accent_color_is_hex(self):
        for dark in (False, True):
            value = theme.accent_color(dark)
            self.assertEqual(len(value), 7)
            self.assertTrue(value.startswith("#"))
            int(value[1:], 16)  # mora biti validan hex


class TestMicaDegrades(unittest.TestCase):
    def test_not_windows_returns_false(self):
        if windows.is_windows():  # pragma: no cover - test host je Linux
            self.skipTest("ovaj test je za ne-Windows")
        self.assertFalse(theme.apply_mica(object()))
        self.assertFalse(theme._is_win11())

    def test_win11_without_dwmapi_returns_false_not_crash(self):
        """Simuliraj Windows bez dwmapi (npr. stariji build): ne smije puci."""
        from unittest.mock import patch

        class FakeWindow:
            def winId(self):
                return 1

        with patch.object(windows, "is_windows", return_value=True), \
             patch.object(windows, "version", return_value=(10, 0, 22621)):
            self.assertFalse(theme.apply_mica(FakeWindow()))  # ctypes nema
            self.assertTrue(theme._is_win11())

    def test_win10_is_not_mica_capable(self):
        from unittest.mock import patch

        with patch.object(windows, "version", return_value=(10, 0, 19045)):
            self.assertFalse(theme._is_win11())


class TestWindowTheme(unittest.TestCase):
    """QSS mora stvarno da pogodi widgete (objectName) i da se primijeni bez greske."""

    @classmethod
    def setUpClass(cls):
        from PySide6.QtWidgets import QApplication

        cls.app = QApplication.instance() or QApplication([])

    def _window(self):
        import tempfile

        from mujofix.ui.main_window import MainWindow

        return MainWindow(scan_fn=lambda: [], quarantine_dir=tempfile.mkdtemp(),
                          lang="bs", ai_build_fn=lambda *a, **k: None)

    def test_object_names_and_stylesheet_apply(self):
        window = self._window()
        try:
            wanted = {"root", "subtitle", "h1", "report", "log", "findings"}
            found = {w.objectName() for w in window.findChildren(QWidget)}
            self.assertTrue(wanted <= found, wanted - found)
            names = {w.objectName() for w in
                     window.findChildren(QPushButton)}
            self.assertIn("primary", names)
            theme.apply(self.app, dark=False)
            self.assertIn("Segoe UI", self.app.styleSheet())
            theme.apply(self.app, dark=True)
            self.assertIn("#202020", self.app.styleSheet())
        finally:
            window.close()
            self.app.setStyleSheet("")


if __name__ == "__main__":
    unittest.main()
