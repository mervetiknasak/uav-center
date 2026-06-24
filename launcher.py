#!/usr/bin/env python3
"""Start the UAV Center development environment on Windows, macOS, or Linux."""

from __future__ import annotations

import argparse
import os
import shutil
import signal
import socket
import subprocess
import sys
import time
from pathlib import Path
from typing import Optional


ROOT_DIR = Path(__file__).resolve().parent
BACKEND_DIR = ROOT_DIR / "backend"
FRONTEND_DIR = ROOT_DIR / "frontend"
VENV_DIR = BACKEND_DIR / ".venv"
REQUIRED_PYTHON = (3, 11)


def is_windows() -> bool:
    return os.name == "nt"


def venv_python() -> Path:
    if is_windows():
        return VENV_DIR / "Scripts" / "python.exe"
    return VENV_DIR / "bin" / "python"


def npm_bin() -> str:
    return "npm.cmd" if is_windows() else "npm"


def python_version_text(version: tuple[int, int]) -> str:
    return ".".join(str(part) for part in version)


def command_python_version(command: list[str]) -> Optional[tuple[int, int]]:
    try:
        output = subprocess.check_output(
            [*command, "-c", "import sys; print(f'{sys.version_info[0]}.{sys.version_info[1]}')"],
            cwd=ROOT_DIR,
            env=child_env(),
            text=True,
            stderr=subprocess.DEVNULL,
        ).strip()
    except (OSError, subprocess.CalledProcessError):
        return None

    try:
        major, minor = output.split(".", 1)
        return int(major), int(minor)
    except ValueError:
        return None


def find_backend_python() -> list[str]:
    if sys.version_info[:2] == REQUIRED_PYTHON:
        return [sys.executable]

    candidates: list[list[str]] = []
    if is_windows():
        candidates.append(["py", f"-{python_version_text(REQUIRED_PYTHON)}"])

    executable = shutil.which(f"python{python_version_text(REQUIRED_PYTHON)}")
    if executable:
        candidates.append([executable])

    for candidate in candidates:
        if command_python_version(candidate) == REQUIRED_PYTHON:
            return candidate

    required = python_version_text(REQUIRED_PYTHON)
    raise SystemExit(f"Python {required} bulunamadı. Backend sanal ortamı için Python {required} kurulu ve PATH içinde olmalı.")


def run_step(label: str, command: list[str], cwd: Path) -> None:
    print(f"\n==> {label}", flush=True)
    print(f"    {format_command(command)}", flush=True)
    subprocess.run(command, cwd=cwd, check=True, env=child_env())


def format_command(command: list[str]) -> str:
    return " ".join(command)


def require_command(command: str, install_hint: str) -> None:
    if shutil.which(command) is None:
        raise SystemExit(f"'{command}' bulunamadı. {install_hint}")


def child_env() -> dict[str, str]:
    env = os.environ.copy()
    env.setdefault("PYTHONUNBUFFERED", "1")
    env.setdefault("PIP_CACHE_DIR", str(ROOT_DIR / ".cache" / "pip"))
    env.setdefault("PIP_DISABLE_PIP_VERSION_CHECK", "1")
    return env


def ensure_port_available(host: str, port: int, service_name: str) -> None:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        try:
            sock.bind((host, port))
        except OSError:
            raise SystemExit(f"{service_name} portu kullanımda: {host}:{port}") from None


def ensure_backend(skip_install: bool) -> None:
    python_path = venv_python()
    if not python_path.exists():
        if skip_install:
            raise SystemExit("Backend sanal ortamı eksik: backend/.venv")
        run_step("Backend sanal ortamı oluşturuluyor", [*find_backend_python(), "-m", "venv", str(VENV_DIR)], ROOT_DIR)
    elif command_python_version([str(python_path)]) != REQUIRED_PYTHON:
        required = python_version_text(REQUIRED_PYTHON)
        raise SystemExit(f"Backend sanal ortamı Python {required} olmalı. Lütfen backend/.venv'i Python {required} ile yeniden oluşturun.")

    if not skip_install:
        run_step(
            "Backend bağımlılıkları kontrol ediliyor",
            [str(python_path), "-m", "pip", "install", "-r", "requirements.txt"],
            BACKEND_DIR,
        )

    run_step("Backend paket tutarlılığı kontrol ediliyor", [str(python_path), "-m", "pip", "check"], BACKEND_DIR)
    run_step("Django migration'ları uygulanıyor", [str(python_path), "manage.py", "migrate"], BACKEND_DIR)


