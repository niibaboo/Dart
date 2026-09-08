from datetime import datetime, timezone
from math import comb
import os

PLAYERS = [
 {"name":"Luke Littler","avg":101.2,"c_pct":48.5,"rate180":0.42},
 {"name":"Luke Humphries","avg":100.1,"c_pct":45.2,"rate180":0.38},
 {"name":"Michael van Gerwen","avg":99.5,"c_pct":43.8,"rate180":0.39},
 {"name":"Gerwyn Price","avg":97.8,"c_pct":41.5,"rate180":0.35},
]

MATCHES = [
 {"p1":"Luke Littler","p2":"Luke Humphries","p_leg":0.58,"ft":7,"book_cs":{"7-3":8.0,"7-4":9.5,"7-2":11.0,"7-5":7.0,"6-7":5.5}},
 {"p1":"van Gerwen","p2":"Price","p_leg":0.54,"ft":7,"book_cs":{"7-3":7.5,"7-4":8.5,"7-2":10.0,"7-5":6.5,"6-7":5.0}},
]

def cs_probs(p, ft):
    res={}
    for opp in range(ft):
        prob_win = comb(ft+opp-1, ft-1) * (p**ft) * ((1-p)**opp)
        prob_lose = comb(ft+opp-1, ft-1) * ((1-p)**ft) * (p**opp)
        res[f"{ft}-{opp}"]=prob_win
        res[f"{opp}-{ft}"]=prob_lose
    return res

html=f"""<!DOCTYPE html><html><head><meta charset='utf-8'><meta name='viewport' content='width=device-width,initial-scale=1'>
<title>Orange Darts ABCD</title>
<style>
body{{background:#081229;color:#e8eefc;font-family:-apple-system;padding:14px;max-width:900px;margin:0 auto}}
h1{{color:#ff9a2e}}.card{{background:#111e3d;border:1px solid #1e3260;border-radius:14px;padding:14px;margin:14px 0}}
.badge{{background:#ff9a2e;color:#000;font-weight:800;padding:3px 9px;border-radius:20px;font-size:11px}}
.pill{{background:#1a2c5e;border-radius:20px;padding:5px 10px;font-size:12px;display:inline-block;margin:3px}}
.model{{background:#173a2a;color:#7dd3a8;border:1px solid #2a6b4a}}.big{{background:#3d2200;color:#ff9a2e;border:1px solid #ff9a2e;font-weight:900;font-size:13px}}
.live{{color:#00ff88;border:1px solid #00ff88;padding:2px 6px;border-radius:10px;font-size:10px}}
table{{width:100%;border-collapse:collapse;margin-top:10px}} th{{color:#8ea2cc;text-align:left;font-size:11px}} td{{padding:8px 4px;border-top:1px solid #1e3260;font-size:13px}}
.odds{{color:#ffcc00;font-weight:800}}.edge{{color:#00ff88;font-weight:900}}
</style></head><body>
<h1>🎯 Orange Line DARTS ABCD — {datetime.now(timezone.utc).strftime('%H:%M UTC')} <span class='live'>BIG ODDS</span></h1>
<h3>D) Correct Score — BIG ODDS MODEL</h3>
"""

for m in MATCHES:
    probs = cs_probs(m['p_leg'], m['ft'])
    html+=f"<div class='card'><b>{m['p1']} vs {m['p2']} — First to {m['ft']}</b><table><tr><th>Score</th><th>True %</th><th>Fair</th><th>Book</th><th>EDGE</th></tr>"
    rows=[]
    for score, true_p in probs.items():
        if score in m['book_cs']:
            book = m['book_cs'][score]
            fair = 1/true_p
            edge = true_p - 1/book
            rows.append((score,true_p,fair,book,edge))
    rows=sorted(rows, key=lambda x: -x[4])
    for score,true_p,fair,book,edge in rows:
        color = "#00ff88" if edge>0.04 else "#ffcc00" if edge>0.01 else "#ff6666"
        emoji = "💣" if book>=8 else "🟢" if edge>0.03 else ""
        html+=f"<tr><td><b>{score}</b></td><td>{true_p*100:.1f}%</td><td class='odds'>{fair:.2f}</td><td class='odds'>{book:.2f}</td><td style='color:{color}' class='edge'>{edge*100:+.1f}% {emoji}</td></tr>"
    html+="</table></div>"

html+=f"<div style='color:#8ea2cc;margin-top:20px'>Built {datetime.now(timezone.utc).isoformat()}</div></body></html>"

os.makedirs("darts", exist_ok=True)
open("darts/index.html","w",encoding="utf-8").write(html)

# C) Live tapper
live_html="""<!DOCTYPE html><html><head><meta charset='utf-8'><meta name='viewport' content='width=device-width,initial-scale=1'><title>Live Checkout</title><style>body{background:#050d24;color:#e8eefc;font-family:-apple-system;padding:14px;max-width:500px;margin:0 auto}h1{color:#ff9a2e}.box{background:#111e3d;border:1px solid #1e3260;border-radius:14px;padding:14px;margin:12px 0}.btn{background:#1a2c5e;color:#fff;border:1px solid #2a4a8e;border-radius:10px;padding:12px;margin:4px;font-size:16px;font-weight:800;width:22%}.big{font-size:42px;font-weight:900;color:#7dd3a8} input{background:#0d1733;border:1px solid #22366e;color:#fff;border-radius:10px;padding:10px;width:70px;font-size:18px;text-align:center}</style></head><body><h1>🎯 LIVE Tapper C</h1><div class='box'>Score: <input id='score' value='32' type='number'> Darts: <input id='darts' value='2' type='number'> Book%: <input id='book' value='57' type='number'></div><div class='box'><div>Model Checkout</div><div class='big' id='model'>71%</div><div>Edge: <span id='edge' style='font-size:28px;color:#ff9a2e;font-weight:900'>+14%</span> <span id='rec'></span></div></div><div class='box'><button class='btn' onclick='upd(32)'>32</button><button class='btn' onclick='upd(40)'>40</button><button class='btn' onclick='upd(16)'>16</button><button class='btn' onclick='upd(170)'>170</button></div><script>function calc(){let s=parseInt(document.getElementById('score').value)||32;let d=parseInt(document.getElementById('darts').value)||2;let pct=s<=40?0.68:s<=60?0.45:0.12;if(d==1)pct*=0.7;if(d==3)pct=Math.min(0.92,pct*1.15);document.getElementById('model').innerText=Math.round(pct*100)+'%';let b=parseInt(document.getElementById('book').value)||57;let e=Math.round(pct*100-b);document.getElementById('edge').innerText=(e>0?'+':'')+e+'%';document.getElementById('rec').innerText=e>8?'BET 🟢':e>3?'LEAN':'NO BET';}function upd(v){document.getElementById('score').value=v;calc();}document.getElementById('score').addEventListener('input',calc);document.getElementById('darts').addEventListener('input',calc);document.getElementById('book').addEventListener('input',calc);calc();</script></body></html>"""
open("darts/live.html","w",encoding="utf-8").write(live_html)
print("DONE A+B+C+D")
