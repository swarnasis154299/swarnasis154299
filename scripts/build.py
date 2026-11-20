"""Draws every graphic on the profile README as hand-built SVG.

Run locally or from the daily GitHub Action:
    python scripts/build.py
Set GITHUB_TOKEN to raise the API rate limit (the Action does this for you).
Edit PROFILE and MISSIONS below to change the text; nothing else needs touching.
"""
import json
import math
import os
import random
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from xml.sax.saxutils import escape

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "assets"

PROFILE = {
    "user": "swarnasis154299",
    "name": "Swarnasis Saha Roy",  # headline on the banner
    "role": "AI AUTOMATION BUILDER",
    "tagline": [
        "I build AI automations that do real work:",
        "voice agents, video pipelines and community bots.",
    ],
    "chips": ["AI AGENTS", "VOICE AI", "VIDEO PIPELINES", "DISCORD BOTS"],
    "status": "status: shipping new missions",
}

# Each repo is a planet. hue = its colour everywhere on the profile.
MISSIONS = [
    {
        "repo": "neon-space-explainer",
        "hue": "#c084fc", "hue2": "#f472b6", "ring": True,
        "lines": ["A Claude skill that turns one prompt into a neon",
                  "'What if...?' science reel, built entirely in code."],
        "tech": ["Claude Skill", "Remotion", "TypeScript", "Web Audio"],
    },
    {
        "repo": "sarvam-voice-agent",
        "hue": "#fbbf24", "hue2": "#fb7185", "ring": False,
        "lines": ["Real-time voice agent that listens, thinks and",
                  "speaks back in 11 Indian languages."],
        "tech": ["Sarvam AI", "LiveKit", "Python"], "lang": "Python",
    },
    {
        "repo": "quickclip",
        "hue": "#22d3ee", "hue2": "#818cf8", "ring": False,
        "lines": ["One long video in, a stack of frame-accurate",
                  "9:16 clips out, from a list of timestamps."],
        "tech": ["Python", "FFmpeg", "CLI"],
    },
    {
        "repo": "discord-calendar-bot",
        "hue": "#818cf8", "hue2": "#38bdf8", "ring": True,
        "lines": ["Puts your Zoom meeting on members' Google,",
                  "Outlook or Apple calendars in one click."],
        "tech": ["discord.py", "FastAPI", "OAuth", "ICS"],
    },
    {
        "repo": "discord-progress-bot",
        "hue": "#34d399", "hue2": "#a3e635", "ring": False,
        "lines": ["Walks members through a step-by-step program",
                  "and tracks everyone's progress on a dashboard."],
        "tech": ["discord.py", "Flask", "SQLite"],
    },
]

TOOLKIT = [
    ("LANGUAGES", "#22d3ee", ["Python", "TypeScript", "SQL"]),
    ("AI + VOICE", "#c084fc", ["Claude", "Sarvam AI", "LiveKit"]),
    ("MEDIA", "#f472b6", ["Remotion", "FFmpeg", "Web Audio"]),
    ("BACKEND", "#34d399", ["FastAPI", "Flask", "SQLite", "OAuth"]),
    ("SHIP", "#fbbf24", ["Docker", "Railway", "GitHub Actions"]),
]

SANS = "'Segoe UI', 'Helvetica Neue', Ubuntu, Arial, sans-serif"
MONO = "ui-monospace, SFMono-Regular, Consolas, 'Liberation Mono', Menlo, monospace"
BG0, BG1 = "#05060f", "#0d0b26"

LANG_COLORS = {"Python": "#3572A5", "TypeScript": "#3178c6", "JavaScript": "#f1e05a",
               "HTML": "#e34c26", "CSS": "#663399", "Shell": "#89e051", "Dockerfile": "#384d54"}


# ---------------------------------------------------------------- data

