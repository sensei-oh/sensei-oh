import base64
import calendar
import datetime
import hashlib
import html
import json
import os
import urllib.request
from pathlib import Path

# ==============================================================================
# PROFILE CONFIGURATION BLOCK (EDIT YOUR INFO HERE)
# ==============================================================================

# 1. Identity & Uptime
GITHUB_USERNAME = "sensei-oh"
NODE_PREFIX = "01 //"
NODE_TITLE = "Node: Janit Sarvaiya"
BIRTH_DATE = datetime.date(2008, 9, 12)  # YYYY, M, D -> live UPTIME

# 2. System Ribbon (2x2 Grid)
SYS_OS = "Windows 11"
SYS_DISCIPLINE = "CSE | AI & DS"
SYS_KERNEL = "Student"
SYS_IDE = "VS Code"

# 3. Dossier Lists (Add or remove items freely; lists auto-join with ' · ')
PROG_LANGUAGES = ["JS"]
MARKUP_LANGUAGES = ["HTML", "CSS"]
SPOKEN_LANGUAGES = ["English", "Hindi", "Marathi"]
FOCUS_TAGS = ["Web Dev", "Creative Dev"]  # Add future tags here
PERSONAL_TAGS = ["Music", "Film", "Midnight Mode"]

# 4. Comms Footer
COMMS_EMAIL = "janit.sarvaiya1208@gmail.com"
COMMS_GITHUB = "sensei-oh"
COMMS_LINKEDIN = "janit-x"

# 5. Root File Paths (zeofr/zeofr structure)
DISC_IMAGE_PATH = Path("disc.png")
DARK_SVG_PATH = Path("dark_mode.svg")
LIGHT_SVG_PATH = Path("light_mode.svg")
CACHE_DIR = Path("cache")

# 6. Theme Palettes (Dark = Neutral Charcoal-Black | Light = Inverted Crisp Slate)
THEMES = {
    "dark": {
        "canvas_bg": "#000000",       # Pitch-black outer canvas
        "panel_bg": "#0c0c0c",        # Neutral charcoal-black section bodies & disc bezel mat
        "header_band_bg": "#181818",  # Slightly lighter neutral charcoal section title bands
        "border_color": "#25364d",    # Muted steel-blue module borders
        "hairline_color": "#242424",  # Neutral dark grey internal row/cell dividers
        "bracket_color": "#7aa2f7",   # Ice-blue corner brackets
        "heading_pink": "#cf7f96",    # Dusty rose-pink section headers & '>' arrows
        "metric_blue": "#7aa2f7",     # Ice-blue telemetry numbers
        "accent_orange": "#d0952f",   # Burnt-orange micro-accents ('01 //' & 'LIVE' bar)
        "loc_add": "#4ade80",         # Additions green
        "matrix_blue": "#5882b8",     # Steel-blue 'J' LEDs
        "matrix_pink": "#cf7f96",     # Dusty rose-pink 'S' LEDs
        "matrix_off": "#1c1c1c",      # Subtle inactive LED dot fill on #0c0c0c header
        "text_primary": "#e6e8ec",    # Crisp off-white values
        "text_muted": "#737373",      # Neutral slate uppercase field labels
    },
    "light": {
        "canvas_bg": "#f6f8fa",       # Soft cool off-white outer canvas
        "panel_bg": "#ffffff",        # Pure crisp white section bodies & disc bezel mat
        "header_band_bg": "#eef1f5",  # Slightly shaded cool slate section title bands
        "border_color": "#d0d7de",    # Cool slate module borders
        "hairline_color": "#e5e9f0",  # Light grey internal row/cell dividers
        "bracket_color": "#4a72a8",   # Steel-blue corner brackets
        "heading_pink": "#b85d78",    # Deeper dusty rose-pink section headers & '>' arrows
        "metric_blue": "#3a6fb0",     # Deep steel-blue telemetry numbers
        "accent_orange": "#b87b1e",   # Rich amber-ochre micro-accents ('01 //' & 'LIVE' bar)
        "loc_add": "#1a7f37",         # GitHub light additions green
        "matrix_blue": "#4a72a8",     # Steel-blue 'J' LEDs
        "matrix_pink": "#b85d78",     # Dusty rose-pink 'S' LEDs
        "matrix_off": "#e5e9f0",      # Subtle inactive LED dot fill on #ffffff header
        "text_primary": "#1f2328",    # Deep charcoal ink values
        "text_muted": "#656d76",      # Muted slate uppercase field labels
    },
}

