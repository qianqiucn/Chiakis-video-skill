"""run_queue.py — cross-platform machine-wide queue for headless Chrome & Blender rendering jobs.

At most 1 browser job and 2 Blender jobs run at once across projects and sessions, starting only when the machine
has enough free RAM. Prevents concurrent headless Chromes or Blenders from starving RAM/GPU.

Usage:
  python -X utf8 scripts/run_queue.py web --lane <who> -- node scripts/snap.mjs <index.html> <outDir> "0-120:4" --sheet s
  python -X utf8 scripts/run_queue.py web --lane <who> -- node scripts/render_fast.mjs <index.html> 0 10 out.mp4
  python -X utf8 scripts/run_queue.py blender --lane relief -- blender -b --python scripts/blender/depth_relief.py -- ...
  python -X utf8 scripts/run_queue.py --status

Options before `--`:
  --lane <who>         label shown in --status (default: program name)
  --min-free-gb G      free RAM floor in GB (default: 4.0)
  --max-workers N      worker cap exported as CHIAKI_MAX_WORKERS and applied to --workers (default: 2)

Lock directory: env CHIAKI_QUEUE_DIR, else <system temp>/chiaki_video_queue.
Nested calls from a child already holding the slot (CHIAKI_QUEUE_HELD) inherit the parent's slot
so tools like qa.mjs spawning render_fast.mjs never deadlock.
"""
from __future__ import annotations

import datetime
import itertools
import json
import os
import re
import signal
import subprocess
import sys
import tempfile
import time

IS_WIN = sys.platform == "win32"
if IS_WIN:
    import ctypes
    import msvcrt
    from ctypes import wintypes
else:
    import fcntl


def _env_slots(name: str, default: int) -> int:
    try:
        return max(1, int(os.environ.get(name, "").strip() or default))
    except ValueError:
        return default


KINDS = {
    "web": {"slots": _env_slots("CHIAKI_WEB_SLOTS", 1), "min_free_gb": 4.0},
    "blender": {"slots": _env_slots("CHIAKI_BLENDER_SLOTS", 2), "min_free_gb": 4.0},
}
MAX_WORKERS = 2
POLL, REMIND, MEM_POLL, MEM_REMIND = 2, 300, 5, 60
_seq = itertools.count()


def root() -> str:
    return os.environ.get("CHIAKI_QUEUE_DIR") or os.path.join(tempfile.gettempdir(), "chiaki_video_queue")


def kind_dir(kind: str) -> str:
    return os.path.join(root(), kind)


def slot_count(kind: str) -> int:
    try:
        with open(os.path.join(kind_dir(kind), "slots.txt"), encoding="utf-8") as f:
            return max(1, min(4, int(f.read().strip())))
    except (OSError, ValueError):
        return KINDS[kind]["slots"]


def slot_names(kind: str) -> list[str]:
    return [f"slot{i}" for i in range(slot_count(kind))]


def now() -> str:
    return datetime.datetime.now().strftime("%m-%d %H:%M:%S")


def _print(msg: str) -> None:
    try:
        print(f"[run_queue {now()}] {msg}", flush=True)
    except Exception:
        pass


def _lock(path: str):
    fd = os.open(path, os.O_RDWR | os.O_CREAT, 0o666)
    try:
        if IS_WIN:
            os.lseek(fd, 0, 0)
            msvcrt.locking(fd, msvcrt.LK_NBLCK, 1)
        else:
            fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        return fd
    except OSError:
        os.close(fd)
        return None


def _unlock(fd) -> None:
    try:
        if IS_WIN:
            os.lseek(fd, 0, 0)
            msvcrt.locking(fd, msvcrt.LK_UNLCK, 1)
        else:
            fcntl.flock(fd, fcntl.LOCK_UN)
    except OSError:
        pass
    try:
        os.close(fd)
    except OSError:
        pass


