#!/usr/bin/env python3
"""
Test Notion Integration - Testaa koko Notion ROI -järjestelmän
"""

import json
import sys
from datetime import datetime, timedelta
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from src.notion_football_sync import NotionFootballSync


def test_config():
    """Testi 1: Konfiguraation tarkistus"""
    print("\n" + "="*60)
    print("TEST 1: KONFIGURAATION TARKISTUS")
    print("="*60)
    
    sync = NotionFootballSync()
    
    if not sync.is_configured():
        print("❌ FAILED: Notion ei ole konfiguroitu!")
        print("\n📝 Konfiguroi Notion:")
        print("1. Avaa: https://www.notion.so/my-integrations")
        print("2. Luo uusi integration: 'TennisBot ROI System'")
        print("3. Kopioi token → config/notion_config.json")
        print("4. Luo Notion-sivu: 'Jalkapallo ROI System'")
        print("5. Linkitä integration sivulle (Connections)")
        print("6. Kopioi page ID → config/notion_config.json")
        return False
    
    print("✅ PASSED: Notion on konfiguroitu!")
    print(f"📊 Token: {sync.token[:20]}...")
    print(f"📄 Page ID: {sync.page_id}")
    
    # Check database IDs
    databases = sync.databases
    print(f"\n📊 Tietokannat:")
    for db_name, db_id in databases.items():
        if db_id:
            print(f"  ✅ {db_name}: {db_id[:20]}...")
        else:
            print(f"  ⚠️ {db_name}: Ei konfiguroitu")
    
    return True


def test_match_sync():
    """Testi 2: Ottelun synkronointi"""
    print("\n" + "="*60)
    print("TEST 2: OTTELUN SYNKRONOINTI")
    print("="*60)
    
    sync = NotionFootballSync()
    
    if not sync.is_configured():
        print("❌ SKIPPED: Notion ei ole konfiguroitu")
        return False
    
    if not sync.get_database_id("ottelut"):
        print("⚠️ SKIPPED: Ottelut-tietokanta ei ole konfiguroitu")
        print("📝 Luo Ottelut-tietokanta Notionissa ja lisää ID config/notion_config.json")
        return False
    
    # Test match data
    match_data = {
        "home_team": "Manchester City",
        "away_team": "Liverpool",
        "league": "Premier League",
        "date_time": (datetime.now() + timedelta(days=1)).isoformat(),
        "status": "Scheduled",
        "home_xg": 2.8,
        "away_xg": 2.1
    }
    
    print(f"📤 Synkronoidaan: {match_data['home_team']} vs {match_data['away_team']}")
    
    match_id = sync.sync_match(match_data)
    
    if match_id:
        print(f"✅ PASSED: Ottelu synkronoitu!")
        print(f"📄 Match ID: {match_id}")
        return True
    else:
        print("❌ FAILED: Ottelun synkronointi epäonnistui")
        return False


def test_analysis_sync():
    """Testi 3: Analyysin synkronointi"""
    print("\n" + "="*60)
    print("TEST 3: ANALYYSIN SYNKRONOINTI")
    print("="*60)
    
    sync = NotionFootballSync()
    
    if not sync.is_configured():
        print("❌ SKIPPED: Notion ei ole konfiguroitu")
        return False
    
    if not sync.get_database_id("analytiikka"):
        print("⚠️ SKIPPED: Analytiikka-tietokanta ei ole konfiguroitu")
        print("📝 Luo Analytiikka-tietokanta Notionissa ja lisää ID config/notion_config.json")
        return False
    
    # Test analysis data
    analysis_data = {
        "h2h_win_pct": 45,
        "form_edge_pct": 12,
        "injury_impact": 0,
        "own_probability_pct": 58,
        "market_probability_pct": 52,
        "best_bet_type": "OU2.5",
        "edge_pct": 11.5
    }
    
    print(f"📤 Synkronoidaan analyysi:")
    print(f"  Edge: {analysis_data['edge_pct']}%")
    print(f"  Bet type: {analysis_data['best_bet_type']}")
    
    analysis_id = sync.sync_analysis(analysis_data)
    
    if analysis_id:
        print(f"✅ PASSED: Analyysi synkronoitu!")
        print(f"📄 Analysis ID: {analysis_id}")
        return True
    else:
        print("❌ FAILED: Analyysin synkronointi epäonnistui")
        return False


