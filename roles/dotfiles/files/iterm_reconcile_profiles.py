#!/usr/bin/env python3
"""Retire hand-imported copies of the dotfiles iTerm2 profile.

The dotfiles default bundle installs ``iterm/Profiles.json`` as an iTerm2 *dynamic*
profile.  Machines bootstrapped before that existed had the same profile imported by
hand through the iTerm2 GUI, which leaves a regular saved profile carrying one of the
repo's GUIDs in ``com.googlecode.iterm2 › New Bookmarks``.  Such a profile shadows the
dynamic one (iTerm2 logs "Dynamic profile with Guid … conflicts with non-dynamic
profile with same Guid" at every launch when the GUIDs are equal) or simply lingers
as a duplicate once the dynamic GUID moved on.

Rules (mirroring amun's stock-dotfiles convention: remove ONLY what is provably
untouched):

* A candidate is a non-dynamic saved profile whose Guid appears in one of the repo
  payload files (``~/.dotfiles/iterm/*.json``).
* It is retired only when its content equals one of those payload profiles, ignoring
  identity/bookkeeping keys (Name, Guid, Tags, dynamic-profile markers).  A profile the
  user customised in the GUI is kept and reported so the changes can be ported to
  ``iterm/Profiles.json``.
* Retiring means deleting it — unless it is the last saved profile, in which case it is
  converted into the dynamic profile's bookmark (iTerm2 would otherwise create a stock
  "Default" profile at launch before loading dynamic profiles).  The GUID becomes the
  dynamic one, so the default-profile setting stays valid.
* Nothing is written while iTerm2 is running: it rewrites ``New Bookmarks`` from memory
  on save and would clobber the edit.  The run is reported as skipped and amun retries
  next time.

Preferences are read and written through ``defaults export/import`` (cfprefsd), never
by editing the plist file directly.  ``--plist/--out`` switch to plain file mode for
tests.  The last stdout line is ``result=<clean|changed|skipped-running|kept>``.
"""

import argparse
import datetime as _dt
import json
import os
import plistlib
import subprocess
import sys

KEY_BOOKMARKS = "New Bookmarks"
KEY_GUID = "Guid"
KEY_NAME = "Name"
KEY_IS_DYNAMIC = "Is Dynamic Profile"
KEY_DYNAMIC_FILENAME = "Dynamic Profile Filename"

# Identity and bookkeeping keys that legitimately differ between a saved copy and the
# payload file; everything else must match for a profile to count as untouched.
VOLATILE_KEYS = {
    KEY_GUID,
    KEY_NAME,
    "Tags",
    KEY_IS_DYNAMIC,
    KEY_DYNAMIC_FILENAME,
    "Dynamic Profile Parent Name",
    "Dynamic Profile Parent GUID",
    "Rewritable",
}


def log(msg):
    print(msg, flush=True)


def normalize(value):
    """Make plist values (real numbers, bools) comparable with JSON ones (strings)."""
    if isinstance(value, dict):
        return {k: normalize(v) for k, v in value.items()}
    if isinstance(value, list):
        return [normalize(v) for v in value]
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return round(float(value), 6)
    if isinstance(value, str):
        try:
            return round(float(value), 6)
        except ValueError:
            return value
    return value


def comparable(profile):
    return {k: normalize(v) for k, v in profile.items() if k not in VOLATILE_KEYS}


def differing_keys(a, b):
    ca, cb = comparable(a), comparable(b)
    return sorted(k for k in set(ca) | set(cb) if ca.get(k) != cb.get(k))


def load_payload_profiles(payload_dir):
    """Return [(filename, profile)] for every profile in the repo payload directory."""
    found = []
    if not os.path.isdir(payload_dir):
        return found
    for name in sorted(os.listdir(payload_dir)):
        if not name.endswith(".json"):
            continue
        path = os.path.join(payload_dir, name)
        try:
            with open(path, encoding="utf-8") as fh:
                data = json.load(fh)
        except (OSError, ValueError) as exc:
            log(f"warning: cannot read payload {path}: {exc}")
            continue
        profiles = data.get("Profiles", [data]) if isinstance(data, dict) else []
        for profile in profiles:
            if isinstance(profile, dict) and isinstance(profile.get(KEY_GUID), str):
                found.append((name, profile))
    return found


def is_dynamic(bookmark):
    return bool(bookmark.get(KEY_IS_DYNAMIC)) or bookmark.get(KEY_DYNAMIC_FILENAME) is not None


def iterm_running():
    checks = (
        ["pgrep", "-x", "iTerm2"],
        ["lsappinfo", "info", "-only", "pid", "-app", "com.googlecode.iterm2"],
    )
    for cmd in checks:
        try:
            out = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
        except (OSError, subprocess.TimeoutExpired):
            continue
        if out.returncode == 0 and out.stdout.strip():
            return True
    try:
        ps = subprocess.run(["ps", "-axo", "comm="], capture_output=True, text=True, timeout=10)
    except (OSError, subprocess.TimeoutExpired):
        return False
    return any(line.rstrip().endswith("/MacOS/iTerm2") for line in ps.stdout.splitlines())


def read_prefs(domain, plist_path):
    if plist_path:
        with open(plist_path, "rb") as fh:
            return plistlib.load(fh)
    out = subprocess.run(["defaults", "export", domain, "-"], capture_output=True, check=True)
    return plistlib.loads(out.stdout)


