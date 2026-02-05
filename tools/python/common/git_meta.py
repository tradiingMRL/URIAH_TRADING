import subprocess


def _git_cmd(args):
    try:
        return subprocess.check_output(
            ["git"] + args,
            stderr=subprocess.DEVNULL
        ).decode().strip()
    except Exception:
        return "UNKNOWN"


def git_metadata():
    return {
        "commit": _git_cmd(["rev-parse", "HEAD"]),
        "branch": _git_cmd(["rev-parse", "--abbrev-ref", "HEAD"]),
        "dirty": bool(_git_cmd(["status", "--porcelain"]))
    }