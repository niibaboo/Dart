import os, requests
from datetime import datetime, timezone
from math import comb

API_KEY = os.getenv("ODDS_API_KEY")
os.makedirs("darts", exist_ok=True)
print(f"KEY SET: {bool(API_KEY)} len={len(API_KEY) if API_KEY else 0}")

def fetch_bet365():
    if not API_KEY:
        print("No ODDS_API_KEY!")
        return []
    # ONE call gets ALL darts including Modus - way better
    url = f"https://api.the-odds-api.com/v4/sports/darts/odds/?apiKey={API_KEY}&regions=uk&markets=h2h,totals&bookmakers=bet365&oddsFormat=decimal"
    try:
        r = requests.get(url, timeout=25)
        print(f"API status: {r.status_code} remaining: {r.headers.get('x-requests-remaining','?')}")
        if r.status_code!= 200:
            print(r.text[:400])
            return []
        data = r.json()
        print(f"FOUND: {len(data)} darts events from Bet365")
        for ev in data[:3]:
            print(f" - {ev.get('home_team')} vs {ev.get('away_team')} [{ev.get('sport_key')}]")
        return data
    except Exception as e:
        print(f"Fetch error: {e}")
        return []

raw = fetch_bet365()
matches=[]
if raw:
    for ev in raw[:10]:
        p1=ev.get('home_team','P1'); p2=ev.get('away_team','P2'); ft=7
        book_h2h={}; book_total={}
        for bm in ev.get('bookmakers',[]):
            if bm['key']=='bet365':
                for mk in bm.get('markets',[]):
                    if mk['key']=='h2h':
                        for o in mk['outcomes']: book_h2h[o['name']]=o['price']
                    if mk['key']=='totals':
                        for o in mk['outcomes']: book_total[f"{o['name']} {o['point']}"]=o['price']
        if book_h2h:
            matches.append({"p1":p1,"p2":p2,"ft":ft,"book_h2h":book_h2h,"book_total":book_total})

print(f"Matches to show: {len(matches)}")

# BUILD HTML (same as before)
def match_win_prob(p_leg, ft):
    prob=0
    for k in range(ft):
        prob+=comb(ft+k-1,k)*(p_leg**ft)*((1-p_leg)**k)
    return prob

now = datetime.now(timezone.utc).strftime('%H:%M UTC %d %b')
html = f"""<!DOCTYPE html><html><head><meta charset='utf-8'><meta name='viewport' content='width=device-width,initial-scale=1'>
<title>Darts V3 LIVE</title><style>
body{{background:#0a0a0a;color:#eee;font-family:-apple-system;padding:12px;max-width:960px;margin:0 auto}}
h1{{color:#ff6a00}}.card{{background:#151515;border:1px solid #333;border-radius:16px;padding:14px;margin:16px 0}}
.badge{{padding:4px 10px;border-radius:20px;font-size:11px;font-weight:900}}.live{{background:#00ff88;color:#000}}
table{{width:100%;border-collapse:collapse;margin-top:8px}} th{{color:#999;font-size:11px;text-align:left}} td{{padding:7px 4px;border-top:1px solid #2a2a2a;font-size:13px}}
.odds{{color:#ffcc00;font-weight:800}}.pos{{color:#00ff88;font-weight:900}}.neg{{color:#ff5a5a}}.safe{{background:#0f2a18;border-left:4px solid #00ff88}}
.section{{margin-top:12px;padding:8px;background:#1c1c1c;border-radius:10px}}
</style></head><body><h1>🟠 DARTS V3 — LIVE</h1><div style='color:#999;font-size:13px'>Modus + PDC | {now} | API: {'LIVE ✅' if raw else 'No Events'} | Bet365 events: {len(raw) if raw else 0}</div>"""

if not matches:
    html+=f"<div class='card'><b>No Bet365 Darts odds today</b><br>Raw events: {len(raw) if raw else 0}. Check API key credits.</div>"
else:
    for m in matches:
        win_p=match_win_prob(0.55, m['ft'])
        html+=f"<div class='card'><b>{m['p1']} vs {m['p2']} — FT{m['ft']}</b> <span class='badge live'>BET365 LIVE ✅</span>"
        html+=f"<div class='section safe'><b>🛡️ Match Winner</b><table><tr><th>Player</th><th>True%</th><th>Fair</th><th>Bet365</th><th>EDGE</th></tr>"
        bh=m.get('book_h2h',{}); vals=list(bh.values())
        for idx,(name,true_p) in enumerate([(m['p1'],win_p),(m['p2'],1-win_p)]):
            book=list(bh.values())[idx] if len(vals)>idx else None
            if book:
                fair=1/true_p if true_p>0 else 99; edge=(true_p-(1/book))*100
                cls="pos" if edge>0 else "neg"
                html+=f"<tr><td><b>{name}</b></td><td>{true_p*100:.1f}%</td><td>{fair:.2f}</td><td class='odds'>{book:.2f}</td><td class='{cls}'>{edge:+.1f}%</td></tr>"
        html+="</table></div></div>"

html+=f"<div style='margin-top:20px;color:#777;font-size:11px'>API Live: {bool(raw)} | Events: {len(raw) if raw else 0} | Built {datetime.now(timezone.utc).isoformat()}</div></body></html>"
open("darts/index.html","w",encoding="utf-8").write(html)
print(f"Built HTML with {len(matches)} cards")
