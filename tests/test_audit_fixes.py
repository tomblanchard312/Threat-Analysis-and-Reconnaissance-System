"""Headless regressions: load real model/GUI methods without starting Tk or Ollama."""
import ast
import __future__
import json
import os
from pathlib import Path
import re
import shlex
import subprocess
import sys
import tempfile
import threading
import time
import unittest
from unittest.mock import Mock, patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'agent'))
from tool_process import CommandCancelled, ToolProcess, tool_arguments


def definitions(path, names, namespace):
    tree = ast.parse(path.read_text())
    nodes = [n for n in tree.body if isinstance(n, (ast.ClassDef, ast.FunctionDef)) and n.name in names]
    # Class methods have no GUI dependencies; replace only the widget base class.
    for n in nodes:
        if isinstance(n, ast.ClassDef) and n.name == 'PentestGUI':
            n.bases = []
    exec(compile(ast.Module(body=nodes, type_ignores=[]), str(path), 'exec',
                 flags=__future__.annotations.compiler_flag), namespace)
    return namespace


GUI = definitions(ROOT / 'agent/pentest-gui.py',
                  {'CaseFile', 'PentestGUI', 'is_valid_tool_command', 'parse_planning_response_to_tasks'},
                  dict(os=os, re=re, json=json, shlex=shlex, subprocess=subprocess,
                       ToolProcess=ToolProcess, CommandCancelled=CommandCancelled,
                       tool_arguments=tool_arguments, check_docker=lambda: False,
                       DOCKER_PASSTHROUGH=True, DOCKER_CONTAINER='htb-kali',
                       VALID_TOOLS_PORTABLE={'curl', 'nmap'}, TOOL_TIMEOUTS={}, TIMEOUT_SECONDS=5,
                       COLORS={'success': 'blue'}))
CaseFile = GUI['CaseFile']


