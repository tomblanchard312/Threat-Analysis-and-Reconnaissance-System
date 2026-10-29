"""Shell-free tool arguments and cancellable native, WSL and Docker processes."""

import os
import queue
import re
import shlex
import signal
import subprocess
import threading
import time


def tool_arguments(command, args):
    if not isinstance(command, str) or not re.fullmatch(r"[a-zA-Z][a-zA-Z0-9_.-]{1,}", command):
        raise ValueError("Expected one tool name, without paths or shell syntax")
    if not isinstance(args, str) or "\x00" in args:
        raise ValueError("Expected text arguments without NUL characters")
    return [command, *shlex.split(args)]


def stop_process_tree(process):
    if os.name == "nt":
        if process.poll() is None:
            subprocess.run(["taskkill", "/PID", str(process.pid), "/T", "/F"],
                           capture_output=True, check=True, timeout=10)
    else:
        try:
            os.killpg(process.pid, signal.SIGKILL)
        except ProcessLookupError:
            pass
    process.wait(timeout=10)


class CommandCancelled(Exception):
    pass


class ToolProcess:
    def __init__(self, argv, cwd=None, remote_prefix=None):
        self.remote_prefix = remote_prefix
        self.remote_pid = None
        self.ready = threading.Event()
        self.cancelled = threading.Event()
        self._stop_lock = threading.Lock()
        self._stopped = False
        self.lines = queue.Queue()
        if remote_prefix:
            # setsid makes the reported PID the group leader inside Docker/WSL.
            argv = [*remote_prefix, "setsid", "sh", "-c",
                    'exec 2>&1; printf "%s\\n" "$$"; exec "$@"', "tool", *argv]
        self.process = subprocess.Popen(
            argv, shell=False, cwd=cwd, stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT, text=True, encoding="utf-8", errors="replace",
            start_new_session=os.name != "nt",
            creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0)
        self.pid = self.process.pid
        self.reader = threading.Thread(target=self._read, daemon=True)
        self.reader.start()

    def _read(self):
        try:
            if self.remote_prefix:
                line = self.process.stdout.readline()
                if line.strip().isdigit() and int(line.strip()) > 1:
                    self.remote_pid = int(line.strip())
                else:
                    self.lines.put(line)
            self.ready.set()
            for line in self.process.stdout:
                self.lines.put(line)
        finally:
            self.ready.set()
            self.process.stdout.close()
            self.lines.put(None)

    def stop(self):
        self.cancelled.set()
        with self._stop_lock:
            if self._stopped:
                return
            if self.remote_prefix:
                if not self.ready.wait(10):
                    raise RuntimeError("Cannot confirm remote process ID; cancellation failed")
                if self.remote_pid:
                    result = subprocess.run(
                        [*self.remote_prefix, "env", "LC_ALL=C", "/bin/kill",
                         "-KILL", "--", f"-{self.remote_pid}"],
                        capture_output=True, text=True, timeout=10)
                    if result.returncode and "No such process" not in result.stderr:
                        raise RuntimeError(f"Remote cancellation failed: {result.stderr.strip()}")
                elif self.process.poll() is None:
                    raise RuntimeError("No remote process ID; cancellation could not be confirmed")
            stop_process_tree(self.process)
            self._stopped = True

    def collect_output(self, timeout, cancelled=lambda: False, output_callback=None):
        output = []
        deadline = time.monotonic() + timeout
        try:
            while True:
                if self.cancelled.is_set() or cancelled():
                    self.stop()
                    raise CommandCancelled()
                if time.monotonic() >= deadline:
                    self.stop()
                    raise subprocess.TimeoutExpired(self.process.args, timeout)
                try:
                    line = self.lines.get(timeout=0.05)
                except queue.Empty:
                    continue
                if line is None:
                    break
                output.append(line)
                if output_callback:
                    output_callback(line)
            self.process.wait(timeout=max(0.01, deadline - time.monotonic()))
            return "".join(output)
        except BaseException:
            self.stop()
            raise
