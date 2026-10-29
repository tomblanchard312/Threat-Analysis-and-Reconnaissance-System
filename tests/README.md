# Local regression checks

Run the headless regression suite without installing GUI, model, or training dependencies:

```sh
python -m unittest discover -s tests -p test_audit_fixes.py -v
bash agent/docker/test-scripts.sh
```

The tests compile the actual case and GUI method definitions without importing Tk or starting Ollama. They exercise command validation, literal arguments, quoted portable paths, process-tree cancellation and timeouts, stderr draining, multi-host scan parsing, HTML escaping, scoped case persistence, and generated Ollama templates.

`test_docker_process.py` is an opt-in integration suite. Set `AUDIT_DOCKER_CONTAINER` to a **disposable** running Linux container with `setsid`, `/bin/kill`, `sh`, `head`, `cat`, and `sleep`, then run:

```sh
python -m unittest discover -s tests -p test_docker_process.py -v
```

The integration suite runs harmless output and sleep commands and kills their process groups. It does not require network access or host mounts. Native Windows/WSL, the Kali image build, the interactive GUI, Ollama inference, and GPU training require separate validation.