class ProcessTests(unittest.TestCase):
    def test_executable_validation_and_quoted_arguments(self):
        for command in ['curl --version; echo marker', '/tmp/curl', 'curl\necho', 'curl.exe&echo', None]:
            with self.subTest(command=command):
                with self.assertRaises(ValueError):
                    tool_arguments(command, '')
                self.assertFalse(GUI['is_valid_tool_command'](command, True))
        self.assertEqual(tool_arguments('curl', '-H "User Agent: hello" "https://example.test/?a=1&b=2"'),
                         ['curl', '-H', 'User Agent: hello', 'https://example.test/?a=1&b=2'])
        with self.assertRaises(ValueError):
            tool_arguments('curl', '"unfinished')

    def test_arguments_are_literal_and_stderr_is_drained(self):
        marker = '$(echo injected); echo marker | another & command'
        proc = ToolProcess([sys.executable, '-c',
                            'import sys; print(sys.argv[1]); sys.stderr.write("e" * 300000)', marker])
        output = proc.collect_output(5)
        self.assertIn(marker + '\n', output)
        self.assertEqual(output.count('e') - marker.count('e'), 300000)

    def test_gui_rejects_injected_executable_before_start(self):
        app = GUI['PentestGUI'].__new__(GUI['PentestGUI'])
        with patch.dict(GUI, ToolProcess=Mock()):
            self.assertIn('[BLOCKED]', app.execute_command('curl --version; echo marker', ''))
            GUI['ToolProcess'].assert_not_called()

    def test_cli_rejects_injected_executable_before_routing(self):
        cli = definitions(ROOT / 'agent/pentest-agent.py', {'execute_command'},
                          dict(tool_arguments=tool_arguments, get_tool_path=Mock()))
        self.assertIn('[BLOCKED]', cli['execute_command']('curl; echo marker', ''))
        cli['get_tool_path'].assert_not_called()

    def test_gui_portable_path_with_spaces(self):
        app = GUI['PentestGUI'].__new__(GUI['PentestGUI'])
        app.running_process = None
        app.process_cancelled = False
        app.get_tool_path = Mock(return_value=('/tmp/tools with spaces/curl.exe', 'portable'))
        app.translate_to_windows = lambda c, a: (c, a)
        proc = Mock()
        proc.collect_output.return_value = 'ok'
        with patch.dict(GUI, ToolProcess=Mock(return_value=proc), TOOLS_DIR='/tmp/tools with spaces'):
            self.assertIn('ok', app.execute_command('curl', '"https://example.test/?a=1&b=2"'))
            self.assertEqual(GUI['ToolProcess'].call_args.args[0],
                             ['/tmp/tools with spaces/curl.exe', 'https://example.test/?a=1&b=2'])
        self.assertIsNone(app.running_process)

    def test_docker_ui_paths_stop_before_analysis_on_cancel(self):
        for method, args in [('_execute_recommendation_command', ('nmap example.test', 'example.test')),
                             ('_execute_nlp_tool_command', ('nmap', 'nmap example.test')),
                             ('_execute_docker_command', ('nmap_scan', 'example.test'))]:
            with self.subTest(method=method):
                app = GUI['PentestGUI'].__new__(GUI['PentestGUI'])
                app.chat_area = Mock()
                app.after = lambda delay, callback: callback()
                app.set_processing = Mock()
                app.update_status = Mock()
                app.chat = Mock()
                app._run_tool_process = Mock(side_effect=CommandCancelled())
                sync_threads = Mock(Thread=lambda target, daemon: Mock(start=target))
                with patch.dict(GUI, threading=sync_threads):
                    getattr(app, method)(*args)
                app._run_tool_process.assert_called_once()
                app.chat.assert_not_called()
                self.assertTrue(any('[CANCELLED]' in str(call) for call in app.chat_area.add_message.call_args_list))

    @unittest.skipUnless(os.name == 'posix', 'POSIX process groups')
    def test_cancellation_and_timeout_stop_descendants(self):
        # Use a local exec proxy to exercise the actual remote wrapper without Docker/WSL.
        with tempfile.TemporaryDirectory() as folder:
            proxy = Path(folder) / 'proxy.py'
            proxy.write_text('import os,sys\nos.execvp(sys.argv[1],sys.argv[1:])\n')
            for remote in [None, [sys.executable, str(proxy)]]:
                for cancel in [True, False]:
                    with self.subTest(remote=bool(remote), cancel=cancel):
                        proc = ToolProcess([sys.executable, '-u', '-c',
                            'import subprocess,time; p=subprocess.Popen(["sleep","60"]); '
                            'print(p.pid,flush=True); time.sleep(60)'], remote_prefix=remote)
                        children = []
                        event = threading.Event()
                        def received(line):
                            children.append(int(line))
                            if cancel:
                                event.set()
                        try:
                            with self.assertRaises(CommandCancelled if cancel else subprocess.TimeoutExpired):
                                proc.collect_output(0.5, cancelled=event.is_set, output_callback=received)
                            self.assertTrue(children)
                            self.assertIsNotNone(proc.process.poll())
                            for child in children:
                                deadline = time.monotonic() + 2
                                while time.monotonic() < deadline:
                                    stat = Path(f'/proc/{child}/stat')
                                    try:
                                        if stat.read_text().split()[2] == 'Z':
                                            break
                                    except FileNotFoundError:
                                        break
                                    time.sleep(0.02)
                                else:
                                    self.fail(f'Child {child} still running')
                        finally:
                            proc.stop()

    @unittest.skipUnless(os.name == 'posix', 'POSIX process groups')
    def test_cancel_during_remote_startup(self):
        with tempfile.TemporaryDirectory() as folder:
            proxy = Path(folder) / 'slow_proxy.py'
            proxy.write_text('import os,sys,time\ntime.sleep(.15)\nos.execvp(sys.argv[1],sys.argv[1:])\n')
            proc = ToolProcess(['sleep', '60'], remote_prefix=[sys.executable, str(proxy)])
            try:
                with self.assertRaises(CommandCancelled):
                    proc.collect_output(5, cancelled=lambda: True)
                self.assertIsNotNone(proc.remote_pid)
                self.assertIsNotNone(proc.process.poll())
            finally:
                proc.stop()

    def test_cancel_before_launch_keeps_cancellation_until_worker_finishes(self):
        app = GUI['PentestGUI'].__new__(GUI['PentestGUI'])
        app.running_process = None
        app.task_execution_active = False
        app.process_cancelled = False
        app.set_processing = Mock()
        app.cancel_running_command()
        self.assertTrue(app.process_cancelled)
        app.set_processing.assert_not_called()

    def test_remote_kill_failure_is_reported(self):
        import tool_process
        proc = ToolProcess.__new__(ToolProcess)
        proc.remote_prefix = ['docker', 'exec', 'disposable']
        proc.remote_pid = 123
        proc.ready = threading.Event()
        proc.ready.set()
        proc.cancelled = threading.Event()
        proc._stop_lock = threading.Lock()
        proc._stopped = False
        proc.process = Mock()
        result = Mock(returncode=1, stderr='Operation not permitted')
        with patch.object(tool_process.subprocess, 'run', return_value=result):
            with self.assertRaisesRegex(RuntimeError, 'Remote cancellation failed'):
                proc.stop()
        self.assertFalse(proc._stopped)

    def test_auto_install_rejects_shell_syntax_in_model_package(self):
        app = GUI['PentestGUI'].__new__(GUI['PentestGUI'])
        app._ask_llm_for_install_info = Mock(return_value={'method': 'apt', 'package': 'thing;id'})
        app._run_tool_process = Mock()
        with patch.dict(GUI, check_docker=lambda: True, TOOL_INSTALL_REGISTRY={}):
            with patch.object(subprocess, 'run', return_value=Mock(returncode=1)):
                self.assertFalse(app.ensure_tool_available('exampletool'))
        app._run_tool_process.assert_not_called()

    def test_windows_tree_termination_uses_taskkill(self):
        import tool_process
        proc = Mock(pid=123)
        proc.poll.return_value = None
        with patch.object(tool_process.os, 'name', 'nt'), patch.object(tool_process.subprocess, 'run') as run:
            tool_process.stop_process_tree(proc)
        self.assertEqual(run.call_args.args[0], ['taskkill', '/PID', '123', '/T', '/F'])