def free_ram_gb() -> float:
    if IS_WIN:
        class MEMSTAT(ctypes.Structure):
            _fields_ = [
                ("dwLength", wintypes.DWORD),
                ("dwMemoryLoad", wintypes.DWORD),
                ("ullTotalPhys", ctypes.c_uint64),
                ("ullAvailPhys", ctypes.c_uint64),
                ("ullTotalPageFile", ctypes.c_uint64),
                ("ullAvailPageFile", ctypes.c_uint64),
                ("ullTotalVirtual", ctypes.c_uint64),
                ("ullAvailVirtual", ctypes.c_uint64),
                ("ullAvailExtendedVirtual", ctypes.c_uint64),
            ]
        ms = MEMSTAT(dwLength=ctypes.sizeof(MEMSTAT))
        if ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(ms)):
            return ms.ullAvailPhys / (1024 ** 3)
        return 99.0
    # Linux /proc/meminfo
    try:
        with open("/proc/meminfo", encoding="utf-8") as f:
            for line in f:
                if line.startswith("MemAvailable:"):
                    return int(line.split()[1]) / (1024 ** 2)
    except OSError:
        pass
    # macOS vm_stat fallback
    try:
        out = subprocess.check_output(["vm_stat"], text=True)
        page_sz = 4096
        m = re.search(r"page size of (\d+) bytes", out)
        if m:
            page_sz = int(m.group(1))
        free_pages = 0
        for key in ("Pages free", "Pages inactive", "Pages speculative"):
            mm = re.search(rf"{key}:\s+(\d+)", out)
            if mm:
                free_pages += int(mm.group(1))
        if free_pages:
            return (free_pages * page_sz) / (1024 ** 3)
    except Exception:
        pass
    return 99.0


def _pid_alive(pid: int) -> bool:
    if pid <= 0:
        return False
    if IS_WIN:
        SYNCHRONIZE = 0x00100000
        h = ctypes.windll.kernel32.OpenProcess(SYNCHRONIZE, False, pid)
        if not h:
            return False
        res = ctypes.windll.kernel32.WaitForSingleObject(h, 0)
        ctypes.windll.kernel32.CloseHandle(h)
        return res == 0x00000102  # WAIT_TIMEOUT
    try:
        os.kill(pid, 0)
        return True
    except OSError:
        return False


def _win_job_object():
    if not IS_WIN:
        return None
    k32 = ctypes.windll.kernel32
    job = k32.CreateJobObjectW(None, None)
    if not job:
        return None

    class BASIC(ctypes.Structure):
        _fields_ = [
            ("PerProcessUserTimeLimit", ctypes.c_int64),
            ("PerJobUserTimeLimit", ctypes.c_int64),
            ("LimitFlags", wintypes.DWORD),
            ("MinimumWorkingSetSize", ctypes.c_size_t),
            ("MaximumWorkingSetSize", ctypes.c_size_t),
            ("ActiveProcessLimit", wintypes.DWORD),
            ("Affinity", ctypes.c_size_t),
            ("PriorityClass", wintypes.DWORD),
            ("SchedulingClass", wintypes.DWORD),
        ]

    class IO(ctypes.Structure):
        _fields_ = [(n, ctypes.c_uint64) for n in ("ReadOperationCount", "WriteOperationCount", "OtherOperationCount", "ReadTransferCount", "WriteTransferCount", "OtherTransferCount")]

    class EXT(ctypes.Structure):
        _fields_ = [
            ("BasicLimitInformation", BASIC),
            ("IoInfo", IO),
            ("ProcessMemoryLimit", ctypes.c_size_t),
            ("JobMemoryLimit", ctypes.c_size_t),
            ("PeakProcessMemoryUsed", ctypes.c_size_t),
            ("PeakJobMemoryUsed", ctypes.c_size_t),
        ]

    ext = EXT()
    ext.BasicLimitInformation.LimitFlags = 0x00002000  # JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE
    k32.SetInformationJobObject(job, 9, ctypes.byref(ext), ctypes.sizeof(ext))
    return job


def _cap_workers(cmd: list[str], cap: int) -> list[str]:
    out = list(cmd)
    if not any(re.search(r"render_fast\.mjs$", str(x), re.I) for x in out):
        return out
    found = False
    i = 0
    while i < len(out):
        if out[i] == "--workers":
            found = True
            if i + 1 < len(out):
                try:
                    n = int(out[i + 1])
                    out[i + 1] = str(max(1, min(n, cap)))
                except ValueError:
                    out[i + 1] = str(cap)
            i += 2
            continue
        m = re.match(r"^--workers=(\d+)$", out[i])
        if m:
            found = True
            out[i] = f"--workers={max(1, min(int(m.group(1)), cap))}"
        i += 1
    if not found:
        out += ["--workers", str(cap)]
    return out


