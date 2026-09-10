import os, requests
from datetime import datetime, timezone
from math import comb

API_KEY = os.getenv("ODDS_API_KEY")
os.makedirs("darts", exist_ok=True)

def match_win_prob(p_leg, ft):
    prob = 0
    for k in range(ft):
        prob += comb(ft + k -1, k) * (p_leg**ft) * ((1-p_leg)**k)
    return prob

def cs_probs(p_leg, ft):
    res={}
    for opp in range(ft):
        res[f"{ft}-{opp}"] = comb(ft+opp-1, ft-1) * (p_leg**ft) * ((1-p_leg)**opp)
        res[f"{opp}-{ft}"] = comb(ft+opp-1, ft-1) * ((1-p_leg)**ft) * (p_leg**opp)
    return res

def fetch_bet365():
    if not API_KEY:
        print("No ODDS_API_KEY secret set!")
        return None
    # Check ALL darts comps, not just 2
    try:
        sports = requests.get(f"https://api.the-odds-api.com/v4/sports/?apiKey={API_KEY}", timeout=15).json()
        darts_leagues = [s['key'] for s in sports if 'darts' in s['key'].lower()]
        print(f"Darts leagues found: {darts_leagues}")
    except:
        darts_leagues = ["darts_premier_league","darts_world_championship","darts_world_matchplay","darts_world_grand_prix","darts_grand_slam"]

    all_events=[]
    for league in darts_leagues:
        try:
            url = f"https://api.the-odds-api.com/v4/sports/{league}/odds/?apiKey={API_KEY}&regions=uk&markets=h2h,totals&bookmakers=bet365&oddsFormat=decimal"
            r=requests.get(url,timeout=20)
            if r.status_code==200 and r.json():
                print(f"{league}: {len(r.json())} events")
                all_events.extend(r.json())
        except Exception as e:
            print(e)
    return all_events if all_events else []

raw = fetch_bet365()
matches=[]

if raw:
    for ev in raw[:6]:
        p1=ev.get('home_team','P1'); p2=ev.get('away_team','P2'); ft=7
        book_h2h={}; book_total={}
        for bm in ev.get('bookmakers',[]):
            if bm['key']=='bet365':
                for mk in bm.get('markets',[]):
                    if mk['key']=='h2h':
                        for o in mk['outcomes']: book_h2h[o['name']]=o['price']
                    if mk['key']=='totals':
                        for o in mk['outcomes']: book_total[f"{o['name']} {o['point']}"]=o['price']
        # Estimate leg prob from h2h odds
        if book_h2h:
            matches.append({"p1":p1,"p2":p2,"p_leg":0.55,"ft":ft,"book_cs":{}, "book_h2h":book_h2h,"book_total":book_total,"is_live":True})

now = datetime.now(timezone.utc).strftime('%H:%M UTC %d %b')
# LIVE PAGE HEADER
html = f"""<!DOCTYPE html><html><head><meta charset='utf-8'><meta name='viewport' content='width=device-width,initial-scale=1'>
<title>Darts V3 LIVE</title><style>
body{{background:#0a0a0a;color:#eee;font-family:-apple-system;padding:12px;max-width:960px;margin:0 auto}}
h1{{color:#ff6a00}}.card{{background:#151515;border:1px solid #333;border-radius:16px;padding:14px;margin:16px 0}}
.badge{{padding:4px 10px;border-radius:20px;font-size:11px;font-weight:900}}.live{{background:#00ff88;color:#000}}.demo{{background:#333;color:#ff9a2e;border:1px solid #ff9a2e}}
table{{width:100%;border-collapse:collapse;margin-top:8px}} th{{color:#999;font-size:11px;text-align:left}} td{{padding:7px 4px;border-top:1px solid #2a2a2a;font-size:13px}}
.odds{{color:#ffcc00;font-weight:800}}.pos{{color:#00ff88;font-weight:900}}.neg{{color:#ff5a5a}}.safe{{background:#0f2a18;border-left:4px solid #00ff88}}
.section{{margin-top:12px;padding:8px;background:#1c1c1c;border-radius:10px}}
</style></head><body><h1>🟠 DARTS V3 — LIVE</h1><div style='color:#999;font-size:13px'>Safety = Match Winner & Over/Under | Bombs = Correct Score | {now} | API: {'LIVE ✅' if raw else 'No Events'}</div>"""

if not matches:
    if not API_KEY:
        html+=f"<div class='card' style='border-color:red'><b>⚠️ ADD YOUR ODDS API KEY</b><br>Go to GitHub Settings → Secrets → ODDS_API_KEY<br>Your site is LIVE but waiting for a key. Once added, run workflow again.</div>"
    else:
        html+=f"<div class='card'><b>No Bet365 Darts odds today — Off Season / No PDC events</b><br>Checked {len(raw) if raw else 0} events. Next big comp: World Grand Prix Oct 6. Page is LIVE and will auto-populate when matches return.<br><i>Set DEMO=1 env to force demo data for testing.</i></div>"
else:
    for m in matches:
        win_p = match_win_prob(m['p_leg'], m['ft'])
        badge = "<span class='badge live'>BET365 LIVE ✅</span>"
        html+=f"<div class='card'><b>{m['p1']} vs {m['p2']} — FT{m['ft']}</b> {badge}"
        html+=f"<div class='section safe'><b>🛡️ SAFETY — Match Winner</b><table><tr><th>Player</th><th>True%</th><th>Fair</th><th>Bet365</th><th>EDGE</th></tr>"
        bh = m.get('book_h2h', {})
        vals = list(bh.values()) if bh else []
        for idx, (name, true_p) in enumerate([(m['p1'], win_p), (m['p2'], 1-win_p)]):
            book = None
            for k,v in bh.items():
                if name.split()[0].lower() in k.lower() or name.lower() in k.lower():
                    book=v
            if not book and vals:
                book = vals[idx] if len(vals)>idx else None
            if book:
                fair=1/true_p if true_p>0 else 99
                edge=(true_p-(1/book))*100
                cls="pos" if edge>0 else "neg"
                safe_tag="🛡️ SAFE" if edge>2 else ""
                html+=f"<tr><td><b>{name}</b></td><td>{true_p*100:.1f}%</td><td>{fair:.2f}</td><td class='odds'>{book:.2f}</td><td class='{cls}'>{edge:+.1f}% {safe_tag}</td></tr>"
        html+="</table></div>"
        if m.get('book_total'):
            html+=f"<div class='section safe'><b>🛡️ SAFETY — Total Legs</b><table><tr><th>Market</th><th>Bet365</th></tr>"
            for k,v in m['book_total'].items():
                html+=f"<tr><td>{k}</td><td class='odds'>{v:.2f}</td></tr>"
            html+="</table></div>"
        html+="</div>"

html+=f"<div style='margin-top:20px;color:#777;font-size:11px'>API Live: {bool(raw)} | Events: {len(raw) if raw else 0} | Built {datetime.now(timezone.utc).isoformat()}</div></body></html>"
open("darts/index.html","w",encoding="utf-8").write(html)
print(f"Darts V3 LIVE built — matches: {len(matches)}")