def api(path):
    req = urllib.request.Request("https://api.github.com" + path,
                                 headers={"Accept": "application/vnd.github+json",
                                          "User-Agent": "profile-telemetry"})
    tok = os.environ.get("GITHUB_TOKEN")
    if tok:
        req.add_header("Authorization", "Bearer " + tok)
    with urllib.request.urlopen(req, timeout=20) as r:
        return json.load(r)


def fetch_stats():
    u = PROFILE["user"]
    try:
        user = api(f"/users/{u}")
        repos = [r for r in api(f"/users/{u}/repos?per_page=100&type=owner") if not r["fork"]]
        langs = {}
        for r in repos:
            if r["name"] == u:
                continue
            for k, v in api(f"/repos/{u}/{r['name']}/languages").items():
                langs[k] = langs.get(k, 0) + v
        return {
            "repos": len([r for r in repos if r["name"] != u]),
            "stars": sum(r["stargazers_count"] for r in repos),
            "forks": sum(r["forks_count"] for r in repos),
            "followers": user["followers"],
            "created": user["created_at"],
            "per_repo": {r["name"]: (r["stargazers_count"], r["language"]) for r in repos},
            "langs": langs,
        }
    except Exception as e:  # offline: draw with zeros rather than fail
        print("stats unavailable:", e)
        return {"repos": len(MISSIONS), "stars": 0, "forks": 0, "followers": 0,
                "created": None, "per_repo": {}, "langs": {}}


# ---------------------------------------------------------------- helpers

def t(x, y, s, size, fill, font=SANS, weight=400, ls=0, anchor="start", extra=""):
    return (f'<text x="{x}" y="{y}" font-family="{font}" font-size="{size}" font-weight="{weight}" '
            f'fill="{fill}" letter-spacing="{ls}" text-anchor="{anchor}" {extra}>{escape(s)}</text>')


def text_w(s, size, mono=False):
    return len(s) * size * (0.61 if mono else 0.56)


def pill(x, y, label, color, size=12, mono=True, fill_op=0.12):
    w =text_w(label, size, mono) + size * 1.8 + len(label) * 1.2
    h = size * 2.1
    return (f'<rect x="{x:.1f}" y="{y:.1f}" width="{w:.1f}" height="{h:.1f}" rx="{h/2:.1f}" fill="{color}" '
            f'fill-opacity="{fill_op}" stroke="{color}" stroke-opacity=".55"/>'
            + t(x + w / 2, y + h * 0.68, label, size, color, MONO if mono else SANS, 600, 1.2, "middle")), w


def stars(rng, w, h, n, twinkle=True, cls="tw"):
    out = []
    for i in range(n):
        x, y = rng.uniform(0, w), rng.uniform(0, h)
        r = rng.choice([0.6, 0.8, 0.8, 1.0, 1.2, 1.6])
        op = rng.uniform(0.35, 0.95)
        c = rng.choice(["#ffffff", "#ffffff", "#c7d2fe", "#a5f3fc", "#f5d0fe"])
        anim = ""
        if twinkle and rng.random() < 0.45:
            anim = (f' class="{cls}" style="animation-duration:{rng.uniform(2.5, 6):.1f}s;'
                    f'animation-delay:{rng.uniform(0, 5):.1f}s"')
        out.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{r}" fill="{c}" opacity="{op:.2f}"{anim}/>')
    return "".join(out)


def svg(w, h, body, defs="", style=""):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}" '
            f'role="img">\n<defs>{defs}</defs>\n<style>{style}</style>\n{body}\n</svg>\n')


BASE_STYLE = """
.tw{animation-name:tw;animation-iteration-count:infinite;animation-timing-function:ease-in-out}
@keyframes tw{0%,100%{opacity:.15}50%{opacity:1}}
.blink{animation:bl 1.1s steps(1) infinite}@keyframes bl{50%{opacity:0}}
@media (prefers-reduced-motion: reduce){*{animation:none!important}}
"""


