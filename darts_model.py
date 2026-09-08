import os, requests, json
from datetime import datetime, timezone
from math import comb

API_KEY = os.getenv("ODDS_API_KEY")
os.makedirs("darts", exist_ok=True)

def cs_probs(p, ft=7):
    res={}
    for opp in range(ft):
        res[f"{ft}-{opp}"] = comb(ft+opp-1, ft-1) * (p**ft) * ((1-p)**opp)
        res[f"{opp}-{ft}"] = comb(ft+opp-1, ft-1) * ((1-p)**ft) * (p**opp)
    return res

DEFAULT_MATCHES = [
  {"p1":"Luke Littler","p2":"Luke Humphries","p_leg":0.58,"ft":7,"book":{"7-4":9.5,"7-3":8.0,"7-2":11.0,"7-5":7.0,"6-7":5.5}},
  {"p1":"MVG","p2":"Gerwyn Price","p_leg":0.54,"ft":7,"book":{"7-4":8.5,"7-3":7.5,"7-2":10.0,"7-5":6.5,"6-7":5.0}},
]

def fetch_bet365():
    if not API_KEY: return None
    try:
        url = f"https://api.the-odds-api.com/v4/sports/darts_premier_league/odds/?apiKey={API_KEY}&regions=uk&markets=correct_score,h2h&bookmakers=bet365&oddsFormat=decimal"
        r = requests.get(url, timeout=20)
        print(f"Status {r.status_code} Remaining {r.headers.get('x-requests-remaining')}")
        if r.status_code!= 200:
            print(r.text[:1000])
            return None
        data = r.json()
        open("darts/bet365_raw.json","w").write(json.dumps(data, indent=2))
        return data
    except Exception as e:
        print(f"fetch fail {e}")
        return None

raw = fetch_bet365()
matches_to_render = []

if raw:
    for ev in raw[:6]:
        p1 = ev.get('home_team','P1')
        p2 = ev.get('away_team','P2')
        book_cs = {}
        for bm in ev.get('bookmakers',[]):
            if bm['key']=='bet365':
                for mk in bm.get('markets',[]):
                    if mk['key']=='correct_score':
                        for out in mk.get('outcomes',[]):
                            book_cs[out['name']] = out['price']
        if book_cs:
            matches_to_render.append({"p1":p1,"p2":p2,"p_leg":0.55,"ft":7,"book":book_cs,"is_live":True})

if not matches_to_render:
    for m in DEFAULT_MATCHES:
        matches_to_render.append({**m,"is_live":False})

html = f"""<!DOCTYPE html><html><head><meta charset='utf-8'><meta name='viewport' content='width=device-width,initial-scale=1'>
<title>Orange Darts V2 LIVE</title><style>body{{background:#081229;color:#e8eefc;font-family:-apple-system;padding:14px;max-width:900px;margin:0 auto}}h1{{color:#ff9a2e}}.card{{background:#111e3d;border:1px solid #1e3260;border-radius:14px;padding:14px;margin:14px 0}}.badge{{background:#007a33;color:#fff;font-weight:900;padding:3px 10px;border-radius:20px;font-size:11px}}.badge-demo{{background:#5a2a00;color:#ff9a2e;border:1px solid #ff9a2e}} table{{width:100%;border-collapse:collapse;margin-top:8px}} th{{color:#8ea2cc;text-align:left;font-size:11px}} td{{padding:8px 4px;border-top:1px solid #1e3260;font-size:13px}}.odds{{color:#ffcc00;font-weight:800}}.edge-pos{{color:#00ff88;font-weight:900}}.edge-neg{{color:#ff6b6b}}</style></head><body>
<h1>🎯 Orange DARTS V2 — Bet365 LIVE</h1><div style='color:#8ea2cc;font-size:13px'>Big Odds Correct Score vs Bet365 — {datetime.now(timezone.utc).strftime('%H:%M UTC')}</div>"""

for m in matches_to_render:
    probs = cs_probs(m['p_leg'], m['ft'])
    badge = "<span class='badge'>BET365 LIVE ✅</span>" if m.get('is_live') else "<span class='badge badge-demo'>DEMO — Waiting for live events</span>"
    html+=f"<div class='card'><b>{m['p1']} vs {m['p2']} — FT{m['ft']}</b> {badge}<table><tr><th>Score</th><th>True%</th><th>Fair</th><th>Bet365</th><th>EDGE</th></tr>"
    rows=[]
    for score,true_p in probs.items():
        if score in m['book']:
            book=m['book'][score]; fair=1/true_p if true_p>0 else 99; edge=true_p-(1/book)
            rows.append((score,true_p,fair,book,edge))
    rows=sorted(rows, key=lambda x: -x[4])
    for score,true_p,fair,book,edge in rows:
        edge_pct=edge*100; cls="edge-pos" if edge_pct>0 else "edge-neg"
        emoji="💣 BIG" if book>=8 and edge_pct>3 else "🟢" if edge_pct>2 else "";
        if edge_pct>5: emoji="💣💣 MEGA"
        html+=f"<tr><td><b>{score}</b></td><td>{true_p*100:.1f}%</td><td>{fair:.2f}</td><td class='odds'>{book:.2f}</td><td class='{cls}'>{edge_pct:+.1f}% {emoji}</td></tr>"
    html+="</table></div>"

html+=f"<div style='margin-top:20px;color:#8ea2cc;font-size:12px'>API Live: {bool(raw)} | Events: {len(matches_to_render)} | {datetime.now(timezone.utc).isoformat()}<br><a href='live.html' style='color:#ff9a2e'>→ Live Checkout Tapper C</a></div></body></html>"

open("darts/index.html","w",encoding="utf-8").write(html)
print("V2 built OK")
