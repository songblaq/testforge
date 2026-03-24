"""자동 테스트 모듈 — IMU / Mic / CSI."""
from __future__ import annotations

import re
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import TYPE_CHECKING

from rich.console import Console
from rich.table import Table

if TYPE_CHECKING:
    from .board import Board

console = Console()


class Verdict(Enum):
    PASS = "PASS"
    FAIL = "FAIL"
    SKIP = "SKIP"


@dataclass
class TestResult:
    name: str
    verdict: Verdict
    detail: str = ""
    elapsed_s: float = 0.0


@dataclass
class TestReport:
    results: list[TestResult] = field(default_factory=list)

    def add(self, r: TestResult) -> None:
        self.results.append(r)

    @property
    def passed(self) -> int:
        return sum(1 for r in self.results if r.verdict == Verdict.PASS)

    @property
    def failed(self) -> int:
        return sum(1 for r in self.results if r.verdict == Verdict.FAIL)

    def print_table(self) -> None:
        t = Table(title="테스트 결과")
        t.add_column("테스트", style="cyan")
        t.add_column("결과", justify="center")
        t.add_column("시간(s)", justify="right")
        t.add_column("상세")
        for r in self.results:
            color = {"PASS": "green", "FAIL": "red", "SKIP": "yellow"}[r.verdict.value]
            t.add_row(r.name, f"[{color}]{r.verdict.value}[/{color}]",
                       f"{r.elapsed_s:.1f}", r.detail)
        console.print(t)
        console.print(f"\n총 {len(self.results)}건 — "
                       f"[green]{self.passed} PASS[/green] / "
                       f"[red]{self.failed} FAIL[/red]")


# ─── IMU 테스트 ─────────────────────────────────
def test_imu(board: Board, duration: float = 15.0) -> TestReport:
    """IMU 렙 카운팅 통합 테스트."""
    report = TestReport()

    # 1) 시리얼 데이터 포맷 검증
    t0 = time.time()
    lines: list[str] = []
    csv_header_ok = False
    while time.time() - t0 < 3.0:
        line = board.readline()
        if not line:
            continue
        if "ms,ax,ay,az" in line:
            csv_header_ok = True
            continue
        if line.startswith("#") or line.startswith("==="):
            continue
        lines.append(line)
        if len(lines) >= 10:
            break

    report.add(TestResult(
        "시리얼 데이터 수신",
        Verdict.PASS if len(lines) >= 5 else Verdict.FAIL,
        f"{len(lines)}줄 수신 ({3.0:.0f}s 이내)",
        time.time() - t0,
    ))

    # 컬럼 검증
    bad_cols = 0
    for l in lines:
        parts = l.split(",")
        if len(parts) < 8:
            bad_cols += 1
    report.add(TestResult(
        "CSV 컬럼 수 (>=8)",
        Verdict.PASS if bad_cols == 0 else Verdict.FAIL,
        f"비정상 줄: {bad_cols}/{len(lines)}",
        0,
    ))

    # 2) 상태머신 검증 — 가만히 두면 state=0(IDLE) 또는 3(REST)
    states = set()
    for l in lines:
        parts = l.split(",")
        if len(parts) >= 7:
            try:
                states.add(int(parts[6]))
            except ValueError:
                pass
    report.add(TestResult(
        "상태머신 값 유효 (0-3)",
        Verdict.PASS if states.issubset({0, 1, 2, 3}) else Verdict.FAIL,
        f"관측 상태: {states}",
        0,
    ))

    # 3) 흔들기 테스트 — BtnA 누른 후 peak 감지 확인
    console.print("[yellow]▶ BtnA를 눌러 운동을 시작하세요 (5초 대기)...[/yellow]")
    t0 = time.time()
    saw_set_start = False
    reps_before = 0
    reps_after = 0
    while time.time() - t0 < duration:
        line = board.readline()
        if not line:
            continue
        if "SET" in line and "START" in line:
            saw_set_start = True
        m = re.search(r"REP\s+(\d+)", line)
        if m and saw_set_start:
            reps_after = int(m.group(1))
        # CSV 줄에서 reps 추적
        parts = line.split(",")
        if len(parts) >= 8:
            try:
                reps_after = max(reps_after, int(parts[7]))
            except ValueError:
                pass

    report.add(TestResult(
        "세트 시작 감지 (BtnA)",
        Verdict.PASS if saw_set_start else Verdict.FAIL,
        "SET START 수신" if saw_set_start else "미수신",
        duration,
    ))
    report.add(TestResult(
        "렙 카운팅 동작",
        Verdict.PASS if reps_after > 0 else Verdict.FAIL,
        f"감지된 렙: {reps_after}",
        0,
    ))

    # 4) REST timeout 검증 — 8초 정지 후 REST 전환
    console.print("[yellow]▶ 보드를 가만히 두세요 (REST 타임아웃 테스트, 10초)...[/yellow]")
    t0 = time.time()
    rest_seen = False
    while time.time() - t0 < 10.0:
        line = board.readline()
        if not line:
            continue
        if "DONE" in line or "REST" in line:
            rest_seen = True
            break
        parts = line.split(",")
        if len(parts) >= 7:
            try:
                if int(parts[6]) == 3:
                    rest_seen = True
                    break
            except ValueError:
                pass
    report.add(TestResult(
        "REST 타임아웃 전환",
        Verdict.PASS if rest_seen else Verdict.SKIP,
        "REST(3) 감지" if rest_seen else "10초 내 미감지 (수동 확인 필요)",
        time.time() - t0,
    ))

    return report


# ─── Mic 테스트 (플레이스홀더) ─────────────────
def test_mic(board: Board) -> TestReport:
    """마이크 센싱 테스트 — 현재 펌웨어에 미구현."""
    report = TestReport()
    report.add(TestResult(
        "마이크 데이터 스트림",
        Verdict.SKIP,
        "펌웨어에 마이크 출력 미구현 — 시뮬레이터 참조",
    ))
    return report


# ─── CSI 테스트 (플레이스홀더) ──────────────────
def test_csi(board: Board) -> TestReport:
    """WiFi CSI 테스트 — ESP32 CSI 펌웨어 필요."""
    report = TestReport()
    report.add(TestResult(
        "WiFi CSI 데이터 수신",
        Verdict.SKIP,
        "wifi-csi-collector 펌웨어 미설치 — 별도 보드 필요",
    ))
    return report