class Slot:
    """Context manager holding one queue slot (or inheriting CHIAKI_QUEUE_HELD)."""

    def __init__(self, kind: str = "web", lane: str = "", min_free_gb: float | None = None,
                 max_workers: int = MAX_WORKERS, say=_print, where: str = ""):
        if kind not in KINDS:
            raise ValueError(f"unknown queue kind {kind!r}; expected one of {list(KINDS)}")
        self.kind = kind
        self.lane = lane or "job"
        self.min_free_gb = KINDS[kind]["min_free_gb"] if min_free_gb is None else float(min_free_gb)
        self.max_workers = max(1, int(max_workers))
        self.say = say
        self.where = where or os.getcwd()
        self.fd = None
        self.slot_name = ""
        self.who_path = ""
        self.ticket_path = ""
        self.inherited = False

    def __enter__(self):
        held = os.environ.get("CHIAKI_QUEUE_HELD", "")
        if held:
            parts = held.split(":")
            if len(parts) == 3 and parts[0] == self.kind and _pid_alive(int(parts[2])):
                self.inherited = True
                self.slot_name = parts[1]
                self.say(f"inheriting parent {self.kind}/{self.slot_name} (holder PID {parts[2]})")
                return self

        kdir = kind_dir(self.kind)
        wdir = os.path.join(kdir, "wait")
        os.makedirs(wdir, exist_ok=True)
        tk_name = f"{time.time_ns():020d}_{os.getpid()}_{next(_seq)}.tk"
        self.ticket_path = os.path.join(wdir, tk_name)
        with open(self.ticket_path, "w", encoding="utf-8") as f:
            json.dump({"pid": os.getpid(), "lane": self.lane, "since": now(), "where": self.where}, f)

        last_say = 0.0
        try:
            while True:
                # Prune dead tickets ahead
                tickets = sorted(n for n in os.listdir(wdir) if n.endswith(".tk"))
                live = []
                for n in tickets:
                    p = os.path.join(wdir, n)
                    try:
                        info = json.loads(open(p, encoding="utf-8").read())
                        if _pid_alive(int(info.get("pid", 0))):
                            live.append(n)
                        else:
                            os.remove(p)
                    except OSError:
                        pass
                pos = live.index(tk_name) if tk_name in live else 0
                if pos == 0:
                    # Try acquiring a free slot
                    for sname in slot_names(self.kind):
                        lpath = os.path.join(kdir, f"{sname}.lock")
                        fd = _lock(lpath)
                        if fd is not None:
                            # Wait for free RAM floor
                            mem_say = 0.0
                            while free_ram_gb() < self.min_free_gb:
                                if time.time() - mem_say >= MEM_REMIND:
                                    self.say(f"waiting for RAM ({free_ram_gb():.1f} GB free < {self.min_free_gb:.1f} GB floor)")
                                    mem_say = time.time()
                                time.sleep(MEM_POLL)
                            self.fd = fd
                            self.slot_name = sname
                            self.who_path = os.path.join(kdir, f"{sname}.who")
                            with open(self.who_path, "w", encoding="utf-8") as f:
                                json.dump({"pid": os.getpid(), "lane": self.lane, "since": now(), "where": self.where}, f)
                            try:
                                os.remove(self.ticket_path)
                            except OSError:
                                pass
                            self.ticket_path = ""
                            return self
                if time.time() - last_say >= REMIND:
                    self.say(f"queued for {self.kind} (position #{pos + 1} of {len(live)}, free RAM {free_ram_gb():.1f} GB)")
                    last_say = time.time()
                time.sleep(POLL)
        except BaseException:
            if self.ticket_path and os.path.exists(self.ticket_path):
                try:
                    os.remove(self.ticket_path)
                except OSError:
                    pass
            raise

    def _child_env(self, extra=None) -> dict[str, str]:
        env = dict(os.environ)
        env["CHIAKI_QUEUE_HELD"] = f"{self.kind}:{self.slot_name}:{os.getpid()}"
        env["CHIAKI_MAX_WORKERS"] = str(self.max_workers)
        if extra:
            env.update(extra)
        return env

    def run(self, cmd: list[str], timeout: float | None = None, env=None, cwd=None, capture: bool = False):
        cmd = _cap_workers(cmd, self.max_workers)
        kw = {"env": self._child_env(env), "cwd": cwd}
        if capture:
            kw["stdout"] = subprocess.PIPE
            kw["stderr"] = subprocess.PIPE
            kw["text"] = True
        if not IS_WIN:
            kw["start_new_session"] = True
        proc = subprocess.Popen(cmd, **kw)
        job = _win_job_object()
        if job and IS_WIN:
            ctypes.windll.kernel32.AssignProcessToJobObject(job, int(proc._handle))
        try:
            out, err = proc.communicate(timeout=timeout)
            return subprocess.CompletedProcess(cmd, proc.returncode, out, err)
        except subprocess.TimeoutExpired:
            if not IS_WIN:
                try:
                    os.killpg(proc.pid, signal.SIGKILL)
                except OSError:
                    proc.kill()
            else:
                proc.kill()
            proc.wait()
            raise
        finally:
            if job and IS_WIN:
                ctypes.windll.kernel32.CloseHandle(job)

    def __exit__(self, *_):
        if self.inherited:
            return
        if self.who_path and os.path.exists(self.who_path):
            try:
                os.remove(self.who_path)
            except OSError:
                pass
        if self.fd is not None:
            _unlock(self.fd)
            self.fd = None