def write_prefs(prefs, domain, out_path, backup_dir):
    data = plistlib.dumps(prefs, fmt=plistlib.FMT_XML)
    if out_path:
        with open(out_path, "wb") as fh:
            fh.write(data)
        return
    os.makedirs(backup_dir, exist_ok=True)
    stamp = _dt.datetime.now().strftime("%Y%m%d-%H%M%S")
    backup = os.path.join(backup_dir, f"{domain}.{stamp}.plist")
    subprocess.run(["defaults", "export", domain, backup], check=True)
    log(f"backup: {backup}")
    subprocess.run(["defaults", "import", domain, "-"], input=data, check=True)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--dynamic-guid", required=True, help="Guid of the dynamic profile shipped by dotfiles")
    parser.add_argument("--dynamic-file", required=True, help="installed DynamicProfiles/*.json path")
    parser.add_argument("--payload-dir", required=True, help="repo iterm/ directory with the pristine payload files")
    parser.add_argument("--domain", default="com.googlecode.iterm2")
    parser.add_argument("--backup-dir", default=os.path.expanduser("~/Library/Application Support/iTerm2/amun-prefs-backups"))
    parser.add_argument("--plist", help="test mode: read preferences from this plist file instead of defaults")
    parser.add_argument("--out", help="test mode: write the result to this file instead of defaults import")
    args = parser.parse_args(argv)
    file_mode = bool(args.plist or args.out)
    if file_mode and not (args.plist and args.out):
        parser.error("--plist and --out must be given together")

    payload = load_payload_profiles(args.payload_dir)
    payload_guids = {p[KEY_GUID] for _, p in payload}
    if not payload:
        log(f"no payload profiles under {args.payload_dir}; nothing to reconcile")
        log("result=clean")
        return 0

    prefs = read_prefs(args.domain, args.plist)
    bookmarks = prefs.get(KEY_BOOKMARKS)
    if not isinstance(bookmarks, list) or not bookmarks:
        log("result=clean")
        return 0

    candidates = [b for b in bookmarks if isinstance(b, dict) and not is_dynamic(b) and b.get(KEY_GUID) in payload_guids]
    if not candidates:
        log("result=clean")
        return 0

    retire, keep = [], []
    for bookmark in candidates:
        matches = [name for name, profile in payload if not differing_keys(bookmark, profile)]
        if matches:
            retire.append((bookmark, matches[0]))
        else:
            closest = min(payload, key=lambda item: len(differing_keys(bookmark, item[1])))
            keep.append((bookmark, closest[0], differing_keys(bookmark, closest[1])))

    for bookmark, name, keys in keep:
        log(
            f"kept: saved profile '{bookmark.get(KEY_NAME)}' ({bookmark.get(KEY_GUID)}) is a hand import of "
            f"{name} but was customised in iTerm2 (differs in: {', '.join(keys)}); port the changes to "
            "dotfiles iterm/Profiles.json and delete the saved profile in iTerm2 > Settings > Profiles"
        )
    if not retire:
        log("result=kept")
        return 0

    for bookmark, name in retire:
        log(f"untouched hand import of {name}: '{bookmark.get(KEY_NAME)}' ({bookmark.get(KEY_GUID)})")

    if not file_mode and iterm_running():
        log("iTerm2 is running; leaving its preferences alone (amun retries while it is closed)")
        log("result=skipped-running")
        return 0

    remaining = [b for b in bookmarks if not any(b is r for r, _ in retire)]
    if remaining:
        for bookmark, _ in retire:
            log(f"removing '{bookmark.get(KEY_NAME)}' ({bookmark.get(KEY_GUID)})")
        prefs[KEY_BOOKMARKS] = remaining
    else:
        # Last saved profile: convert instead of delete so iTerm2 never fabricates a stock
        # "Default" profile ahead of loading the dynamic one.
        try:
            with open(args.dynamic_file, encoding="utf-8") as fh:
                dynamic = next(p for p in json.load(fh)["Profiles"] if p.get(KEY_GUID) == args.dynamic_guid)
        except (OSError, ValueError, StopIteration, KeyError):
            dynamic = next((p for _, p in payload if p.get(KEY_GUID) == args.dynamic_guid), None) or {}
        survivor = retire[-1][0]
        for bookmark, _ in retire[:-1]:
            log(f"removing '{bookmark.get(KEY_NAME)}' ({bookmark.get(KEY_GUID)})")
        log(
            f"converting '{survivor.get(KEY_NAME)}' ({survivor.get(KEY_GUID)}) into the dynamic profile "
            f"bookmark {args.dynamic_guid}"
        )
        survivor[KEY_GUID] = args.dynamic_guid
        survivor[KEY_IS_DYNAMIC] = True
        survivor[KEY_DYNAMIC_FILENAME] = args.dynamic_file
        if dynamic.get(KEY_NAME):
            survivor[KEY_NAME] = dynamic[KEY_NAME]
        prefs[KEY_BOOKMARKS] = [survivor]

    write_prefs(prefs, args.domain, args.out, args.backup_dir)
    log("result=changed")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except subprocess.CalledProcessError as exc:
        log(f"error: {' '.join(exc.cmd)} failed with exit {exc.returncode}: {(exc.stderr or b'').decode(errors='replace') if isinstance(exc.stderr, bytes) else exc.stderr}")
        sys.exit(1)
