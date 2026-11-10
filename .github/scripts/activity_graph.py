"""Render the profile activity graph from the same calendar visitors can see."""

from datetime import date, timedelta
from html.parser import HTMLParser
from pathlib import Path
from urllib.request import Request, urlopen
import re


class Calendar(HTMLParser):
    def __init__(self):
        super().__init__()
        self.dates = {}
        self.counts = {}
        self.target = None

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == "td" and "data-date" in attrs:
            self.dates[attrs["id"]] = date.fromisoformat(attrs["data-date"])
        if tag == "tool-tip":
            self.target = attrs.get("for")

    def handle_endtag(self, tag):
        if tag == "tool-tip":
            self.target = None

    def handle_data(self, data):
        match = re.match(r"(No|[\d,]+) contributions? on ", data.strip())
        if self.target and match:
            number = match[1].replace(",", "")
            self.counts[self.target] = 0 if number == "No" else int(number)


def main():
    page = Request("https://github.com/users/EthanJia0627/contributions",
                   headers={"Accept-Language": "en"})
    cal = Calendar()
    with urlopen(page, timeout=20) as response:
        cal.feed(response.read().decode())
    counts = {day: cal.counts[key] for key, day in cal.dates.items() if key in cal.counts}
    end = max(counts)
    days = [end - timedelta(days=n) for n in range(30, -1, -1)]
    ceiling = max(4, ((max(counts[d] for d in days) + 3) // 4) * 4)
    x = lambda i: 52 + i * 27
    y = lambda count: 188 - 126 * count / ceiling
    svg = ['<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 900 230" role="img">',
           f'<title>Daily contributions: {days[0]} to {end}</title>',
           '<rect width="900" height="230" rx="8" fill="#0d1117"/>',
           '<g font-family="system-ui,sans-serif" fill="#36bcf7">',
           '<text x="450" y="32" text-anchor="middle" font-size="19">Daily GitHub contributions</text>']
    for i in range(5):
        v = i * ceiling // 4
        svg += [f'<path d="M52 {y(v)}h810" stroke="#23303c"/>',
                f'<text x="40" y="{y(v)+4}" text-anchor="end" font-size="12">{v}</text>']
    pts = " ".join(f"{x(i)},{y(counts[d]):.1f}" for i, d in enumerate(days))
    svg += [f'<polygon points="52,188 {pts} 862,188" fill="#36bcf7" opacity=".16"/>',
            f'<polyline points="{pts}" stroke="#36bcf7" fill="none" stroke-width="2.5"/>']
    for i, d in enumerate(days):
        svg.append(f'<circle cx="{x(i)}" cy="{y(counts[d]):.1f}" r="3.5" fill="#ff6f61"><title>{d}: {counts[d]}</title></circle>')
        if i % 5 == 0:
            svg.append(f'<text x="{x(i)}" y="214" text-anchor="middle" font-size="12">{d:%d %b}</text>')
    Path("generated/activity.svg").write_text("\n".join(svg + ["</g></svg>", ""]), encoding="utf-8")


if __name__ == "__main__":
    main()
