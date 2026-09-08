import os, requests, json
from datetime import datetime, timezone
from math import comb

API_KEY = os.getenv("ODDS_API_KEY")
os.makedirs("snooker", exist_ok=True)

def cs_probs(p_frame, ft):
    res={}
    for opp in range(ft):
        # p wins ft-opp
        res[f"{ft}-{opp}"] = comb(ft+opp-1, ft-1) * (p_frame**ft) * ((1-p_frame)**opp)
        res[f"{opp}-{ft}"] = comb(ft+opp-1, ft-1) * ((1-p_frame)**ft) * (p_frame**opp)
    return res

DEFAULT_MATCHES = [
  {"p1":"Ronnie O'Sullivan","p2":"Judd Trump","p_frame":0.56,"ft":6,"book":{"6-2":9.0,"6-3":7.5,"6-1":12.0,"6-4":6.5,"5-6":5.0}},
  {"p1":"Mark Selby","p2":"Kyren Wilson","p_frame":0.53,"ft":6,"book":{"6-3":8.0,"6-2":9.5,"6-4":6.0,"6-1":13.0,"5-6":4.8}},
  {"p1":"Neil Robertson","p2":"Shaun Murphy","p_frame":0.54,"ft":10,"book":{"10-6":10.0,"10-7":8.5,"10-5":11.0,"10-8":7.0,"9-10":5.2}},
]

def fetch_bet365_snooker():
    if not API_KEY: return None
    # Try 3 snooker tours - World Championship is most liquid
    leagues = ["snooker_world_championship","snooker_world_open","snooker_uk_championship"]
    all_events=[]
    for league in leagues:
        try:
            url = f"https://api.the-odds-api.com/v4/sports/{league}/odds/?apiKey={API_KEY}&regions=uk&markets=correct_score,h2h&bookmakers=bet365&oddsFormat=decimal"
            r = requests.get(url, timeout=20)
            print(f"{league} Status {r.status_code} Remaining {r.headers.get('x-requests-remaining')}")
            if r.status_code==200:
                data=r.json()
                if data:
                    all_events.extend(data)
                    open(f"snooker/bet365_raw_{league}.json","w").write(json.dumps(data,indent=2))
        except Exception as e:
            print(f"fail {league} {e}")
    return all_events if all_events else None

raw = fetch_bet365_snooker()
matches_to_render=[]

if raw:
    for ev in raw[:8]:
        p1 = ev.get('home_team','P1')
        p2 = ev.get('away_team','P2')
        # guess FT from tournament name
        ft = 6
        title = ev.get('sport_title','').lower()
        if '10' in str(ev.get('id','')) or 'world' in title: ft=10
        book_cs={}
        for bm in ev.get('bookmakers',[]):
            if bm['key']=='bet365':
                for mk in bm.get('markets',[]):
                    if mk['key']=='correct_score':
                        for out in mk.get('outcomes',[]):
                            book_cs[out['name']]=out['price']
        if book_cs:
            matches_to_render.append({"p1":p1,"p2":p2,"p_frame":0.55,"ft":ft,"book":book_cs,"is_live":True})

if not matches_to_render:
    for m in DEFAULT_MATCHES:
        matches_to_render.append({**m,"is_live":False})

html = f"""<!DOCTYPE html><html><head><meta charset='utf-8'><meta name='viewport' content='width=device-width,initial-scale=1'>
<title>Green Snooker V1 LIVE</title><style>body{{background:#04120a;color:#e8fcec;font-family:-apple-system;padding:14px;max-width:900px;margin:0 auto}}h1{{color:#00ff88}}.card{{background:#0f2a1a;border:1px solid #1e5c33;border-radius:14px;padding:14px;margin:14px 0}}.badge{{background:#007a33;color:#fff;font-weight:900;padding:3px 10px;border-radius:20px;font-size:11px}}.badge-demo{{background:#4a1a00;color:#ff9a2e;border:1px solid #ff9a2e}} table{{width:100%;border-collapse:collapse;margin-top:8px}} th{{color:#8ec8a0;text-align:left;font-size:11px}} td{{padding:8px 4px;border-top:1px solid #1e5c33;font-size:13px}}.odds{{color:#ffcc00;font-weight:800}}.edge-pos{{color:#00ff88;font-weight:900}}.edge-neg{{color:#ff6b6b}}</style></head><body>
<h1>🟢 Orange SNOOKER V1 — Bet365 LIVE</h1><div style='color:#8ec8a0;font-size:13px'>Same ABCD as Darts — Frame win prob → Correct Score — {datetime.now(timezone.utc).strftime('%H:%M UTC')}</div>"""

for m in matches_to_render:
    probs = cs_probs(m['p_frame'], m['ft'])
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
        emoji="💣 BIG" if book>=8 and edge_pct>3 else "🟢" if edge_pct>2 else ""
        if edge_pct>5: emoji="💣💣 MEGA"
        html+=f"<tr><td><b>{score}</b></td><td>{true_p*100:.1f}%</td><td>{fair:.2f}</td><td class='odds'>{book:.2f}</td><td class='{cls}'>{edge_pct:+.1f}% {emoji}</td></tr>"
    html+="</table></div>"

html+=f"<div style='margin-top:20px;color:#8ec8a0;font-size:12px'>API Live: {bool(raw)} | Events: {len(matches_to_render)} | {datetime.now(timezone.utc).isoformat()}<br><a href='../darts/' style='color:#00ff88'>→ Darts V2</a> | <a href='../' style='color:#00ff88'>→ Home</a></div></body></html>"

open("snooker/index.html","w",encoding="utf-8").write(html)
print("Snooker V1 built OK")
