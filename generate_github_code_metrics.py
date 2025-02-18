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
    year_additions, year_deletions, year_updates = 0, 0, 0
    current_year_add, current_year_del, current_year_upd = 0, 0, 0
    prev_year_add, prev_year_del, prev_year_upd = 0, 0, 0
    
    current_year = datetime.datetime.now().year
    previous_year = current_year - 1

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
                elif week_year == previous_year:
                    prev_year_add += additions
                    prev_year_del += deletions
                    prev_year_upd += min(additions, deletions)

    return {
        "lifetime": {
            "Added": total_additions,
            "Removed": total_deletions,
            "Updated": total_updates
        },
        "yearly": {
            "Previous Year": {
                "Added": prev_year_add,
                "Removed": prev_year_del,
                "Updated": prev_year_upd
            },
            "Current Year": {
                "Added": current_year_add,
                "Removed": current_year_del,
                "Updated": current_year_upd
            }
        }
    }

def generate_charts(stats):
    """Generate two side-by-side GitHub contribution bar charts."""
    categories = list(stats["lifetime"].keys())
    lifetime_values = list(stats["lifetime"].values())

    yearly_categories = list(stats["yearly"]["Current Year"].keys())
    prev_year_values = list(stats["yearly"]["Previous Year"].values())
    curr_year_values = list(stats["yearly"]["Current Year"].values())

    formatted_lifetime = [f"{value:,}" for value in lifetime_values]
    formatted_prev_year = [f"{value:,}" for value in prev_year_values]
    formatted_curr_year = [f"{value:,}" for value in curr_year_values]

    fig, axes = plt.subplots(1, 2, figsize=(18, 6), sharey=False, facecolor="black")  # Larger spacing
    #plt.subplots_adjust(wspace=1.0)  # Increase spacing between the two plots
    plt.subplots_adjust(left=0.05, right=0.95, wspace=0.4)  # Adjust spacing to fill screen width

    # Black background and white text
    for ax in axes:
        ax.set_facecolor("black")
        
    # Monochromatic color scheme transitioning from blue to green
    #colors = ["#E69F00", "#56B4E9", "#009E73"]  # Orange, Blue, Green
    colors = ["#4C72B0", "#5A89C9", "#6DAEDB"]  # Darker to lighter blue
    #colors = ["#1F77B4", "#2CA02C", "#17BECF"]  # Blue, Green, Cyan
    
    # Generate horizontal bar positions
    y_pos = np.arange(len(categories))

    # Left Chart: Lifetime Contributions
    bars1 = axes[0].barh(y_pos, lifetime_values, color=colors, alpha=0.9, edgecolor="white", linewidth=1.5, height=0.5)
    axes[0].set_title("Lifetime Contributions", fontsize=16, fontweight="bold", color="white")
    axes[0].set_xlabel("Total Lines of Code", fontsize=14, fontweight="bold", color="white", labelpad=15)
    axes[0].set_yticks(y_pos)
    axes[0].set_yticklabels(categories, fontsize=14, fontweight="bold", color="white")

    for bar, label in zip(bars1, formatted_lifetime):
        width = bar.get_width()
        #axes[0].text(width + max(lifetime_values) * 0.02, bar.get_y() + bar.get_height()/2, label, va="center", fontsize=12, fontweight="bold", color="white")
        axes[0].text(width + max(lifetime_values) * 0.02, bar.get_y(), label, va="center", fontsize=12, fontweight="bold", color="white")

    # Right Chart: Previous Year vs Current Year (Side-by-Side Bars)
    y_pos = np.arange(len(yearly_categories))
    bar_width = 0.4  # Width for side-by-side bars

    bars2 = axes[1].barh(y_pos - bar_width/2, prev_year_values, color="#1F77B4", alpha=0.9, edgecolor="white", linewidth=1.5, height=bar_width, label="Previous Year")
    bars3 = axes[1].barh(y_pos + bar_width/2, curr_year_values, color="#2CA02C", alpha=0.9, edgecolor="white", linewidth=1.5, height=bar_width, label="Current Year")

    axes[1].set_title(f"Previous vs Current Year Contributions", fontsize=16, fontweight="bold", color="white")
    axes[1].set_xlabel("Total Lines of Code", fontsize=14, fontweight="bold", color="white", labelpad=15)
    axes[1].set_yticks(y_pos)
    axes[1].set_yticklabels(yearly_categories, fontsize=14, fontweight="bold", color="white")

    """
    for bar, label in zip(bars2, formatted_prev_year):
        width = bar.get_width()
        axes[1].text(width + max(prev_year_values) * 0.02, bar.get_y(), label, va="center", fontsize=12, fontweight="bold", color="white")

    for bar, label in zip(bars3, formatted_curr_year):
        width = bar.get_width()
        axes[1].text(width + max(curr_year_values) * 0.02, bar.get_y(), label, va="center", fontsize=12, fontweight="bold", color="white")

    """
    #axes[1].legend(loc="lower right", fontsize=12, facecolor="black", edgecolor="white")


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
