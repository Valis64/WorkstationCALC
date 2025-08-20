from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import datetime
from typing import List, Set

from bs4 import BeautifulSoup


@dataclass
class Step:
    name: str
    timestamp: datetime | None = None


@dataclass
class Order:
    company: str
    number: str
    status: str
    priority: str
    steps: List[Step]


def parse_orders(html: str) -> List[Order]:
    soup = BeautifulSoup(html, "html.parser")
    orders: List[Order] = []
    for row in soup.select("tbody tr"):
        cells = row.find_all("td")
        if not cells:
            continue
        first = cells[0]
        parts = list(first.stripped_strings)
        company = parts[0] if parts else ""
        number_match = re.search(r"#(\w+)", parts[1] if len(parts) > 1 else "")
        number = number_match.group(1) if number_match else ""
        status = cells[2].get_text(strip=True) if len(cells) > 2 else ""
        priority_input = cells[4].find("input") if len(cells) > 4 else None
        priority = priority_input.get("value", "") if priority_input else ""
        steps: List[Step] = []
        for li in first.select("ul.workplaces li"):
            ps = li.find_all("p")
            if len(ps) >= 2:
                name = re.sub(r"^\d+", "", ps[0].get_text(strip=True))
                ts_text = ps[1].get_text(strip=True)
                try:
                    ts = datetime.strptime(ts_text, "%m/%d/%y %H:%M")
                except ValueError:
                    ts = None
                steps.append(Step(name=name, timestamp=ts))
        orders.append(Order(company=company, number=number, status=status, priority=priority, steps=steps))
    return orders


def parse_queue(html: str) -> Set[str]:
    soup = BeautifulSoup(html, "html.parser")
    orders: Set[str] = set()
    for td in soup.select("tbody td"):
        text = td.get_text(strip=True)
        if text.lower().startswith("order "):
            text = text.split(" ", 1)[1]
        orders.add(text)
    return orders
