"""qfw-service: run this rank's QFw site services as children of the broker.

A Python broker module (flux-module(1)). It replaces the ssh path
qfw-site-services used to start the directory service and the QPMs on their
hosts: Flux already has a process on every rank, so the module loaded on a
rank starts whatever the [qfw] table of the broker config assigns to that
rank's hostname, supervises it, exposes it over RPC, and stops it at unload.

    [qfw]
    prefix = "/opt/openqse/qfw"            # QFw install, has bin/qfw-activate
    venv = "/opt/openqse/qfw-venv"         # its Python venv
    site-config = "/etc/openqse/qfw/site.yaml"
    shared-root = "/workspace/qfw-container-base"
    run-root = "/var/lib/qfw-site-services"
    start-timeout = 300                    # seconds a start may take
    autostart = true                       # start at load, not only on RPC
    launch-agent = "/usr/local/libexec/qfw-flux/flux-launch-agent"
                                           # PRRTE launch agent for a QPM's DVM:
                                           # flux exec instead of ssh; "" for ssh
    directory = "flux-lead"                # host that runs qfw-dir-svc
    [qfw.qpm.iqm-ornl-20q]                 # one table per QPM, keyed by service id
    host = "flux-lead"                     # any broker hostname
    [qfw.qpm.nwqsim]
    scope = "job"                          # a simulator: the job runs it on its
                                           # own nodes (flux-qfw); no service here

The module is loaded on every rank (modprobe.d/qfw.toml, rc1.d); a rank
whose hostname no entry names stays idle. Devices behind an external queue
need no service here: flux-qfw submits a scout job for them (see flux-qfw's
scout.py). The services themselves are the
installed QFw managers, run through qfw-activate so they get the QFw venv:
qfw-dir-svc and qfw-qpm-svc start|status|stop, exactly the commands the ssh
path ran, in the broker's environment (which has MODULEPATH). A QPM is not
started until the directory service reports ready, on this rank or, over
RPC, on the rank that runs it.

RPCs, owner only, answered by the rank that runs the service; every one
returns the same report as status:

    qfw-service.status   {}                        -> report
    qfw-service.start    {"service": NAME|"all"}   -> report; start is async, poll status
    qfw-service.stop     {"service": NAME|"all"}   -> report; stop is synchronous
    qfw-service.restart  {"service": NAME|"all"}   -> report

    report = {"rank": R, "hostname": H, "services": {NAME: {
        "role": "directory"|"qpm", "state": STATE, "desired": "up"|"down",
        "run_dir": PATH, "detail": <last manager document>, "error": TEXT}}}

    STATE: stopped | waiting-directory | starting | ready | down | failed
    A failed start is retried with backoff (30 s, doubling, up to 5 min); a
    start RPC retries it at once.

tools/qfw-site-services is the command-line client.
"""

import json
import os
import subprocess
import syslog
import tempfile
import time

import flux.hostlist
from flux.brokermod import BrokerModule, request_handler

STATUS_INTERVAL = 30.0  # seconds between health checks of a ready service
TICK = 2.0
CRASH_WINDOW = 60.0  # a service that dies this soon after starting is failed, not restarted
RETRY_MIN = 30.0  # a failed start is retried after this long, doubling each time...
RETRY_MAX = 300.0  # ...up to this


def first_document(text):
    """The first JSON object in text, or None; the managers print one."""
    start = text.find("{")
    if start < 0:
        return None
    try:
        value, _ = json.JSONDecoder().raw_decode(text[start:])
    except json.JSONDecodeError:
        return None
    return value if isinstance(value, dict) else None


class Service:
    def __init__(self, name, role, spec, cfg, autostart):
        self.name = name
        self.role = role
        self.spec = spec
        self.cfg = cfg
        self.run_dir = (
            os.path.join(cfg["run-root"], "directory")
            if role == "directory"
            else os.path.join(cfg["run-root"], "qpm", name)
        )
        self.desired = "up" if autostart else "down"
        self.state = "stopped"
        self.detail = None
        self.error = None
        self.proc = None  # (Popen, kind, stdout file, stderr file)
        self.started_at = 0.0
        self.checked_at = 0.0
        self.retry_at = 0.0
        self.backoff = RETRY_MIN

    def argv(self, action):
        tool = "qfw-dir-svc" if self.role == "directory" else "qfw-qpm-svc"
        argv = [tool, action, "--run-dir", self.run_dir]
        if action == "start":
            argv += ["--scope", "site", "--site-config", self.cfg["site-config"],
                     "--timeout", str(int(self.cfg["start-timeout"]))]
            if self.role == "qpm":
                argv += ["--service-id", self.name]
        return argv

    def env(self):
        env = dict(os.environ)
        env["QFW_SHARED_ROOT"] = self.cfg["shared-root"]
        env["QFW_SITE_CONFIG"] = self.cfg["site-config"]
        nodes = self.spec.get("simulator-nodes")
        if nodes:
            env["QFW_SIMULATOR_NODES"] = nodes
        agent = self.cfg.get("launch-agent")
        if agent:
            # the QPM's PRTE DVM launches its daemons through flux exec
            # (flux-launch-agent) instead of ssh; no tree spawn, so every
            # daemon is launched from this rank, which has the agent
            env["PRTE_MCA_plm_ssh_agent"] = agent
            env["PRTE_MCA_plm_ssh_no_tree_spawn"] = "1"
        return env

    def report(self):
        return {
            "role": self.role,
            "state": self.state,
            "desired": self.desired,
            "run_dir": self.run_dir,
            "detail": self.detail,
            "error": self.error,
        }


