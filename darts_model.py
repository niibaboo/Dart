import os, requests
from datetime import datetime, timezone
from math import comb
import json

API_KEY = os.getenv("ODDS_API_KEY")
print(f"API Key present: {bool(API_KEY)}")

def cs_probs(p, ft=7):
    res={}
    for opp in range(ft):
        # Win ft-opp and Lose opp-ft
        res[f"{ft}-{opp}"] = comb(ft+opp-1, ft-1) * (p**ft) * ((1-p)**opp)
        res[f"{opp}-{ft}"] = comb(ft+opp-1, ft-1) * ((1-p)**ft) * (p**opp)
    return res

# === DEFAULTS (used if no API key yet) ===
DEFAULT_MATCHES = [
  {"p1":"Luke Littler","p2":"Luke Humphries","p_leg":0.58,"ft":7,"book":{"7-4":9.5,"7-3":8.0,"7-2":11.0,"7-5":7.0,"6-7":5.5}},
  {"p1":"Michael van Gerwen","p2":"Gerwyn Price","p_leg":0.54,"ft":7,"book":{"7-4":8.5,"7-3":7.5,"7-2":10.0,"7-5":6.5,"6-7":5.0}},
]

def fetch_bet365():
    if not API_KEY:
        return None
    try:
        # PDC events - Bet365 market includes correct score for darts
        url = f"https://api.the-odds-api.com/v4/sports/darts_premier_league/odds/?apiKey={API_KEY}&regions=uk&markets=correct_score,h2h&bookmakers=bet365&oddsFormat=decimal"
        r = requests.get(url, timeout=15)
        print(f"Odds API status {r.status_code}")
        if r.status_code!= 200:
            print(r.text[:500])
            return None
        data = r.json()
        # Save raw for debug
        open("darts/bet365_raw.json","w").write(json.dumps(data, indent=2))
        return data
    except Exception as e:
        print(f"fetch fail {e}")
        return None

raw = fetch_bet365()
matches_to_render = []

if raw:
    # Parse API into our format
    for ev in raw[:6]: # top 6 games
        p1 = ev.get('home_team','Player1')
        p2 = ev.get('away_team','Player2')
        # find bet365
        book_cs = {}
        for bm in ev.get('bookmakers',[]):
            if bm['key']=='bet365':
                for mk in bm.get('markets',[]):
                    if mk['key']=='correct_score':
                        for out in mk.get('outcomes',[]):
                            name = out['name'] # like "7-4"
                            book_cs[name] = out['price']
        if book_cs:
            matches_to_render.append({"p1":p1,"p2":p2,"p_leg":0.55,"ft":7,"book":book_cs,"is_live":True})
else:
    # fallback
    for m in DEFAULT_MATCHES:
        matches_to_render.append({**m,"is_live":False})

# === BUILD HTML ===
html = f"""<!DOCTYPE html><html><head><meta charset='utf-8'><meta name='viewport' content='width=device-width,initial-scale=1'>
<title>Orange Darts — Bet365 V2 LIVE</title>
<style>
body{{background:#081229;color:#e8eefc;font-family:-apple-system,Segoe UI,Roboto;padding:14px;max-width:900px;margin:0 auto}}
h1{{color:#ff9a2e;font-size:22px}}.card{{background:#111e3d;border:1px solid #1e3260;border-radius:14px;padding:14px;margin:14px 0}}
.badge{{background:#007a33;color:#fff;font-weight:900;padding:3px 10px;border-radius:20px;font-size:11px}}
.badge-demo{{background:#5a2a00;color:#ff9a2e;border:1px solid #ff9a2e}}
table{{width:100%;border-collapse:collapse;margin-top:8px}} th{{color:#8ea2cc;text-align:left;font-size:11px;text-transform:uppercase}}
td{{padding:8px 4px;border-top:1px solid #1e3260;font-size:13px}}.live{{color:#00ff88;border:1px solid #00ff88;padding:2px 7px;border-radius:10px;font-size:10px;font-weight:900}}
.odds{{color:#ffcc00;font-weight:800}}.edge-pos{{color:#00ff88;font-weight:900}}.edge-neg{{color:#ff6b6b}}
</style></head><body>
<h1>🎯 Orange Line DARTS V2 — Bet365 LIVE <span class='live'>AUTO</span></h1>
<div style='color:#8ea2cc;font-size:13px'>Correct Score BIG ODDS vs Bet365 — {datetime.now(timezone.utc).strftime('%H:%M UTC')} — True Prob vs Fair vs Book</div>
"""

