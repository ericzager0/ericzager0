#!/usr/bin/env python3
"""
Dibuja tu actividad de GitHub del último año: el total acumulado como un relieve
que crece, y debajo las contribuciones de cada semana.

Genera assets/relieve-light.svg y assets/relieve-dark.svg.
Solo consulta la cantidad de contribuciones por día; nunca lee código ni repos.

Uso:
  GH_TOKEN=... GH_USER=ericzager0 python scripts/relieve.py
  python scripts/relieve.py --demo     (datos inventados, para probar el diseño)
"""
import datetime as dt
import json
import os
import random
import sys
import urllib.request
from zoneinfo import ZoneInfo

from typeset import THEMES, Type, svg

USER = os.environ.get("GH_USER", "ericzager0")
OUT = os.environ.get("OUT_DIR", "assets")
TZ = ZoneInfo("America/Argentina/Buenos_Aires")
MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]

QUERY = """
query($login: String!) {
  user(login: $login) {
    contributionsCollection {
      contributionCalendar {
        totalContributions
        weeks { contributionDays { date contributionCount weekday } }
      }
    }
  }
}"""


# ---------- datos ----------
def fetch():
    token = os.environ.get("GH_TOKEN")
    if not token:
        sys.exit("Falta GH_TOKEN.")
    body = json.dumps({"query": QUERY, "variables": {"login": USER}}).encode()
    req = urllib.request.Request(
        "https://api.github.com/graphql", data=body,
        headers={"Authorization": f"bearer {token}", "Content-Type": "application/json",
                 "User-Agent": "relieve-de-actividad"})
    with urllib.request.urlopen(req, timeout=30) as r:
        data = json.load(r)
    if data.get("errors"):
        sys.exit(f"Error de la API: {data['errors']}")
    cal = data["data"]["user"]["contributionsCollection"]["contributionCalendar"]
    weeks = [[(d["date"], d["contributionCount"], d["weekday"]) for d in w["contributionDays"]]
             for w in cal["weeks"]]
    return cal["totalContributions"], weeks


def demo():
    rng = random.Random(3)
    end = dt.date.today()
    start = end - dt.timedelta(days=364 + (end.weekday() + 1) % 7)
    weeks, cur, total = [], [], 0
    d = start
    while d <= end:
        n = rng.choice([0, 0, 0, 1, 2, 3, 5, 8]) if rng.random() > .25 else 0
        wd = (d.weekday() + 1) % 7
        cur.append((d.isoformat(), n, wd)); total += n
        if wd == 6:
            weeks.append(cur); cur = []
        d += dt.timedelta(days=1)
    if cur:
        weeks.append(cur)
    return total, weeks


# ---------- geometría ----------
W, H = 1200, 540
X0, X1 = 80, 1120
TOP, BASE = 200, 336         # banda del acumulado
BAR_BASE, BAR_H = 420, 52    # banda de las semanas


def monotone(pts):
    """Curva suave que nunca baja entre dos puntos que suben (Fritsch-Carlson)."""
    n = len(pts)
    if n < 3:
        return "M" + " L".join(f"{x:.1f} {y:.1f}" for x, y in pts)
    dx = [pts[i + 1][0] - pts[i][0] for i in range(n - 1)]
    sl = [(pts[i + 1][1] - pts[i][1])/dx[i] for i in range(n - 1)]
    m = [sl[0]] + [0 if sl[i - 1]*sl[i] <= 0 else 3*(dx[i - 1] + dx[i]) /
                   ((2*dx[i] + dx[i - 1])/sl[i - 1] + (dx[i] + 2*dx[i - 1])/sl[i]) for i in range(1, n - 1)] + [sl[-1]]
    d = f"M{pts[0][0]:.1f} {pts[0][1]:.1f}"
    for i in range(n - 1):
        (x0, y0), (x1, y1), h = pts[i], pts[i + 1], dx[i]/3
        d += f" C{x0 + h:.1f} {y0 + m[i]*h:.1f} {x1 - h:.1f} {y1 - m[i + 1]*h:.1f} {x1:.1f} {y1:.1f}"
    return d


def bar(x, w, h, base, r=4):
    r = min(r, h, w/2)
    return (f"M{x:.1f} {base}V{base - h + r:.1f}Q{x:.1f} {base - h:.1f} {x + r:.1f} {base - h:.1f}"
            f"H{x + w - r:.1f}Q{x + w:.1f} {base - h:.1f} {x + w:.1f} {base - h + r:.1f}V{base}Z")


def fmt_date(d):
    return f"{MONTHS[d.month - 1]} {d.day}, {d.year}"


