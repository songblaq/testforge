"""health-device CLI 진입점."""
from __future__ import annotations

import sys
import time

import click
from rich.console import Console
from rich.live import Live
from rich.text import Text

console = Console()


@click.group()
@click.version_option(package_name="health-device")
def cli():
    """운동기기 프로젝트 CLI — 보드 연결·테스트·시뮬레이터."""
    pass


# ─── connect ────────────────────────────────────
@cli.command()
@click.option("-p", "--port", default=None, help="시리얼 포트 (자동 감지 생략)")
def connect(port: str | None):
    """보드 자동 감지 + 연결 확인."""
    from .board import Board, auto_connect, detect_ports

    if port:
        console.print(f"지정 포트: {port}")
        b = Board(port=port)
        try:
            b.open()
        except Exception as e:
            console.print(f"[red]연결 실패: {e}[/red]")
            raise SystemExit(1)
    else:
        console.print("USB-시리얼 포트 탐색 중...")
        ports = detect_ports()
        if not ports:
            console.print("[red]감지된 포트 없음. USB 케이블을 확인하세요.[/red]")
            raise SystemExit(1)
        console.print(f"감지 포트: {ports}")
        b = auto_connect()
        if not b:
            console.print("[red]자동 연결 실패[/red]")
            raise SystemExit(1)

    console.print(f"[green]✓ 연결 성공: {b.port}[/green]")
    console.print(f"  펌웨어: {b.firmware_ver}")
    # 샘플 5줄 출력
    for i, line in enumerate(b.stream()):
        console.print(f"  [{i}] {line}")
        if i >= 4:
            break
    b.close()


# ─── stream ─────────────────────────────────────
@cli.command()
@click.option("-p", "--port", default=None)
@click.option("--websocket", is_flag=True, help="WebSocket 브릿지 모드")
@click.option("--ws-port", default=8889, type=int)
@click.option("--csv", "csv_file", default=None, type=click.Path(), help="CSV 파일로 저장")
def stream(port: str | None, websocket: bool, ws_port: int, csv_file: str | None):
    """시리얼 데이터 실시간 스트리밍."""
    from .board import Board, auto_connect

    b = _get_board(port)
    if websocket:
        from .simulator import run_ws_bridge
        console.print(f"[cyan]WebSocket 브릿지 모드 (ws://localhost:{ws_port})[/cyan]")
        run_ws_bridge(b, port=ws_port)
        return

    fh = open(csv_file, "w") if csv_file else None
    try:
        if fh:
            console.print(f"[cyan]CSV 저장: {csv_file}[/cyan]")
        console.print("[dim]Ctrl+C로 종료[/dim]")
        for line in b.stream():
            console.print(line)
            if fh:
                fh.write(line + "\n")
    except KeyboardInterrupt:
        console.print("\n스트리밍 종료")
    finally:
        if fh:
            fh.close()
        b.close()


# ─── test ───────────────────────────────────────
@cli.group()
def test():
    """하드웨어 자동 테스트."""
    pass


@test.command("imu")
@click.option("-p", "--port", default=None)
@click.option("-d", "--duration", default=15.0, type=float, help="렙 테스트 대기 시간(초)")
def test_imu_cmd(port: str | None, duration: float):
    """IMU 렙카운팅 테스트."""
    from .testing import test_imu
    b = _get_board(port)
    console.print("[bold cyan]═══ IMU 렙카운팅 테스트 ═══[/bold cyan]")
    report = test_imu(b, duration=duration)
    report.print_table()
    b.close()
    raise SystemExit(0 if report.failed == 0 else 1)


@test.command("mic")
@click.option("-p", "--port", default=None)
def test_mic_cmd(port: str | None):
    """마이크 센싱 테스트."""
    from .testing import test_mic
    b = _get_board(port)
    console.print("[bold cyan]═══ 마이크 센싱 테스트 ═══[/bold cyan]")
    report = test_mic(b)
    report.print_table()
    b.close()


@test.command("csi")
@click.option("-p", "--port", default=None)
def test_csi_cmd(port: str | None):
    """WiFi CSI 테스트."""
    from .testing import test_csi
    b = _get_board(port)
    console.print("[bold cyan]═══ WiFi CSI 테스트 ═══[/bold cyan]")
    report = test_csi(b)
    report.print_table()
    b.close()


# ─── flash ──────────────────────────────────────
@cli.group()
def flash():
    """펌웨어 빌드 + 업로드 (PlatformIO)."""
    pass


@flash.command("imu")
def flash_imu():
    """IMU 펌웨어 빌드+업로드."""
    from .flash import flash as do_flash
    raise SystemExit(do_flash("imu"))


@flash.command("csi")
def flash_csi():
    """CSI 펌웨어 빌드+업로드."""
    from .flash import flash as do_flash
    raise SystemExit(do_flash("csi"))


# ─── simulate ───────────────────────────────────
@cli.command()
@click.option("--port", "http_port", default=8888, type=int, help="HTTP 포트")
def simulate(http_port: int):
    """웹 시뮬레이터 서버 시작."""
    from .simulator import serve_simulator
    serve_simulator(port=http_port)


# ─── report ─────────────────────────────────────
@cli.command()
@click.option("-o", "--output", default="output/report.html", help="리포트 출력 경로")
def report(output: str):
    """TestForge 리포트 생성."""
    import subprocess
    console.print("[cyan]TestForge 리포트 생성 중...[/cyan]")
    result = subprocess.run(
        ["python", "-m", "testforge", "report", "Health Device QA", "-o", output],
        capture_output=True, text=True,
    )
    if result.returncode == 0:
        console.print(f"[green]✓ 리포트 생성: {output}[/green]")
    else:
        console.print(f"[red]TestForge 리포트 실패:[/red]\n{result.stderr}")
    raise SystemExit(result.returncode)


# ─── 헬퍼 ──────────────────────────────────────
def _get_board(port: str | None):
    from .board import Board, auto_connect
    if port:
        b = Board(port=port)
        try:
            b.open()
        except Exception as e:
            console.print(f"[red]연결 실패: {e}[/red]")
            raise SystemExit(1)
        return b
    b = auto_connect()
    if not b:
        console.print("[red]보드 미감지. --port 옵션을 사용하세요.[/red]")
        raise SystemExit(1)
    console.print(f"[green]✓ 자동 연결: {b.port} (FW {b.firmware_ver})[/green]")
    return b


if __name__ == "__main__":
    cli()