class CaseTests(unittest.TestCase):
    def test_subnet_ports_os_and_scripts_stay_with_each_host(self):
        case = CaseFile()
        case.parse_nmap_output('''Nmap scan report for first.test (192.0.2.1)
22/tcp open ssh OpenSSH
OS details: First OS
| smb-vuln-test:
|   first host evidence
Nmap scan report for 192.0.2.2
443/tcp open https Second server
OS details: Second OS
''', '192.0.2.0/24')
        self.assertEqual(set(case.targets), {'192.0.2.1', '192.0.2.2'})
        self.assertEqual([p['port'] for p in case.targets['192.0.2.1']['ports']], [22])
        self.assertEqual([p['port'] for p in case.targets['192.0.2.2']['ports']], [443])
        self.assertEqual(case.targets['192.0.2.1']['hostname'], 'first.test')
        self.assertEqual(case.targets['192.0.2.2']['os_guess'], 'Second OS')
        vuln = next(f for f in case.findings if f['type'] == 'vulnerability')
        self.assertEqual(vuln['target'], '192.0.2.1')

    def test_ipv6_hostname_and_headerless_output(self):
        case = CaseFile()
        case.parse_nmap_output('Nmap scan report for ipv6.test (2001:db8::1)\n80/tcp open http\n', 'ignored')
        case.parse_nmap_output('53/udp open domain\n', 'dns.test')
        self.assertEqual(case.targets['2001:db8::1']['hostname'], 'ipv6.test')
        self.assertEqual(case.targets['dns.test']['ports'][0]['port'], 53)

    def test_html_export_escapes_untrusted_fields_in_both_formats(self):
        from html.parser import HTMLParser
        class Tags(HTMLParser):
            def __init__(self):
                super().__init__()
                self.tags = []
            def handle_starttag(self, tag, attrs):
                self.tags.append(tag)
        payload = '</pre><img src=x onerror="alert(1)"><script>bad()</script>'
        case = CaseFile(name=payload)
        case.scope = payload
        case.analyst = payload
        case.add_target(payload, payload)
        case.add_port(payload, 80, service=payload, version=payload)
        case.targets[payload]['os_guess'] = payload
        case.add_finding(payload, payload, payload, 'high', payload, payload)
        case.add_credential(payload, password=payload, target=payload, source=payload)
        case.log_action(payload, tool=payload, target=payload)
        for professional in [False, True]:
            with self.subTest(professional=professional):
                html = case.export_html(professional=professional, report_meta={'client_name': payload})
                parsed = Tags()
                parsed.feed(html)
                self.assertNotIn(payload, html)
                self.assertNotIn('img', parsed.tags)
                self.assertEqual(parsed.tags.count('script'), 2 if professional else 0)
                self.assertIn('&lt;img', html)

    def test_scoped_case_is_saved_and_receives_results(self):
        with tempfile.TemporaryDirectory() as folder, patch.dict(GUI, CASE_FILES_DIR=folder):
            app = GUI['PentestGUI'].__new__(GUI['PentestGUI'])
            app.sidebar = Mock()
            app.chat_area = Mock()
            app.task_plan_panel = Mock()
            app.set_processing = Mock()
            app.update_status = Mock()
            app._launch_scoped_pentest('192.0.2.1', 'Network Penetration Test', 'Light', True, True)
            case = app.active_case
            saved = Path(folder) / f'{case.case_id}.json'
            self.assertTrue(saved.exists())
            self.assertEqual(json.loads(saved.read_text())['name'], '192_0_2_1')
            app.after = lambda delay, callback: callback()
            app.capture_to_case('nmap', 'Nmap scan report for 192.0.2.1\n22/tcp open ssh\n')
            self.assertEqual(json.loads(saved.read_text())['targets']['192.0.2.1']['ports'][0]['port'], 22)
            app._launch_scoped_pentest('192.0.2.2', 'Network Penetration Test', 'Light', True, False)
            self.assertIs(app.active_case, case)

    def test_planning_parser_still_accepts_full_commands(self):
        tasks = GUI['parse_planning_response_to_tasks']('Run `nmap -sV 192.0.2.1` then `curl https://example.test`')
        self.assertEqual({t['command'] for t in tasks}, {'nmap -sV 192.0.2.1', 'curl https://example.test'})


class PackagingTests(unittest.TestCase):
    def test_ollama_template_preserves_double_braces(self):
        ns = definitions(ROOT / 'htb-model-training/scripts/convert_to_gguf.py', {'create_modelfile'}, {})
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder)
            result = ns['create_modelfile'](path / 'model.gguf', path).read_text()
            for key in ('System', 'Prompt', 'Response'):
                self.assertIn('{{ .' + key + ' }}', result)
                self.assertNotIn('{{{', result)

    def test_shared_runtime_is_in_deployment_manifests(self):
        for manifest in ['deploy/usb-deploy/deploy-to-usb.ps1',
                         'deploy/orin-nano-deploy/deploy-to-jetson.sh',
                         'deploy/orin-nano-deploy/remote-deploy.sh']:
            self.assertIn('tool_process.py', (ROOT / manifest).read_text())

    def test_docker_scripts_are_executable(self):
        for path in (ROOT / 'agent/docker').glob('*.sh'):
            self.assertTrue(os.access(path, os.X_OK), str(path))


if __name__ == '__main__':
    unittest.main()
