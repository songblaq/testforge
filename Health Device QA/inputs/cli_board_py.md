# Source: cli_board.py

```
"""보드 감지 및 시리얼 연결 관리."""
from __future__ import annotations

import glob
import sys
import time
from dataclasses import dataclass, field
from typing import Generator

import serial
from rich.console import Console

console = Console()

KNOWN_PATTERNS = [
    "/dev/cu.wchusbserial*",   # CH340 (macOS)
    "/dev/cu.usbserial*",      # 일반 USB-Serial (macOS)
    "/dev/ttyUSB*",            # Linux
    "/dev/ttyACM*",            # Linux CDC-ACM
    "COM*",                    # Windows
]
BAUD = 115200


@dataclass
class Board:
    """연결된 보드 상태."""
    port: str
    ser: serial.Serial | None = field(default=None, repr=False)
    firmware_ver: str = "unknown"

    # --- 연결 ---
    def open(self, timeout: float = 2.0) -> None:
        self.ser = serial.Serial(self.port, BAUD, timeout=timeout)
        time.sleep(0.3)  # 보드 리셋 대기
        self._detect_firmware()

    def close(self) -> None:
        if self.ser and self.ser.is_open:
            self.ser.close()
            self.ser = None

    @property
    def is_open(self) -> bool:
        return self.ser is not None and self.ser.is_open

    # --- 읽기 ---
    def readline(self) -> str | None:
        if not self.is_open:
            return None
        try:
            raw = self.ser.readline()
            if raw:
                return raw.decode("utf-8", errors="replace").strip()
        except serial.SerialException:
            return None
        return None

    def stream(self) -> Generator[str, None, None]:
        """줄 단위 무한 스트림 제너레이터."""
        while self.is_open:
            line = self.readline()
            if line is not None:
                yield line

    # --- 내부 ---
    def _detect_firmware(self) -> None:
        """처음 몇 줄에서 버전 문자열 파싱."""
        deadline = time.time() + 3.0
        while time.time() < deadline:
            line = self.readline()
            if line and "Rep Counter" in line:
                # === IMU Rep Counter v0.7 ===
                parts = line.split("v")
                if len(parts) >= 2:
                    self.firmware_ver = "v" + parts[-1].strip().rstrip("=").strip()
                return
        self.firmware_ver = "unknown"


def detect_ports() -> list[str]:
    """시스템에서 USB-시리얼 포트 자동 감지."""
    found: list[str] = []
    for pat in KNOWN_PATTERNS:
        found.extend(glob.glob(pat))
    return sorted(set(found))


def auto_connect() -> Board | None:
    """첫 번째 감지 포트에 자동 연결. 실패 시 None."""
    ports = detect_ports()
    if not ports:
        return None
    for p in ports:
        try:
            b = Board(port=p)
            b.open()
            return b
        except (serial.SerialException, OSError):
            continue
    return None
```