# ---------- dibujo ----------
def render(total, weeks, t, today):
    ty = Type()
    raw = [sum(n for _, n, _ in w) for w in weeks]
    n = len(raw)
    slot = (X1 - X0)/n
    bw = min(12, slot*.62)
    cx = [X0 + slot*(i + .5) for i in range(n)]

    run, acc = [], 0
    for v in raw:
        acc += v; run.append(acc)
    top_v = max(acc, 1)
    pts = [(X0, BASE)] + [(x, BASE - v/top_v*(BASE - TOP)) for x, v in zip(cx, run)]
    line = monotone(pts)

    best = max(range(n), key=lambda i: raw[i]) if acc else None
    peak_v = max(raw) or 1
    bars = []
    for i, v in enumerate(raw):
        x = cx[i] - bw/2
        if v:
            fill = t["accent"] if i == best else t["bar"]
            bars.append(f'<path d="{bar(x, bw, max(v/peak_v*BAR_H, 3), BAR_BASE)}" fill="{fill}"/>')
        else:
            bars.append(f'<rect x="{cx[i] - 1.5:.1f}" y="{BAR_BASE - 3}" width="3" height="3" rx="1.5" fill="{t["topo"]}" fill-opacity=".6"/>')

    axis, last = [], None
    for i, w in enumerate(weeks):
        m = int(w[0][0][5:7])
        if m != last and 2 < i < n - 2:
            axis.append(ty.text(MONTHS[m - 1], cx[i], BAR_BASE + 36, "mono", 15, t["muted"], anchor="middle", tracking=.04))
        last = m

    if acc:
        ex, ey = pts[-1]
        chart = f'''<defs><linearGradient id="area" x1="0" x2="0" y1="0" y2="1">
  <stop offset="0" stop-color="{t['accent']}" stop-opacity=".16"/><stop offset="1" stop-color="{t['accent']}" stop-opacity=".02"/>
</linearGradient></defs>
<path class="in" d="{line} L{ex:.1f} {BASE} Z" fill="url(#area)" style="animation-delay:1.4s"/>
<path class="draw" pathLength="1" d="{line}" fill="none" stroke="{t['accent']}" stroke-width="2.5" stroke-linejoin="round" stroke-linecap="round"/>
<g class="in" style="animation-delay:2.6s"><circle cx="{ex:.1f}" cy="{ey:.1f}" r="9" fill="{t['paper']}"/><circle cx="{ex:.1f}" cy="{ey:.1f}" r="5.5" fill="{t['accent']}"/></g>'''
        d0 = dt.date.fromisoformat(weeks[best][0][0])
        best_txt = f"week of {MONTHS[d0.month - 1]} {d0.day} ({raw[best]})"
        caption = f"Running total above, weekly contributions below. Busiest {best_txt}."
    else:
        chart = ty.text("No activity yet this year.", W/2, (TOP + BASE)/2, "text", 22, t["muted"], anchor="middle")
        best_txt, caption = "", "Weekly contributions below."

    total_txt = f"{total:,}"
    updated = f"Updated {fmt_date(today)}"
    body = f'''<rect x=".75" y=".75" width="{W - 1.5}" height="{H - 1.5}" rx="19.25" fill="{t['paper']}" stroke="{t['edge']}" stroke-width="1.5"/>
{ty.text("ACTIVITY", X0, 76, "mono-md", 16, t["accent"], tracking=.14)}
{ty.text("The last twelve months", X0 - 2, 140, "heading", 52, t["ink"], tracking=-.01)}
{ty.text("CONTRIBUTIONS", X1, 76, "mono-md", 16, t["muted"], anchor="end", tracking=.14)}
{ty.text(total_txt, X1 + 2, 140, "display", 64, t["ink"], anchor="end", features={"lnum": True})}
<path d="M{X0} {BASE}H{X1}" stroke="{t['rule']}" stroke-width="1.5"/>
{chart}
<path d="M{X0} {BAR_BASE}H{X1}" stroke="{t['rule']}" stroke-width="1.5"/>
{chr(10).join(bars)}
{chr(10).join(axis)}
{ty.text(caption, X0, H - 44, "text", 20, t["ink2"])}
{ty.text(updated.upper(), X1, H - 45, "mono", 14, t["muted"], anchor="end", tracking=.12)}'''
    label = (f"GitHub activity of {USER} over the last twelve months: {total_txt} contributions"
             f"{', busiest ' + best_txt if best_txt else ''}. {updated}.")
    return svg(W, H, label, body, ty)


def main():
    total, weeks = demo() if "--demo" in sys.argv else fetch()
    today = dt.datetime.now(TZ).date()
    os.makedirs(OUT, exist_ok=True)
    for name, t in THEMES.items():
        with open(os.path.join(OUT, f"relieve-{name}.svg"), "w", encoding="utf-8") as f:
            f.write(render(total, weeks, t, today))
    print(f"Listo: {total} contribuciones en {len(weeks)} semanas.")


if __name__ == "__main__":
    main()
