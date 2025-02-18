import os
import requests
import time
import numpy as np
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
                #updates = additions - deletions  # Updated lines

                total_additions += additions
                total_deletions += deletions
                #total_updates += updates
                total_updates += min(additions, deletions)  # Actual modified (updated) lines

    return {
        "Added": total_additions,
        "Removed": total_deletions,
        "Updated": total_updates
    }

def generate_chart(stats):
    """Generate a lifetime GitHub contribution bar chart."""
    formatted_values = [f"{value:,}" for value in stats.values()]
    values = list(stats.values())
    categories = list(stats.keys())

    #fig, ax = plt.subplots(figsize=(8, 5), facecolor="black")
    fig, ax = plt.subplots(figsize=(8, 5))
    #ax.set_facecolor("black")  # Black background
    
    # Color-blind-friendly colors
    #colors = ["#E69F00", "#56B4E9", "#009E73"]  # Orange, Blue, Green
    #colors = ["#4C72B0", "#5A89C9", "#6DAEDB"]  # Darker to lighter blue
    colors = ["#1F77B4", "#2CA02C", "#17BECF"]  # Blue, Green, Cyan
    
    # Generate horizontal bar positions
    y_pos = np.arange(len(categories))
    
    # Create horizontal bars
    bars = ax.barh(y_pos, values, color=colors, alpha=0.9, edgecolor="black", linewidth=1.5, height=0.5)
    
    # Annotate bars with values in white
    for bar, label in zip(bars, formatted_values):
        width = bar.get_width()
        ax.text(width + max(values) * 0.02, bar.get_y() + bar.get_height()/2, label, 
                va="center", fontsize=12, fontweight="bold", color="black")
    
    # Customize labels in white for better contrast
    ax.set_yticks(y_pos)
    ax.set_yticklabels(categories, fontsize=14, fontweight="bold", color="black")
    ax.set_xlabel("Total Lines of Code", fontsize=14, fontweight="bold", color="black", labelpad=15)
    ax.set_title("Lifetime GitHub Code Contributions", fontsize=16, fontweight="black", color="white", pad=20)
    
    # Remove axis lines for a sleek look
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["left"].set_visible(False)
    ax.spines["bottom"].set_visible(False)

    # Remove x-ticks for a cleaner look
    ax.xaxis.set_ticks([])

    # Save the PNG file
    plt.savefig("github_code_metrics.png", dpi=300, bbox_inches="tight", transparent=True)
    print("Graph saved as github_code_metrics.png")

if __name__ == "__main__":
    print("Fetching GitHub repositories...")
    repositories = fetch_repositories()
    
    if repositories:
        print("Fetching lifetime stats for all repositories...")
        processed_stats = process_stats(repositories)
        print("Generating lifetime chart...")
        generate_chart(processed_stats)
        print("Done! Check github_code_metrics.png.")
