import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from scipy import stats

def break_line(): print("\n", "="*70, "\n")

def match_open_close_events(user_events):
    stack = []

    matched_pairs = []

    orphaned_closes = 0

    for i, row in user_events.iterrows():
        if row["event"] == "opened":
            stack.append({
                "open_timestamp" : row["timestamp"],
                "open_type" : row["open_type"]
            })
        
        elif row["event"] == "closed":
            if stack:
                open_event = stack.pop()
                duration_ms = row["timestamp"] - open_event["open_timestamp"]
                matched_pairs.append({
                    "user_id" : row["user_id"],
                    "duration_minutes" : duration_ms / 60_000,
                    "open_type" : open_event["open_type"]
                })
            else:
                orphaned_closes += 1
    
    return matched_pairs, len(stack), orphaned_closes


# load data into data frame 
df = pd.read_csv("toolwindow_data.csv")



break_line()

# Display basic overview of data 
print("Data overview")
print(f"Rows: {len(df)}\n")

print("First 10 rows")
print(df.head())

print("Data types:")
print(df.dtypes)


# sort by user and timestamp
df = df.sort_values(["user_id", "timestamp"]).reset_index(drop=True)



break_line()

# process all users
all_pairs = []
total_orphaned_opens = 0
total_orphaned_closes = 0

processed = 0
n_users = len(df["user_id"].unique())

for user_id in df["user_id"].unique():
    user_events = df[df["user_id"] == user_id]

    pairs, orphan_opens, orphan_closes = match_open_close_events(user_events)

    all_pairs.extend(pairs)

    total_orphaned_opens += orphan_opens

    total_orphaned_closes += orphan_closes

    processed += 1

    print(f"Processed: {float((processed/n_users)):.3f}")



break_line()

sessions = pd.DataFrame(all_pairs)

print(f"Matched sessions: {len(sessions)} ")
print(f"Orphaned opens: {total_orphaned_opens}")
print(f"Orphaned closes: {total_orphaned_closes}")

# filter outliers (aka session time > 24 hours)
sessions_clean = sessions[sessions["duration_minutes"] <= 1440].copy()

outliers_count = len(sessions) - len(sessions_clean)

print(f"Number of removed outliers (>24 hours): {outliers_count}")

break_line()

manual = sessions_clean[sessions_clean["open_type"] == "manual"]["duration_minutes"]

auto = sessions_clean[sessions_clean["open_type"] == "auto"]["duration_minutes"]

# mean, madians, std dev, quartiles 
print(f"Manual opens, n={len(manual)}:")
print(f"Mean: {manual.mean():.3f} min")
print(f"Meadian(Q2): {manual.median():.3f} min")
print(f"Std dev: {manual.std():.3f} min")
print(f"Q1: {manual.quantile(0.25):.3f} min")
print(f"Q3: {manual.quantile(0.75):3f} min")

print(f"\nAuto opens, n={len(auto)}:")
print(f"Mean: {auto.mean():.3f} min")
print(f"Meadian(Q2): {auto.median():.3f} min")
print(f"Std dev: {auto.std():.3f} min")
print(f"Q1: {auto.quantile(0.25):.3f} min")
print(f"Q3: {auto.quantile(0.75):.3f} min")



break_line()
# statiscal testing

# mann-whitney u test
u_stat, p_value = stats.mannwhitneyu(manual, auto, alternative="two-sided")

print("Mann-Whitney u test:")
print(f"Test stat: {u_stat:.4f}")
print(f"p-value: {p_value:.6f}")

if p_value < 0.001: print("  Result: HIGHLY significant (p < 0.001)")
elif p_value < 0.01: print("  Result: VERY significant (p < 0.01)")
elif p_value < 0.05: print("  Result: significant (p < 0.05)")
else: print("  Result: NOT significant (p >= 0.05)")



break_line()
# cohen"s d effe
pooled_std = np.sqrt(((len(manual)-1)*manual.std()**2 + (len(auto)-1)*auto.std()**2) / (len(manual) + len(auto) - 2))

cohens_d = (manual.mean() - auto.mean()) / pooled_std

effects = {0.2: "SMALL", 0.5: "MEDIUM", 0.8: "LARGE"}

# default effect
effect = "NEGLIGIBLE"

for threshold, eff in sorted(effects.items()):
    if abs(cohens_d) >= threshold:
        effect = eff 

print(f"Cohen's d, effect size:")
print(f"d = {cohens_d:.3f}")
print(f"Interpretation: {effect} effect")



break_line()

print("Bootstrap 95 %\ confidence interval:")

np.random.seed(42)

median_diffs = []

for i in range(10000):
    manual_sample = np.random.choice(manual, size=len(manual), replace=True)

    auto_sample = np.random.choice(auto, size=len(auto), replace=True)

    median_diffs.append(np.median(manual_sample) - np.median(auto_sample))

