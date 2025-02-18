import os
import requests
import datetime
import matplotlib.pyplot as plt

# GitHub API settings
GITHUB_USERNAME = "mkr302"
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")  # Set this in GitHub Secrets

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
    """Fetch contributor stats for a single repository."""
    url = f"https://api.github.com/repos/{GITHUB_USERNAME}/{repo_name}/stats/contributors"
    headers = {"Authorization": f"token {GITHUB_TOKEN}"}
    response = requests.get(url, headers=headers)

    if response.status_code != 200:
        print(f"Skipping {repo_name}: {response.json()}")
        return None
    
    return response.json()

def process_stats(repos):
    """Aggregate GitHub stats across all repositories."""
    total_additions, total_deletions, total_updates = 0, 0, 0

    for repo in repos:
        print(f"Processing {repo}...")
        stats = fetch_repo_stats(repo)
        if not stats:
            continue

        for contributor in stats:
            for week in contributor["weeks"]:
                additions = week["a"]
                deletions = week["d"]
                updates = additions - deletions  # Updated lines

                total_additions += additions
                total_deletions += deletions
                total_updates += updates

    return {
        "Added": total_additions,
        "Removed": total_deletions,
        "Updated": total_updates
    }

def generate_chart(stats):
    """Generate a bar chart for GitHub code changes."""
    categories = list(stats.keys())
    values = [stats[cat] for cat in categories]

    plt.figure(figsize=(8, 5), facecolor="#181818")
    ax = plt.gca()
    ax.set_facecolor("#181818")

    plt.bar(categories, values, color=["#3CB371", "#FF4500", "#1E90FF"], alpha=0.85)
    plt.xlabel("Code Changes", fontsize=14, color="white")
    plt.ylabel("Lines of Code", fontsize=14, color="white")
    plt.title(f"GitHub Code Contributions - {GITHUB_USERNAME}", fontsize=16, color="white")

    plt.xticks(fontsize=12, color="white")
    plt.yticks(fontsize=12, color="white")
    plt.grid(axis="y", linestyle="--", alpha=0.5, color="gray")

    # Save the PNG file
    plt.savefig("github_code_metrics.png", dpi=300, bbox_inches="tight", facecolor="#181818")
    print("Graph saved as github_code_metrics.png")

if __name__ == "__main__":
    print("Fetching GitHub repositories...")
    repositories = fetch_repositories()
    
    if repositories:
        print("Fetching stats for all repositories...")
        processed_stats = process_stats(repositories)
        print("Generating chart...")
        generate_chart(processed_stats)
        print("Done! Check github_code_metrics.png.")