def planet(cx, cy, r, hue, hue2, gid, ring=False, glow=True):
    d = (f'<radialGradient id="{gid}" cx="35%" cy="30%" r="75%">'
         f'<stop offset="0" stop-color="#ffffff" stop-opacity=".95"/>'
         f'<stop offset=".25" stop-color="{hue}"/><stop offset="1" stop-color="{hue2}" stop-opacity=".9"/>'
         f'</radialGradient>')
    b = ""
    if glow:
        b += f'<circle cx="{cx}" cy="{cy}" r="{r*1.55:.1f}" fill="{hue}" opacity=".28" filter="url(#blur)"/>'
    if ring:
        b += (f'<ellipse cx="{cx}" cy="{cy}" rx="{r*1.9:.1f}" ry="{r*0.5:.1f}" fill="none" stroke="{hue}" '
              f'stroke-width="{max(1.5, r*0.09):.1f}" opacity=".55" transform="rotate(-18 {cx} {cy})"/>')
    b += f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="url(#{gid})"/>'
    # terminator shading
    b += (f'<path d="M{cx + r*0.15:.1f},{cy - r:.1f} A{r},{r} 0 0 1 {cx + r*0.15:.1f},{cy + r:.1f} '
          f'A{r*0.75:.1f},{r} 0 0 0 {cx + r*0.15:.1f},{cy - r:.1f}Z" fill="#05060f" opacity=".28"/>')
    if ring:
        b += (f'<path d="M{cx - r*1.9:.1f},{cy} A{r*1.9:.1f},{r*0.5:.1f} 0 0 0 {cx + r*1.9:.1f},{cy}" '
              f'fill="none" stroke="{hue}" stroke-width="{max(1.5, r*0.09):.1f}" opacity=".9" '
              f'transform="rotate(-18 {cx} {cy})"/>')
    return d, b


BLUR = '<filter id="blur" x="-1" y="-1" width="3" height="3"><feGaussianBlur stdDeviation="9"/></filter>'
SOFT = '<filter id="soft" x="-1" y="-1" width="3" height="3"><feGaussianBlur stdDeviation="40"/></filter>'


def ellipse_path(cx, cy, rx, ry, a0):
    p = lambda a: (cx + rx * math.cos(a), cy + ry * math.sin(a))
    (x0, y0), (x1, y1) = p(a0), p(a0 + math.pi)
    return (f"M{x0:.1f},{y0:.1f} A{rx},{ry} 0 1 1 {x1:.1f},{y1:.1f} "
            f"A{rx},{ry} 0 1 1 {x0:.1f},{y0:.1f}")


# ---------------------------------------------------------------- header