ci_lower = np.percentile(median_diffs, 2.5)
ci_upper = np.percentile(median_diffs, 97.5)

median_diff = manual.median() - auto.median()

print(f"Median diff: {median_diff:.3f} min")
print(f"(95 % CI: [{ci_lower:.3f}, {ci_upper:.3f}] min")

if ci_lower > 0: print("Manual sessions are LONGER")
elif ci_upper < 0: print("Manual sessions are SHORTER")



break_line()
# visualization 
sns.set_style("whitegrid")

plt.rcParams["figure.figsize"] = (12, 8)

fig, axes = plt.subplots(2, 2, figsize=(15, 12))

# histograms 
print("Computing Histograms ...")

ax1 = axes[0, 0]

bins = np.linspace(0, min(30, sessions_clean["duration_minutes"].quantile(0.95)), 50)

ax1.hist(manual, bins=bins, alpha=0.6, label="Manual", color="blue", density=True)

ax1.hist(auto, bins=bins, alpha=0.6, label="Auto", color="coral", density=True)

ax1.set_xlabel("Duration (min)", fontsize=11)

ax1.set_ylabel("Density", fontsize=11)

ax1.set_title("Distribution of Session Durations", fontsize=12, fontweight="bold")

ax1.legend(fontsize=10)

ax1.grid(True, alpha=0.3)



break_line()
#  Box plots 
print("Computing Box plots ...")

ax2 = axes[0, 1]

bp = ax2.boxplot([manual, auto], labels=["Manual", "Auto"], patch_artist=True, widths=0.6)

bp["boxes"][0].set_facecolor("blue")

bp["boxes"][1].set_facecolor("coral")

for element in ["whiskers", "fliers", "means", "medians", "caps"]:
    plt.setp(bp[element], color="black", linewidth=1.5)

ax2.set_ylabel("Duration (min)", fontsize=11)

ax2.set_title("Box Plot Comparison", fontsize=12, fontweight="bold")

ax2.grid(True, alpha=0.3, axis="y")



break_line()
# Cumulative distribution 
print("Computing cumulative distributions ...")

ax3 = axes[1, 0]

manual_sorted = np.sort(manual)

auto_sorted = np.sort(auto)

ax3.plot(manual_sorted, np.linspace(0, 1, len(manual_sorted)), label="Manual", linewidth=2, color="blue")

ax3.plot(auto_sorted, np.linspace(0, 1, len(auto_sorted)), label="Auto", linewidth=2, color="coral")

ax3.set_xlabel("Duration (min)", fontsize=11)

ax3.set_ylabel("Cumulative Probability", fontsize=11)

ax3.set_title("Cumulative Distribution Functions CDFs", fontsize=12, fontweight="bold")

ax3.legend(fontsize=10)

ax3.grid(True, alpha=0.3)

ax3.set_xlim(0, 30)



break_line()
# Summary stats
print("Sumarizing... ")

ax4 = axes[1, 1]

categories = ["mean", "median", "75th percentile"]

manual_stats = [manual.mean(), manual.median(), manual.quantile(0.75)]

auto_stats = [auto.mean(), auto.median(), auto.quantile(0.75)]

x = np.arange(len(categories))

width = 0.35

ax4.bar(x - width/2, manual_stats, width, label="Manual", color="blue", alpha=0.8)

ax4.bar(x + width/2, auto_stats, width, label="Auto", color="coral", alpha=0.8)

ax4.set_ylabel("Duration (min)", fontsize=11)

ax4.set_title("Key Statistical Comparison", fontsize=12, fontweight="bold")

ax4.set_xticks(x)

ax4.set_xticklabels(categories)

ax4.legend(fontsize=10)

ax4.grid(True, alpha=0.3, axis="y")



plt.tight_layout()
plt.savefig("toolwindow_analysis.png", dpi=300, bbox_inches = "tight")



break_line()
# Violin plot
print("Computing violin plot...")

fig2, ax = plt.subplots(figsize=(10, 6))

parts = ax.violinplot([manual[manual <= 30], auto[auto <= 30]], positions=[1, 2], showmeans=True, showmedians=True, widths=0.7)

for pc in parts['bodies']:
    pc.set_facecolor('lightblue')
    pc.set_alpha(0.7)

ax.set_xticks([1, 2])

ax.set_xticklabels(['Manual', 'Auto'], fontsize=12)

ax.set_ylabel('Duration (min)', fontsize=12)

ax.set_title('Violin Plot: Distribution Comparison (capped at 30 min)', fontsize=13, fontweight='bold')

ax.grid(True, alpha=0.3, axis='y')

plt.tight_layout()

plt.savefig('toolwindow_violin.png', dpi=300, bbox_inches='tight')

# Save processed data
sessions_clean.to_csv('matched_sessions.csv', index=False)