"""
Utility to parse raw betting history text, extract SINGLE bets, compute ROI,
and export structured data to JSON and CSV.

Usage (from project root):

    python parse_betting_history.py input.txt --json single_bets.json --csv single_bets.csv

`input.txt` should contain the raw copy-paste from the betting site, similar
to the long example provided in the task description.
"""

from __future__ import annotations

import argparse
import csv
import json
import logging
import re
from dataclasses import asdict, dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


logger = logging.getLogger(__name__)


@dataclass
class BetRecord:
    """
    Normalized representation of a single betting ticket.

    This focuses on SINGLE bets; COMBO and other bet types are parsed only
    if needed for diagnostics but are not included in the main output.
    """

    ticket_id: str
    placed_at: datetime
    event_datetime: Optional[datetime]
    category: str  # e.g. "SINGLE", "COMBO", "UNKNOWN"

    sport_league: Optional[str]
    match: Optional[str]

    bet_type: Optional[str]  # e.g. "Winner", "Total over 2.5", "1x2"
    selection: Optional[str]  # e.g. "Inter Miami CF", "Over 2.5"

    odds: Optional[float]
    stake: Optional[float]

    result: str  # "WON", "LOST", "CASHED_OUT", "REFUND", "OPEN", "UNKNOWN"
    payout: Optional[float]
    profit: Optional[float]
    roi: Optional[float]  # percentage, e.g. 12.5 for +12.5%

    # Raw text can be useful for debugging parsing issues
    raw_block: str = field(repr=False)

    def to_serializable(self) -> Dict[str, Any]:
        """Convert to JSON-serializable dict."""
        data = asdict(self)
        # Convert datetimes to ISO strings
        data["placed_at"] = self.placed_at.isoformat()
        if self.event_datetime is not None:
            data["event_datetime"] = self.event_datetime.isoformat()
        else:
            data["event_datetime"] = None
        return data


# Patterns for dates in the raw text
PLACED_AT_RE = re.compile(
    r"^(?P<month>[A-Z][a-z]{2})\s+(?P<day>\d{1,2}),\s+(?P<year>\d{4})\s+at\s+(?P<hour>\d{1,2}):(?P<minute>\d{2})"
)

EVENT_AT_RE = re.compile(
    r"^(?P<month>[A-Z][a-z]{2})\s+(?P<day>\d{1,2})\s+at\s+(?P<hour>\d{1,2}):(?P<minute>\d{2})"
)

TICKET_ID_RE = re.compile(r"Ticket ID:\s*(\d+)")

NUMBER_RE = re.compile(r"([-+]?\d+(?:\.\d+)?)")


RESULT_KEYWORDS = {
    "WON": "WON",
    "YOU WON": "WON",
    "LOST": "LOST",
    "CASHED OUT": "CASHED_OUT",
    "YOU CASHED OUT": "CASHED_OUT",
    "BET REFUND": "REFUND",
    "REFUND": "REFUND",
    "OPEN": "OPEN",
}


def _parse_placed_at(lines: List[str]) -> Optional[Tuple[datetime, int]]:
    """Find and parse the 'placed at' datetime from the block."""
    for idx, line in enumerate(lines):
        m = PLACED_AT_RE.match(line.strip())
        if not m:
            continue
        try:
            dt = datetime.strptime(line.strip(), "%b %d, %Y at %H:%M")
            return dt, idx
        except ValueError:
            logger.warning("Failed to parse placed_at line: %r", line)
            return None
    return None


def _parse_event_datetime(lines: List[str], start_idx: int, placed_year: int) -> Optional[datetime]:
    """
    Parse the event datetime (which often omits the year) after a given index.
    """
    for line in lines[start_idx + 1 :]:
        text = line.strip()
        if not text:
            continue
        # First, try full format with year (same as placed_at)
        try:
            dt = datetime.strptime(text, "%b %d, %Y at %H:%M")
            return dt
        except ValueError:
            pass

        # Then, try the shorter format and attach year from placed_at
        m = EVENT_AT_RE.match(text)
        if m:
            try:
                dt = datetime.strptime(
                    f"{text}, {placed_year}", "%b %d at %H:%M, %Y"
                )
                return dt
            except ValueError:
                logger.warning("Failed to parse event datetime line: %r", line)
                return None
    return None


