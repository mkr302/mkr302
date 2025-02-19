import os
import requests
import time
import datetime
import matplotlib.pyplot as plt
import numpy as np

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
                total_updates += min(additions, deletions)
                total_deletions += deletions

                # Current year stats
                if week_year == current_year:
                    current_year_add += additions
                    current_year_upd += min(additions, deletions)
                    current_year_del += deletions

    return {
        "lifetime": {
            "Lines Added": total_additions,
            "Lines Updated": total_updates,
            "Lines Removed": total_deletions
        },
        "current_year": {
            "Lines Added": current_year_add,
            "Lines Updated": current_year_upd,
            "Lines Removed": current_year_del
        }
    }

def generate_horizontal_bar_charts(stats):
    """Generate two horizontal bar charts for lifetime and current year contributions with auto-scaling."""
    
    # Define reordered data (Reversed Order for Correct Display)
    categories = ["Lines Added", "Lines Updated", "Lines Removed"]
    categories.reverse()  # Reverse the order so "Lines Added" appears at the top

    #lifetime_values = [stats["lifetime"][cat] for cat in reversed(categories)]
    #current_values = [stats["current_year"][cat] for cat in reversed(categories)]
    lifetime_values = [stats["lifetime"][cat] for cat in categories]
    current_values = [stats["current_year"][cat] for cat in categories]

    # Define colors (monochromatic shades of blue)
    colors = ["#4A90E2", "#357ABD", "#2C5DAA"]  

    fig, axes = plt.subplots(1, 2, figsize=(14, 5), facecolor="#0d1117")  # Increased figure size for spacing
    fig.suptitle("Code Contribution Summary", fontsize=18, fontweight="bold", color="white")

    # Get max value across both graphs & set x-axis limit dynamically
    max_value = max(max(lifetime_values), max(current_values))
    x_limit = max_value * 1.10  # Add a 10% margin

    # Function to add labels on bars
    def add_labels(ax, values):
        for index, value in enumerate(values):
            ax.text(value + (x_limit * 0.02), index, f"{value:,}",  # Adjust label position dynamically
                    fontsize=12, fontweight="bold", color="white", va="center")

    # Lifetime Contributions Chart
    axes[0].barh(categories, lifetime_values, color=colors, alpha=0.9, height=0.4)  # Reduced bar width
    axes[0].set_title("Lifetime Contributions", fontsize=14, fontweight="bold", color="white", pad=40)  # Increased spacing
    #axes[0].set_xlabel("Total Lines of Code", fontsize=12, color="white")
    axes[0].set_yticks(np.arange(len(categories)))
    axes[0].set_yticklabels(categories, fontsize=12, color="white")
    axes[0].set_facecolor("#0d1117")
    axes[0].set_xlim([0, x_limit])  # Set dynamic x-axis limit

    # Remove y tick marks
    axes[0].tick_params(axis="y", left=False)  
    # Remove x ticks and grid lines
    axes[0].tick_params(axis="x", colors="white", bottom=False, labelbottom=False)
    axes[0].grid(False)

    # Remove bounding box
    for spine in axes[0].spines.values():
        spine.set_visible(False)
    
    # Add labels on top of bars
    add_labels(axes[0], lifetime_values)

    # Current Year Contributions Chart
    axes[1].barh(categories, current_values, color=colors, alpha=0.9, height=0.4)  # Reduced bar width
    axes[1].set_title(f"Contributions in {datetime.datetime.now().year}", fontsize=14, fontweight="bold", color="white", pad=40)  # Increased spacing
    #axes[1].set_xlabel("Total Lines of Code", fontsize=12, color="white")
    axes[1].set_xlim([0, x_limit])  # **Set dynamic x-axis limit**

    # Remove y labels and ticks in second graph
    axes[1].set_yticks(np.arange(len(categories)))
    axes[1].set_yticklabels([""] * len(categories))  # Remove labels
    axes[1].tick_params(axis="y", left=False)  # Remove tick marks
    
    axes[1].set_facecolor("#0d1117")

    # Remove x ticks and grid lines
    axes[1].tick_params(axis="x", colors="white", bottom=False, labelbottom=False)
    axes[1].grid(False)

    # Remove bounding box
    for spine in axes[1].spines.values():
        spine.set_visible(False)

    # Add labels on top of bars
    add_labels(axes[1], current_values)

    # Adjust layout for better spacing
    plt.tight_layout(pad=4.5)  # Increase spacing between plots

    # Save the PNG file
    plt.savefig("github_code_metrics.png", dpi=300, bbox_inches="tight", facecolor="#0d1117")
    print("Graph saved as github_code_metrics.png with auto-scaling.")

if __name__ == "__main__":
    print("Fetching GitHub repositories...")
    repositories = fetch_repositories()
    
    if repositories:
        print("Fetching lifetime and current year stats for all repositories...")
        processed_stats = process_stats(repositories)
        print("Generating horizontal bar charts with auto-scaling...")
        generate_horizontal_bar_charts(processed_stats)
        print("Done! Check github_code_metrics.png.")
