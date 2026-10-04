"""Async scraper for the official LKL standings page."""

from __future__ import annotations

import asyncio
import re
from dataclasses import dataclass, field
from html.parser import HTMLParser
from typing import Any
from urllib.parse import urljoin

from aiohttp import ClientError, ClientSession

from .const import SOURCE_URL


class LklApiError(Exception):
    """Raised when LKL data cannot be loaded or parsed."""


@dataclass
class _Cell:
    text_parts: list[str] = field(default_factory=list)
    image: str | None = None
    link: str | None = None

    @property
    def text(self) -> str:
        return " ".join(" ".join(self.text_parts).split())


class _TableParser(HTMLParser):
    """Tiny HTML table parser so the integration has no extra dependencies."""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.tables: list[list[list[_Cell]]] = []
        self._table_depth = 0
        self._table: list[list[_Cell]] | None = None
        self._row: list[_Cell] | None = None
        self._cell: _Cell | None = None

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attrs_d = dict(attrs)
        if tag == "table":
            self._table_depth += 1
            if self._table_depth == 1:
                self._table = []
            return
        if self._table_depth != 1:
            return
        if tag == "tr":
            self._row = []
        elif tag in ("th", "td") and self._row is not None:
            self._cell = _Cell()
        elif tag == "img" and self._cell is not None:
            self._cell.image = (
                attrs_d.get("src")
                or attrs_d.get("data-src")
                or attrs_d.get("data-lazy-src")
            )
        elif tag == "a" and self._cell is not None:
            self._cell.link = attrs_d.get("href")
        elif tag == "br" and self._cell is not None:
            self._cell.text_parts.append(" ")

    def handle_endtag(self, tag: str) -> None:
        if tag == "table":
            if self._table_depth == 1 and self._table is not None:
                self.tables.append(self._table)
                self._table = None
            self._table_depth = max(0, self._table_depth - 1)
            return
        if self._table_depth != 1:
            return
        if tag in ("th", "td") and self._cell is not None and self._row is not None:
            self._row.append(self._cell)
            self._cell = None
        elif tag == "tr" and self._row is not None and self._table is not None:
            if self._row:
                self._table.append(self._row)
            self._row = None

    def handle_data(self, data: str) -> None:
        if self._table_depth == 1 and self._cell is not None and data.strip():
            self._cell.text_parts.append(data)


TEAM_CODES = {
    "gargždai": "GAR",
    "hipocredit": "HIP",
    "juventus": "JUV",
    "lietkabelis": "LIE",
    "neptūnas": "NEP",
    "nevėžis-paskolų klubas": "NEV",
    "nevėžis": "NEV",
    "rytas": "RYT",
    "šiauliai": "SIA",
    "tauragė": "TAU",
    "žalgiris": "ZAL",
}


def _norm(value: str) -> str:
    return re.sub(r"[^a-ząčęėįšųūž0-9%]+", "", value.lower())


def _as_int(value: str, fallback: int = 0) -> int:
    match = re.search(r"-?\d+", value.replace("\xa0", " "))
    return int(match.group(0)) if match else fallback


def _as_float(value: str) -> float | None:
    match = re.search(r"-?\d+(?:[.,]\d+)?", value.replace("\xa0", " "))
    return float(match.group(0).replace(",", ".")) if match else None


def _team_code(name: str) -> str:
    key = name.strip().lower()
    if key in TEAM_CODES:
        return TEAM_CODES[key]
    letters = re.sub(r"[^A-Za-zĄČĘĖĮŠŲŪŽąčęėįšųūž]", "", name).upper()
    return letters[:3] or "LKL"


def _current_season_label() -> str:
    # LKL season normally begins in the second half of the calendar year.
    from datetime import datetime

    now = datetime.now()
    start = now.year if now.month >= 7 else now.year - 1
    return f"{start}/{str(start + 1)[-2:]}"