# ==============================================================================
# DATA FETCHING, CACHING & UPTIME CALCULATION
# ==============================================================================

TOKEN = os.environ.get("ACCESS_TOKEN") or os.environ.get("GITHUB_TOKEN", "")


def esc(text: str) -> str:
    return html.escape(str(text), quote=True)


def calculate_uptime(start: datetime.date, today: datetime.date) -> str:
    years = today.year - start.year
    months = today.month - start.month
    days = today.day - start.day

    if days < 0:
        months -= 1
        prev_month = today.month - 1 or 12
        prev_year = today.year if today.month > 1 else today.year - 1
        days += calendar.monthrange(prev_year, prev_month)[1]

    if months < 0:
        years -= 1
        months += 12

    return f"{years} years, {months} months, {days} days"


def github_graphql(query: str, variables: dict) -> dict:
    req = urllib.request.Request(
        "https://api.github.com/graphql",
        data=json.dumps({"query": query, "variables": variables}).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {TOKEN}",
            "Content-Type": "application/json",
            "User-Agent": f"{GITHUB_USERNAME}-readme-hud",
        },
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read().decode("utf-8"))


def get_cached_repo_metrics(repo_node: dict, username_lower: str) -> tuple[int, int, int]:
    """Caches per-repo (commits, additions, deletions) keyed by HEAD commit OID."""
    name = repo_node["nameWithOwner"]
    cache_file = CACHE_DIR / f"{hashlib.sha256(name.encode()).hexdigest()[:16]}.json"

    branch = repo_node.get("defaultBranchRef")
    if not branch or not branch.get("target"):
        return 0, 0, 0

    target = branch["target"]
    head_oid = target.get("oid", "")
    history = target["history"]

    if cache_file.exists():
        try:
            cached = json.loads(cache_file.read_text(encoding="utf-8"))
            if cached.get("oid") == head_oid:
                return cached["commits"], cached["additions"], cached["deletions"]
        except (json.JSONDecodeError, KeyError):
            pass

    commits = history["totalCount"]
    additions = 0
    deletions = 0
    for c in history["nodes"]:
        author_login = ((c.get("author") or {}).get("user") or {}).get("login", "")
        if author_login.lower() == username_lower:
            additions += c.get("additions", 0)
            deletions += c.get("deletions", 0)

    cache_file.write_text(
        json.dumps(
            {
                "repo": name,
                "oid": head_oid,
                "commits": commits,
                "additions": additions,
                "deletions": deletions,
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    return commits, additions, deletions


def fetch_github_stats() -> dict:
    if not TOKEN:
        return {
            "commits": "816",
            "repos": "24",
            "contrib": "50",
            "loc_net": "48,920",
            "loc_add": "+61,400",
            "loc_del": "-12,480",
        }

    query = """
    query($login: String!) {
      user(login: $login) {
        repositories(ownerAffiliations: OWNER, isFork: false, first: 100) {
          totalCount
          nodes {
            nameWithOwner
            defaultBranchRef {
              target {
                ... on Commit {
                  oid
                  history(first: 100) {
                    totalCount
                    nodes {
                      additions
                      deletions
                      author { user { login } }
                    }
                  }
                }
              }
            }
          }
        }
        repositoriesContributedTo(
          first: 100
          contributionTypes: [COMMIT, ISSUE, PULL_REQUEST, REPOSITORY]
          includeUserRepositories: false
        ) {
          totalCount
        }
        contributionsCollection {
          totalCommitContributions
          restrictedContributionsCount
        }
      }
    }
    """
    res = github_graphql(query, {"login": GITHUB_USERNAME})
    user = res["data"]["user"]

    repos_count = user["repositories"]["totalCount"]
    contrib_count = user["repositoriesContributedTo"]["totalCount"]

    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    username_lower = GITHUB_USERNAME.lower()
    total_commits = 0
    additions = 0
    deletions = 0
    for repo in user["repositories"]["nodes"]:
        c, a, d = get_cached_repo_metrics(repo, username_lower)
        total_commits += c
        additions += a
        deletions += d

    cc = user["contributionsCollection"]
    yearly_commits = cc["totalCommitContributions"] + cc["restrictedContributionsCount"]
    total_commits = max(total_commits, yearly_commits)
    net_loc = max(0, additions - deletions)

    return {
        "commits": f"{total_commits:,}",
        "repos": f"{repos_count:,}",
        "contrib": f"{contrib_count:,}",
        "loc_net": f"{net_loc:,}",
        "loc_add": f"+{additions:,}",
        "loc_del": f"-{deletions:,}",
    }


# ==============================================================================
# SVG COMPONENT BUILDERS (zeofr/zeofr 985x530 Canvas Dimensions)
# ==============================================================================

def corner_brackets(x: int, y: int, w: int, h: int, color: str, size: int = 8) -> str:
    x2, y2 = x + w, y + h
    return (
        f'<path d="M{x} {y + size} V{y} H{x + size}" stroke="{color}" stroke-width="1.5"/>'
        f'<path d="M{x2 - size} {y} H{x2} V{y + size}" stroke="{color}" stroke-width="1.5"/>'
        f'<path d="M{x} {y2 - size} V{y2} H{x + size}" stroke="{color}" stroke-width="1.5"/>'
        f'<path d="M{x2 - size} {y2} H{x2} V{y2 - size}" stroke="{color}" stroke-width="1.5"/>'
    )


def build_js_dot_matrix(t: dict, origin_x: int = 880, origin_y: int = 20) -> str:
    j_dots = {
        (0, 3), (0, 4), (0, 5), (0, 6),
        (1, 5), (1, 6),
        (2, 5), (2, 6),
        (3, 5), (3, 6),
        (4, 1), (4, 2), (4, 5), (4, 6),
        (5, 1), (5, 2), (5, 5), (5, 6),
        (6, 2), (6, 3), (6, 4), (6, 5),
    }
    s_dots = {
        (0, 9), (0, 10), (0, 11), (0, 12), (0, 13),
        (1, 8), (1, 9),
        (2, 8), (2, 9),
        (3, 9), (3, 10), (3, 11), (3, 12),
        (4, 12), (4, 13),
        (5, 12), (5, 13),
        (6, 8), (6, 9), (6, 10), (6, 11), (6, 12),
    }
    circles = []
    step_x = 4.8
    step_y = 4.4
    for r in range(7):
        for c in range(15):
            cx = origin_x + c * step_x + 2.4
            cy = origin_y + r * step_y
            if (r, c) in j_dots:
                fill = t["matrix_blue"]
            elif (r, c) in s_dots:
                fill = t["matrix_pink"]
            else:
                fill = t["matrix_off"]
            circles.append(f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="1.65" fill="{fill}"/>')
    return "\n    ".join(circles)


def get_disc_data_uri() -> str:
    if DISC_IMAGE_PATH.exists():
        encoded = base64.b64encode(DISC_IMAGE_PATH.read_bytes()).decode("ascii")
        return f"data:image/png;base64,{encoded}"
    return ""


def build_svg(uptime_str: str, stats: dict, disc_uri: str, theme_name: str) -> str:
    t = THEMES[theme_name]
    prog_str = " · ".join(PROG_LANGUAGES)
    markup_str = " · ".join(MARKUP_LANGUAGES)
    spoken_str = " · ".join(SPOKEN_LANGUAGES)
    focus_str = " · ".join(FOCUS_TAGS)
    personal_str = " · ".join(PERSONAL_TAGS)

    # Strict 1:1 square viewport (398x398) centered inside the right bezel stage (x=520..969, y=64..476)
    disc_layer = (
        f'<image href="{disc_uri}" x="545" y="71" width="398" height="398" preserveAspectRatio="xMidYMid meet"/>'
        if disc_uri
        else f'<text x="744" y="274" class="mono" fill="{t["text_muted"]}" font-size="13" text-anchor="middle">[ PLACE disc.png IN ROOT ]</text>'
    )

    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="985" height="530" viewBox="0 0 985 530" fill="none">
  <defs>
    <style>
      .mono {{ font-family: 'JetBrains Mono', 'Fira Code', 'Cascadia Code', Consolas, monospace; }}
      .label {{ font-size: 11px; font-weight: 600; fill: {t["text_muted"]}; letter-spacing: 1.2px; }}
      .val {{ font-size: 13.5px; font-weight: 500; fill: {t["text_primary"]}; }}
      .sec-title {{ font-size: 12px; font-weight: 700; fill: {t["heading_pink"]}; letter-spacing: 1.5px; }}
      .stat-num {{ font-size: 20px; font-weight: 700; fill: {t["metric_blue"]}; }}
    </style>
    <pattern id="live-hatch-{theme_name}" width="7" height="7" patternTransform="rotate(35 0 0)" patternUnits="userSpaceOnUse">
      <line x1="0" y1="0" x2="0" y2="7" stroke="{t["accent_orange"]}" stroke-width="2.2"/>
    </pattern>
  </defs>

  <!-- Outer Canvas (zeofr/zeofr 985x530) -->
  <rect width="985" height="530" fill="{t["canvas_bg"]}"/>

  <!-- ==================== 1. TOP STATUS HEADER ==================== -->
  <rect x="16" y="11" width="953" height="44" fill="{t["panel_bg"]}" stroke="{t["border_color"]}" stroke-width="1"/>
  {corner_brackets(16, 11, 953, 44, t["bracket_color"], 7)}
  <text x="30" y="38" class="mono" font-size="15.5" font-weight="700">
    <tspan fill="{t["accent_orange"]}">{esc(NODE_PREFIX)} </tspan><tspan fill="{t["text_primary"]}">{esc(NODE_TITLE)}</tspan>
  </text>
  {build_js_dot_matrix(t, 880, 20)}

  <!-- ==================== 2. LEFT COLUMN: SYSTEM 2x2 ==================== -->
  <rect x="16" y="64" width="492" height="56" fill="{t["panel_bg"]}" stroke="{t["border_color"]}" stroke-width="1"/>
  {corner_brackets(16, 64, 492, 56, t["bracket_color"], 7)}
  <line x1="258" y1="64" x2="258" y2="120" stroke="{t["hairline_color"]}" stroke-width="1"/>
  <line x1="16" y1="92" x2="508" y2="92" stroke="{t["hairline_color"]}" stroke-width="1"/>

  <text x="30" y="82" class="mono"><tspan class="label">OS // </tspan><tspan class="val">{esc(SYS_OS)}</tspan></text>
  <text x="270" y="82" class="mono"><tspan class="label">DISCIPLINE // </tspan><tspan class="val">{esc(SYS_DISCIPLINE)}</tspan></text>
  <text x="30" y="110" class="mono"><tspan class="label">KERNEL // </tspan><tspan class="val">{esc(SYS_KERNEL)}</tspan></text>
  <text x="270" y="110" class="mono"><tspan class="label">IDE // </tspan><tspan class="val">{esc(SYS_IDE)}</tspan></text>

  <!-- ==================== 3. LEFT COLUMN: // DOSSIER ==================== -->
  <rect x="16" y="129" width="492" height="199" fill="{t["panel_bg"]}" stroke="{t["border_color"]}" stroke-width="1"/>
  <rect x="16.5" y="129.5" width="491" height="27.5" fill="{t["header_band_bg"]}"/>
  {corner_brackets(16, 129, 492, 199, t["bracket_color"], 7)}
  <text x="30" y="148" class="mono sec-title">// DOSSIER</text>
  <line x1="16" y1="157" x2="508" y2="157" stroke="{t["hairline_color"]}" stroke-width="1"/>

  <!-- Row 1: LANGUAGES -->
  <text x="30" y="176" class="mono label">LANGUAGES</text>
  <text x="150" y="176" class="mono val"><tspan fill="{t["heading_pink"]}" font-weight="700">&gt; </tspan><tspan fill="{t["text_muted"]}" font-size="12">PROG   </tspan><tspan>{esc(prog_str)}</tspan></text>
  <text x="150" y="195" class="mono val"><tspan fill="{t["heading_pink"]}" font-weight="700">&gt; </tspan><tspan fill="{t["text_muted"]}" font-size="12">MARKUP </tspan><tspan>{esc(markup_str)}</tspan></text>
  <line x1="16" y1="205" x2="508" y2="205" stroke="{t["hairline_color"]}" stroke-width="1"/>

  <!-- Row 2: SPOKEN -->
  <text x="30" y="225" class="mono label">SPOKEN</text>
  <text x="150" y="225" class="mono val">{esc(spoken_str)}</text>
  <line x1="16" y1="236" x2="508" y2="236" stroke="{t["hairline_color"]}" stroke-width="1"/>

  <!-- Row 3: UPTIME -->
  <text x="30" y="256" class="mono label">UPTIME</text>
  <text x="150" y="256" class="mono val">{esc(uptime_str)}</text>
  <line x1="16" y1="267" x2="508" y2="267" stroke="{t["hairline_color"]}" stroke-width="1"/>

  <!-- Row 4: FOCUS -->
  <text x="30" y="287" class="mono label">FOCUS</text>
  <text x="150" y="287" class="mono val">{esc(focus_str)}</text>
  <line x1="16" y1="298" x2="508" y2="298" stroke="{t["hairline_color"]}" stroke-width="1"/>

  <!-- Row 5: PERSONAL -->
  <text x="30" y="318" class="mono label">PERSONAL</text>
  <text x="150" y="318" class="mono val">{esc(personal_str)}</text>

  <!-- ==================== 4. LEFT COLUMN: // TELEMETRY ==================== -->
  <rect x="16" y="337" width="492" height="139" fill="{t["panel_bg"]}" stroke="{t["border_color"]}" stroke-width="1"/>
  <rect x="16.5" y="337.5" width="491" height="27.5" fill="{t["header_band_bg"]}"/>
  {corner_brackets(16, 337, 492, 139, t["bracket_color"], 7)}
  <text x="30" y="356" class="mono sec-title">// TELEMETRY</text>
  <line x1="16" y1="365" x2="508" y2="365" stroke="{t["hairline_color"]}" stroke-width="1"/>

  <!-- 2x2 Telemetry Grid -->
  <line x1="258" y1="365" x2="258" y2="449" stroke="{t["hairline_color"]}" stroke-width="1"/>
  <line x1="16" y1="407" x2="508" y2="407" stroke="{t["hairline_color"]}" stroke-width="1"/>

  <text x="30" y="382" class="mono label">COMMITS</text>
  <text x="30" y="401" class="mono stat-num">{esc(stats["commits"])}</text>

  <text x="272" y="382" class="mono label">REPOS</text>
  <text x="272" y="401" class="mono stat-num">{esc(stats["repos"])}</text>

  <text x="30" y="424" class="mono label">CONTRIB</text>
  <text x="30" y="443" class="mono stat-num">{esc(stats["contrib"])}</text>

  <text x="272" y="424" class="mono label">LINES OF CODE</text>
  <text x="272" y="443" class="mono">
    <tspan class="stat-num" font-size="18.5">{esc(stats["loc_net"])} </tspan>
    <tspan fill="{t["loc_add"]}" font-size="11.5">({esc(stats["loc_add"])}</tspan>
    <tspan fill="{t["text_muted"]}" font-size="11.5"> / </tspan>
    <tspan fill="{t["heading_pink"]}" font-size="11.5">{esc(stats["loc_del"])})</tspan>
  </text>

  <!-- Hatched LIVE Progress Bar -->
  <line x1="16" y1="449" x2="508" y2="449" stroke="{t["hairline_color"]}" stroke-width="1"/>
  <rect x="30" y="457" width="426" height="10" fill="{t["canvas_bg"]}" stroke="{t["accent_orange"]}" stroke-width="0.9"/>
  <rect x="32" y="459" width="352" height="6" fill="url(#live-hatch-{theme_name})"/>
  <text x="494" y="466" class="mono" fill="{t["accent_orange"]}" font-size="11" font-weight="700" text-anchor="end">LIVE</text>

  <!-- ==================== 5. RIGHT COLUMN: 1:1 VINYL DISC STAGE ==================== -->
  <rect x="520" y="64" width="449" height="412" fill="{t["panel_bg"]}" stroke="{t["border_color"]}" stroke-width="1"/>
  {corner_brackets(520, 64, 449, 412, t["bracket_color"], 9)}
  {disc_layer}

  <!-- ==================== 6. BOTTOM FULL-WIDTH ROW: // COMMS ==================== -->
  <rect x="16" y="485" width="953" height="34" fill="{t["panel_bg"]}" stroke="{t["border_color"]}" stroke-width="1"/>
  <rect x="16.5" y="485.5" width="107.5" height="33" fill="{t["header_band_bg"]}"/>
  {corner_brackets(16, 485, 953, 34, t["bracket_color"], 7)}
  <line x1="124" y1="485" x2="124" y2="519" stroke="{t["hairline_color"]}" stroke-width="1"/>
  <line x1="478" y1="485" x2="478" y2="519" stroke="{t["hairline_color"]}" stroke-width="1"/>
  <line x1="726" y1="485" x2="726" y2="519" stroke="{t["hairline_color"]}" stroke-width="1"/>

  <text x="30" y="506" class="mono sec-title">// COMMS</text>
  <text x="140" y="506" class="mono"><tspan class="label">MAIL // </tspan><tspan class="val">{esc(COMMS_EMAIL)}</tspan></text>
  <text x="494" y="506" class="mono"><tspan class="label">GITHUB // </tspan><tspan class="val">{esc(COMMS_GITHUB)}</tspan></text>
  <text x="742" y="506" class="mono"><tspan class="label">LINKEDIN // </tspan><tspan class="val">{esc(COMMS_LINKEDIN)}</tspan></text>
</svg>
"""


def write_if_changed(path: Path, content: str) -> bool:
    if path.exists() and path.read_text(encoding="utf-8") == content:
        return False
    path.write_text(content, encoding="utf-8")
    return True


def main() -> None:
    today = datetime.date.today()
    uptime_str = calculate_uptime(BIRTH_DATE, today)
    stats = fetch_github_stats()
    disc_uri = get_disc_data_uri()

    dark_changed = write_if_changed(DARK_SVG_PATH, build_svg(uptime_str, stats, disc_uri, "dark"))
    light_changed = write_if_changed(LIGHT_SVG_PATH, build_svg(uptime_str, stats, disc_uri, "light"))

    status = f"dark={'updated' if dark_changed else 'unchanged'}, light={'updated' if light_changed else 'unchanged'}"
    print(f"HUD Build ({status}) | Uptime: {uptime_str} | Stats: {stats}")


if __name__ == "__main__":
    main()
