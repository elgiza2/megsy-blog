#!/usr/bin/env python3
"""Megsy Blog — static site generator (Markdown -> HTML, brand-styled, SEO-ready)."""
import os, re, glob, html, datetime, json

ROOT = os.path.dirname(os.path.abspath(__file__))
CONTENT = os.path.join(ROOT, "content")
OUT = os.path.join(ROOT, "public")
SITE = "https://elgiza2.github.io/megsy-blog"
BRAND = "Megsy"

CSS = """
:root{--blue:#2D6CFF;--sky:#7EB6EE;--ink:#0A0A0A;--parch:#F7F9FC;--gold:#E0B25A;--slate:#6B7A90;--line:#E4EAF2}
*{margin:0;padding:0;box-sizing:border-box}
body{background:var(--ink);color:var(--parch);font-family:Inter,-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;line-height:1.65;-webkit-font-smoothing:antialiased}
a{color:var(--sky);text-decoration:none}a:hover{color:var(--blue)}
.wrap{max-width:760px;margin:0 auto;padding:0 24px}
header.site{border-bottom:1px solid #1c1c1f;padding:22px 0;position:sticky;top:0;background:rgba(10,10,10,.92);backdrop-filter:blur(10px);z-index:9}
header.site .wrap{display:flex;align-items:center;gap:12px}
.logo{width:11px;height:11px;border-radius:50%;background:var(--blue);box-shadow:0 0 22px rgba(45,108,255,.85)}
.brand{font-family:'Instrument Serif',Georgia,serif;font-size:23px;letter-spacing:.01em}
.brand span{color:var(--slate);font-size:14px;font-family:Inter,sans-serif;letter-spacing:.14em;text-transform:uppercase;margin-left:10px}
header.site nav{margin-left:auto;font-size:14px}
.hero{padding:72px 0 40px}
.hero h1{font-family:'Instrument Serif',Georgia,serif;font-size:clamp(38px,6vw,60px);line-height:1.05;font-weight:400;letter-spacing:-.015em}
.hero p{color:#9FB0C6;font-size:19px;margin-top:18px;max-width:600px}
.tagline{display:inline-block;font-size:12px;letter-spacing:.18em;text-transform:uppercase;color:var(--gold);border:1px solid rgba(224,178,90,.45);border-radius:100px;padding:6px 16px;margin-bottom:22px}
ul.posts{list-style:none;padding-bottom:80px}
ul.posts li{border-top:1px solid #1c1c1f;padding:30px 0}
ul.posts time{font-size:13px;color:var(--slate);letter-spacing:.05em}
ul.posts h2{font-family:'Instrument Serif',Georgia,serif;font-size:30px;font-weight:400;margin:8px 0 10px;line-height:1.2}
ul.posts h2 a{color:var(--parch)}ul.posts h2 a:hover{color:var(--sky)}
ul.posts p{color:#9FB0C6;font-size:16px}
article{padding:60px 0 90px}
article h1{font-family:'Instrument Serif',Georgia,serif;font-size:clamp(34px,5.2vw,50px);line-height:1.1;font-weight:400;margin-bottom:14px}
article .meta{color:var(--slate);font-size:14px;margin-bottom:36px}
article h2{font-family:'Instrument Serif',Georgia,serif;font-size:29px;font-weight:400;margin:44px 0 14px}
article h3{font-size:20px;margin:32px 0 10px}
article p{margin:16px 0;font-size:18px;color:#E7EDF5}
article ul,article ol{margin:16px 0 16px 26px;color:#E7EDF5;font-size:18px}
article li{margin:8px 0}
article blockquote{border-left:3px solid var(--blue);padding:6px 0 6px 20px;margin:24px 0;color:#9FB0C6;font-style:italic}
article code{background:#161616;border:1px solid #232323;border-radius:5px;padding:2px 6px;font-size:15px}
article pre{background:#121212;border:1px solid #232323;border-radius:12px;padding:18px;overflow:auto;margin:22px 0}
article pre code{border:0;padding:0}
article strong{color:#fff}
article hr{border:0;border-top:1px solid #1c1c1f;margin:40px 0}
.cta{margin:52px 0 0;padding:32px;border:1px solid rgba(45,108,255,.35);border-radius:18px;background:linear-gradient(160deg,rgba(45,108,255,.12),rgba(10,10,10,0))}
.cta h3{font-family:'Instrument Serif',Georgia,serif;font-size:26px;font-weight:400;margin:0 0 10px}
.cta p{color:#9FB0C6;margin:0 0 18px}
.btn{display:inline-block;background:var(--blue);color:#fff;padding:12px 24px;border-radius:100px;font-weight:600;font-size:15px}
.btn:hover{background:#4a80ff;color:#fff}
footer{border-top:1px solid #1c1c1f;padding:34px 0;color:var(--slate);font-size:14px}
footer a{color:var(--slate)}
@media(max-width:600px){.hero{padding:48px 0 24px}article{padding:36px 0 60px}}
"""

FONTS = ("<link rel='preconnect' href='https://fonts.googleapis.com'>"
         "<link rel='preconnect' href='https://fonts.gstatic.com' crossorigin>"
         "<link href='https://fonts.googleapis.com/css2?family=Instrument+Serif:ital@0;1&family=Inter:wght@400;600;700&display=swap' rel='stylesheet'>")

CTA = """<div class="cta"><h3>One calm place for all your work</h3>
<p>Megsy is an AI agent workspace: chat, deep research, images, video, slides, browser tasks and coding agents in one place. First month 7 dollars, then 20.</p>
<a class="btn" href="https://www.megsyai.com">Try Megsy free &rarr;</a></div>"""


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
    meta.setdefault("date", datetime.date.today().isoformat())
    return meta


