"""
GitHub Contribution Graph SVG Generator.
Fetches real contribution calendar data from GitHub and generates a custom,
terminal-themed SVG graph featuring dark mode (#080B12), cyan and blue bars,
green highlights, rounded elements, and monospace typography.
"""

import os
import re
import json
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional
import requests
from bs4 import BeautifulSoup

from src.utils import ensure_dir

logger = logging.getLogger("contributions")
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")


class ContributionGraphEngine:
    """
    Fetches GitHub contribution calendar and renders an aesthetic
    terminal-inspired SVG activity graph.
    """

    def __init__(self, username: str = "gauravgupta5813-coder"):
        self.username = username
        self.cache_path = "assets/generated/contributions_data.json"

    def fetch_contributions(self) -> Dict[str, Any]:
        """
        Fetch real contributions using GitHub GraphQL API (if token available)
        or public contributions HTML endpoint, with fallback to local cache.
        """
        token = os.environ.get("GITHUB_TOKEN")
        if token:
            try:
                logger.info("Attempting fetch via GitHub GraphQL API...")
                data = self._fetch_via_graphql(token)
                self._save_cache(data)
                return data
            except Exception as e:
                logger.warning(f"GraphQL fetch failed: {e}. Falling back to public HTML scraper.")

        # Fallback to public HTML scraper
        try:
            logger.info(f"Fetching public contribution data for {self.username}...")
            data = self._fetch_via_html_scraper()
            self._save_cache(data)
            return data
        except Exception as e:
            logger.warning(f"HTML scraper fetch failed: {e}.")
            if os.path.exists(self.cache_path):
                logger.info(f"Loading cached contribution data from {self.cache_path}...")
                with open(self.cache_path, "r", encoding="utf-8") as f:
                    return json.load(f)
            raise RuntimeError(f"Could not retrieve contribution data and no cache exists: {e}")

    def _fetch_via_graphql(self, token: str) -> Dict[str, Any]:
        """Fetch using GitHub GraphQL API."""
        query = """
        query($userName: String!) {
          user(login: $userName) {
            contributionsCollection {
              contributionCalendar {
                totalContributions
                weeks {
                  contributionDays {
                    contributionCount
                    date
                    weekday
                  }
                }
                months {
                  name
                  firstDay
                  totalWeeks
                }
              }
            }
          }
        }
        """
        headers = {
            "Authorization": f"Bearer {token}",
            "User-Agent": "GitHub-Profile-Activity-Generator",
        }
        resp = requests.post(
            "https://api.github.com/graphql",
            json={"query": query, "variables": {"userName": self.username}},
            headers=headers,
            timeout=15,
        )
        if resp.status_code != 200:
            raise ValueError(f"GraphQL error: HTTP {resp.status_code} - {resp.text}")

        res_json = resp.json()
        if "errors" in res_json:
            raise ValueError(f"GraphQL returned errors: {res_json['errors']}")

        calendar = res_json["data"]["user"]["contributionsCollection"]["contributionCalendar"]
        weeks_data = []
        for w in calendar["weeks"]:
            days = []
            for d in w["contributionDays"]:
                days.append({
                    "date": d["date"],
                    "count": d["contributionCount"],
                    "weekday": d["weekday"],
                })
            weeks_data.append(days)

        return {
            "username": self.username,
            "totalContributions": calendar["totalContributions"],
            "weeks": weeks_data,
            "fetched_at": datetime.now().isoformat(),
        }

    def _fetch_via_html_scraper(self) -> Dict[str, Any]:
        """Fetch and parse GitHub's public HTML contributions component."""
        url = f"https://github.com/users/{self.username}/contributions"
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml",
        }
        resp = requests.get(url, headers=headers, timeout=15)
        if resp.status_code != 200:
            raise ValueError(f"Failed to fetch contributions HTML: HTTP {resp.status_code}")

        soup = BeautifulSoup(resp.text, "html.parser")
        day_cells = soup.find_all("td", class_="ContributionCalendar-day")
        
        # Parse tooltips for exact counts
        tooltips = {}
        for tt in soup.find_all("tool-tip"):
            for_id = tt.get("for")
            if for_id:
                tooltips[for_id] = tt.text.strip()

        all_days = []
        total_count = 0

        for cell in day_cells:
            date_str = cell.get("data-date")
            if not date_str:
                continue
            day_id = cell.get("id")
            tt_text = tooltips.get(day_id, "")
            
            # Extract count: "X contributions on Month Day"
            match = re.search(r"(\d+)\s+contribution", tt_text)
            count = int(match.group(1)) if match else 0
            level = int(cell.get("data-level", 0))

            total_count += count
            
            # Compute weekday from date (0=Monday, 6=Sunday -> GitHub: 0=Sunday)
            try:
                dt = datetime.strptime(date_str, "%Y-%m-%d")
                weekday = (dt.weekday() + 1) % 7  # 0: Sunday, 1: Monday, ...
            except Exception:
                weekday = 0

            all_days.append({
                "date": date_str,
                "count": count,
                "level": level,
                "weekday": weekday,
            })

        # Group days into weeks of up to 7 days
        weeks = []
        current_week = []
        for day in all_days:
            current_week.append(day)
            if len(current_week) == 7:
                weeks.append(current_week)
                current_week = []
        if current_week:
            weeks.append(current_week)

        return {
            "username": self.username,
            "totalContributions": total_count,
            "weeks": weeks,
            "fetched_at": datetime.now().isoformat(),
        }

    def _save_cache(self, data: Dict[str, Any]) -> None:
        """Save data to local cache file."""
        ensure_dir(os.path.dirname(self.cache_path))
        with open(self.cache_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
        logger.info(f"Cached contribution data to {self.cache_path}")

    def render_svg(self, data: Optional[Dict[str, Any]] = None, output_path: str = "assets/generated/contribution-graph.svg") -> str:
        """
        Generate terminal-styled SVG contribution graph.
        
        Args:
            data: Contribution data dictionary (fetches if None)
            output_path: Path to save the generated SVG file
            
        Returns:
            SVG XML content string
        """
        if data is None:
            data = self.fetch_contributions()

        weeks = data.get("weeks", [])
        total_contribs = data.get("totalContributions", 0)

        # Calculate weekly sums and metadata
        weekly_stats = []
        max_week_count = 0
        active_weeks_count = 0

        for w_idx, week in enumerate(weeks):
            week_sum = sum(day.get("count", 0) for day in week)
            if week_sum > 0:
                active_weeks_count += 1
            if week_sum > max_week_count:
                max_week_count = week_sum
            
            # Extract month of the first day in week for axis labels
            first_date_str = week[0].get("date", "") if week else ""
            month_name = ""
            if first_date_str:
                try:
                    dt = datetime.strptime(first_date_str, "%Y-%m-%d")
                    # Label if day <= 7 (start of month)
                    if dt.day <= 7:
                        month_name = dt.strftime("%b")
                except Exception:
                    pass

            weekly_stats.append({
                "index": w_idx,
                "sum": week_sum,
                "first_date": first_date_str,
                "month_label": month_name,
            })

        # Ensure max_week_count is at least 1 to avoid division by zero
        max_week_count = max(max_week_count, 1)

        # SVG layout parameters
        svg_w = 880
        svg_h = 320

        # Graph plot area
        plot_x = 55
        plot_y = 95
        plot_w = 770
        plot_h = 160
        bottom_y = plot_y + plot_h

        num_weeks = len(weekly_stats)
        col_width = plot_w / max(num_weeks, 1)
        bar_w = max(4.0, min(10.5, col_width - 3.5))

        # Generate SVG elements
        bars_xml = []
        trend_points = []
        month_labels_xml = []

        for item in weekly_stats:
            idx = item["index"]
            c_sum = item["sum"]
            cx = plot_x + idx * col_width + (col_width / 2.0)

            # Month label along bottom
            if item["month_label"]:
                month_labels_xml.append(
                    f'<text x="{cx:.1f}" y="{bottom_y + 24}" class="axis-label" text-anchor="middle">{item["month_label"]}</text>'
                )

            # Bar height calculation
            if c_sum == 0:
                bar_h = 4.0
                bar_y = bottom_y - bar_h
                bars_xml.append(
                    f'<rect x="{cx - bar_w/2.0:.1f}" y="{bar_y:.1f}" width="{bar_w:.1f}" height="{bar_h:.1f}" '
                    f'rx="2" ry="2" fill="#131D2E" opacity="0.65" />'
                )
                trend_points.append((cx, bottom_y - 2.0))
            else:
                # Proportional height with minimum visible height
                ratio = c_sum / float(max_week_count)
                bar_h = 12.0 + ratio * (plot_h - 22.0)
                bar_y = bottom_y - bar_h

                # Choose bar gradient based on activity intensity
                if ratio >= 0.70:
                    bar_fill = "url(#peakGreenGrad)"
                    glow_class = "glow-bar"
                elif ratio >= 0.35:
                    bar_fill = "url(#vibrantCyanGrad)"
                    glow_class = "glow-bar-cyan"
                else:
                    bar_fill = "url(#electricBlueGrad)"
                    glow_class = "glow-bar-blue"

                bars_xml.append(
                    f'<rect x="{cx - bar_w/2.0:.1f}" y="{bar_y:.1f}" width="{bar_w:.1f}" height="{bar_h:.1f}" '
                    f'rx="3.5" ry="3.5" fill="{bar_fill}" class="{glow_class}">'
                    f'<title>{c_sum} contributions week of {item["first_date"]}</title>'
                    f'</rect>'
                )
                trend_points.append((cx, bar_y))

        # Generate smoothed spline curve for trendline
        curve_d = self._build_smooth_path(trend_points)
        area_d = f"{curve_d} L {trend_points[-1][0]:.1f} {bottom_y} L {trend_points[0][0]:.1f} {bottom_y} Z"

        # Y-axis dashed grid lines
        grid_lines = []
        for fraction, val in [(0.25, int(max_week_count * 0.75)), (0.50, int(max_week_count * 0.50)), (0.75, int(max_week_count * 0.25))]:
            gy = plot_y + fraction * plot_h
            grid_lines.append(
                f'<line x1="{plot_x}" y1="{gy:.1f}" x2="{plot_x + plot_w}" y2="{gy:.1f}" stroke="#162238" stroke-dasharray="3,5" stroke-width="1" />\n'
                f'<text x="{plot_x - 8}" y="{gy + 4:.1f}" class="y-label" text-anchor="end">{val}</text>'
            )

        # Baseline axis line
        grid_lines.append(
            f'<line x1="{plot_x}" y1="{bottom_y}" x2="{plot_x + plot_w}" y2="{bottom_y}" stroke="#1E293D" stroke-width="1.5" />\n'
            f'<text x="{plot_x - 8}" y="{bottom_y + 4:.1f}" class="y-label" text-anchor="end">0</text>'
        )

        grid_lines_str = "\n  ".join(grid_lines)
        bars_xml_str = "\n  ".join(bars_xml)
        month_labels_xml_str = "\n  ".join(month_labels_xml)

        svg_content = f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {svg_w} {svg_h}" width="100%" height="auto">
  <defs>
    <!-- Background terminal gradient -->
    <linearGradient id="bgGrad" x1="0%" y1="0%" x2="0%" y2="100%">
      <stop offset="0%" stop-color="#0B0F19" />
      <stop offset="100%" stop-color="#080B12" />
    </linearGradient>

    <!-- Contribution Bar Gradients -->
    <linearGradient id="electricBlueGrad" x1="0%" y1="0%" x2="0%" y2="100%">
      <stop offset="0%" stop-color="#00D9FF" />
      <stop offset="60%" stop-color="#0066FF" />
      <stop offset="100%" stop-color="#1E3A8A" />
    </linearGradient>

    <linearGradient id="vibrantCyanGrad" x1="0%" y1="0%" x2="0%" y2="100%">
      <stop offset="0%" stop-color="#38BDF8" />
      <stop offset="50%" stop-color="#0284C7" />
      <stop offset="100%" stop-color="#0369A1" />
    </linearGradient>

    <linearGradient id="peakGreenGrad" x1="0%" y1="0%" x2="0%" y2="100%">
      <stop offset="0%" stop-color="#00FF88" />
      <stop offset="65%" stop-color="#00D9FF" />
      <stop offset="100%" stop-color="#0066FF" />
    </linearGradient>

    <!-- Translucent Area Fill Under Curve -->
    <linearGradient id="areaGrad" x1="0%" y1="0%" x2="0%" y2="100%">
      <stop offset="0%" stop-color="#00D9FF" stop-opacity="0.22" />
      <stop offset="70%" stop-color="#0066FF" stop-opacity="0.06" />
      <stop offset="100%" stop-color="#080B12" stop-opacity="0.0" />
    </linearGradient>

    <!-- Glowing Trendline Stroke -->
    <linearGradient id="trendStroke" x1="0%" y1="0%" x2="100%" y2="0%">
      <stop offset="0%" stop-color="#0066FF" />
      <stop offset="50%" stop-color="#00D9FF" />
      <stop offset="100%" stop-color="#00FF88" />
    </linearGradient>
  </defs>

  <style>
    .terminal-title {{ font-family: 'Fira Code', 'Courier New', monospace; font-size: 13.5px; fill: #E5E7EB; }}
    .prompt-user {{ fill: #00FF88; font-weight: 600; }}
    .prompt-cmd {{ fill: #00D9FF; }}
    .axis-label {{ font-family: 'Segoe UI', -apple-system, sans-serif; font-size: 10.5px; fill: #64748B; }}
    .y-label {{ font-family: 'Fira Code', monospace; font-size: 9.5px; fill: #475569; }}
    .metric-value {{ font-family: 'Fira Code', monospace; font-size: 12px; font-weight: 700; fill: #00FF88; }}
    .metric-label {{ font-family: 'Segoe UI', -apple-system, sans-serif; font-size: 11px; fill: #94A3B8; }}
    .glow-bar {{ filter: drop-shadow(0 0 4px rgba(0, 255, 136, 0.45)); }}
    .glow-bar-cyan {{ filter: drop-shadow(0 0 4px rgba(0, 217, 255, 0.35)); }}
    .glow-bar-blue {{ filter: drop-shadow(0 0 3px rgba(0, 102, 255, 0.25)); }}
  </style>

  <!-- Outer Terminal Window Frame -->
  <rect x="2" y="2" width="{svg_w - 4}" height="{svg_h - 4}" rx="14" ry="14" fill="url(#bgGrad)" stroke="#1E293D" stroke-width="1.8" />

  <!-- Terminal Title Bar -->
  <!-- Window Control Buttons (Red, Yellow, Green) -->
  <circle cx="28" cy="28" r="5" fill="#FF5F56" />
  <circle cx="46" cy="28" r="5" fill="#FFBD2E" />
  <circle cx="64" cy="28" r="5" fill="#27C93F" />

  <!-- Terminal Prompt Command -->
  <text x="86" y="32" class="terminal-title">
    <tspan class="prompt-user">{self.username}@github</tspan>
    <tspan fill="#64748B"> ~ $ </tspan>
    <tspan class="prompt-cmd">git activity --live --contribs</tspan>
  </text>

  <!-- Metric Badges on Right Header -->
  <g transform="translate({svg_w - 245}, 16)">
    <rect x="0" y="0" width="220" height="26" rx="6" ry="6" fill="#0D131F" stroke="#1E293D" stroke-width="1" />
    <circle cx="14" cy="13" r="3.5" fill="#00FF88" />
    <text x="25" y="17" class="metric-label">Total:</text>
    <text x="62" y="17" class="metric-value">{total_contribs}</text>
    <text x="95" y="17" class="metric-label">Max/Wk:</text>
    <text x="156" y="17" class="metric-value">{max_week_count}</text>
  </g>

  <!-- Subtle Divider Under Header -->
  <line x1="16" y1="52" x2="{svg_w - 16}" y2="52" stroke="#162238" stroke-width="1.2" />

  <!-- Y-Axis Grid Lines -->
  {grid_lines_str}

  <!-- Area Gradient Under Curve -->
  <path d="{area_d}" fill="url(#areaGrad)" />

  <!-- Smoothed Trendline Curve -->
  <path d="{curve_d}" fill="none" stroke="url(#trendStroke)" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round" />

  <!-- Contribution Bars -->
  {bars_xml_str}

  <!-- Month Labels on X-Axis -->
  {month_labels_xml_str}

  <!-- Footer Activity Summary -->
  <g transform="translate({plot_x}, {svg_h - 16})">
    <circle cx="4" cy="-4" r="3" fill="#00D9FF" />
    <text x="14" y="0" class="axis-label">Active Weeks: <tspan fill="#E5E7EB" font-weight="600">{active_weeks_count}</tspan> / {num_weeks}</text>
    <text x="220" y="0" class="axis-label">Data Source: <tspan fill="#38BDF8">GitHub Contribution Calendar</tspan></text>
  </g>
</svg>"""

        ensure_dir(os.path.dirname(output_path))
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(svg_content)
        logger.info(f"Generated contribution graph SVG saved to {output_path}")

        # Also copy to root assets/contribution-graph.svg for immediate deployment
        deploy_path = "assets/contribution-graph.svg"
        ensure_dir(os.path.dirname(deploy_path))
        with open(deploy_path, "w", encoding="utf-8") as f:
            f.write(svg_content)
        logger.info(f"Deployed contribution graph SVG to {deploy_path}")

        return svg_content

    def _build_smooth_path(self, points: List[tuple]) -> str:
        """Construct smooth cubic bezier spline through points."""
        if not points:
            return ""
        if len(points) == 1:
            return f"M {points[0][0]:.1f} {points[0][1]:.1f}"

        path = [f"M {points[0][0]:.1f} {points[0][1]:.1f}"]
        for i in range(len(points) - 1):
            p0 = points[i - 1] if i > 0 else points[i]
            p1 = points[i]
            p2 = points[i + 1]
            p3 = points[i + 2] if i + 2 < len(points) else p2

            # Catmull-Rom to Cubic Bezier control points
            cp1x = p1[0] + (p2[0] - p0[0]) / 6.0
            cp1y = p1[1] + (p2[1] - p0[1]) / 6.0
            cp2x = p2[0] - (p3[0] - p1[0]) / 6.0
            cp2y = p2[1] - (p3[1] - p1[1]) / 6.0

            path.append(f"C {cp1x:.1f} {cp1y:.1f}, {cp2x:.1f} {cp2y:.1f}, {p2[0]:.1f} {p2[1]:.1f}")

        return " ".join(path)


def main():
    engine = ContributionGraphEngine("gauravgupta5813-coder")
    engine.render_svg(output_path="assets/generated/contribution-graph.svg")


if __name__ == "__main__":
    main()