def header():
    W, H = 1280, 420
    rng = random.Random(7)
    defs = [BLUR, SOFT,
            f'<linearGradient id="bg" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="{BG0}"/>'
            f'<stop offset="1" stop-color="{BG1}"/></linearGradient>',
            '<linearGradient id="name" x1="0" x2="1"><stop offset="0" stop-color="#ffffff"/>'
            '<stop offset=".55" stop-color="#e9d5ff"/><stop offset="1" stop-color="#a5f3fc"/></linearGradient>',
            '<radialGradient id="core" cx="40%" cy="35%" r="70%"><stop offset="0" stop-color="#fff"/>'
            '<stop offset=".35" stop-color="#e9d5ff"/><stop offset="1" stop-color="#7c3aed"/></radialGradient>',
            '<linearGradient id="streak" x1="0" x2="1"><stop offset="0" stop-color="#fff" stop-opacity="0"/>'
            '<stop offset="1" stop-color="#fff"/></linearGradient>',
            f'<clipPath id="frame"><rect width="{W}" height="{H}" rx="22"/></clipPath>']
    b = [f'<g clip-path="url(#frame)">',
         f'<rect width="{W}" height="{H}" fill="url(#bg)"/>',
         # nebulae
         '<ellipse cx="980" cy="120" rx="260" ry="140" fill="#7c3aed" opacity=".30" filter="url(#soft)"/>',
         '<ellipse cx="1160" cy="330" rx="200" ry="110" fill="#0891b2" opacity=".28" filter="url(#soft)"/>',
         '<ellipse cx="160" cy="400" rx="300" ry="90" fill="#db2777" opacity=".16" filter="url(#soft)"/>',
         stars(rng, W, H, 140),
         # shooting star
         '<g class="shoot"><line x1="0" y1="0" x2="120" y2="0" stroke="url(#streak)" stroke-width="2" '
         'stroke-linecap="round"/></g>']

    # orbit system on the right
    cx, cy = 1000, 214
    orbits = [(96, 36), (165, 62), (238, 90)]
    sys = [f'<g transform="rotate(-10 {cx} {cy})">']
    for rx, ry in orbits:
        sys.append(f'<ellipse cx="{cx}" cy="{cy}" rx="{rx}" ry="{ry}" fill="none" stroke="#a5b4fc" '
                   f'stroke-opacity=".32" stroke-dasharray="3 7"/>')
    sys.append(f'<circle cx="{cx}" cy="{cy}" r="46" fill="#a78bfa" opacity=".45" filter="url(#blur)"/>')
    sys.append(f'<circle cx="{cx}" cy="{cy}" r="24" fill="url(#core)"/>')
    placements = [(0, 0.4, 16), (1, 2.3, 22), (1, 5.4, 26), (2, 1.2, 34), (2, 4.2, 40)]
    for i, (oi, a0, dur) in enumerate(placements):
        m = MISSIONS[i]
        rx, ry = orbits[oi]
        r = [9, 12, 10, 13, 11][i]
        pd, pb = planet(0, 0, r, m["hue"], m["hue2"], f"hp{i}", ring=m["ring"], glow=True)
        defs.append(pd)
        sys.append(f'<g>{pb}<animateMotion dur="{dur}s" repeatCount="indefinite" '
                   f'path="{ellipse_path(cx, cy, rx, ry, a0)}"/></g>')
    sys.append('</g>')
    b += sys

    # "you are here" leader label
    b.append(f'<path d="M{cx+14},{cy-20} L{cx+44},{cy-66} L{cx+70},{cy-66}" fill="none" stroke="#e9d5ff" '
             f'stroke-opacity=".8" stroke-width="1.2"/>')
    b.append(f'<circle cx="{cx+14}" cy="{cy-20}" r="2.5" fill="#e9d5ff"/>')
    p, _ = pill(cx + 70, cy - 79, "YOU ARE HERE", "#e9d5ff", 11)
    b.append(p)
    p, pw = pill(0, 0, "NOT TO SCALE", "#94a3b8", 10, fill_op=0.05)
    b.append(f'<g transform="translate({W - 40 - pw:.0f},{H - 46})">{p}</g>')

    # left column text
    x = 72
    b.append(t(x, 96, f"◉  MISSION CONTROL  //  @{PROFILE['user']}", 14, "#7dd3fc", MONO, 600, 3))
    name = PROFILE["name"]
    size = 64 if len(name) <= 16 else max(40, int(64 * 16 / len(name)))
    b.append(t(x - 3, 168, name, size, "url(#name)", SANS, 800, -1))
    b.append(t(x, 204, PROFILE["role"], 15, "#f0abfc", MONO, 700, 4))
    for i, line in enumerate(PROFILE["tagline"]):
        b.append(t(x, 248 + i * 30, line, 21, "#cbd5e1"))
    px = x
    for i, c in enumerate(PROFILE["chips"]):
        p, w = pill(px, 300, c, [m["hue"] for m in MISSIONS][i % 5], 11)
        b.append(p)
        px += w + 10
    b.append(t(x, 368, "> " + PROFILE["status"], 15, "#34d399", MONO, 500))
    cur_x = x + text_w("> " + PROFILE["status"], 15, True) + 6
    b.append(f'<rect class="blink" x="{cur_x:.0f}" y="355" width="9" height="16" fill="#34d399"/>')
    b.append('</g>')
    b.append(f'<rect x=".5" y=".5" width="{W-1}" height="{H-1}" rx="22" fill="none" stroke="#a5b4fc" '
             f'stroke-opacity=".22"/>')

    style = BASE_STYLE + """
.shoot{animation:sh 9s linear infinite;opacity:0}
@keyframes sh{0%{transform:translate(300px,30px) rotate(18deg);opacity:0}
3%{opacity:1}12%{transform:translate(760px,180px) rotate(18deg);opacity:0}100%{opacity:0}}
"""
    return svg(W, H, "\n".join(b), "".join(defs), style)


