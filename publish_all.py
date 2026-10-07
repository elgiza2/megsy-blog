#!/usr/bin/env python3
"""Publish every Megsy article to all captcha-free destinations:
   - telegra.ph  (no account, no captcha)
   - rentry.co   (no account, no captcha, markdown -> HTML page)
State kept in /home/ubuntu/.megsy_publish_state.json so re-runs never duplicate."""
import os, re, json, glob, http.cookiejar, urllib.request, urllib.parse

ROOT = os.path.dirname(os.path.abspath(__file__))
CONTENT = os.path.join(ROOT, "content")
STATE = "/home/ubuntu/.megsy_publish_state.json"
TG_STATE = "/home/ubuntu/.megsy_telegraph.json"
UA = {"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/120 Safari/537.36"}
CTA = "\n\n---\n\nOne calm place for all your work. Megsy is an AI agent workspace: chat, deep research, images, video, slides, browser tasks and coding agents. First month 7 dollars, then 20. Start free at https://www.megsyai.com"


def load(path, default):
    return json.load(open(path)) if os.path.exists(path) else default


def save(path, data, secret=False):
    json.dump(data, open(path, "w"), indent=1)
    if secret:
        os.chmod(path, 0o600)


def parse(path):
    raw = open(path, encoding="utf-8").read()
    meta, body = {}, raw
    m = re.match(r"^---\n(.*?)\n---\n(.*)$", raw, re.S)
    if m:
        for line in m.group(1).splitlines():
            if ":" in line:
                k, v = line.split(":", 1)
                meta[k.strip()] = v.strip().strip('"')
        body = m.group(2)
    meta["_body"] = body.strip()
    meta.setdefault("slug", os.path.basename(path)[:-3])
    return meta


# ---------- Telegraph ----------
def tg_nodes(md):
    nodes, bullets = [], []

    def flush():
        if bullets:
            nodes.append({"tag": "ul", "children": [{"tag": "li", "children": [b]} for b in bullets]})
            bullets.clear()

    for line in md.split("\n"):
        s = line.rstrip()
        if s.startswith("- ") or s.startswith("* "):
            bullets.append(s[2:])
            continue
        flush()
        if not s.strip():
            continue
        if s.strip() == "---":
            nodes.append({"tag": "hr"})
        elif s.startswith("### "):
            nodes.append({"tag": "h4", "children": [s[4:]]})
        elif s.startswith("## ") or s.startswith("# "):
            nodes.append({"tag": "h3", "children": [s.lstrip("# ")]})
        elif s.startswith("> "):
            nodes.append({"tag": "blockquote", "children": [{"tag": "p", "children": [s[2:]]}]})
        else:
            nodes.append({"tag": "p", "children": [s]})
    flush()
    return nodes


def publish_telegraph(p, state):
    tg = load(TG_STATE, None)
    if tg is None:
        d = urllib.parse.urlencode({"short_name": "Megsy", "author_name": "Megsy AI"}).encode()
        r = json.loads(urllib.request.urlopen("https://api.telegra.ph/createAccount", data=d, timeout=30).read())
        tg = {"access_token": r["result"]["access_token"], "published": {}}
        save(TG_STATE, tg, secret=True)
    slug = p["slug"]
    if slug in tg["published"]:
        return tg["published"][slug]
    d = urllib.parse.urlencode({
        "access_token": tg["access_token"], "title": p.get("title", slug),
        "author_name": "Megsy AI", "content": json.dumps(tg_nodes(p["_body"] + CTA)),
        "return_content": "false"}).encode()
    r = json.loads(urllib.request.urlopen("https://api.telegra.ph/createPage", data=d, timeout=30).read())
    if r.get("ok"):
        url = r["result"]["url"]
        tg["published"][slug] = url
        save(TG_STATE, tg, secret=True)
        return url
    return None


# ---------- Rentry ----------
def publish_rentry(p, state):
    slug = p["slug"]
    if slug in state.get("rentry", {}):
        return state["rentry"][slug]
    cj = http.cookiejar.CookieJar()
    op = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj))
    page = op.open(urllib.request.Request("https://rentry.co", headers=UA), timeout=30).read().decode()
    m = re.search(r'name="csrfmiddlewaretoken" value="([^"]+)"', page)
    if not m:
        return None
    text = f"# {p.get('title', slug)}\n\n{p['_body']}{CTA}"
    data = urllib.parse.urlencode({"csrfmiddlewaretoken": m.group(1), "url": slug,
                                   "edit_code": "megsy2026", "text": text}).encode()
    h = dict(UA)
    h.update({"Referer": "https://rentry.co", "Content-Type": "application/x-www-form-urlencoded"})
    r = json.loads(op.open(urllib.request.Request("https://rentry.co/api/new", data=data, headers=h), timeout=30).read())
    if r.get("status") == "200":
        state.setdefault("rentry", {})[slug] = r["url"]
        save(STATE, state)
        return r["url"]
    return None


def main():
    state = load(STATE, {})
    for f in sorted(glob.glob(os.path.join(CONTENT, "*.md"))):
        p = parse(f)
        try:
            t = publish_telegraph(p, state)
            print(("TELEGRAPH " + str(t)) if t else "TELEGRAPH failed", "|", p["slug"])
        except Exception as e:
            print("TELEGRAPH ERR", p["slug"], str(e)[:80])
        try:
            r = publish_rentry(p, state)
            print(("RENTRY    " + str(r)) if r else "RENTRY skipped", "|", p["slug"])
        except Exception as e:
            print("RENTRY ERR", p["slug"], str(e)[:80])
    print("\nstate:", json.dumps(state, indent=1))


if __name__ == "__main__":
    main()
