import os
from datetime import date, datetime, timezone

import requests

TOKEN = os.environ["GITHUB_TOKEN"]
USERNAME = os.environ["GITHUB_USERNAME"]

HEADERS = {
    "Authorization": f"Bearer {TOKEN}",
    "Accept": "application/vnd.github+json",
}

PRIORITY_TOPICS = ["software", "plugins", "scripts", "daemon"]

# Aliases acceptés par topic (singulier, variantes)
TOPIC_ALIASES = {
    "software": {"software"},
    "plugins": {"plugins", "plugin"},
    "scripts": {"scripts", "script"},
    "daemon": {"daemon", "daemons"},
}
EXCLUDED_REPOS = {USERNAME.lower(), f"{USERNAME.lower()}.github.io"}

# Emoji + couleur shields.io par catégorie
CATEGORY_META = {
    "software": {"emoji": "💻", "label": "𝐏𝐑𝐎𝐆𝐑𝐀𝐌𝐒", "color": "278BF5"},
    "plugins": {"emoji": "🔌", "label": "𝐏𝐋𝐔𝐆𝐈𝐍𝐒", "color": "C80A0A"},
    "scripts": {"emoji": "📜", "label": "𝐒𝐂𝐑𝐈𝐏𝐓𝐒", "color": "2EA043"},
    "daemon": {"emoji": "⚙️", "label": "𝐃𝐀𝐄𝐌𝐎𝐍𝐒", "color": "8B5CF6"},
    "else": {"emoji": "🛠️", "label": "𝐄𝐋𝐒𝐄", "color": "334455"},
}


def get_public_repos():
    repos, page = [], 1
    while True:
        r = requests.get(
            f"https://api.github.com/users/{USERNAME}/repos",
            headers=HEADERS,
            params={"type": "public", "per_page": 100, "page": page},
        )
        r.raise_for_status()
        batch = r.json()
        if not batch:
            break
        repos.extend(batch)
        page += 1
    return [r for r in repos if not r["fork"]]


def get_topics(repo_name):
    r = requests.get(
        f"https://api.github.com/repos/{USERNAME}/{repo_name}/topics",
        headers={**HEADERS, "Accept": "application/vnd.github.mercy-preview+json"},
    )
    return set(r.json().get("names", []))


def make_badge(repo, category_key):
    """Génère un badge shields.io cliquable pour un repo."""
    name = repo["name"]
    description = repo.get("description") or ""
    url = repo["html_url"]
    meta = CATEGORY_META[category_key]
    color = meta["color"]
    emoji = meta["emoji"]

    # Le label du badge = emoji + nom du repo (encode les espaces et tirets)
    badge_label = f"{emoji}_{name}".replace("-", "_").replace(" ", "_")
    badge_url = (
        f"https://img.shields.io/badge/{badge_label}-{color}?style=for-the-badge"
    )

    line = f"* [![{name}]({badge_url})]({url})"
    if description:
        line += f" : {description}"
    return line


# --- Récupération & tri ---
repos = get_public_repos()

categorized = {t: [] for t in PRIORITY_TOPICS}
elsewhere = []

for repo in repos:
    name = repo["name"]
    if name.lower() in EXCLUDED_REPOS:
        continue
    topics = get_topics(name)

    matched = [t for t in PRIORITY_TOPICS if topics & TOPIC_ALIASES[t]]
    if matched:
        categorized[matched[0]].append(repo)
    else:
        elsewhere.append(repo)

for key in categorized:
    categorized[key].sort(key=lambda r: r["name"].lower())
elsewhere.sort(key=lambda r: r["name"].lower())


# --- Calcul de l'âge ---
BIRTHDATE = date(2002, 4, 15)


def compute_age(today: date = None) -> int:
    today = today or date.today()
    age = today.year - BIRTHDATE.year
    if (today.month, today.day) < (BIRTHDATE.month, BIRTHDATE.day):
        age -= 1
    return age


# --- Génération du tape VHS ---
def generate_tape(age: int, out_path: str = "fastfetch.gif"):
    tape = f"""\
Output {out_path}

Set FontFamily "JetBrainsMonoNL Nerd Font Mono"
Set FontSize 12
Set Width 860
Set Height 480
Set Framerate 24
Set PlaybackSpeed 1

Hide

Type "fastfetch --set-config none --structure Title:OS:Kernel:Packages:Shell:Terminal:Font:Blank:Age --age {age}\\ years"
Enter
Sleep 3s

Show
"""
    with open("fastfetch.tape", "w", encoding="utf-8") as f:
        f.write(tape)


age = compute_age()
generate_tape(age)

# --- Construction du README ---
with open("INTRO.md", "r", encoding="utf-8") as f:
    intro = f.read().rstrip("\n")

lines = intro.splitlines()
lines = [
    '<div align="center">',
    "",
    "![fastfetch](assets/fastfetch.gif)",
    "",
    "</div>",
    "",
] + lines
lines.append("")  # ligne vide de séparation avant les sections

for topic in PRIORITY_TOPICS:
    entries = categorized[topic]
    if not entries:
        continue
    meta = CATEGORY_META[topic]
    lines.append(f"### {meta['emoji']} {meta['label']}")
    for repo in entries:
        lines.append(make_badge(repo, topic))
    lines.append("")

if elsewhere:
    meta = CATEGORY_META["else"]
    lines.append(f"### {meta['emoji']} {meta['label']}")
    for repo in elsewhere:
        lines.append(make_badge(repo, "else"))
    lines.append("")

readme = "\n".join(lines)

with open("README.md", "w", encoding="utf-8") as f:
    f.write(readme)

print("README generated.")