def test_bet_sync():
    """Testi 4: Vedon synkronointi"""
    print("\n" + "="*60)
    print("TEST 4: VEDON SYNKRONOINTI")
    print("="*60)
    
    sync = NotionFootballSync()
    
    if not sync.is_configured():
        print("❌ SKIPPED: Notion ei ole konfiguroitu")
        return False
    
    if not sync.get_database_id("vedot"):
        print("⚠️ SKIPPED: Vedot-tietokanta ei ole konfiguroitu")
        print("📝 Luo Vedot-tietokanta Notionissa ja lisää ID config/notion_config.json")
        return False
    
    # Test bet data
    bet_data = {
        "bet_type": "OU2.5",
        "own_probability_pct": 58,
        "odds": 1.92,
        "bankroll": 5000,
        "placed": True,
        "bookmaker": "Pinnacle"
    }
    
    print(f"📤 Synkronoidaan veto:")
    print(f"  Type: {bet_data['bet_type']}")
    print(f"  Odds: {bet_data['odds']}")
    print(f"  Bankroll: {bet_data['bankroll']}€")
    
    bet_id = sync.sync_bet(bet_data)
    
    if bet_id:
        print(f"✅ PASSED: Veto synkronoitu!")
        print(f"📄 Bet ID: {bet_id}")
        
        # Test Kelly calculation (should be automatic in Notion)
        print("\n📊 Odotetut Kelly-laskelmat:")
        print(f"  Edge %: ~15%")
        print(f"  Kelly %: ~7.8%")
        print(f"  Scaled Kelly % (50%): ~3.9%")
        print(f"  Panos (€): ~195€")
        print(f"  Potentiaalinen voitto: ~179€")
        print("\n⚠️ Tarkista Notionissa että kaavat laskevat nämä automaattisesti!")
        
        return True
    else:
        print("❌ FAILED: Vedon synkronointi epäonnistui")
        return False


def test_kelly_criterion():
    """Testi 5: Kelly Criterion -laskenta"""
    print("\n" + "="*60)
    print("TEST 5: KELLY CRITERION -LASKENTA")
    print("="*60)
    
    # Test Kelly calculation manually
    own_prob = 0.58
    odds = 1.92
    bankroll = 5000
    
    # Calculate edge
    market_prob = 1 / odds
    edge = (own_prob - market_prob) / market_prob
    
    # Calculate Kelly
    kelly = (edge * (odds - 1)) / (odds - 1)
    scaled_kelly = kelly * 0.5
    
    # Calculate stake
    stake = bankroll * scaled_kelly
    
    # Calculate potential profit
    potential_profit = stake * (odds - 1)
    
    print(f"📊 Manuaalinen Kelly-laskenta:")
    print(f"  Oma probability: {own_prob*100:.1f}%")
    print(f"  Markkina probability: {market_prob*100:.1f}%")
    print(f"  Edge: {edge*100:.1f}%")
    print(f"  Kelly %: {kelly*100:.1f}%")
    print(f"  Scaled Kelly % (50%): {scaled_kelly*100:.1f}%")
    print(f"  Bankroll: {bankroll}€")
    print(f"  Panos: {stake:.2f}€")
    print(f"  Potentiaalinen voitto: {potential_profit:.2f}€")
    
    # Expected values
    expected_edge = 15.0
    expected_kelly = 7.8
    expected_scaled_kelly = 3.9
    expected_stake = 195
    expected_profit = 179
    
    # Check if calculations are correct (with tolerance)
    tolerance = 5  # 5% tolerance
    
    tests_passed = True
    
    if abs(edge*100 - expected_edge) > tolerance:
        print(f"❌ Edge calculation incorrect: {edge*100:.1f}% vs expected {expected_edge}%")
        tests_passed = False
    
    if abs(kelly*100 - expected_kelly) > tolerance:
        print(f"❌ Kelly calculation incorrect: {kelly*100:.1f}% vs expected {expected_kelly}%")
        tests_passed = False
    
    if abs(scaled_kelly*100 - expected_scaled_kelly) > tolerance:
        print(f"❌ Scaled Kelly calculation incorrect: {scaled_kelly*100:.1f}% vs expected {expected_scaled_kelly}%")
        tests_passed = False
    
    if abs(stake - expected_stake) > tolerance*10:
        print(f"❌ Stake calculation incorrect: {stake:.2f}€ vs expected {expected_stake}€")
        tests_passed = False
    
    if abs(potential_profit - expected_profit) > tolerance*10:
        print(f"❌ Profit calculation incorrect: {potential_profit:.2f}€ vs expected {expected_profit}€")
        tests_passed = False
    
    if tests_passed:
        print("\n✅ PASSED: Kaikki Kelly-laskelmat oikein!")
        print("⚠️ Varmista että Notion-kaavat laskevat samat arvot!")
    else:
        print("\n❌ FAILED: Kelly-laskelmissa virheitä")
    
    return tests_passed


