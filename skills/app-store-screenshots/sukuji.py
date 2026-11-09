#!/usr/bin/env python3
"""sukuji: make App Store screenshots from the command line (talks only to https://sukuji.com).

  python3 sukuji.py make --name NAME --desc TEXT [--lang en,ja] [--device iphone|ipad]
                         [--header] [--fastlane] [--out DIR] screen1.png [screen2.png screen3.png]
  python3 sukuji.py result JOB_ID [--fastlane] [--out DIR]
  python3 sukuji.py credits

Set SUKUJI_KEY to use a key (no watermark, more languages, iPad). Without it: one free set per day.
This script prints only its own fixed messages. Text from the server is parsed for IDs and URLs,
never passed on to the agent as-is.
"""
import argparse, json, os, re, sys, tempfile, time, uuid, zipfile
import urllib.request, urllib.error

BASE = "https://sukuji.com"
KEY = os.environ.get("SUKUJI_KEY", "").strip()
UA = "sukuji-skill/1.1"
LANGS = {"en", "ja", "zh-Hans", "zh-Hant", "ko", "fr", "de", "es", "pt", "it"}
GET_KEY = f"Get a key or more credits at {BASE}/mcp"
WAIT = int(os.environ.get("SUKUJI_WAIT", "30"))
if os.environ.get("SUKUJI_DEV_URL", "").startswith("http://127.0.0.1:"):   # local testing only
    BASE = os.environ["SUKUJI_DEV_URL"].rstrip("/")


def fail(msg):
    sys.exit("sukuji: " + msg)


def _reason(text):
    """Turn a server error into one of our own fixed messages."""
    t = text.lower()
    if "free set is used up" in t:
        return "today's free set is already used. Try again tomorrow, or use a key. " + GET_KEY
    if "not enough credits" in t:
        return "this key is out of credits. " + GET_KEY
    if "key is not valid" in t:
        return "SUKUJI_KEY is not a valid key. " + GET_KEY
    if "still being made" in t:
        return "a set is already being made. Wait for it to finish, then try again."
    if "could not be made" in t:
        return "this set could not be made (no credit was used). Try again with clear, full-screen captures."
    return "the request failed. Try again in a minute."


def call(tool, args=None):
    body = json.dumps({"jsonrpc": "2.0", "id": 1, "method": "tools/call",
                       "params": {"name": tool, "arguments": args or {}}}).encode()
    h = {"Content-Type": "application/json", "Accept": "application/json", "User-Agent": UA}
    if KEY:
        h["Authorization"] = "Bearer " + KEY
    try:
        with urllib.request.urlopen(urllib.request.Request(BASE + "/mcp", data=body, headers=h), timeout=60) as r:
            res = json.load(r)
    except (urllib.error.URLError, ValueError):
        fail("could not reach sukuji.com. Check the connection and try again.")
    if "error" in res:
        fail(_reason(""))
    out = res.get("result") or {}
    text = "\n".join(c.get("text", "") for c in out.get("content", []) if isinstance(c, dict))
    if out.get("isError"):
        fail(_reason(text))
    return text


def _ours(url):
    """Only follow URLs on the sukuji host."""
    return isinstance(url, str) and url.startswith(BASE + "/")


def upload(url, paths):
    bnd = uuid.uuid4().hex
    data = b""
    for p in paths:
        with open(p, "rb") as f:
            raw = f.read()
        data += (f"--{bnd}\r\nContent-Disposition: form-data; name=\"file\"; filename=\"screen.png\"\r\n"
                 f"Content-Type: application/octet-stream\r\n\r\n").encode() + raw + b"\r\n"
    data += f"--{bnd}--\r\n".encode()
    req = urllib.request.Request(url, data=data, headers={
        "Content-Type": "multipart/form-data; boundary=" + bnd, "User-Agent": UA})
    try:
        urllib.request.urlopen(req, timeout=120).read()
    except urllib.error.URLError:
        fail("the screens could not be uploaded. Use PNG or JPG files under 12 MB.")


