"""Optional USB device collector using Windows WMI when available."""

from __future__ import annotations

from typing import Any

from backend.collectors.base import BaseCollector, make_event


class USBCollector(BaseCollector):
    """Emits usb_connected / usb_disconnected from a WMI PnP inventory diff."""

    name = "usb"
    supported_platforms = ("Windows",)

    def __init__(self, ingest_callback, enabled: bool = True):
        super().__init__(ingest_callback, enabled)
        self.poll_interval = 10
        self._previous: dict[str, str] = {}
        self._primed = False
        self._wmi = None
        if not self.is_platform_supported():
            self.mark_unavailable(f"USB WMI collection requires Windows, found {self.current_platform()}")
            return
        try:
            import win32com.client  # type: ignore
        except ImportError:
            self.mark_unavailable("pywin32 unavailable; USB collector disabled")
            return
        try:
            locator = win32com.client.Dispatch("WbemScripting.SWbemLocator")
            self._wmi = locator.ConnectServer(".", "root\\cimv2")
        except Exception as exc:
            self.mark_unavailable(f"WMI provider unavailable: {exc}")

    def _inventory(self) -> dict[str, str]:
        query = (
            "SELECT DeviceID, Name, Description, PNPDeviceID "
            "FROM Win32_PnPEntity WHERE PNPDeviceID LIKE 'USB%'"
        )
        devices: dict[str, str] = {}
        for item in self._wmi.ExecQuery(query):
            device_id = str(getattr(item, "PNPDeviceID", None) or getattr(item, "DeviceID", "") or "")
            if not device_id:
                continue
            name = str(getattr(item, "Name", None) or getattr(item, "Description", None) or device_id)
            devices[device_id] = name
        return devices

    async def collect(self) -> list[dict[str, Any]]:
        if not self._wmi:
            return []
        try:
            current = self._inventory()
        except Exception as exc:
            self.logger.warning("USB WMI query failed: %s", exc)
            return []

        if not self._primed:
            self._previous = current
            self._primed = True
            return []

        events: list[dict[str, Any]] = []
        previous_ids = set(self._previous)
        current_ids = set(current)

        for device_id in current_ids - previous_ids:
            name = current[device_id]
            events.append(
                make_event(
                    "usb_connected",
                    self.name,
                    action="usb_connected",
                    target=name,
                    severity="INFO",
                    metadata={"device_id": device_id, "name": name},
                )
            )

        for device_id in previous_ids - current_ids:
            name = self._previous.get(device_id, device_id)
            events.append(
                make_event(
                    "usb_disconnected",
                    self.name,
                    action="usb_disconnected",
                    target=name,
                    severity="INFO",
                    metadata={"device_id": device_id, "name": name},
                )
            )

        self._previous = current
        return events
