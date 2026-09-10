def fetch_bet365():
    if not API_KEY:
        print("No ODDS_API_KEY secret set!")
        return None
    try:
        sports = requests.get(f"https://api.the-odds-api.com/v4/sports/?apiKey={API_KEY}", timeout=15).json()
        darts_leagues = [s['key'] for s in sports if 'darts' in s['key'].lower()]
        print(f"Darts leagues found: {darts_leagues}")
    except Exception as e:
        print(f"sports list failed: {e}")
        darts_leagues = []

    # Fallback + always include Modus + all PDC (Modus is ON now)
    fallback = [
        "darts_pdc_world_championship","darts_premier_league_darts",
        "darts_world_matchplay","darts_world_grand_prix","darts_grand_slam_of_darts",
        "darts_modus_super_series","darts_world_cup_of_darts","darts_european_tour",
        "darts_players_championship","darts_pdc_world_masters"
    ]
    # Use both found + fallback, unique
    if not darts_leagues:
        darts_leagues = fallback
    else:
        for f in fallback:
            if f not in darts_leagues:
                darts_leagues.append(f)

    all_events=[]
    for league in darts_leagues:
        try:
            url = f"https://api.the-odds-api.com/v4/sports/{league}/odds/?apiKey={API_KEY}&regions=uk&markets=h2h,totals&bookmakers=bet365&oddsFormat=decimal"
            r=requests.get(url,timeout=20)
            if r.status_code==200 and r.json():
                print(f"{league}: {len(r.json())} events")
                all_events.extend(r.json())
            else:
                print(f"{league}: {r.status_code}")
        except Exception as e:
            print(f"{league} err: {e}")
    return all_events if all_events else []
