"""Rewrite the activity section of README.md with recent public GitHub events."""

import json
import os
import re
import urllib.request

USER = os.environ.get("GITHUB_USER", "ryangii")
TOKEN = os.environ.get("GITHUB_TOKEN")
README = os.environ.get("README_PATH", "README.md")
LIMIT = int(os.environ.get("ACTIVITY_LIMIT", "5"))

START = "<!--START_SECTION:activity-->"
END = "<!--END_SECTION:activity-->"


def fetch_events():
    req = urllib.request.Request(
        f"https://api.github.com/users/{USER}/events/public?per_page=100",
        headers={"Accept": "application/vnd.github+json", "User-Agent": USER},
    )
    if TOKEN:
        req.add_header("Authorization", f"Bearer {TOKEN}")
    with urllib.request.urlopen(req) as resp:
        return json.load(resp)


def repo_link(event):
    name = event["repo"]["name"]
    return f"[{name}](https://github.com/{name})"


def describe(event):
    kind, p, repo = event["type"], event["payload"], repo_link(event)
    if kind == "PushEvent":
        n = p.get("size") or len(p.get("commits", [])) or 1
        return f"⬆️ Pushed {n} commit{'s' if n != 1 else ''} to {repo}"
    if kind == "PullRequestEvent":
        pr = p["pull_request"]
        action = "Merged" if p["action"] == "closed" and pr.get("merged") else p["action"].capitalize()
        return f"🔀 {action} PR [#{pr['number']}]({pr['html_url']}) in {repo}"
    if kind == "IssuesEvent":
        issue = p["issue"]
        return f"🐛 {p['action'].capitalize()} issue [#{issue['number']}]({issue['html_url']}) in {repo}"
    if kind == "IssueCommentEvent":
        issue = p["issue"]
        return f"💬 Commented on [#{issue['number']}]({p['comment']['html_url']}) in {repo}"
    if kind == "PullRequestReviewEvent":
        pr = p["pull_request"]
        return f"👀 Reviewed PR [#{pr['number']}]({pr['html_url']}) in {repo}"
    if kind == "CreateEvent" and p.get("ref_type") == "repository":
        return f"✨ Created repository {repo}"
    if kind == "ReleaseEvent":
        rel = p["release"]
        return f"🚀 Released [{rel['tag_name']}]({rel['html_url']}) in {repo}"
    if kind == "WatchEvent":
        return f"⭐ Starred {repo}"
    if kind == "ForkEvent":
        return f"🍴 Forked {repo}"
    return None


def render(events):
    lines = []
    for event in events:
        text = describe(event)
        if text and (not lines or lines[-1] != text):
            lines.append(text)
        if len(lines) == LIMIT:
            break
    if not lines:
        return "_No recent public activity._"
    return "\n".join(f"{i}. {line}" for i, line in enumerate(lines, 1))


def main():
    with open(README, encoding="utf-8") as f:
        readme = f.read()
    pattern = re.compile(re.escape(START) + r".*?" + re.escape(END), re.DOTALL)
    if not pattern.search(readme):
        raise SystemExit(f"Markers {START} / {END} not found in {README}")
    body = render(fetch_events())
    updated = pattern.sub(lambda _: f"{START}\n{body}\n{END}", readme)
    if updated != readme:
        with open(README, "w", encoding="utf-8") as f:
            f.write(updated)
        print("README updated")
    else:
        print("No changes")


if __name__ == "__main__":
    main()