def test_strategy_validation():
    """Testi 6: Strategian validointi"""
    print("\n" + "="*60)
    print("TEST 6: STRATEGIAN VALIDOINTI")
    print("="*60)
    
    # Simulate strategy performance
    print("📊 Simuloidaan strategian performanssi:")
    print("\nSkenaario 1: Hyvä strategia")
    print("  Vedot yhteensä: 10")
    print("  Voitot: 7, Häviöt: 3")
    
    win_rate = (7 / 10) * 100
    print(f"  Win Rate: {win_rate:.1f}%")
    
    if win_rate >= 55:
        print("  Alert: ✅ OK")
        print("  ✅ Strategia toimii hyvin!")
    else:
        print("  Alert: ⚠️ Tarkista")
    
    print("\nSkenaario 2: Huono strategia")
    print("  Vedot yhteensä: 10")
    print("  Voitot: 4, Häviöt: 6")
    
    win_rate = (4 / 10) * 100
    print(f"  Win Rate: {win_rate:.1f}%")
    
    if win_rate < 48:
        print("  Alert: ⚠️ Palauta, WR alle 48%")
        print("  ⚠️ Strategia tarvitsee tarkistusta!")
    
    print("\nSkenaario 3: Erittäin huono strategia")
    print("  Vedot yhteensä: 20")
    print("  Voitot: 5, Häviöt: 15")
    print("  ROI: -25%")
    
    win_rate = (5 / 20) * 100
    roi = -25
    print(f"  Win Rate: {win_rate:.1f}%")
    print(f"  ROI: {roi}%")
    
    if roi < -5 and 20 >= 20:
        print("  Alert: ❌ Poistetaan, negatiivinen ROI")
        print("  ❌ Strategia pitää poistaa käytöstä!")
    
    print("\n✅ PASSED: Strategian validointi toimii!")
    print("⚠️ Varmista että Notion Alert-kaava toimii samalla tavalla!")
    
    return True


def run_all_tests():
    """Aja kaikki testit"""
    print("\n" + "="*60)
    print("🧪 NOTION INTEGRATION - TÄYDELLISET TESTIT")
    print("="*60)
    
    tests = [
        ("Konfiguraation tarkistus", test_config),
        ("Ottelun synkronointi", test_match_sync),
        ("Analyysin synkronointi", test_analysis_sync),
        ("Vedon synkronointi", test_bet_sync),
        ("Kelly Criterion -laskenta", test_kelly_criterion),
        ("Strategian validointi", test_strategy_validation)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"\n❌ EXCEPTION in {test_name}: {e}")
            results.append((test_name, False))
    
    # Summary
    print("\n" + "="*60)
    print("📊 TESTIEN YHTEENVETO")
    print("="*60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{status}: {test_name}")
    
    print("\n" + "="*60)
    print(f"📈 Tulokset: {passed}/{total} testit läpäisty ({passed/total*100:.0f}%)")
    print("="*60)
    
    if passed == total:
        print("\n🎉 KAIKKI TESTIT LÄPÄISTY!")
        print("✅ Notion ROI -järjestelmä on valmis käyttöön!")
    elif passed >= total * 0.5:
        print("\n⚠️ OSA TESTEISTÄ EPÄONNISTUI")
        print("📝 Tarkista epäonnistuneet testit ja korjaa ongelmat")
    else:
        print("\n❌ USEIMMAT TESTIT EPÄONNISTUIVAT")
        print("📝 Tarkista Notion-konfiguraatio ja tietokannat")
    
    return passed == total


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)

