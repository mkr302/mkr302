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

    #previous_year = current_year - 1

    for repo in repos:
        print(f"Processing {repo}...")
        stats = fetch_repo_stats(repo)
        if not stats:
            continue

        for contributor in stats:
            for week in contributor["weeks"]:
                additions = week["a"]
                deletions = week["d"]
                #updates = additions - deletions  # Updated lines
                timestamp = week["w"]
                week_year = datetime.datetime.utcfromtimestamp(timestamp).year

                # Lifetime stats
                total_additions += additions
                total_deletions += deletions
                #total_updates += updates
                total_updates += min(additions, deletions)  # Actual modified (updated) lines
                
                # Current year stats
                if week_year == current_year:
                    current_year_add += additions
                    current_year_del += deletions
                    current_year_upd += min(additions, deletions)

    return {
        "lifetime": {
            "Added": total_additions,
            "Removed": total_deletions,
            "Updated": total_updates
        },
        "current_year": {
            "Added": current_year_add,
            "Removed": current_year_del,
            "Updated": current_year_upd
        }
    }

def generate_charts(stats):
    """Display lifetime and current year GitHub contributions as numbers."""
    
    fig, ax = plt.subplots(figsize=(18, 4), facecolor="black")
    ax.set_facecolor("black")
    ax.axis("off")  # Hide axes

    categories = list(stats["lifetime"].keys())
    lifetime_values = list(stats["lifetime"].values())
    current_values = list(stats["current_year"].values())

    # White text for contrast
    text_color = "white"

    # Title
    ax.text(0.5, 1.1, "GitHub Contribution Summary", fontsize=20, fontweight="bold", color=text_color, ha="center", va="center")

    # Labels and values for Lifetime Contributions
    ax.text(0.25, 0.7, "Lifetime Contributions", fontsize=16, fontweight="bold", color=text_color, ha="center", va="center")
    for i, (category, value) in enumerate(zip(categories, lifetime_values)):
        ax.text(0.25, 0.6 - i * 0.15, f"{category}: {value:,}", fontsize=14, color=text_color, ha="center", va="center")

    # Labels and values for Current Year Contributions
    ax.text(0.75, 0.7, f"Contributions in {datetime.datetime.now().year}", fontsize=16, fontweight="bold", color=text_color, ha="center", va="center")
    for i, (category, value) in enumerate(zip(categories, current_values)):
        ax.text(0.75, 0.6 - i * 0.15, f"{category}: {value:,}", fontsize=14, color=text_color, ha="center", va="center")



    # Save the PNG file
    #plt.savefig("github_code_metrics.png", dpi=300, bbox_inches="tight", transparent=False)
    plt.savefig("github_code_metrics.png", dpi=300, bbox_inches="tight", facecolor="black")
    print("Graph saved as github_code_metrics.png")

if __name__ == "__main__":
    print("Fetching GitHub repositories...")
    repositories = fetch_repositories()
    
    if repositories:
        print("Fetching lifetime stats and current year stats for all repositories...")
        processed_stats = process_stats(repositories)
        print("Generating lifetime and yearly charts...")
        generate_charts(processed_stats)
        print("Done! Check github_code_metrics.png.")
