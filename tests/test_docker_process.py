"""Opt-in smoke checks against a disposable container, never a working Kali session."""
import os
from pathlib import Path
import subprocess
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'agent'))
from tool_process import CommandCancelled, ToolProcess


@unittest.skipUnless(os.environ.get('AUDIT_DOCKER_CONTAINER'), 'Set AUDIT_DOCKER_CONTAINER to a disposable test container')
class DockerProcessTests(unittest.TestCase):
    def setUp(self):
        self.prefix = ['docker', 'exec', os.environ['AUDIT_DOCKER_CONTAINER']]

    def test_stderr_is_drained(self):
        proc = ToolProcess(['sh', '-c', 'head -c 300000 /dev/zero >&2; printf done'],
                           remote_prefix=self.prefix)
        self.assertEqual(proc.collect_output(10), '\x00' * 300000 + 'done')

    def test_cancel_and_timeout_stop_container_descendants(self):
        for cancel in [True, False]:
            with self.subTest(cancel=cancel):
                proc = ToolProcess(['sh', '-c', 'sleep 60 & echo $!; wait'], remote_prefix=self.prefix)
                children = []
                def received(line):
                    children.append(int(line))
                try:
                    with self.assertRaises(CommandCancelled if cancel else subprocess.TimeoutExpired):
                        proc.collect_output(2, cancelled=lambda: cancel and bool(children),
                                            output_callback=received)
                    self.assertTrue(children)
                    for pid in [proc.remote_pid, *children]:
                        result = subprocess.run([*self.prefix, 'cat', f'/proc/{pid}/stat'],
                                                capture_output=True, text=True, timeout=10)
                        if result.returncode == 0:
                            self.assertEqual(result.stdout.split()[2], 'Z', result.stdout)
                finally:
                    proc.stop()


if __name__ == '__main__':
    unittest.main()
