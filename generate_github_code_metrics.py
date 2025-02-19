import os
import requests
import time
import datetime
import matplotlib.pyplot as plt

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

def generate_text_summary(stats):
    """Generate a text-based GitHub contribution summary with correctly formatted green icons."""

    fig, ax = plt.subplots(figsize=(12, 5), facecolor="black")
    ax.set_facecolor("black")
    ax.axis("off")  # Hide axes

    categories = list(stats["lifetime"].keys())
    lifetime_values = list(stats["lifetime"].values())
    current_values = list(stats["current_year"].values())

    # Define colors
    text_color = "white"
    icon_color = "#00FF00"  # Green

    # Title
    ax.text(0.5, 1.1, "Code Contribution Summary", fontsize=18, fontweight="bold", color=text_color, ha="center", va="center")

    # Labels and values for Lifetime Contributions
    ax.text(0.25, 0.7, "Lifetime Contributions", fontsize=16, fontweight="bold", color=text_color, ha="center", va="center")
    for i, (category, value) in enumerate(zip(categories, lifetime_values)):
        ax.text(0.25, 0.6 - i * 0.15, f"{category}:", fontsize=13, color=text_color, ha="right", va="left")
        ax.text(0.3, 0.6 - i * 0.15, f"{value:,}", fontsize=13, color=icon_color, ha="left", va="left")

    # Labels and values for Current Year Contributions
    ax.text(0.75, 0.7, f"Contributions in {datetime.datetime.now().year}", fontsize=16, fontweight="bold", color=text_color, ha="center", va="center")
    for i, (category, value) in enumerate(zip(categories, current_values)):
        ax.text(0.75, 0.6 - i * 0.15, f"{category}:", fontsize=13, color=text_color, ha="right", va="left")
        ax.text(0.8, 0.6 - i * 0.15, f"{value:,}", fontsize=13, color=icon_color, ha="left", va="left")

    # Save the PNG file with a **black background**
    plt.savefig("github_code_metrics.png", dpi=300, bbox_inches="tight", facecolor="#0d1117")
    print("Graph saved as github_code_metrics.png (black background, green symbols, properly formatted text)")

if __name__ == "__main__":
    print("Fetching GitHub repositories...")
    repositories = fetch_repositories()
    
    if repositories:
        print("Fetching lifetime and current year stats for all repositories...")
        processed_stats = process_stats(repositories)
        print("Generating text-based summary with correctly formatted green icons...")
        generate_text_summary(processed_stats)
        print("Done! Check github_code_text_summary.png.")
