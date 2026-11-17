#!/usr/bin/env python3
"""生成主页统计卡片 SVG（Stats / Top-Langs / Pin）。替代 github-readme-stats 的公共实例。"""
import os, json, pathlib
import requests

LOGIN = os.environ.get("GH_LOGIN", "qianqianhhh3")
TOK = os.environ["GH_TOKEN"]
H = {"Authorization": f"Bearer {TOK}", "Accept": "application/vnd.github+json", "User-Agent": "stats-bot"}
API = "https://api.github.com"

BG, BORDER, TITLE, LABEL, VAL = "#1a1b27", "#2f334d", "#7aa2f7", "#a9b1d6", "#7aa2f7"
FONT = "'Segoe UI',Ubuntu,'Helvetica Neue',sans-serif"


def esc(s):
    return (str(s or "")).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;")


def txt(x, y, s, size, fill, weight=400, anchor="start"):
    return (f'<text x="{x}" y="{y}" font-family="{FONT}" font-size="{size}" '
            f'font-weight="{weight}" fill="{fill}" text-anchor="{anchor}">{esc(s)}</text>')


def dot(x, y, c="#bb9af7"):
    return f'<circle cx="{x}" cy="{y}" r="3.5" fill="{c}"/>'


def head(w, h):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" '
            f'viewBox="0 0 {w} {h}" fill="none">'
            f'<rect x="0.5" y="0.5" rx="6" width="{w-1}" height="{h-1}" fill="{BG}" stroke="{BORDER}"/>')


def fmt(n):
    return f"{n:,}" if n < 1000 else (f"{n/1000:.1f}k" if n < 1e6 else f"{n/1e6:.1f}M")


def get(url, **kw):
    try:
        return requests.get(url, headers=H, timeout=25, **kw).json()
    except Exception:
        return {}


def collect():
    repos, page = [], 1
    while page <= 5:
        d = get(f"{API}/user/repos?affiliation=owner&per_page=100&page={page}")
        if not isinstance(d, list) or not d:
            break
        repos += d
        if len(d) < 100:
            break
        page += 1
    user = get(f"{API}/users/{LOGIN}")

    def search(kind, q):
        ep = "commits" if kind == "commits" else "issues"
        hh = dict(H)
        if kind == "commits":
            hh["Accept"] = "application/vnd.github.cloak-preview+json"
        try:
            r = requests.get(f"{API}/search/{ep}", headers=hh, params={"q": q, "per_page": 1}, timeout=25)
            return r.json().get("total_count", 0) if r.status_code == 200 else 0
        except Exception:
            return 0

    lang = {}
    for x in repos:
        if x.get("fork"):
            continue
        for k, v in (get(f"{API}/repos/{LOGIN}/{x['name']}/languages") or {}).items():
            lang[k] = lang.get(k, 0) + v

    return {
        "login": LOGIN,
        "public_repos": user.get("public_repos", len(repos)),
        "followers": user.get("followers", 0),
        "stars": sum(x.get("stargazers_count", 0) for x in repos),
        "forks": sum(x.get("forks_count", 0) for x in repos),
        "commits": search("commits", f"author:{LOGIN}"),
        "prs": search("issues", f"author:{LOGIN} type:pr"),
        "issues": search("issues", f"author:{LOGIN} type:issue"),
        "lang": lang,
        "repos": [{"name": x["name"], "desc": x.get("description"), "lang": x.get("language"),
                   "star": x.get("stargazers_count", 0)} for x in repos],
    }


def stats_svg(d):
    items = [("Total Stars", fmt(d["stars"])), ("Total Commits", fmt(d["commits"])),
             ("Total PRs", fmt(d["prs"])), ("Total Issues", fmt(d["issues"])),
             ("Followers", fmt(d["followers"])), ("Public Repos", fmt(d["public_repos"]))]
    W, Hh = 495, 195
    s = [head(W, Hh), txt(28, 38, f"{d['login']}\u2019s GitHub Stats", 18, TITLE, 600),
         f'<line x1="28" y1="52" x2="{W-28}" y2="52" stroke="{BORDER}"/>']
    for i, (label, val) in enumerate(items):
        x = 40 + (i % 2) * 232
        y = 82 + (i // 2) * 38
        s += [dot(x, y - 4), txt(x + 14, y, label, 13, LABEL), txt(x + 122, y, val, 13, VAL, 700)]
    s.append("</svg>")
    return "".join(s)


COLORS = {"Kotlin": "#A97BFF", "GLSL": "#5686A5", "Java": "#B07219", "Python": "#3572A5",
          "JavaScript": "#F1E05A", "TypeScript": "#3178C6", "Astro": "#ff5a03", "Kotlin/JS": "#A97BFF"}


def lang_svg(d):
    total = sum(d["lang"].values()) or 1
    W, Hh = 495, 195
    s = [head(W, Hh), txt(28, 38, "Most Used Languages", 18, TITLE, 600),
         f'<line x1="28" y1="52" x2="{W-28}" y2="52" stroke="{BORDER}"/>']
    y = 78
    for name, byte in sorted(d["lang"].items(), key=lambda k: -k[1])[:5]:
        pct = byte / total * 100
        c = COLORS.get(name, "#8b949e")
        s += [dot(40, y - 4, c), txt(54, y, name, 13, LABEL), txt(457, y, f"{pct:.1f}%", 13, VAL, 700, "end"),
              f'<rect x="54" y="{y+6}" rx="3" width="383" height="7" fill="{BORDER}"/>',
              f'<rect x="54" y="{y+6}" rx="3" width="{max(4, pct/100*383):.1f}" height="7" fill="{c}"/>']
        y += 38
    s.append("</svg>")
    return "".join(s)


def pin_svg(d, name="jianyin"):
    repo = next((x for x in d["repos"] if x["name"] == name), {"name": name, "desc": "", "lang": "", "star": 0})
    W, Hh = 495, 128
    return "".join([
        head(W, Hh), txt(28, 38, repo["name"], 18, TITLE, 700),
        txt(28, 64, repo["desc"] or "No description", 12.5, LABEL),
        txt(28, 88, "Android 全平台音乐播放器", 12, "#7dcfff"),
        dot(34, 110, "#A97BFF"), txt(46, 114, repo["lang"] or "Text", 12, LABEL),
        txt(140, 114, "\u2605", 13, "#e0af68"), txt(158, 114, str(repo["star"]), 12, LABEL),
        txt(200, 114, "Forks", 12, LABEL), txt(240, 114, str(d["forks"]), 12, LABEL),
        f'<path d="M{W-46} 28 l7 7 7-7" stroke="{TITLE}" stroke-width="2" fill="none" '
        f'stroke-linecap="round" stroke-linejoin="round"/>',
        "</svg>"])


if __name__ == "__main__":
    d = collect()
    out = pathlib.Path(os.environ.get("OUT_DIR", "out"))
    out.mkdir(exist_ok=True)
    (out / "stats.svg").write_text(stats_svg(d), encoding="utf-8")
    (out / "top-langs.svg").write_text(lang_svg(d), encoding="utf-8")
    (out / "pin-jianyin.svg").write_text(pin_svg(d), encoding="utf-8")
    print(json.dumps({k: v for k, v in d.items() if k != "repos"}, ensure_ascii=False))
