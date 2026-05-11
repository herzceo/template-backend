from typing import TypedDict

from backend.domain.enums import DeviceType, IpType


class ClientDeviceInfo(TypedDict, total=False):
    timezone: str
    screen_width: int
    pixel_ratio: float
    webgl_vendor: str
    webgl_renderer: str
    hardware_concurrency: int
    device_memory: float
    languages: list[str]


class ServerDeviceInfo(TypedDict, total=False):
    asn_org: str
    ip_type: IpType
    device_type: DeviceType
    os_name: str
    browser_name: str


__all__ = ("ClientDeviceInfo", "ServerDeviceInfo")