def slot(kind: str = "web", lane: str = "", **kw) -> Slot:
    return Slot(kind=kind, lane=lane, **kw)


def show_status() -> int:
    print(f"Queue dir: {root()}  |  Free RAM: {free_ram_gb():.1f} GB")
    for kind in KINDS:
        kdir = kind_dir(kind)
        print(f"  [{kind}] slots={slot_count(kind)}, floor={KINDS[kind]['min_free_gb']} GB")
        for sname in slot_names(kind):
            lpath = os.path.join(kdir, f"{sname}.lock")
            wpath = os.path.join(kdir, f"{sname}.who")
            fd = _lock(lpath) if os.path.exists(lpath) else -1
            if fd is None:
                info = {}
                try:
                    info = json.loads(open(wpath, encoding="utf-8").read())
                except Exception:
                    pass
                print(f"    {sname}: BUSY  lane={info.get('lane','?')} pid={info.get('pid','?')} since={info.get('since','?')}")
            else:
                if fd != -1:
                    _unlock(fd)
                print(f"    {sname}: free")
        wdir = os.path.join(kdir, "wait")
        waiters = sorted(n for n in os.listdir(wdir) if n.endswith(".tk")) if os.path.isdir(wdir) else []
        if waiters:
            print(f"    waiting: {len(waiters)}")
    return 0


def main(argv: list[str]) -> int:
    if not argv or argv[0] in ("-h", "--help"):
        print(__doc__)
        return 0
    if argv[0] == "--status":
        return show_status()
    if "--" not in argv:
        sys.exit("run_queue.py: expected `-- <command ...>` (run with --help for usage)")
    sep = argv.index("--")
    opts, cmd = argv[:sep], argv[sep + 1 :]
    if not cmd:
        sys.exit("run_queue.py: missing command after `--`")
    kind = opts[0] if opts and not opts[0].startswith("-") else "web"
    rest = opts[1:] if opts and not opts[0].startswith("-") else opts
    lane, min_gb, max_w = os.path.basename(cmd[0]), None, MAX_WORKERS
    i = 0
    while i < len(rest):
        if rest[i] == "--lane" and i + 1 < len(rest):
            lane = rest[i + 1]; i += 2
        elif rest[i] == "--min-free-gb" and i + 1 < len(rest):
            min_gb = float(rest[i + 1]); i += 2
        elif rest[i] == "--max-workers" and i + 1 < len(rest):
            max_w = int(rest[i + 1]); i += 2
        else:
            sys.exit(f"run_queue.py: unknown option {rest[i]!r}")
    with slot(kind, lane=lane, min_free_gb=min_gb, max_workers=max_w) as s:
        _print(f"acquired {kind}/{s.slot_name} (lane={lane}, pid={os.getpid()})")
        res = s.run(cmd)
        return res.returncode


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