def md_to_html(md):
    out, in_code = [], False
    for block in md.split("\n"):
        if block.startswith("```"):
            out.append("</code></pre>" if in_code else "<pre><code>")
            in_code = not in_code
            continue
        if in_code:
            out.append(html.escape(block))
            continue
        line = block
        if not line.strip():
            out.append("")
            continue
        esc = html.escape(line)
        esc = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", esc)
        esc = re.sub(r"\*(.+?)\*", r"<em>\1</em>", esc)
        esc = re.sub(r"\[(.+?)\]\((https?://[^\s)]+)\)", r'<a href="\2">\1</a>', esc)
        esc = re.sub(r"`(.+?)`", r"<code>\1</code>", esc)
        if esc.startswith("### "):
            out.append("<h3>" + esc[4:] + "</h3>")
        elif esc.startswith("## "):
            out.append("<h2>" + esc[3:] + "</h2>")
        elif esc.startswith("# "):
            out.append("<h2>" + esc[2:] + "</h2>")
        elif esc.startswith("> "):
            out.append("<blockquote>" + esc[2:] + "</blockquote>")
        elif esc.startswith("- ") or esc.startswith("* "):
            out.append("<li>" + esc[2:] + "</li>")
        elif esc.strip() == "---":
            out.append("<hr>")
        else:
            out.append("<p>" + esc + "</p>")
    html_out = "\n".join(out)
    html_out = re.sub(r"(<li>.*?</li>\n?)+", lambda m: "<ul>" + m.group(0) + "</ul>", html_out, flags=re.S)
    return html_out


def page(title, desc, body, canonical, base="", extra_head=""):
    return f"""<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{html.escape(title)}</title>
<meta name="description" content="{html.escape(desc)}">
<link rel="canonical" href="{canonical}">
<meta property="og:type" content="article"><meta property="og:title" content="{html.escape(title)}">
<meta property="og:description" content="{html.escape(desc)}"><meta property="og:url" content="{canonical}">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="{html.escape(title)}"><meta name="twitter:description" content="{html.escape(desc)}">
<link rel="alternate" type="application/rss+xml" title="{BRAND} Blog" href="{SITE}/feed.xml">
{FONTS}<style>{CSS}</style>{extra_head}</head><body>
<header class="site"><div class="wrap"><span class="logo"></span>
<a class="brand" href="{base}index.html">{BRAND}<span>Blog</span></a>
<nav><a href="https://www.megsyai.com">megsyai.com &rarr;</a></nav></div></header>
{body}
<footer><div class="wrap">&copy; {datetime.date.today().year} {BRAND} &middot; <a href="https://www.megsyai.com">megsyai.com</a> &middot; <a href="{base}feed.xml">RSS</a> &middot; <a href="{base}sitemap.xml">Sitemap</a></div></footer>
</body></html>"""


def main():
    posts = sorted([parse(p) for p in glob.glob(os.path.join(CONTENT, "*.md"))],
                   key=lambda p: p["date"], reverse=True)
    os.makedirs(os.path.join(OUT, "posts"), exist_ok=True)

    items = []
    for p in posts:
        url = f"{SITE}/posts/{p['slug']}.html"
        art = f"""<article class="wrap"><h1>{html.escape(p.get('title',''))}</h1>
<div class="meta">{p['date']} &middot; {html.escape(p.get('tags',''))}</div>
{md_to_html(p['_body'])}
{CTA}</article>"""
        open(os.path.join(OUT, "posts", p["slug"] + ".html"), "w", encoding="utf-8").write(
            page(f"{p.get('title','')} — {BRAND}", p.get("description", ""), art, url, base="../"))
        items.append(f"""<li><time>{p['date']}</time>
<h2><a href="posts/{p['slug']}.html">{html.escape(p.get('title',''))}</a></h2>
<p>{html.escape(p.get('description',''))}</p></li>""")

    home = f"""<section class="hero"><div class="wrap"><span class="tagline">AI agents &amp; the future of work</span>
<h1>Notes on building an AI workspace that actually does the work.</h1>
<p>Practical writing on AI agents, automation, and shipping real products. New article every day.</p></div></section>
<ul class="posts wrap">{''.join(items)}</ul>"""
    open(os.path.join(OUT, "index.html"), "w", encoding="utf-8").write(
        page(f"{BRAND} Blog — AI agents and the future of work",
             "Daily writing on AI agents, automation and building products, from the team behind Megsy.",
             home, SITE + "/"))

    urls = [f"<url><loc>{SITE}/</loc></url>"] + [
        f"<url><loc>{SITE}/posts/{p['slug']}.html</loc><lastmod>{p['date']}</lastmod></url>" for p in posts]
    open(os.path.join(OUT, "sitemap.xml"), "w").write(
        '<?xml version="1.0" encoding="UTF-8"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'
        + "".join(urls) + "</urlset>")
    open(os.path.join(OUT, "robots.txt"), "w").write(f"User-agent: *\nAllow: /\nSitemap: {SITE}/sitemap.xml\n")

    rss = "".join(
        f"<item><title>{html.escape(p.get('title',''))}</title><link>{SITE}/posts/{p['slug']}.html</link>"
        f"<description>{html.escape(p.get('description',''))}</description><pubDate>{p['date']}</pubDate></item>"
        for p in posts)
    open(os.path.join(OUT, "feed.xml"), "w").write(
        f'<?xml version="1.0" encoding="UTF-8"?><rss version="2.0"><channel><title>{BRAND} Blog</title>'
        f"<link>{SITE}</link><description>Daily writing on AI agents and automation.</description>{rss}</channel></rss>")
    open(os.path.join(OUT, ".nojekyll"), "w").write("")
    print(f"built {len(posts)} posts -> {OUT}")


if __name__ == "__main__":
    main()