def _normalize_result(lines: List[str]) -> str:
    """
    Determine the normalized result keyword for the bet block.
    Priority is given to explicit status lines near the top.
    """
    for line in lines[:10]:  # status is always near the top
        text = line.strip().upper()
        if not text:
            continue
        for key, normalized in RESULT_KEYWORDS.items():
            if text == key:
                return normalized
    # Fallback: inspect any line that contains a known keyword
    for line in lines:
        text = line.strip().upper()
        for key, normalized in RESULT_KEYWORDS.items():
            if key in text:
                return normalized
    return "UNKNOWN"


def _detect_category(category_hint: str, block_text: str) -> str:
    """
    Decide whether the ticket is SINGLE or COMBO.

    We trust the explicit category if given; if it's UNKNOWN, we infer from
    the presence of 'TOTAL ODDS' (strong COMBO indicator).
    """
    if category_hint in {"SINGLE", "COMBO"}:
        return category_hint

    if "TOTAL ODDS" in block_text:
        return "COMBO"
    return "SINGLE"


def _extract_ticket_id(lines: List[str]) -> Optional[str]:
    for line in lines:
        m = TICKET_ID_RE.search(line)
        if m:
            return m.group(1)
    return None


def _extract_sport_league_and_match(lines: List[str], start_idx: int) -> Tuple[Optional[str], Optional[str]]:
    """
    After the event datetime line, the next non-empty line is typically the
    sport/league descriptor, followed by the match line (containing 'vs').
    """
    sport_league = None
    match = None
    # Find first non-empty after start_idx as sport/league
    idx = start_idx + 1
    while idx < len(lines) and not lines[idx].strip():
        idx += 1
    if idx < len(lines):
        sport_league = lines[idx].strip() or None
        idx += 1
    # Find first line that looks like a match (contains 'vs')
    while idx < len(lines):
        text = lines[idx].strip()
        if "vs" in text or "vs" in text.replace(" ", ""):
            match = text
            break
        # In some football lines, the market is immediately after league and the
        # match is already embedded there; we still try to capture a 'vs' line.
        idx += 1
    return sport_league, match


def _extract_market_and_odds(lines: List[str], ticket_idx: int) -> Tuple[Optional[str], Optional[float]]:
    """
    After the Ticket ID line, the first non-empty line that is not a keyword
    like 'Stake' or 'TOTAL ODDS' is treated as the market/selection description.
    The next numeric-looking line is treated as odds.
    """
    market: Optional[str] = None
    odds: Optional[float] = None

    i = ticket_idx + 1
    # Find market/selection line
    while i < len(lines):
        text = lines[i].strip()
        if not text:
            i += 1
            continue
        upper = text.upper()
        if any(
            kw in upper
            for kw in (
                "STAKE",
                "TOTAL ODDS",
                "YOU WON",
                "YOU CASHED OUT",
                "BET REFUND",
                "REFUND",
                "ODDS FORMAT",
            )
        ):
            i += 1
            continue
        market = text
        i += 1
        break

    # Find odds line
    while i < len(lines):
        text = lines[i].strip()
        if not text:
            i += 1
            continue
        m = NUMBER_RE.search(text)
        if m:
            try:
                odds = float(m.group(1))
                break
            except ValueError:
                pass
        i += 1

    return market, odds


def _extract_stake(lines: List[str]) -> Optional[float]:
    for idx, line in enumerate(lines):
        if line.strip().upper() == "STAKE":
            # Next non-empty line should contain amount
            for j in range(idx + 1, len(lines)):
                text = lines[j].strip()
                if not text:
                    continue
                m = NUMBER_RE.search(text)
                if m:
                    try:
                        return float(m.group(1))
                    except ValueError:
                        logger.warning("Failed to parse stake from line: %r", text)
                        return None
            break
    return None