# ---------------------------------------------------------------- mission cards

def card(i, m, stats, wide=False):
    W, H = (1280, 260) if wide else (630, 250)
    rng = random.Random(100 + i)
    hue, hue2 = m["hue"], m["hue2"]
    stars_n, lang = stats["per_repo"].get(m["repo"], (0, None))
    lang = m.get("lang", lang)
    defs = [BLUR, SOFT, f'<clipPath id="c"><rect width="{W}" height="{H}" rx="20"/></clipPath>',
            f'<linearGradient id="edge" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="{hue}"/>'
            f'<stop offset="1" stop-color="{hue2}" stop-opacity=".25"/></linearGradient>']
    b = ['<g clip-path="url(#c)">', f'<rect width="{W}" height="{H}" fill="{BG0}"/>',
         f'<ellipse cx="110" cy="{H/2}" rx="190" ry="150" fill="{hue}" opacity=".16" filter="url(#soft)"/>',
         f'<ellipse cx="{W-60}" cy="0" rx="220" ry="90" fill="{hue2}" opacity=".10" filter="url(#soft)"/>',
         stars(rng, W, H, 45 if not wide else 90)]
    pcx, pcy, pr = (130, H / 2, 54) if not wide else (170, H / 2, 70)
    orbit_r = pr + 30
    b.append(f'<circle cx="{pcx}" cy="{pcy}" r="{orbit_r}" fill="none" stroke="{hue}" stroke-opacity=".35" '
             f'stroke-dasharray="2 6"/>')
    pd, pb = planet(pcx, pcy, pr, hue, hue2, "pl", ring=m["ring"])
    defs.append(pd)
    b.append(pb)
    b.append(f'<g><circle cx="{pcx + orbit_r}" cy="{pcy}" r="4.5" fill="#fff"/>'
             f'<circle cx="{pcx + orbit_r}" cy="{pcy}" r="9" fill="{hue}" opacity=".35"/>'
             f'<animateTransform attributeName="transform" type="rotate" from="0 {pcx} {pcy}" '
             f'to="360 {pcx} {pcy}" dur="{12 + i * 3}s" repeatCount="indefinite"/></g>')

    x = 262 if not wide else 340
    kicker = f"MISSION {i+1:02d}" + (f"  ·  {lang.upper()}" if lang else "")
    if wide:
        kicker += "  ·  FEATURED"
    b.append(t(x, 58, kicker, 12, hue, MONO, 700, 3))
    b.append(t(x, 100, m["repo"], 30 if not wide else 38, "#ffffff", SANS, 800, -0.5))
    for j, line in enumerate(m["lines"]):
        b.append(t(x, (136 if not wide else 146) + j * 24, line, 16 if not wide else 19, "#aeb8cc"))
    px, py = x, H - 56
    for tech in m["tech"]:
        p, w = pill(px, py, tech, hue, 10.5, fill_op=0.10)
        b.append(p)
        px += w + 8
    b.append(t(W - 30, 58, f"★ {stars_n}", 14, "#fde68a", MONO, 700, 1, "end"))
    if wide:
        b.append(t(W - 30, H - 33, "OPEN REPO →", 12, hue, MONO, 700, 2.5, "end"))
    b.append('</g>')
    b.append(f'<rect x="1" y="1" width="{W-2}" height="{H-2}" rx="19" fill="none" stroke="url(#edge)" '
             f'stroke-opacity=".7" stroke-width="1.5"/>')
    return svg(W, H, "\n".join(b), "".join(defs), BASE_STYLE)