class QfwServiceModule(BrokerModule):
    def __init__(self, h, *args):
        super().__init__(h, *args)
        self.rank = int(h.attr_get("rank"))
        self.hostname = h.attr_get("hostname")
        self.hostlist = flux.hostlist.Hostlist(h.attr_get("hostlist"))
        cfg = dict(h.conf_get("qfw") or {})
        cfg.setdefault("prefix", "/opt/openqse/qfw")
        cfg.setdefault("venv", "/opt/openqse/qfw-venv")
        cfg.setdefault("site-config", "/etc/openqse/qfw/site.yaml")
        cfg.setdefault("shared-root", "/workspace/qfw-container-base")
        cfg.setdefault("run-root", "/var/lib/qfw-site-services")
        cfg.setdefault("start-timeout", 300)
        cfg.setdefault("autostart", True)
        cfg.setdefault("stop-on-unload", True)
        cfg.setdefault("launch-agent", "/usr/local/libexec/qfw-flux/flux-launch-agent")
        for arg in args:  # flux module load qfw-service autostart=false
            key, _, value = str(arg).partition("=")
            cfg[key] = value if key not in ("autostart", "stop-on-unload") else value.lower() in ("1", "true", "yes")
        self.cfg = cfg
        self.directory_host = cfg.get("directory")
        self.services = {}  # ordered: directory first, so "all" stops in reverse
        if self.directory_host == self.hostname:
            self.services["directory"] = Service("directory", "directory", {}, cfg, cfg["autostart"])
        for sid, spec in (cfg.get("qpm") or {}).items():
            if spec.get("scope", "site") == "job":
                continue  # a simulator the job runs itself; nothing persistent
            if spec.get("host") == self.hostname:
                self.services[sid] = Service(sid, "qpm", spec, cfg, cfg["autostart"])
        self.info("rank %d (%s): %s", self.rank, self.hostname,
                  ", ".join("{} ({})".format(s.name, s.role) for s in self.services.values()) or "no service assigned")
        if self.services:
            self.timer = h.timer_watcher_create(0.5, self._tick, repeat=TICK)
            self.timer.start()

    # -- logging -----------------------------------------------------------

    def info(self, fmt, *args):
        self.handle.log(syslog.LOG_INFO, "qfw-service: " + fmt % args)

    def err(self, fmt, *args):
        self.handle.log(syslog.LOG_ERR, "qfw-service: " + fmt % args)

    # -- running the QFw managers --------------------------------------------

    def _command(self, argv):
        # source qfw-activate for the venv, then exec the manager; the
        # module's own environment (the broker's) is inherited underneath
        script = 'source "$1/bin/qfw-activate" --venv "$2" >/dev/null || exit 97; shift 2; exec "$@"'
        return ["bash", "-c", script, "qfw-service", self.cfg["prefix"], self.cfg["venv"]] + argv

    def _launch(self, svc, action):
        out = tempfile.TemporaryFile(mode="w+")
        errf = tempfile.TemporaryFile(mode="w+")
        proc = subprocess.Popen(self._command(svc.argv(action)), env=svc.env(),
                                stdout=out, stderr=errf, stdin=subprocess.DEVNULL)
        svc.proc = (proc, action, out, errf)
        if action == "start":
            svc.state = "starting"
            svc.started_at = time.time()
            svc.error = None
            self.info("starting %s (%s)", svc.name, " ".join(svc.argv(action)))

    def _collect(self, svc):
        proc, action, out, errf = svc.proc
        svc.proc = None
        out.seek(0)
        errf.seek(0)
        stdout, stderr = out.read(), errf.read()
        out.close()
        errf.close()
        doc = first_document(stdout)
        return proc.returncode, doc, (stderr.strip() or stdout.strip())[-2000:], action

    def _run_sync(self, svc, action, timeout=180):
        self._launch(svc, action)
        proc = svc.proc[0]
        try:
            proc.wait(timeout=timeout)
        except subprocess.TimeoutExpired:
            proc.kill()
            proc.wait()
        return self._collect(svc)

    def _stop(self, svc):
        if svc.proc:
            svc.proc[0].terminate()
            self._collect(svc)
        rc, doc, text, _ = self._run_sync(svc, "stop")
        svc.state = "stopped"
        svc.detail = doc
        svc.error = None if rc == 0 else "stop exited {}: {}".format(rc, text)
        self.info("stopped %s (rc=%d)", svc.name, rc)

    def _directory_ready(self):
        directory = self.services.get("directory")
        if directory is not None:
            return directory.state == "ready"
        if not self.directory_host:
            return True  # nothing to wait for
        try:
            found = self.hostlist.index(self.directory_host)  # a list of indices
        except (ValueError, OSError):
            found = []
        if not found:
            self.err("directory host %r is not in the instance hostlist", self.directory_host)
            return False
        rank = int(found[0])
        try:
            report = self.handle.rpc(self.name + ".status", {}, nodeid=rank).wait_for(5).get()
        except Exception as error:  # module not loaded there yet, or unreachable
            self.err("directory status on rank %d: %s", rank, error)
            return False
        return report.get("services", {}).get("directory", {}).get("state") == "ready"

    # -- the state machine, driven by the timer -------------------------------

    def _tick(self, h=None, watcher=None, revents=None, args=None):
        now = time.time()
        for svc in self.services.values():
            if svc.proc:
                if svc.proc[0].poll() is None:
                    continue
                rc, doc, text, action = self._collect(svc)
                if action == "start":
                    if rc == 0 and doc is not None and str(doc.get("state", "")).lower() == "ready":
                        svc.state, svc.detail, svc.error = "ready", doc, None
                        svc.checked_at = now
                        svc.backoff = RETRY_MIN
                        self.info("%s is ready", svc.name)
                    else:
                        svc.state, svc.detail = "failed", doc
                        svc.error = "start exited {}: {}".format(rc, text)
                        svc.retry_at = now + svc.backoff
                        self.err("%s failed to start (retry in %ds): %s", svc.name, svc.backoff, svc.error)
                        svc.backoff = min(svc.backoff * 2, RETRY_MAX)
                elif action == "status":
                    svc.checked_at = now
                    if rc == 0 and doc is not None and str(doc.get("state", "")).lower() == "ready":
                        svc.detail = doc
                    else:
                        svc.state, svc.detail = "down", doc
                        svc.error = "status exited {}: {}".format(rc, text)
                        self.err("%s is down: %s", svc.name, svc.error)
                continue
            if svc.desired != "up":
                continue
            if svc.state == "failed" and now >= svc.retry_at:
                # retry with backoff, like a service manager would: the
                # site config may only land after boot, the directory may
                # come back, an operator may have fixed the cause
                svc.state = "stopped"
            if svc.state in ("stopped", "waiting-directory", "down"):
                if svc.state == "down":
                    if now - svc.started_at < CRASH_WINDOW:
                        svc.state = "failed"
                        self.err("%s died within %ds of starting; not restarting it", svc.name, CRASH_WINDOW)
                        continue
                    self.info("%s went down; cleaning up and restarting", svc.name)
                    self._stop(svc)
                if svc.role == "qpm" and not self._directory_ready():
                    svc.state = "waiting-directory"
                    continue
                self._launch(svc, "start")
            elif svc.state == "ready" and now - svc.checked_at >= STATUS_INTERVAL:
                self._launch(svc, "status")

    # -- RPCs ----------------------------------------------------------------

    def report(self, error=None):
        doc = {
            "rank": self.rank,
            "hostname": self.hostname,
            "services": {name: svc.report() for name, svc in self.services.items()},
        }
        if error:
            doc["error"] = error
        return doc

    def _selected(self, msg):
        payload = msg.payload or {}
        name = payload.get("service", "all")
        if name == "all":
            return list(self.services.values()), None
        svc = self.services.get(name)
        if svc is None:
            return [], "no service {!r} on rank {} ({}); here: {}".format(
                name, self.rank, self.hostname, ", ".join(self.services) or "none")
        return [svc], None

    @request_handler("status")
    def status_rpc(self, msg):
        self.handle.respond(msg, self.report())

    @request_handler("start")
    def start_rpc(self, msg):
        selected, error = self._selected(msg)
        for svc in selected:
            svc.desired = "up"
            if svc.state == "failed":
                svc.state = "stopped"
                svc.backoff = RETRY_MIN
        if selected:
            self._tick()
        self.handle.respond(msg, self.report(error))

    @request_handler("stop")
    def stop_rpc(self, msg):
        selected, error = self._selected(msg)
        for svc in reversed(selected):
            svc.desired = "down"
            self._stop(svc)
        self.handle.respond(msg, self.report(error))

    @request_handler("restart")
    def restart_rpc(self, msg):
        selected, error = self._selected(msg)
        for svc in reversed(selected):
            self._stop(svc)
        for svc in selected:
            svc.desired = "up"
        if selected:
            self._tick()
        self.handle.respond(msg, self.report(error))

    # -- unload ----------------------------------------------------------------

    def shutdown(self):
        if not self.cfg.get("stop-on-unload", True):
            return
        for svc in reversed(list(self.services.values())):
            if svc.state != "stopped":
                self._stop(svc)


def mod_main(h, *args):
    module = QfwServiceModule(h, *args)
    try:
        module.run()
    finally:
        module.shutdown()
