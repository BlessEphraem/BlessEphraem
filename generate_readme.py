import os

import requests

TOKEN = os.environ["GITHUB_TOKEN"]
USERNAME = os.environ["GITHUB_USERNAME"]

HEADERS = {
    "Authorization": f"Bearer {TOKEN}",
    "Accept": "application/vnd.github+json",
}

PRIORITY_TOPICS = ["software", "plugin", "scripts", "daemon"]
EXCLUDED_REPOS = {USERNAME.lower(), f"{USERNAME.lower()}.github.io"}


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
    return [r for r in repos if not r["fork"]]  # <-- filtre forks


def get_topics(repo_name):
    r = requests.get(
        f"https://api.github.com/repos/{USERNAME}/{repo_name}/topics",
        headers={**HEADERS, "Accept": "application/vnd.github.mercy-preview+json"},
    )
    return set(r.json().get("names", []))


def build_row(repo, topics):
    name = repo["name"]
    description = repo.get("description") or ""
    url = repo["html_url"]
    lang = repo.get("language") or "—"
    stars = repo["stargazers_count"]
    tags = " ".join(f"`{t}`" for t in sorted(topics))
    return f"| [{name}]({url}) | {description} | {lang} | {stars} | {tags} |"


def section_table(rows):
    header = "| Repo | Description | Language | ⭐ | Topics |\n|---|---|---|---|---|"
    return header + "\n" + "\n".join(rows)


repos = get_public_repos()

categorized = {t: [] for t in PRIORITY_TOPICS}
elsewhere = []

for repo in repos:
    name = repo["name"]
    if name in EXCLUDED_REPOS:
        continue
    topics = get_topics(name)

    matched = [t for t in PRIORITY_TOPICS if t in topics]
    if matched:
        # place le repo dans la première catégorie prioritaire trouvée
        categorized[matched[0]].append((repo, topics))
    else:
        elsewhere.append((repo, topics))

# tri alphabétique dans chaque section
for key in categorized:
    categorized[key].sort(key=lambda x: x[0]["name"].lower())
elsewhere.sort(key=lambda x: x[0]["name"].lower())

# --- Construction du README ---
lines = [f"# {USERNAME}\n"]

for topic in PRIORITY_TOPICS:
    entries = categorized[topic]
    if not entries:
        continue
    lines.append(f"\n## {topic.capitalize()}\n")
    rows = [build_row(r, t) for r, t in entries]
    lines.append(section_table(rows))

if elsewhere:
    lines.append("\n## Else\n")
    rows = [build_row(r, t) for r, t in elsewhere]
    lines.append(section_table(rows))

# Ton site perso en pied de page
lines.append(f"\n---\n🌐 [blessephraem.github.io](https://{USERNAME}.github.io)\n")

readme = "\n".join(lines)

with open("README.md", "w", encoding="utf-8") as f:
    f.write(readme)

print("README generated.")
