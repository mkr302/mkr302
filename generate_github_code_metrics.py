import os
import requests
import time
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
    """Fetch lifetime contributor stats for a repository."""
    url = f"https://api.github.com/repos/{GITHUB_USERNAME}/{repo_name}/stats/contributors"
    headers = {"Authorization": f"token {GITHUB_TOKEN}"}
    
    # Handle GitHub API rate limits
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
    """Aggregate lifetime GitHub stats across all repositories."""
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
    """Generate a lifetime GitHub contribution bar chart."""
    categories = list(stats.keys())
    values = [stats[cat] for cat in categories]

    plt.figure(figsize=(8, 5), facecolor="white")
    ax = plt.gca()
    ax.set_facecolor("#F9F9F9")

    plt.bar(categories, values, color=["#2E8B57", "#B22222", "#1E90FF"], alpha=0.85)

    plt.xlabel("Code Changes", fontsize=14, fontweight="bold", color="black")
    plt.ylabel("Total Lines of Code", fontsize=14, fontweight="bold", color="black")
    plt.title(f"Lifetime GitHub Code Contributions - {GITHUB_USERNAME}", fontsize=16, fontweight="bold", color="black")

    plt.xticks(fontsize=12, color="black")
    plt.yticks(fontsize=12, color="black")
    plt.grid(axis="y", linestyle="--", alpha=0.6, color="gray")

    # Save the PNG file
    plt.savefig("github_code_metrics.png", dpi=300, bbox_inches="tight", facecolor="white")
    print("Graph saved as github_code_metrics.png")

if __name__ == "__main__":
    print("Fetching GitHub repositories...")
    repositories = fetch_repositories()
    
    if repositories:
        print("Fetching lifetime stats for all repositories...")
        processed_stats = process_stats(repositories)
        print("Generating lifetime chart...")
        generate_chart(processed_stats)
        print("Done! Check github_lifetime_code_metrics.png.")