def frontend_dependencies_current() -> bool:
    node_modules = FRONTEND_DIR / "node_modules"
    package_json = FRONTEND_DIR / "package.json"
    package_lock = FRONTEND_DIR / "package-lock.json"

    if not node_modules.exists():
        return False

    dependency_stamp = node_modules.stat().st_mtime
    package_stamp = package_json.stat().st_mtime
    lock_stamp = package_lock.stat().st_mtime if package_lock.exists() else 0
    return dependency_stamp >= max(package_stamp, lock_stamp)


def ensure_frontend(skip_install: bool) -> None:
    require_command("node", "Node.js kurulu ve PATH içinde olmalı.")
    require_command("npm", "npm kurulu ve PATH içinde olmalı.")

    if skip_install:
        if not (FRONTEND_DIR / "node_modules").exists():
            raise SystemExit("Frontend bağımlılıkları eksik: frontend/node_modules")
        return

    if frontend_dependencies_current():
        print("\n==> Frontend bağımlılıkları güncel görünüyor")
        return

    install_command = [npm_bin(), "ci"] if (FRONTEND_DIR / "package-lock.json").exists() else [npm_bin(), "install"]
    run_step("Frontend bağımlılıkları kuruluyor", install_command, FRONTEND_DIR)


def popen(command: list[str], cwd: Path) -> subprocess.Popen:
    creationflags = subprocess.CREATE_NEW_PROCESS_GROUP if is_windows() else 0
    return subprocess.Popen(command, cwd=cwd, creationflags=creationflags, env=child_env())


def stop_process(process: subprocess.Popen) -> None:
    if process.poll() is not None:
        return

    if is_windows():
        process.send_signal(signal.CTRL_BREAK_EVENT)
    else:
        process.terminate()


def wait_for_processes(processes: list[tuple[str, subprocess.Popen]]) -> int:
    try:
        while True:
            for name, process in processes:
                exit_code = process.poll()
                if exit_code is not None:
                    print(f"\n{name} durdu. Çıkış kodu: {exit_code}")
                    return exit_code
            time.sleep(0.5)
    except KeyboardInterrupt:
        print("\nKapatılıyor...")
        return 130
    finally:
        for _, process in processes:
            stop_process(process)
        for _, process in processes:
            try:
                process.wait(timeout=8)
            except subprocess.TimeoutExpired:
                process.kill()


def start_backend(port: int, reload: bool) -> subprocess.Popen:
    python_path = venv_python()
    command = [str(python_path), "manage.py", "runserver", f"127.0.0.1:{port}"]
    if not reload:
        command.append("--noreload")
    return popen(command, BACKEND_DIR)


def start_frontend(host: str, port: int) -> subprocess.Popen:
    return popen([npm_bin(), "run", "dev", "--", "--host", host, "--port", str(port), "--strictPort"], FRONTEND_DIR)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="UAV Center geliştirme ortamını başlatır.")
    parser.add_argument("--skip-install", action="store_true", help="Bağımlılık kurulum adımlarını atla.")
    parser.add_argument("--backend-only", action="store_true", help="Sadece Django backend'i başlat.")
    parser.add_argument("--frontend-only", action="store_true", help="Sadece Vite frontend'i başlat.")
    parser.add_argument("--backend-port", type=int, default=8000, help="Django portu. Varsayılan: 8000")
    parser.add_argument("--frontend-host", default="127.0.0.1", help="Vite host'u. Varsayılan: 127.0.0.1")
    parser.add_argument("--frontend-port", type=int, default=5173, help="Vite portu. Varsayılan: 5173")
    parser.add_argument("--reload", action="store_true", help="Django auto-reload izleyicisini etkinleştir.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()

    if args.backend_only and args.frontend_only:
        raise SystemExit("--backend-only ve --frontend-only birlikte kullanılamaz.")

    start_backend_service = not args.frontend_only
    start_frontend_service = not args.backend_only

    if start_backend_service:
        ensure_backend(args.skip_install)
    if start_frontend_service:
        ensure_frontend(args.skip_install)

    if start_backend_service:
        ensure_port_available("127.0.0.1", args.backend_port, "Backend")
    if start_frontend_service:
        ensure_port_available(args.frontend_host, args.frontend_port, "Frontend")

    processes: list[tuple[str, subprocess.Popen]] = []

    if start_backend_service:
        processes.append(("Backend", start_backend(args.backend_port, args.reload)))
    if start_frontend_service:
        processes.append(("Frontend", start_frontend(args.frontend_host, args.frontend_port)))

    print("\nOrtam ayakta.")
    if start_backend_service:
        print(f"Backend:  http://127.0.0.1:{args.backend_port}")
    if start_frontend_service:
        print(f"Frontend: http://localhost:{args.frontend_port}")
    print("Durdurmak için Ctrl+C.")

    return wait_for_processes(processes)


if __name__ == "__main__":
    raise SystemExit(main())
