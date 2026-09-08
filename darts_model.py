import os, requests, json
from datetime import datetime, timezone
from math import comb

API_KEY = os.getenv("ODDS_API_KEY")
os.makedirs("darts", exist_ok=True)

def match_win_prob(p_leg, ft):
    # Prob to win FT legs before opponent (negative binomial)
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

DEFAULT = [
 {"p1":"Luke Littler","p2":"Luke Humphries","p_leg":0.57,"ft":7,"book_cs":{"7-4":9.5,"7-5":7.0,"7-3":11.0,"6-7":5.5},"book_h2h":{"Littler":1.85,"Humphries":2.05},"book_total":{"Over 12.5":1.90,"Under 12.5":1.90}},
 {"p1":"Michael van Gerwen","p2":"Gerwyn Price","p_leg":0.55,"ft":7,"book_cs":{"7-5":8.0,"7-4":9.0,"6-7":5.0},"book_h2h":{"van Gerwen":1.95,"Price":1.95},"book_total":{"Over 12.5":1.85,"Under 12.5":1.95}},
]

def fetch_bet365():
    if not API_KEY: return None
    leagues = ["darts_premier_league","darts_world_championship"]
    all_events=[]
    for league in leagues:
        try:
            url = f"https://api.the-odds-api.com/v4/sports/{league}/odds/?apiKey={API_KEY}&regions=uk&markets=h2h,correct_score,totals,spreads&bookmakers=bet365&oddsFormat=decimal"
            r=requests.get(url,timeout=20)
            print(f"{league} {r.status_code} left {r.headers.get('x-requests-remaining')}")
            if r.status_code==200 and r.json():
                all_events.extend(r.json())
                open(f"darts/bet365_raw_{league}.json","w").write(json.dumps(r.json(),indent=2))
        except Exception as e:
            print(e)
    return all_events if all_events else None

raw = fetch_bet365()
matches=[]

if raw:
    for ev in raw[:6]:
        p1=ev.get('home_team','P1'); p2=ev.get('away_team','P2'); ft=7
        book_cs={}; book_h2h={}; book_total={}
        for bm in ev.get('bookmakers',[]):
            if bm['key']=='bet365':
                for mk in bm.get('markets',[]):
                    if mk['key']=='correct_score':
                        for o in mk['outcomes']: book_cs[o['name']]=o['price']
                    if mk['key']=='h2h':
                        for o in mk['outcomes']: book_h2h[o['name']]=o['price']
                    if mk['key']=='totals':
                        for o in mk['outcomes']: book_total[f"{o['name']} {o['point']}"]=o['price']
        if book_h2h or book_cs:
            matches.append({"p1":p1,"p2":p2,"p_leg":0.55,"ft":ft,"book_cs":book_cs,"book_h2h":book_h2h,"book_total":book_total,"is_live":True})
if not matches:
    for m in DEFAULT:
        matches.append({**m,"is_live":False})

now = datetime.now(timezone.utc).strftime('%H:%M UTC %d %b')
html = f"""<!DOCTYPE html><html><head><meta charset='utf-8'><meta name='viewport' content='width=device-width,initial-scale=1'>
<title>Darts V3 Safety+Bomb</title><style>
body{{background:#0a0a0a;color:#eee;font-family:-apple-system;padding:12px;max-width:960px;margin:0 auto}}
h1{{color:#ff6a00}}.card{{background:#151515;border:1px solid #333;border-radius:16px;padding:14px;margin:16px 0}}
.badge{{padding:4px 10px;border-radius:20px;font-size:11px;font-weight:900}}.live{{background:#ff6a00;color:#000}}.demo{{background:#333;color:#ff9a2e;border:1px solid #ff9a2e}}
table{{width:100%;border-collapse:collapse;margin-top:8px}} th{{color:#999;font-size:11px;text-align:left}} td{{padding:7px 4px;border-top:1px solid #2a2a2a;font-size:13px}}
.odds{{color:#ffcc00;font-weight:800}}.pos{{color:#00ff88;font-weight:900}}.neg{{color:#ff5a5a}}.safe{{background:#0f2a18;border-left:4px solid #00ff88}}.bomb{{background:#2a1600;border-left:4px solid #ff6a00}}
.section{{margin-top:12px;padding:8px;background:#1c1c1c;border-radius:10px}}
</style></head><body><h1>🟠 DARTS V3 — Safety + Bombs</h1><div style='color:#999;font-size:13px'>Safety = Match Winner & Over/Under | Bombs = Correct Score | {now}</div>"""

