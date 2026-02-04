"""
Portable Docker Daemon Manager
Manages a self-contained Docker daemon running from USB drive
"""

import os
import subprocess
import time
import platform
from pathlib import Path

class PortableDockerManager:
    """Manages portable Docker daemon lifecycle."""

    def __init__(self, usb_root: str):
        """
        Initialize portable Docker manager.

        Args:
            usb_root: Root directory of USB drive (e.g., "L:" or "/media/usb")
        """
        self.usb_root = Path(usb_root)
        self.docker_root = self.usb_root / "docker-runtime"
        self.docker_bin = self.docker_root / "bin"
        self.docker_sock = self.docker_root / "docker.sock"
        self.docker_pid = self.docker_root / "docker.pid"
        self.docker_log = self.docker_root / "docker.log"
        self.docker_data = self.docker_root / "data"

        self.is_portable = self._check_portable_available()
        self.is_running = False
        self.pid = None

    def _check_portable_available(self) -> bool:
        """Check if portable Docker binaries are available."""
        if platform.system() == "Windows":
            # Windows doesn't support portable dockerd easily
            return False

        dockerd_path = self.docker_bin / "dockerd"
        return dockerd_path.exists() and os.access(dockerd_path, os.X_OK)

    def is_daemon_running(self) -> bool:
        """Check if portable daemon is currently running."""
        if not self.docker_pid.exists():
            return False

        try:
            with open(self.docker_pid, 'r') as f:
                pid = int(f.read().strip())

            # Check if process is alive
            os.kill(pid, 0)
            self.pid = pid
            self.is_running = True
            return True
        except (ValueError, ProcessLookupError, FileNotFoundError):
            # Stale PID file
            if self.docker_pid.exists():
                self.docker_pid.unlink()
            return False

    def start_daemon(self, timeout: int = 30) -> tuple[bool, str]:
        """
        Start the portable Docker daemon.

        Args:
            timeout: Maximum seconds to wait for daemon to start

        Returns:
            tuple: (success: bool, message: str)
        """
        if platform.system() == "Windows":
            return False, "Portable Docker daemon not supported on Windows (use Docker Desktop)"

        if not self.is_portable:
            return False, f"Portable Docker binaries not found. Run setup-portable-daemon.sh first."

        if self.is_daemon_running():
            return True, f"Daemon already running (PID: {self.pid})"

        # Create necessary directories
        self.docker_data.mkdir(parents=True, exist_ok=True)
        (self.docker_root / "run").mkdir(exist_ok=True)
        (self.docker_root / "tmp").mkdir(exist_ok=True)

        # Start dockerd in background
        dockerd = self.docker_bin / "dockerd"
        cmd = [
            str(dockerd),
            f"--data-root={self.docker_data}",
            f"--host=unix://{self.docker_sock}",
            f"--pidfile={self.docker_pid}",
            f"--exec-root={self.docker_root / 'run'}",
            "--storage-driver=overlay2",
            "--userland-proxy=false",
            "--iptables=false",
            "--ip-forward=false",
            "--log-level=error"
        ]

        try:
            # Start daemon in background
            with open(self.docker_log, 'w') as log:
                process = subprocess.Popen(
                    cmd,
                    stdout=log,
                    stderr=subprocess.STDOUT,
                    start_new_session=True  # Detach from parent
                )

            # Wait for socket to appear
            start_time = time.time()
            while time.time() - start_time < timeout:
                if self.docker_sock.exists():
                    # Test connection
                    docker_client = self.docker_bin / "docker"
                    test_cmd = [str(docker_client), "info"]
                    env = os.environ.copy()
                    env['DOCKER_HOST'] = f"unix://{self.docker_sock}"

                    try:
                        subprocess.run(
                            test_cmd,
                            env=env,
                            capture_output=True,
                            timeout=5,
                            check=True
                        )
                        # Success!
                        self.is_running = True
                        with open(self.docker_pid, 'r') as f:
                            self.pid = int(f.read().strip())
                        return True, f"Portable Docker daemon started (PID: {self.pid})"
                    except (subprocess.CalledProcessError, subprocess.TimeoutExpired):
                        pass

                time.sleep(0.5)

            # Timeout
            return False, f"Daemon failed to start within {timeout}s. Check log: {self.docker_log}"

        except Exception as e:
            return False, f"Failed to start daemon: {e}"

    def stop_daemon(self, timeout: int = 10) -> tuple[bool, str]:
        """
        Stop the portable Docker daemon.

        Args:
            timeout: Maximum seconds to wait for graceful shutdown

        Returns:
            tuple: (success: bool, message: str)
        """
        if not self.is_daemon_running():
            return True, "Daemon not running"

        try:
            # Stop containers first
            if self.docker_sock.exists():
                docker_client = self.docker_bin / "docker"
                env = os.environ.copy()
                env['DOCKER_HOST'] = f"unix://{self.docker_sock}"

                # Get running containers
                ps_cmd = [str(docker_client), "ps", "-q"]
                result = subprocess.run(ps_cmd, env=env, capture_output=True, text=True)
                container_ids = result.stdout.strip().split('\n')

                if container_ids and container_ids[0]:
                    # Stop containers
                    stop_cmd = [str(docker_client), "stop"] + container_ids
                    subprocess.run(stop_cmd, env=env, timeout=timeout)

            # Send TERM signal to daemon
            os.kill(self.pid, 15)  # SIGTERM

            # Wait for graceful shutdown
            start_time = time.time()
            while time.time() - start_time < timeout:
                try:
                    os.kill(self.pid, 0)
                    time.sleep(0.5)
                except ProcessLookupError:
                    break

            # Force kill if still running
            try:
                os.kill(self.pid, 0)
                os.kill(self.pid, 9)  # SIGKILL
                time.sleep(0.5)
            except ProcessLookupError:
                pass

            # Cleanup
            if self.docker_pid.exists():
                self.docker_pid.unlink()
            if self.docker_sock.exists():
                self.docker_sock.unlink()

            self.is_running = False
            self.pid = None
            return True, "Daemon stopped successfully"

        except Exception as e:
            return False, f"Failed to stop daemon: {e}"

    def get_docker_env(self) -> dict:
        """
        Get environment variables to use portable Docker.

        Returns:
            dict: Environment variables (DOCKER_HOST, PATH)
        """
        if not self.is_running:
            return {}

        env = os.environ.copy()
        env['DOCKER_HOST'] = f"unix://{self.docker_sock}"

        # Add bin to PATH
        if 'PATH' in env:
            env['PATH'] = f"{self.docker_bin}:{env['PATH']}"
        else:
            env['PATH'] = str(self.docker_bin)

        return env

    def get_status(self) -> dict:
        """
        Get current status of portable Docker.

        Returns:
            dict: Status information
        """
        return {
            'available': self.is_portable,
            'running': self.is_running,
            'pid': self.pid,
            'socket': str(self.docker_sock) if self.docker_sock.exists() else None,
            'data_root': str(self.docker_data),
            'log': str(self.docker_log)
        }
