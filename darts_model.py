import os, requests
from datetime import datetime, timezone
from math import comb

API_KEY = os.getenv("ODDS_API_KEY")
os.makedirs("darts", exist_ok=True)
print(f"KEY len={len(API_KEY) if API_KEY else 0}")

# STEP 1 - Find what darts leagues exist for YOUR key
sports_url = f"https://api.the-odds-api.com/v4/sports/?apiKey={API_KEY}"
r = requests.get(sports_url, timeout=15)
print(f"sports status: {r.status_code}")
all_sports = r.json()
darts_keys = []
for s in all_sports:
    if 'darts' in s['key'].lower() or s.get('group','').lower()=='darts':
        darts_keys.append(s['key'])
        print(f"FOUND DARTS LEAGUE: {s['key']} | {s.get('title')} | active={s.get('active')}")

if not darts_keys:
    print("No darts keys found, printing first 20 sports to debug:")
    for s in all_sports[:20]:
        print(f" - {s['key']} group={s.get('group')}")

# STEP 2 - Try each darts league + known Modus keys
to_try = list(set(darts_keys + [
    "darts_premier_league","darts_pdc_world_championship","darts_modus_super_series",
    "darts_world_matchplay","darts_world_grand_prix","darts_grand_slam_of_darts",
    "darts_world_cup_of_darts","darts_pdc_world_masters","darts_players_championship"
]))
print(f"Trying {len(to_try)} leagues: {to_try}")

all_events=[]
for league in to_try:
    url = f"https://api.the-odds-api.com/v4/sports/{league}/odds/?apiKey={API_KEY}&regions=uk&markets=h2h,totals&bookmakers=bet365&oddsFormat=decimal"
    try:
        resp = requests.get(url, timeout=20)
        if resp.status_code==200:
            data=resp.json()
            if data:
                print(f"{league}: {len(data)} EVENTS ✅")
                all_events.extend(data)
            else:
                print(f"{league}: 0 events")
        else:
            print(f"{league}: {resp.status_code} - {resp.text[:100]}")
    except Exception as e:
        print(f"{league} err {e}")

print(f"TOTAL EVENTS: {len(all_events)}")
# ... keep rest of your HTML building code same as before ...
# (copy from previous file from 'raw = all_events' onwards)

raw = all_events
matches=[]
for ev in raw[:10]:
    p1=ev.get('home_team','P1'); p2=ev.get('away_team','P2')
    book_h2h={}
    for bm in ev.get('bookmakers',[]):
        if bm['key']=='bet365':
            for mk in bm.get('markets',[]):
                if mk['key']=='h2h':
                    for o in mk['outcomes']: book_h2h[o['name']]=o['price']
    if book_h2h:
        matches.append({"p1":p1,"p2":p2,"ft":7,"book_h2h":book_h2h})

def match_win_prob(p_leg, ft):
    prob=0
    for k in range(ft):
        prob+=comb(ft+k-1,k)*(p_leg**ft)*((1-p_leg)**k)
    return prob

now = datetime.now(timezone.utc).strftime('%H:%M UTC %d %b')
html = f"""<!DOCTYPE html><html><head><meta charset='utf-8'><meta name='viewport' content='width=device-width,initial-scale=1'><title>Darts LIVE</title><style>body{{background:#0a0a0a;color:#eee;font-family:-apple-system;padding:12px;max-width:960px;margin:0 auto}}h1{{color:#ff6a00}}.card{{background:#151515;border:1px solid #333;border-radius:16px;padding:14px;margin:16px 0}}.badge{{padding:4px 10px;border-radius:20px;font-size:11px;font-weight:900}}.live{{background:#00ff88;color:#000}}table{{width:100%;border-collapse:collapse;margin-top:8px}}th{{color:#999;font-size:11px;text-align:left}}td{{padding:7px 4px;border-top:1px solid #2a2a2a;font-size:13px}}.odds{{color:#ffcc00;font-weight:800}}</style></head><body><h1>🟠 DARTS V3 LIVE</h1><div style='color:#999;font-size:13px'>{now} | Events: {len(raw)}</div>"""
if not matches:
    html+=f"<div class='card'><b>No events - check log #42</b><br>Checked leagues: {to_try}</div>"
else:
    for m in matches:
        html+=f"<div class='card'><b>{m['p1']} vs {m['p2']}</b> <span class='badge live'>BET365 LIVE ✅</span><br>"
        for k,v in m['book_h2h'].items():
            html+=f"{k}: <b class='odds'>{v}</b> "
        html+="</div>"
html+=f"<div style='color:#777;font-size:11px'>Built {datetime.now(timezone.utc).isoformat()} | Leagues tried: {len(to_try)}</div></body></html>"
open("darts/index.html","w",encoding="utf-8").write(html)
print(f"Built {len(matches)} cards")