# ---------------------------------------------------------------- toolkit

def toolkit():
    W, H = 1280, 190
    rng = random.Random(3)
    defs = [SOFT, f'<clipPath id="c"><rect width="{W}" height="{H}" rx="20"/></clipPath>']
    b = ['<g clip-path="url(#c)">', f'<rect width="{W}" height="{H}" fill="{BG0}"/>',
         '<ellipse cx="640" cy="200" rx="520" ry="80" fill="#6d28d9" opacity=".22" filter="url(#soft)"/>',
         stars(rng, W, H, 60)]
    b.append(t(40, 46, "CARGO BAY  //  TOOLS ON BOARD", 13, "#7dd3fc", MONO, 700, 3))
    colw = (W - 80 + 14) / len(TOOLKIT)
    for k, (label, hue, items) in enumerate(TOOLKIT):
        x = 40 + k * colw
        b.append(f'<rect x="{x:.0f}" y="66" width="{colw - 14:.0f}" height="98" rx="14" fill="{hue}" '
                 f'fill-opacity=".05" stroke="{hue}" stroke-opacity=".35"/>')
        b.append(f'<circle cx="{x + 18:.0f}" cy="88" r="4" fill="{hue}"/>')
        b.append(t(x + 30, 92, label, 11, hue, MONO, 700, 2.5))
        b.append(t(x + 18, 122, " · ".join(items[:2]), 15, "#e2e8f0", SANS, 600))
        if len(items) > 2:
            b.append(t(x + 18, 146, " · ".join(items[2:]), 15, "#e2e8f0", SANS, 600))
    b.append('</g>')
    b.append(f'<rect x=".5" y=".5" width="{W-1}" height="{H-1}" rx="20" fill="none" stroke="#a5b4fc" '
             f'stroke-opacity=".22"/>')
    return svg(W, H, "\n".join(b), "".join(defs), BASE_STYLE)


# ---------------------------------------------------------------- telemetry