def _extract_payout(lines: List[str]) -> Optional[Tuple[float, str]]:
    """
    Extract explicit payout from 'YOU WON' or 'YOU CASHED OUT' lines.
    Returns (amount, normalized_result) if found.
    """
    for idx, line in enumerate(lines):
        upper = line.strip().upper()
        if "YOU WON" in upper or "YOU CASHED OUT" in upper:
            normalized = "WON" if "YOU WON" in upper else "CASHED_OUT"
            # Next non-empty line should have amount
            for j in range(idx + 1, len(lines)):
                text = lines[j].strip()
                if not text:
                    continue
                m = NUMBER_RE.search(text)
                if m:
                    try:
                        return float(m.group(1)), normalized
                    except ValueError:
                        logger.warning("Failed to parse payout from line: %r", text)
                        return None
            break
    return None


def _compute_financials(
    result: str,
    stake: Optional[float],
    odds: Optional[float],
    explicit_payout: Optional[float],
) -> Tuple[Optional[float], Optional[float], Optional[float]]:
    """
    Compute payout, profit, and ROI given the available information.
    """
    if stake is None or stake <= 0:
        return explicit_payout, None, None

    payout: Optional[float] = explicit_payout

    if payout is None:
        if result == "WON" and odds is not None:
            payout = stake * odds
        elif result == "LOST":
            payout = 0.0
        elif result == "REFUND":
            payout = stake
        # For CASHED_OUT or OPEN without explicit payout, leave as None

    if payout is None:
        return None, None, None

    profit = payout - stake
    roi = (profit / stake) * 100 if stake else None
    return payout, profit, roi


def split_into_blocks(raw_text: str) -> List[Tuple[str, str]]:
    """
    Split the raw text into logical ticket blocks.

    We use 'SINGLE' and 'COMBO' markers as delimiters, but also keep an initial
    block even if no category marker is present.

    Returns a list of (category_hint, block_text).
    """
    lines = raw_text.splitlines()
    blocks: List[Tuple[str, str]] = []
    current_lines: List[str] = []
    current_category = "UNKNOWN"

    for line in lines:
        stripped = line.strip()
        if stripped in ("SINGLE", "COMBO"):
            # Finalize current block if it contains a ticket ID
            if current_lines and any("Ticket ID:" in l for l in current_lines):
                blocks.append((current_category, "\n".join(current_lines).strip("\n")))
            current_lines = []
            current_category = stripped
        else:
            current_lines.append(line)

    if current_lines and any("Ticket ID:" in l for l in current_lines):
        blocks.append((current_category, "\n".join(current_lines).strip("\n")))

    return blocks


def parse_betting_history(raw_text: str) -> List[BetRecord]:
    """
    Parse the raw betting history text into a list of BetRecord objects,
    **filtered to SINGLE bets only** (newest first).

    For access to all bets including COMBO tickets, use `parse_all_tickets`.
    """
    all_bets = parse_all_tickets(raw_text)
    single_bets = [b for b in all_bets if b.category == "SINGLE"]
    single_bets.sort(key=lambda b: b.placed_at, reverse=True)

    logger.info(
        "Parsed %d tickets total, %d SINGLE bets after filtering",
        len(all_bets),
        len(single_bets),
    )
    return single_bets