for m in matches_to_render:
    probs = cs_probs(m['p_leg'], m['ft'])
    badge = "<span class='badge'>BET365 LIVE</span>" if m.get('is_live') else "<span class='badge-demo'>DEMO — Add ODDS_API_KEY</span>"
    html+=f"<div class='card'><b>{m['p1']} vs {m['p2']} — First to {m['ft']}</b> {badge}<table><tr><th>Score</th><th>True %</th><th>Fair</th><th>Bet365</th><th>EDGE</th></tr>"
    rows=[]
    for score,true_p in probs.items():
        if score in m['book']:
            book = m['book'][score]
            fair = 1/true_p if true_p>0 else 99
            edge = true_p - (1/book)
            rows.append((score,true_p,fair,book,edge))
    # sort best edge first
    rows=sorted(rows, key=lambda x: -x[4])
    for score,true_p,fair,book,edge in rows:
        edge_pct = edge*100
        cls = "edge-pos" if edge_pct>0 else "edge-neg"
        emoji = "💣 BIG" if book>=8.0 and edge_pct>3 else "🟢 VALUE" if edge_pct>2 else ""
        if edge_pct>4: emoji = "💣💣 MEGA"
        html+=f"<tr><td><b>{score}</b></td><td>{true_p*100:.1f}%</td><td>{fair:.2f}</td><td class='odds'>{book:.2f}</td><td class='{cls}'>{edge_pct:+.1f}% {emoji}</td></tr>"
    html+="</table></div>"

html+=f"""
<div style='margin-top:20px;color:#8ea2cc;font-size:12px'>
API: {'LIVE Bet365 ✅ '+str(len(raw))+' events' if raw else 'DEMO mode — add secret ODDS_API_KEY for live'}<br>
Built {datetime.now(timezone.utc).isoformat()}<br><br>
<a href='live.html' style='color:#ff9a2e'>→ Live Checkout Tapper C</a>
</div></body></html>
"""

os.makedirs("darts", exist_ok=True)
open("darts/index.html","w",encoding="utf-8").write(html)

# Keep live.html
if not os.path.exists("darts/live.html"):
    live_html="""<!DOCTYPE html><html><head><meta charset='utf-8'><meta name='viewport' content='width=device-width,initial-scale=1'><title>Live Checkout</title><style>body{background:#050d24;color:#e8eefc;font-family:-apple-system;padding:14px;max-width:500px;margin:0 auto}h1{color:#ff9a2e}.box{background:#111e3d;border:1px solid #1e3260;border-radius:14px;padding:14px;margin:12px 0}.btn{background:#1a2c5e;color:#fff;border:1px solid #2a4a8e;border-radius:10px;padding:12px;margin:4px;font-size:16px;font-weight:800;width:22%}.big{font-size:42px;font-weight:900;color:#7dd3a8} input{background:#0d1733;border:1px solid #22366e;color:#fff;border-radius:10px;padding:10px;width:70px;font-size:18px;text-align:center}</style></head><body><h1>🎯 LIVE Tapper C</h1><div class='box'>Score: <input id='score' value='32' type='number'> Darts: <input id='darts' value='2' type='number'> Book%: <input id='book' value='57' type='number'></div><div class='box'><div>Model Checkout</div><div class='big' id='model'>71%</div><div>Edge: <span id='edge' style='font-size:28px;color:#ff9a2e;font-weight:900'>+14%</span> <span id='rec'></span></div></div><div class='box'><button class='btn' onclick='upd(32)'>32</button><button class='btn' onclick='upd(40)'>40</button><button class='btn' onclick='upd(16)'>16</button><button class='btn' onclick='upd(170)'>170</button></div><script>function calc(){let s=parseInt(document.getElementById('score').value)||32;let d=parseInt(document.getElementById('darts').value)||2;let pct=s<=40?0.68:s<=60?0.45:0.12;if(d==1)pct*=0.7;if(d==3)pct=Math.min(0.92,pct*1.15);document.getElementById('model').innerText=Math.round(pct*100)+'%';let b=parseInt(document.getElementById('book').value)||57;let e=Math.round(pct*100-b);document.getElementById('edge').innerText=(e>0?'+':'')+e+'%';document.getElementById('rec').innerText=e>8?'BET 🟢':e>3?'LEAN':'NO BET';}function upd(v){document.getElementById('score').value=v;calc();}document.getElementById('score').addEventListener('input',calc);document.getElementById('darts').addEventListener('input',calc);document.getElementById('book').addEventListener('input',calc);calc();</script></body></html>"""
    open("darts/live.html","w",encoding="utf-8").write(live_html)

print("V2 Bet365 built")