def telemetry(stats):
    W, H = 1280, 230
    rng = random.Random(11)
    now = datetime.now(timezone.utc)
    days = "-"
    if stats["created"]:
        days = str((now - datetime.fromisoformat(stats["created"].replace("Z", "+00:00"))).days)
    gauges = [("MISSIONS LAUNCHED", str(stats["repos"]), "#c084fc"),
              ("STARS EARNED", str(stats["stars"]), "#fde68a"),
              ("FORKS", str(stats["forks"]), "#22d3ee"),
              ("CREW (FOLLOWERS)", str(stats["followers"]), "#34d399"),
              ("DAYS IN ORBIT", days, "#f472b6")]
    defs = [SOFT, f'<clipPath id="c"><rect width="{W}" height="{H}" rx="20"/></clipPath>']
    b = ['<g clip-path="url(#c)">', f'<rect width="{W}" height="{H}" fill="{BG0}"/>',
         '<ellipse cx="200" cy="0" rx="400" ry="90" fill="#0891b2" opacity=".18" filter="url(#soft)"/>',
         stars(rng, W, H, 55)]
    b.append(t(40, 46, "TELEMETRY  //  LIVE FROM GITHUB", 13, "#7dd3fc", MONO, 700, 3))
    b.append(f'<circle class="blink" cx="{W - 236}" cy="41" r="4.5" fill="#34d399"/>')
    b.append(t(W - 40, 46, f"SYNCED {now:%Y-%m-%d} UTC", 12, "#64748b", MONO, 600, 2, "end"))
    colw = (W - 80) / len(gauges)
    for k, (label, val, hue) in enumerate(gauges):
        x = 40 + k * colw
        b.append(t(x, 116, val, 46, hue, SANS, 800, -1))
        b.append(t(x, 142, label, 11, "#94a3b8", MONO, 700, 2.5))
    # language composition bar
    langs = sorted(stats["langs"].items(), key=lambda kv: -kv[1])
    total = sum(v for _, v in langs) or 1
    bx, by, bw = 40, 172, W - 80
    b.append(f'<rect x="{bx}" y="{by}" width="{bw}" height="8" rx="4" fill="#1e293b"/>')
    cx, legend_x = bx, bx
    main = [(k, v) for k, v in langs if v / total >= 0.01][:6]
    for k, v in main:
        w = bw * v / total
        b.append(f'<rect x="{cx:.1f}" y="{by}" width="{max(w - 2, 1):.1f}" height="8" '
                 f'fill="{LANG_COLORS.get(k, "#94a3b8")}"/>')
        cx += w
    b.append(f'<rect x="{bx}" y="{by}" width="{bw}" height="8" rx="4" fill="none" stroke="{BG0}" stroke-width="2"/>')
    for k, v in main:
        label = f"{k} {100 * v / total:.0f}%"
        b.append(f'<circle cx="{legend_x + 5}" cy="{by + 30}" r="5" fill="{LANG_COLORS.get(k, "#94a3b8")}"/>')
        b.append(t(legend_x + 16, by + 35, label, 12, "#cbd5e1", MONO, 500))
        legend_x += text_w(label, 12, True) + 44
    b.append('</g>')
    b.append(f'<rect x=".5" y=".5" width="{W-1}" height="{H-1}" rx="20" fill="none" stroke="#a5b4fc" '
             f'stroke-opacity=".22"/>')
    return svg(W, H, "\n".join(b), "".join(defs), BASE_STYLE)


# ---------------------------------------------------------------- footer

def footer():
    W, H = 1280, 150
    rng = random.Random(21)
    defs = [BLUR, SOFT, f'<clipPath id="c"><rect width="{W}" height="{H}" rx="20"/></clipPath>',
            '<linearGradient id="hz" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#a78bfa"/>'
            '<stop offset="1" stop-color="#1e1b4b"/></linearGradient>']
    b = ['<g clip-path="url(#c)">', f'<rect width="{W}" height="{H}" fill="{BG0}"/>', stars(rng, W, H, 70),
         '<ellipse cx="640" cy="560" rx="900" ry="440" fill="#7c3aed" opacity=".35" filter="url(#soft)"/>',
         '<ellipse cx="640" cy="560" rx="860" ry="440" fill="url(#hz)"/>',
         '<ellipse cx="640" cy="560" rx="860" ry="440" fill="none" stroke="#e9d5ff" stroke-opacity=".8" stroke-width="1.5"/>']
    b.append(t(640, 62, "TRANSMISSION ENDS", 13, "#7dd3fc", MONO, 700, 5, "middle"))
    b.append(t(640, 96, "Got a workflow that should run itself? Let's automate it.", 20, "#f1f5f9", SANS, 600, 0, "middle"))
    b.append('</g>')
    return svg(W, H, "\n".join(b), "".join(defs), BASE_STYLE)


def main():
    OUT.mkdir(exist_ok=True)
    stats = fetch_stats()
    files = {"header.svg": header(), "toolkit.svg": toolkit(), "telemetry.svg": telemetry(stats),
             "footer.svg": footer()}
    for i, m in enumerate(MISSIONS):
        files[f"mission-{m['repo']}.svg"] = card(i, m, stats, wide=(i == 0))
    for name, content in files.items():
        (OUT / name).write_text(content, encoding="utf-8")
    print("wrote", len(files), "graphics:", ", ".join(files))


if __name__ == "__main__":
    main()