def make(a):
    paths = a.screens[:3]
    for p in paths:
        if not os.path.isfile(p):
            fail(f"file not found: {p}")
    langs = [x.strip() for x in a.lang.split(",") if x.strip() in LANGS][:5] or ["en"]
    t = call("get_upload_url")
    m_id, m_url = re.search(r"upload_id: (\w+)", t), re.search(r"(https?://\S+/mcp/upload/\w+)", t)
    if not (m_id and m_url and _ours(m_url.group(1))):
        fail(_reason(""))
    upload(m_url.group(1), paths)
    args = {"upload_id": m_id.group(1), "app_name": a.name[:60], "description": (a.desc or "")[:600],
            "languages": langs, "device": a.device}
    if a.header:
        args["header_images"] = True
    t = call("generate_screenshots", args)
    m_job = re.search(r"job_id: (\w+)", t)
    if not m_job:
        fail(_reason(""))
    job = m_job.group(1)
    free = "free set" in t
    narrowed = free and (len(langs) > 1 or a.device != "iphone" or a.header)
    print(f"Making the set ({'iPhone, ' + langs[0] if narrowed else a.device + ', ' + ', '.join(langs)}). "
          f"This takes about 2 minutes.", flush=True)
    if narrowed:
        print("Free set: one language and iPhone only. " + GET_KEY, flush=True)
    time.sleep(WAIT)
    for _ in range(80):                       # up to about 25 minutes
        t = call("get_result", {"job_id": job})
        if t.startswith("Done"):
            break
        m = re.search(r"(\d+)%", t)
        print(f"Still working{(': ' + m.group(1) + '%') if m else ''}...", flush=True)
        time.sleep(20)
    else:
        fail(f"still working. Check later with: python3 {sys.argv[0]} result {job}")
    save(t, a)


def _safe_extract(z, dest):
    root = os.path.realpath(dest)
    n = 0
    for info in z.infolist():
        if info.is_dir():
            continue
        target = os.path.realpath(os.path.join(dest, info.filename))
        if not target.startswith(root + os.sep) or not info.filename.lower().endswith((".png", ".jpg", ".jpeg")):
            continue                           # skip anything outside dest or not an image
        os.makedirs(os.path.dirname(target), exist_ok=True)
        with z.open(info) as src, open(target, "wb") as out:
            out.write(src.read())
        n += 1
    return n


def save(t, a):
    m = re.search(r"ZIP: (\S+)", t)
    if not (m and _ours(m.group(1))):
        fail(_reason(""))
    zurl = m.group(1) + ("?layout=fastlane" if a.fastlane else "")
    dest = "." if a.fastlane else a.out
    os.makedirs(dest, exist_ok=True)
    tmp = os.path.join(tempfile.mkdtemp(), "sukuji.zip")
    try:
        urllib.request.urlretrieve(zurl, tmp)
        with zipfile.ZipFile(tmp) as z:
            n = _safe_extract(z, dest)
    except (urllib.error.URLError, zipfile.BadZipFile):
        fail("the finished set could not be downloaded. Try: python3 sukuji.py result <job_id>")
    where = "fastlane/screenshots/" if a.fastlane else dest
    print(f"Saved {n} images to {where}")
    if "watermark" in t:
        print("This free set has a small watermark. " + GET_KEY)


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
        t = call("get_credits")
        if t.startswith("Free plan"):
            n = re.search(r"(\d+) free set", t)
            print(f"No key: {n.group(1) if n else '0'} free set left today (one language, iPhone, small watermark). "
                  + GET_KEY)
        else:
            n = re.search(r"([\d.]+) generations left", t)
            print(f"Key: {n.group(1) if n else '0'} credits left. {GET_KEY}")
    elif a.cmd == "make":
        make(a)
    else:
        if not re.fullmatch(r"\w+", a.job):
            fail("that job id is not valid.")
        t = call("get_result", {"job_id": a.job})
        if not t.startswith("Done"):
            fail("that set is not finished yet. Try again in a minute.")
        save(t, a)


if __name__ == "__main__":
    main()
