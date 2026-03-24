"""웹 시뮬레이터 서버 + WebSocket 브릿지."""
from __future__ import annotations

import asyncio
import http.server
import json
import os
import threading
from functools import partial
from pathlib import Path
from typing import TYPE_CHECKING

from rich.console import Console

if TYPE_CHECKING:
    from .board import Board

console = Console()

SIMULATOR_DIR = Path(__file__).resolve().parent.parent.parent / "simulator"
DEFAULT_HTTP_PORT = 8888
DEFAULT_WS_PORT = 8889


def serve_simulator(port: int = DEFAULT_HTTP_PORT) -> None:
    """시뮬레이터 HTML 정적 서버."""
    if not SIMULATOR_DIR.exists():
        console.print(f"[red]시뮬레이터 디렉토리 없음: {SIMULATOR_DIR}[/red]")
        return
    handler = partial(http.server.SimpleHTTPRequestHandler,
                      directory=str(SIMULATOR_DIR))
    with http.server.HTTPServer(("0.0.0.0", port), handler) as srv:
        console.print(f"[green]시뮬레이터 서버 시작: http://localhost:{port}/rep-counter-simulator.html[/green]")
        try:
            srv.serve_forever()
        except KeyboardInterrupt:
            console.print("\n서버 종료")


async def ws_bridge(board: "Board", host: str = "0.0.0.0",
                    port: int = DEFAULT_WS_PORT) -> None:
    """보드 시리얼 → WebSocket 브릿지 (비동기)."""
    import websockets  # lazy import

    clients: set = set()

    async def handler(ws):
        clients.add(ws)
        console.print(f"[cyan]WebSocket 클라이언트 연결 ({len(clients)}명)[/cyan]")
        try:
            async for _ in ws:
                pass  # 클라이언트→서버 메시지 무시
        finally:
            clients.discard(ws)

    async def broadcaster():
        loop = asyncio.get_event_loop()
        while True:
            line = await loop.run_in_executor(None, board.readline)
            if line and clients:
                msg = json.dumps({"type": "serial", "data": line})
                await asyncio.gather(
                    *(c.send(msg) for c in clients.copy()),
                    return_exceptions=True,
                )
            elif not line:
                await asyncio.sleep(0.005)

    async with websockets.serve(handler, host, port):
        console.print(f"[green]WebSocket 브릿지: ws://localhost:{port}[/green]")
        await broadcaster()


def run_ws_bridge(board: "Board", port: int = DEFAULT_WS_PORT) -> None:
    """동기 래퍼."""
    asyncio.run(ws_bridge(board, port=port))