def parse_all_tickets(raw_text: str) -> List[BetRecord]:
    """
    Parse the raw betting history text into a list of BetRecord objects
    for **all** tickets (SINGLE, COMBO, etc.), in the original order.
    """
    result: List[BetRecord] = []
    blocks = split_into_blocks(raw_text)
    logger.info("Detected %d ticket blocks in raw text", len(blocks))

    for category_hint, block_text in blocks:
        block_lines = block_text.splitlines()

        ticket_id = _extract_ticket_id(block_lines)
        if not ticket_id:
            logger.warning("Skipping block without Ticket ID:\n%s", block_text[:200])
            continue

        placed_at_info = _parse_placed_at(block_lines)
        if not placed_at_info:
            logger.warning("Skipping ticket %s: could not parse placed_at", ticket_id)
            continue
        placed_at, placed_idx = placed_at_info

        event_dt = _parse_event_datetime(block_lines, placed_idx, placed_at.year)

        # Determine category and overall result
        category = _detect_category(category_hint, block_text)
        result_norm = _normalize_result(block_lines)

        # Sport/league and match
        sport_league, match = _extract_sport_league_and_match(block_lines, placed_idx)

        # Find index of Ticket ID line for market/odds extraction
        ticket_idx = next(
            (i for i, l in enumerate(block_lines) if "Ticket ID:" in l), -1
        )
        market = None
        odds = None
        if ticket_idx != -1:
            market, odds = _extract_market_and_odds(block_lines, ticket_idx)

        stake = _extract_stake(block_lines)

        payout_info = _extract_payout(block_lines)
        explicit_payout = None
        if payout_info is not None:
            explicit_payout, payout_result = payout_info
            # If payout implies a clearer result, prefer it
            if payout_result != result_norm and result_norm in {"UNKNOWN", "OPEN"}:
                result_norm = payout_result

        payout, profit, roi = _compute_financials(
            result=result_norm,
            stake=stake,
            odds=odds,
            explicit_payout=explicit_payout,
        )

        # Try to separate bet_type and selection from the market line
        bet_type: Optional[str] = None
        selection: Optional[str] = None
        if market:
            # Heuristic splits: e.g. "Winner Peniston, Ryan" -> "Winner" + "Peniston, Ryan"
            parts = market.split(" ", 1)
            if len(parts) == 2 and parts[0].istitle():
                bet_type, selection = parts[0], parts[1]
            else:
                bet_type = None
                selection = market

        record = BetRecord(
            ticket_id=ticket_id,
            placed_at=placed_at,
            event_datetime=event_dt,
            category=category,
            sport_league=sport_league,
            match=match,
            bet_type=bet_type,
            selection=selection,
            odds=odds,
            stake=stake,
            result=result_norm,
            payout=payout,
            profit=profit,
            roi=roi,
            raw_block=block_text,
        )

        result.append(record)

    return result


def compute_metadata(bets: List[BetRecord]) -> Dict[str, Any]:
    """
    Compute aggregate statistics for the given bets.
    """
    if not bets:
        return {
            "total_bets": 0,
            "date_range": None,
            "total_stake": 0.0,
            "total_profit": 0.0,
            "overall_roi": None,
            "win_rate": None,
        }

    total_stake = 0.0
    total_profit = 0.0
    win_count = 0
    counted_bets = 0

    for b in bets:
        if b.stake is not None:
            total_stake += b.stake
        if b.profit is not None:
            total_profit += b.profit
        if b.result == "WON":
            win_count += 1
        counted_bets += 1

    overall_roi = (total_profit / total_stake * 100) if total_stake > 0 else None
    win_rate = (win_count / counted_bets * 100) if counted_bets > 0 else None

    # Bets are already sorted newest first
    newest = bets[0].placed_at
    oldest = bets[-1].placed_at

    return {
        "total_bets": counted_bets,
        "date_range": {
            "start": oldest.date().isoformat(),
            "end": newest.date().isoformat(),
        },
        "total_stake": round(total_stake, 2),
        "total_profit": round(total_profit, 2),
        "overall_roi": round(overall_roi, 2) if overall_roi is not None else None,
        "win_rate": round(win_rate, 2) if win_rate is not None else None,
    }


def export_json(bets: List[BetRecord], out_path: Path) -> None:
    """
    Write bets plus metadata to a JSON file.
    """
    metadata = compute_metadata(bets)
    payload = {
        "metadata": metadata,
        "bets": [b.to_serializable() for b in bets],
    }
    out_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    logger.info("Wrote JSON output to %s", out_path)