for m in matches:
    win_p = match_win_prob(m['p_leg'], m['ft'])
    cs = cs_probs(m['p_leg'], m['ft'])
    badge = "<span class='badge live'>BET365 LIVE ✅</span>" if m.get('is_live') else "<span class='badge demo'>DEMO — Off Season</span>"
    html+=f"<div class='card'><b>{m['p1']} vs {m['p2']} — FT{m['ft']}</b> {badge}"

    # 1 SAFETY - MATCH WINNER
    html+=f"<div class='section safe'><b>🛡️ SAFETY — Match Winner</b><table><tr><th>Player</th><th>True%</th><th>Fair</th><th>Bet365</th><th>EDGE</th></tr>"
    # p1
    for name, true_p in [(m['p1'], win_p), (m['p2'], 1-win_p)]:
        book = None
        for k,v in m.get('book_h2h',{{}}).items():
            if name.split()[0].lower() in k.lower() or name.lower() in k.lower():
                book=v
        if not book and m.get('book_h2h'): # fallback first 2
            vals=list(m['book_h2h'].values())
            book = vals[0] if name==m['p1'] else vals[1] if len(vals)>1 else None
        if book:
            fair=1/true_p if true_p>0 else 99
            edge=(true_p-(1/book))*100
            cls="pos" if edge>0 else "neg"
            safe_tag="🛡️ SAFE" if edge>2 else ""
            html+=f"<tr><td><b>{name}</b></td><td>{true_p*100:.1f}%</td><td>{fair:.2f}</td><td class='odds'>{book:.2f}</td><td class='{cls}'>{edge:+.1f}% {safe_tag}</td></tr>"
    html+="</table></div>"

    # 2 SAFETY - TOTAL LEGS
    if m.get('book_total'):
        html+=f"<div class='section safe'><b>🛡️ SAFETY — Total Legs</b><table><tr><th>Market</th><th>Bet365</th><th>Note</th></tr>"
        for k,v in m['book_total'].items():
            html+=f"<tr><td>{k}</td><td class='odds'>{v:.2f}</td><td style='color:#8f8'>Lower risk than CS</td></tr>"
        html+="</table></div>"

    # 3 BOMB - CORRECT SCORE
    html+=f"<div class='section bomb'><b>💣 BOMB — Correct Score</b><table><tr><th>Score</th><th>True%</th><th>Fair</th><th>Bet365</th><th>EDGE</th></tr>"
    rows=[]
    for sc,tp in cs.items():
        if sc in m.get('book_cs',{}):
            book=m['book_cs'][sc]; fair=1/tp if tp>0 else 99; edge=(tp-(1/book))*100
            rows.append((sc,tp,fair,book,edge))
    for sc,tp,fair,book,edge in sorted(rows, key=lambda x: -x[4]):
        cls="pos" if edge>0 else "neg"
        tag="💣 BIG" if book>=8 and edge>3 else ""
        if edge>5: tag="💣💣 MEGA"
        html+=f"<tr><td><b>{sc}</b></td><td>{tp*100:.1f}%</td><td>{fair:.2f}</td><td class='odds'>{book:.2f}</td><td class='{cls}'>{edge:+.1f}% {tag}</td></tr>"
    html+="</table></div></div>"

html+=f"<div style='margin-top:20px;color:#777;font-size:11px'>API Live: {bool(raw)} | Built {datetime.now(timezone.utc).isoformat()}<br><a href='../snooker/' style='color:#ff6a00'>→ Snooker V1</a></div></body></html>"
open("darts/index.html","w",encoding="utf-8").write(html)
print("Darts V3 built")