def parse_standings_html(html: str) -> dict[str, Any]:
    """Parse the main 'Bendra' standings table from lkl.lt."""
    parser = _TableParser()
    parser.feed(html)

    target: list[list[_Cell]] | None = None
    header_index = -1
    indexes: dict[str, int] = {}

    for table in parser.tables:
        for idx, row in enumerate(table[:4]):
            headers = [_norm(cell.text) for cell in row]
            if not headers:
                continue
            # Official LKL table: Poz. / Komanda / Rng. / Per. / Pr. / Laim.% / Tšk. vid.
            if (
                any(h.startswith("poz") for h in headers)
                and any(h.startswith("komanda") for h in headers)
                and any(h.startswith("rng") for h in headers)
                and any(h.startswith("per") for h in headers)
                and any(h.startswith("pr") for h in headers)
            ):
                target = table
                header_index = idx
                for col, h in enumerate(headers):
                    if h.startswith("poz"):
                        indexes["position"] = col
                    elif h.startswith("komanda"):
                        indexes["team"] = col
                    elif h.startswith("rng"):
                        indexes["played"] = col
                    elif h.startswith("per"):
                        indexes["wins"] = col
                    elif h.startswith("pr"):
                        indexes["losses"] = col
                    elif "laim" in h or "%" in h:
                        indexes["pct"] = col
                    elif h.startswith("tšk") or h.startswith("tsk"):
                        indexes["points_avg"] = col
                break
        if target is not None:
            break

    if target is None:
        raise LklApiError("LKL standings table was not found in the page HTML")

    required = ("position", "team", "played", "wins", "losses")
    if any(key not in indexes for key in required):
        raise LklApiError("LKL standings table format has changed")

    teams: list[dict[str, Any]] = []
    for row in target[header_index + 1 :]:
        if len(row) <= max(indexes.values()):
            continue
        pos = _as_int(row[indexes["position"]].text, 0)
        team_cell = row[indexes["team"]]
        name = team_cell.text.strip()
        if pos <= 0 or not name:
            continue

        played = _as_int(row[indexes["played"]].text)
        wins = _as_int(row[indexes["wins"]].text)
        losses = _as_int(row[indexes["losses"]].text)
        pct = None
        if "pct" in indexes:
            pct = _as_float(row[indexes["pct"]].text)
        if pct is None and played > 0:
            pct = round(wins / played * 100, 1)

        points_for_avg = None
        points_against_avg = None
        if "points_avg" in indexes:
            nums = re.findall(r"-?\d+(?:[.,]\d+)?", row[indexes["points_avg"]].text)
            if nums:
                points_for_avg = float(nums[0].replace(",", "."))
            if len(nums) > 1:
                points_against_avg = float(nums[1].replace(",", "."))

        logo = team_cell.image or ""
        if logo:
            logo = urljoin(SOURCE_URL, logo)
        team_url = team_cell.link or ""
        if team_url:
            team_url = urljoin(SOURCE_URL, team_url)

        teams.append(
            {
                "position": pos,
                "code": _team_code(name),
                "name": name,
                "logo": logo,
                "team_url": team_url,
                "games_played": played,
                "wins": wins,
                "losses": losses,
                "win_percentage": pct,
                "points_for_avg": points_for_avg,
                "points_against_avg": points_against_avg,
            }
        )

    teams.sort(key=lambda item: item["position"])
    if not teams:
        raise LklApiError("LKL standings table contained no team rows")

    return {"season": _current_season_label(), "teams": teams}


class LklApi:
    """Official LKL website client."""

    def __init__(self, session: ClientSession) -> None:
        self._session = session

    async def async_get_standings(self) -> dict[str, Any]:
        try:
            async with asyncio.timeout(20):
                response = await self._session.get(
                    SOURCE_URL,
                    headers={
                        "Accept": "text/html,application/xhtml+xml",
                        "User-Agent": "HomeAssistant-LKL-Standings/1.0",
                    },
                )
                async with response:
                    if response.status >= 400:
                        body = (await response.text())[:200]
                        raise LklApiError(
                            f"LKL website returned HTTP {response.status}: {body}"
                        )
                    html = await response.text()
        except (TimeoutError, ClientError) as err:
            raise LklApiError(f"LKL request failed: {err}") from err

        return parse_standings_html(html)