def export_csv(bets: List[BetRecord], out_path: Path) -> None:
    """
    Write bets to a flat CSV file suitable for Excel/Pandas.
    """
    if not bets:
        out_path.write_text("", encoding="utf-8")
        logger.info("No bets to write to CSV (%s)", out_path)
        return

    fieldnames = [
        "ticket_id",
        "placed_at",
        "event_datetime",
        "category",
        "sport_league",
        "match",
        "bet_type",
        "selection",
        "odds",
        "stake",
        "result",
        "payout",
        "profit",
        "roi",
    ]

    with out_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for b in bets:
            row = {
                "ticket_id": b.ticket_id,
                "placed_at": b.placed_at.isoformat(),
                "event_datetime": b.event_datetime.isoformat()
                if b.event_datetime
                else "",
                "category": b.category,
                "sport_league": b.sport_league or "",
                "match": b.match or "",
                "bet_type": b.bet_type or "",
                "selection": b.selection or "",
                "odds": b.odds if b.odds is not None else "",
                "stake": b.stake if b.stake is not None else "",
                "result": b.result,
                "payout": b.payout if b.payout is not None else "",
                "profit": b.profit if b.profit is not None else "",
                "roi": b.roi if b.roi is not None else "",
            }
            writer.writerow(row)

    logger.info("Wrote CSV output to %s", out_path)


def _setup_logging(verbose: bool) -> None:
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(level=level, format="%(levelname)s:%(name)s:%(message)s")


def main(argv: Optional[List[str]] = None) -> None:
    parser = argparse.ArgumentParser(
        description="Parse raw betting history text and export SINGLE bets to JSON/CSV."
    )
    parser.add_argument(
        "input",
        type=str,
        help="Path to the input text file containing raw betting history.",
    )
    parser.add_argument(
        "--json",
        dest="json_out",
        type=str,
        default=None,
        help="Path to write JSON output for SINGLE bets (metadata + bets).",
    )
    parser.add_argument(
        "--csv",
        dest="csv_out",
        type=str,
        default=None,
        help="Path to write CSV output for SINGLE bets.",
    )
    parser.add_argument(
        "--json-combos",
        dest="json_combos_out",
        type=str,
        default=None,
        help="Optional path to write JSON output for COMBO bets.",
    )
    parser.add_argument(
        "--csv-combos",
        dest="csv_combos_out",
        type=str,
        default=None,
        help="Optional path to write CSV output for COMBO bets.",
    )
    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Enable verbose logging.",
    )

    args = parser.parse_args(argv)
    _setup_logging(verbose=args.verbose)

    input_path = Path(args.input)
    if not input_path.exists():
        raise SystemExit(f"Input file does not exist: {input_path}")

    raw_text = input_path.read_text(encoding="utf-8")

    # Parse all tickets once, then split by category
    all_bets = parse_all_tickets(raw_text)
    single_bets = [b for b in all_bets if b.category == "SINGLE"]
    combo_bets = [b for b in all_bets if b.category == "COMBO"]

    # Sort singles and combos newest first for convenience
    single_bets.sort(key=lambda b: b.placed_at, reverse=True)
    combo_bets.sort(key=lambda b: b.placed_at, reverse=True)

    # Print quick summary for SINGLE bets
    metadata_singles = compute_metadata(single_bets)
    logger.info(
        "SINGLE bets summary: %s (from %d total tickets)",
        metadata_singles,
        len(all_bets),
    )

    if combo_bets:
        metadata_combos = compute_metadata(combo_bets)
        logger.info("COMBO bets summary: %s", metadata_combos)

    if args.json_out:
        export_json(single_bets, Path(args.json_out))
    if args.csv_out:
        export_csv(single_bets, Path(args.csv_out))

    if args.json_combos_out:
        export_json(combo_bets, Path(args.json_combos_out))
    if args.csv_combos_out:
        export_csv(combo_bets, Path(args.csv_combos_out))


if __name__ == "__main__":
    main()


