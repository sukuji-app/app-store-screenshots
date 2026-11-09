#!/usr/bin/env python3
"""sukuji: make App Store screenshots from the command line (talks to https://sukuji.com/mcp).

  python3 sukuji.py make --name NAME --desc TEXT [--lang en,ja] [--device iphone|ipad]
                         [--header] [--fastlane] [--out DIR] screen1.png [screen2.png screen3.png]
  python3 sukuji.py credits

Set SUKUJI_KEY to use a key (no watermark, more languages, iPad). Without it: one free set per day.
"""
import argparse, json, os, re, sys, tempfile, time, uuid, zipfile
import urllib.request, urllib.error

BASE = os.environ.get("SUKUJI_URL", "https://sukuji.com").rstrip("/")
KEY = os.environ.get("SUKUJI_KEY", "").strip()
UA = "sukuji-skill/1.0"


def call(tool, args=None):
    body = json.dumps({"jsonrpc": "2.0", "id": 1, "method": "tools/call",
                       "params": {"name": tool, "arguments": args or {}}}).encode()
    h = {"Content-Type": "application/json", "Accept": "application/json", "User-Agent": UA}
    if KEY:
        h["Authorization"] = "Bearer " + KEY
    req = urllib.request.Request(BASE + "/mcp", data=body, headers=h)
    with urllib.request.urlopen(req, timeout=60) as r:
        res = json.load(r)
    if "error" in res:
        sys.exit("sukuji: " + res["error"].get("message", "error"))
    out = res["result"]
    text = "\n".join(c.get("text", "") for c in out.get("content", []))
    if out.get("isError"):
        sys.exit("sukuji: " + text)
    return text


def upload(url, paths):
    bnd = uuid.uuid4().hex
    data = b""
    for p in paths:
        with open(p, "rb") as f:
            raw = f.read()
        data += (f"--{bnd}\r\nContent-Disposition: form-data; name=\"file\"; filename=\"{os.path.basename(p)}\"\r\n"
                 f"Content-Type: application/octet-stream\r\n\r\n").encode() + raw + b"\r\n"
    data += f"--{bnd}--\r\n".encode()
    req = urllib.request.Request(url, data=data, headers={
        "Content-Type": "multipart/form-data; boundary=" + bnd, "User-Agent": UA})
    try:
        urllib.request.urlopen(req, timeout=120).read()
    except urllib.error.HTTPError as e:
        sys.exit("sukuji: upload failed: " + e.read().decode(errors="replace"))


def make(a):
    paths = a.screens[:3]
    for p in paths:
        if not os.path.isfile(p):
            sys.exit(f"sukuji: not found: {p}")
    t = call("get_upload_url")
    uid = re.search(r"upload_id: (\w+)", t).group(1)
    upload(re.search(r"(https?://\S+/mcp/upload/\w+)", t).group(1), paths)
    args = {"upload_id": uid, "app_name": a.name, "description": a.desc or "",
            "languages": [x.strip() for x in a.lang.split(",") if x.strip()], "device": a.device}
    if a.header:
        args["header_images"] = True
    t = call("generate_screenshots", args)
    job = re.search(r"job_id: (\w+)", t).group(1)
    line = t.split("\n", 1)[-1]
    head, _, rest = line.partition(" Call get_result")
    note = rest.split("until it is done.", 1)[-1].strip() if rest else ""
    print(head + " Making the set, about 2 minutes...", flush=True)
    if note:
        print(note, flush=True)
    time.sleep(int(os.environ.get("SUKUJI_WAIT","30")))
    for _ in range(80):                       # up to about 25 minutes
        t = call("get_result", {"job_id": job})
        if t.startswith("Done"):
            break
        print(t.splitlines()[0], flush=True)
        time.sleep(20)
    else:
        sys.exit(f"sukuji: still working. Check later with: python3 {sys.argv[0]} result {job}")
    save(t, a)


def save(t, a):
    zurl = re.search(r"ZIP: (\S+)", t).group(1) + ("?layout=fastlane" if a.fastlane else "")
    dest = "." if a.fastlane else a.out
    os.makedirs(dest, exist_ok=True)
    tmp = os.path.join(tempfile.mkdtemp(), "sukuji.zip")
    urllib.request.urlretrieve(zurl, tmp)
    with zipfile.ZipFile(tmp) as z:
        z.extractall(dest)
        names = [n for n in z.namelist() if not n.endswith("/")]
    note = re.search(r"\n\n(This free set[^\n]*)", t)
    where = "fastlane/screenshots/" if a.fastlane else dest
    print(f"Saved {len(names)} files to {where}")
    if note:
        print(note.group(1))


def main():
    ap = argparse.ArgumentParser(prog="sukuji")
    sp = ap.add_subparsers(dest="cmd", required=True)
    m = sp.add_parser("make")
    m.add_argument("--name", required=True)
    m.add_argument("--desc", default="")
    m.add_argument("--lang", default="en")
    m.add_argument("--device", choices=["iphone", "ipad"], default="iphone")
    m.add_argument("--header", action="store_true")
    m.add_argument("--fastlane", action="store_true")
    m.add_argument("--out", default="appstore-screenshots")
    m.add_argument("screens", nargs="+")
    r = sp.add_parser("result")
    r.add_argument("job")
    r.add_argument("--fastlane", action="store_true")
    r.add_argument("--out", default="appstore-screenshots")
    sp.add_parser("credits")
    a = ap.parse_args()
    if a.cmd == "credits":
        print(call("get_credits"))
    elif a.cmd == "make":
        make(a)
    else:
        t = call("get_result", {"job_id": a.job})
        if not t.startswith("Done"):
            sys.exit(t)
        save(t, a)


if __name__ == "__main__":
    main()
