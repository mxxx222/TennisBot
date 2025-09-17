#!/usr/bin/env python3
import os, re, json, time, asyncio, aiohttp, websockets
from urllib.parse import urlencode

API_BASE = "https://api.api-tennis.com/tennis/"
API_KEY  = os.getenv("TENNIS_API_KEY")  # .env: TENNIS_API_KEY=xxxx

def _url(method: str, **params):
    q = {"method": method, "APIkey": API_KEY}
    q.update(params)
    return f"{API_BASE}?{urlencode(q)}"

async def _get(session, method, **params):
    async with session.get(_url(method, **params), timeout=30) as r:
        r.raise_for_status()
        data = await r.json(content_type=None)
        if not data or data.get("success") != 1:
            raise RuntimeError(f"API error: {data}")
        return data["result"]

async def search_match(session, date_iso: str, p1: str, p2: str):
    """
    Palauttaa best-match event_id annetulle pelaajaparille ja päivälle.
    """
    # 1) listaa päivän ottelut
    # yleinen metodi on yleensä get_events / get_events_by_date tms.
    # kokeillaan geneerisesti:
    try_methods = [
        ("get_events", {"date_start": date_iso, "date_stop": date_iso}),
        ("get_events_day", {"date": date_iso}),
    ]
    events = []
    for m, params in try_methods:
        try:
            events = await _get(session, m, **params)
            if events: break
        except Exception:
            continue
    if not events:
        raise RuntimeError("Ei tapahtumia annetulle päivälle.")

    norm = lambda s: re.sub(r"[^a-z]", "", s.lower())
    n1, n2 = norm(p1), norm(p2)

    # 2) etsi event, jossa molemmat nimet
    best = None
    for ev in events:
        names = " ".join([str(ev.get(k,"")) for k in ("event_home_player","event_away_player","event_home_team","event_away_team")])
        nm = norm(names)
        if n1 in nm and n2 in nm:
            best = ev
            break
    if not best:
        # fallback: löysin vain toisen nimen -> valitse lähin
        for ev in events:
            names = " ".join([str(ev.get(k,"")) for k in ("event_home_player","event_away_player","event_home_team","event_away_team")])
            nm = norm(names)
            if n1 in nm or n2 in nm:
                best = ev; break
    if not best:
        raise RuntimeError("Ottelua ei löytynyt.")
    return best["event_key"] if "event_key" in best else best["match_id"]

async def get_prematch_bundle(session, event_id):
    """
    Palauttaa prematch-paketin: info + kertoimet + H2H jos saatavilla.
    """
    out = {"event_id": event_id}
    # Perusinfo
    for m in ("get_event", "get_event_details"):
        try:
            res = await _get(session, m, event_key=event_id)
            out["info"] = res[0] if isinstance(res, list) and res else res
            break
        except Exception:
            pass
    # Kertoimet
    for m in ("get_odds", "get_event_odds"):
        try:
            out["odds"] = await _get(session, m, event_key=event_id)
            break
        except Exception:
            pass
    # H2H
    try:
        hm = out["info"].get("event_home_player") or out["info"].get("event_home_team")
        aw = out["info"].get("event_away_player") or out["info"].get("event_away_team")
        if hm and aw:
            out["h2h"] = await _get(session, "get_h2h", first_player=hm, second_player=aw)
    except Exception:
        pass
    return out

async def live_ws(event_id: str, ws_url: str, on_msg=print):
    """
    Kuuntelee tennisapi.com WebSocketia ja suodattaa event_id:n viestit.
    HUOM: syötä oikea ws_url palveluntarjoajalta (esim. wss://live.tennisapi.com/stream)
    """
    async for _ in range(1):
        async with websockets.connect(ws_url, ping_interval=20, ping_timeout=20) as ws:
            # useimmiten täytyy subscribe: {"action":"subscribe","event_key":event_id}
            await ws.send(json.dumps({"action":"subscribe","event_key":str(event_id)}))
            async for msg in ws:
                try:
                    data = json.loads(msg)
                except Exception:
                    data = {"raw": msg}
                if str(data.get("event_key") or data.get("match_id")) == str(event_id):
                    on_msg(data)

async def main():
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument("--date", required=True, help="YYYY-MM-DD")
    p.add_argument("--match", required=True, help="Esim. 'Sinner vs Alcaraz'")
    p.add_argument("--live", action="store_true", help="Kuuntele live WS")
    p.add_argument("--ws_url", default=os.getenv("TENNIS_WS_URL",""))
    args = p.parse_args()
    
    if not API_KEY:
        raise SystemExit("Virhe: TENNIS_API_KEY ympäristömuuttuja puuttuu. Aseta se .env-tiedostossa tai ympäristössä.")
    
    p1, p2 = [s.strip() for s in re.split(r"vs|,|-", args.match, maxsplit=1)]

    async with aiohttp.ClientSession() as session:
        event_id = await search_match(session, args.date, p1, p2)
        bundle = await get_prematch_bundle(session, event_id)
        print(json.dumps(bundle, ensure_ascii=False, indent=2))

        if args.live:
            if not args.ws_url:
                raise SystemExit("Anna --ws_url tai TENNIS_WS_URL ympäristömuuttuja.")
            print("\n[WS] Kuunnellaan liveä… Ctrl+C lopettaa.\n")
            await live_ws(event_id, args.ws_url)

if __name__ == "__main__":
    asyncio.run(main())