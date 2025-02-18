import os
import requests
import time
import numpy as np
import matplotlib.pyplot as plt
import datetime

# GitHub API settings
GITHUB_USERNAME = "mkr302"  
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")

GITHUB_API_URL = f"https://api.github.com/users/{GITHUB_USERNAME}/repos"

def fetch_repositories():
    """Fetch all repositories owned by the user."""
    headers = {"Authorization": f"token {GITHUB_TOKEN}"}
    response = requests.get(GITHUB_API_URL, headers=headers)

    if response.status_code != 200:
        print(f"Error fetching repositories: {response.json()}")
        return []
    
    repos = response.json()
    return [repo["name"] for repo in repos]

def fetch_repo_stats(repo_name):
    """Fetch contributor stats for a repository."""
    url = f"https://api.github.com/repos/{GITHUB_USERNAME}/{repo_name}/stats/contributors"
    headers = {"Authorization": f"token {GITHUB_TOKEN}"}
    
    for _ in range(5):  # Retry up to 5 times
        response = requests.get(url, headers=headers)
        
        if response.status_code == 200:
            return response.json()
        elif response.status_code == 202:  # GitHub is still processing stats
            print(f"GitHub is processing stats for {repo_name}, retrying in 10 seconds...")
            time.sleep(10)
        else:
            print(f"Skipping {repo_name}: {response.json()}")
            return None

    return None

def process_stats(repos):
    """Aggregate both lifetime and current year GitHub stats."""
    total_additions, total_deletions, total_updates = 0, 0, 0
    current_year_add, current_year_del, current_year_upd = 0, 0, 0

    current_year = datetime.datetime.now().year

    for repo in repos:
        print(f"Processing {repo}...")
        stats = fetch_repo_stats(repo)
        if not stats:
            continue

        for contributor in stats:
            for week in contributor["weeks"]:
                additions = week["a"]
                deletions = week["d"]
                timestamp = week["w"]
                week_year = datetime.datetime.utcfromtimestamp(timestamp).year

                # Lifetime stats
                total_additions += additions
                total_deletions += deletions
                total_updates += min(additions, deletions)

                # Current year stats
                if week_year == current_year:
                    current_year_add += additions
                    current_year_del += deletions
                    current_year_upd += min(additions, deletions)

    return {
        "lifetime": {
            "Lines Added": total_additions,
            "Lines Removed": total_deletions,
            "Lines Updated": total_updates
        },
        "current_year": {
            "Lines Added": current_year_add,
            "Lines Removed": current_year_del,
            "Lines Updated": current_year_upd
        }
    }

def generate_donut_charts(stats):
    """Generate side-by-side donut charts for Lifetime & Current Year contributions."""

    categories = list(stats["lifetime"].keys())
    lifetime_values = list(stats["lifetime"].values())
    current_values = list(stats["current_year"].values())

    # Muted, professional journal-style colors
    colors = ["#4C72B0", "#DD8452", "#55A868"]  # Soft Blue, Muted Orange, Subtle Green

    fig, axes = plt.subplots(1, 2, figsize=(14, 6), facecolor="black")

    for ax in axes:
        ax.set_facecolor("black")

    # Left Chart: Lifetime Contributions
    wedges, texts, autotexts = axes[0].pie(
        lifetime_values, labels=categories, autopct="%1.1f%%", startangle=90,
        colors=colors, wedgeprops={"edgecolor": "black"}, pctdistance=0.75
    )
    for text in texts + autotexts:
        text.set_color("white")

    # Add a circle at the center to make it a donut chart
    centre_circle = plt.Circle((0, 0), 0.60, fc="black")
    axes[0].add_artist(centre_circle)

    axes[0].set_title("Lifetime Contributions", fontsize=16, fontweight="bold", color="white")

    # Right Chart: Current Year Contributions
    wedges, texts, autotexts = axes[1].pie(
        current_values, labels=categories, autopct="%1.1f%%", startangle=90,
        colors=colors, wedgeprops={"edgecolor": "black"}, pctdistance=0.75
    )
    for text in texts + autotexts:
        text.set_color("white")

    # Add a circle at the center to make it a donut chart
    centre_circle = plt.Circle((0, 0), 0.60, fc="black")
    axes[1].add_artist(centre_circle)

    axes[1].set_title(f"Contributions in {datetime.datetime.now().year}", fontsize=16, fontweight="bold", color="white")

    # Save the PNG file with a **black background**
    plt.savefig("github_code_metrics.png", dpi=300, bbox_inches="tight", facecolor="gray")
    print("Graph saved as github_code_metrics.png")

if __name__ == "__main__":
    print("Fetching GitHub repositories...")
    repositories = fetch_repositories()
    
    if repositories:
        print("Fetching lifetime and current year stats for all repositories...")
        processed_stats = process_stats(repositories)
        print("Generating donut charts...")
        generate_donut_charts(processed_stats)
        print("Done! Check github_code_donut.png.")
