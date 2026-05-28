import os
import unittest
from unittest.mock import patch

from fastapi.testclient import TestClient

from app import main as app_main


class ShareInfoTests(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app_main.app)
        self._saved_origin = os.environ.pop("PUBLIC_SHARE_ORIGIN", None)

    def tearDown(self):
        if self._saved_origin is not None:
            os.environ["PUBLIC_SHARE_ORIGIN"] = self._saved_origin

    def test_modes_present_with_tailscale_available(self):
        with patch.object(
            app_main, "_tailscale_status",
            return_value={"ip": "100.64.1.2", "status": "available"},
        ):
            res = self.client.get("/share-info")
        self.assertEqual(res.status_code, 200)
        body = res.json()
        self.assertEqual(body["default_mode"], "local")
        self.assertFalse(body["configured_override"])
        self.assertTrue(body["modes"]["local"]["available"])
        self.assertTrue(body["modes"]["tailscale"]["available"])
        self.assertEqual(
            body["modes"]["tailscale"]["share_origin"], "http://100.64.1.2:3001",
        )
        # Legacy field tracks Local, not Tailscale, regardless of availability.
        self.assertEqual(
            body["share_origin"], body["modes"]["local"]["share_origin"],
        )

    def test_local_mode_stays_localhost_from_tailscale_host(self):
        with patch.object(
            app_main, "_tailscale_status",
            return_value={"ip": "100.64.1.2", "status": "available"},
        ):
            body = self.client.get(
                "/share-info",
                headers={"host": "100.64.1.2:8001"},
            ).json()
        self.assertEqual(body["modes"]["local"]["share_origin"], "http://localhost:3001")
        self.assertEqual(body["modes"]["tailscale"]["share_origin"], "http://100.64.1.2:3001")

    def test_tailscale_not_installed_marks_mode_unavailable(self):
        with patch.object(
            app_main, "_tailscale_status",
            return_value={"ip": None, "status": "not_installed"},
        ):
            res = self.client.get("/share-info")
        body = res.json()
        self.assertFalse(body["modes"]["tailscale"]["available"])
        self.assertEqual(body["modes"]["tailscale"]["status"], "not_installed")
        self.assertIsNone(body["modes"]["tailscale"]["share_origin"])
        self.assertIn("tailscale.com", body["modes"]["tailscale"]["install_url"])
        # Legacy share_origin tracks the new default mode (local) so old
        # clients do not silently get a Tailscale URL.
        self.assertEqual(
            body["share_origin"], body["modes"]["local"]["share_origin"],
        )

    def test_tailscale_not_running_distinct_from_not_installed(self):
        with patch.object(
            app_main, "_tailscale_status",
            return_value={"ip": None, "status": "not_running"},
        ):
            body = self.client.get("/share-info").json()
        self.assertEqual(body["modes"]["tailscale"]["status"], "not_running")
        self.assertFalse(body["modes"]["tailscale"]["available"])

    def test_public_share_origin_override_collapses_both_modes(self):
        os.environ["PUBLIC_SHARE_ORIGIN"] = "https://share.example.com/"
        try:
            body = self.client.get("/share-info").json()
        finally:
            del os.environ["PUBLIC_SHARE_ORIGIN"]
        self.assertTrue(body["configured_override"])
        self.assertEqual(
            body["modes"]["local"]["share_origin"], "https://share.example.com",
        )
        self.assertEqual(
            body["modes"]["tailscale"]["share_origin"], "https://share.example.com",
        )
        self.assertTrue(body["modes"]["tailscale"]["available"])
        self.assertEqual(body["share_origin"], "https://share.example.com")


class TailscaleStatusTests(unittest.TestCase):
    def test_returns_not_installed_when_binary_missing(self):
        with patch.object(
            app_main.subprocess, "run", side_effect=FileNotFoundError,
        ), patch.object(
            app_main, "_scan_ifconfig_for_tailnet_ip", return_value=None,
        ), patch.object(
            app_main, "_scan_hostname_for_tailnet_ip", return_value=None,
        ):
            status = app_main._tailscale_status()
        self.assertEqual(status, {"ip": None, "status": "not_installed"})

    def test_returns_not_running_when_command_fails(self):
        class _FailedProc:
            returncode = 1
            stdout = ""

        with patch.object(
            app_main.subprocess, "run", return_value=_FailedProc(),
        ), patch.object(
            app_main, "_scan_ifconfig_for_tailnet_ip", return_value=None,
        ), patch.object(
            app_main, "_scan_hostname_for_tailnet_ip", return_value=None,
        ):
            status = app_main._tailscale_status()
        self.assertEqual(status, {"ip": None, "status": "not_running"})

    def test_returns_available_when_ip_present(self):
        class _OkProc:
            returncode = 0
            stdout = "100.64.42.3\n"

        with patch.object(app_main.subprocess, "run", return_value=_OkProc()):
            status = app_main._tailscale_status()
        self.assertEqual(status, {"ip": "100.64.42.3", "status": "available"})

    def test_returns_no_tailnet_ip_when_command_returns_unrelated_ip(self):
        class _OkProc:
            returncode = 0
            stdout = "192.168.1.50\n"

        with patch.object(
            app_main.subprocess, "run", return_value=_OkProc(),
        ), patch.object(
            app_main, "_scan_ifconfig_for_tailnet_ip", return_value=None,
        ), patch.object(
            app_main, "_scan_hostname_for_tailnet_ip", return_value=None,
        ):
            status = app_main._tailscale_status()
        self.assertEqual(status, {"ip": None, "status": "no_tailnet_ip"})


if __name__ == "__main__":
    unittest.main()
