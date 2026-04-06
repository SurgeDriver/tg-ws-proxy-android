from __future__ import annotations
import json
import logging
import sys
import threading
import time
import asyncio as _asyncio
from pathlib import Path
from typing import Dict, Optional

import proxy.tg_ws_proxy as tg_ws_proxy

APP_NAME = "TgWsProxy"
APP_DIR = Path.home() / APP_NAME
CONFIG_FILE = APP_DIR / "config.json"

DEFAULT_CONFIG = {
    "port": 1080,
    "host": "127.0.0.1",
    "dc_ip": ["2:149.154.167.220", "4:149.154.167.220"],
    "verbose": False,
}

_RESTART_DELAY = 5
_RESTART_MAX   = 10

_proxy_thread: Optional[threading.Thread] = None
_async_stop: Optional[object] = None
_config: dict = {}

log = logging.getLogger("tg-ws-android")


def _ensure_dirs():
    APP_DIR.mkdir(parents=True, exist_ok=True)


def _validate_config(data: dict) -> list[str]:
    errors = []
    port = data.get("port")
    if not isinstance(port, int) or not (1 <= port <= 65535):
        errors.append(f"'port' must be an integer 1-65535, got {port!r}")
    host = data.get("host")
    if not isinstance(host, str) or not host:
        errors.append(f"'host' must be a non-empty string, got {host!r}")
    dc_ip = data.get("dc_ip")
    if not isinstance(dc_ip, list) or len(dc_ip) == 0:
        errors.append("'dc_ip' must be a non-empty list")
    else:
        for entry in dc_ip:
            if not isinstance(entry, str) or ":" not in entry:
                errors.append(f"Invalid dc_ip entry {entry!r}, expected 'DC:IP'")
    return errors


def load_config() -> dict:
    _ensure_dirs()
    if CONFIG_FILE.exists():
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
            for k, v in DEFAULT_CONFIG.items():
                data.setdefault(k, v)
            errs = _validate_config(data)
            if errs:
                for e in errs:
                    log.warning("Config error: %s", e)
                log.warning("Falling back to defaults due to %d error(s)", len(errs))
                return dict(DEFAULT_CONFIG)
            return data
        except json.JSONDecodeError as exc:
            log.warning("Config not valid JSON: %s - using defaults", exc)
        except Exception as exc:
            log.warning("Failed to load config: %s - using defaults", exc)
    return dict(DEFAULT_CONFIG)


def setup_logging(verbose: bool = False):
    root = logging.getLogger()
    root.setLevel(logging.DEBUG if verbose else logging.INFO)
    ch = logging.StreamHandler(sys.stdout)
    ch.setLevel(logging.DEBUG if verbose else logging.INFO)
    ch.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(message)s", datefmt="%H:%M:%S"))
    root.addHandler(ch)


def _run_proxy_thread(port: int, dc_opt: Dict[int, str], verbose: bool, host: str = "127.0.0.1"):
    global _async_stop
    loop = _asyncio.new_event_loop()
    _asyncio.set_event_loop(loop)
    stop_ev = _asyncio.Event()
    _async_stop = (loop, stop_ev)
    try:
        loop.run_until_complete(tg_ws_proxy._run(port, dc_opt, stop_event=stop_ev, host=host))
    except Exception as exc:
        log.error("Proxy thread crashed: %s", exc)
    finally:
        loop.close()
        _async_stop = None


def start_proxy():
    global _proxy_thread, _config
    if _proxy_thread and _proxy_thread.is_alive():
        log.info("Proxy already running")
        return

    cfg = _config
    port = cfg.get("port", DEFAULT_CONFIG["port"])
    host = cfg.get("host", DEFAULT_CONFIG["host"])
    dc_ip_list = cfg.get("dc_ip", DEFAULT_CONFIG["dc_ip"])
    verbose = cfg.get("verbose", False)

    try:
        dc_opt = tg_ws_proxy.parse_dc_ip_list(dc_ip_list)
    except ValueError as e:
        log.error("Bad config dc_ip: %s", e)
        return

    _proxy_thread = threading.Thread(
        target=_run_proxy_thread,
        args=(port, dc_opt, verbose, host),
        daemon=True,
        name="proxy",
    )
    _proxy_thread.start()


def _watchdog(port: int, dc_opt: Dict[int, str], verbose: bool, host: str):
    global _proxy_thread
    consecutive_crashes = 0
    while True:
        time.sleep(2)
        if _proxy_thread is None or not _proxy_thread.is_alive():
            if consecutive_crashes >= _RESTART_MAX:
                log.error("Proxy crashed %d times — giving up.", consecutive_crashes)
                break
            consecutive_crashes += 1
            log.warning("Proxy died (crash #%d), restarting in %ds...",
                        consecutive_crashes, _RESTART_DELAY)
            time.sleep(_RESTART_DELAY)
            _proxy_thread = threading.Thread(
                target=_run_proxy_thread,
                args=(port, dc_opt, verbose, host),
                daemon=True,
                name="proxy",
            )
            _proxy_thread.start()
            log.info("Proxy restarted (attempt #%d)", consecutive_crashes)
        else:
            consecutive_crashes = 0


def main():
    global _config
    _config = load_config()
    setup_logging(_config.get("verbose", False))

    port = _config.get("port", DEFAULT_CONFIG["port"])
    host = _config.get("host", DEFAULT_CONFIG["host"])
    dc_ip_list = _config.get("dc_ip", DEFAULT_CONFIG["dc_ip"])
    verbose = _config.get("verbose", False)

    try:
        dc_opt = tg_ws_proxy.parse_dc_ip_list(dc_ip_list)
    except ValueError as e:
        log.error("Bad dc_ip in config: %s", e)
        import sys; sys.exit(1)

    start_proxy()

    watchdog_thread = threading.Thread(
        target=_watchdog,
        args=(port, dc_opt, verbose, host),
        daemon=True,
        name="watchdog",
    )
    watchdog_thread.start()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nStopped.")


if __name__ == "__main__":
    main()
