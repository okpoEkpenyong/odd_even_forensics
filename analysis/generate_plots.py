import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path

# Load aggregated data
data_path = Path("analysis/results/cell_summary.csv")
if not data_path.exists():
    raise FileNotFoundError("Run aggregate_results.py first.")

df = pd.read_csv(data_path)

# Filter for the most recent/clean experiments (120B focus)
plot_df = df[df['model'].str.contains('120B')]

def save_plot(name):
    plt.tight_layout()
    plt.savefig(f"analysis/results/{name}.png", dpi=300)
    print(f"Saved {name}.png")
    plt.close()

# Plot 1: Hacking Rate across Key Frames
plt.figure(figsize=(10, 6))
frames_of_interest = ['step0_bare_env', 'baseline', 'hierarchy_only_bare', 'persona_only', 'user_as_developer']
subset = plot_df[plot_df['frame'].isin(frames_of_interest)].sort_values('odd_rate_pct')

sns.barplot(data=subset, x='frame', y='odd_rate_pct', palette='viridis')
plt.title("Hacking Rate by Frame (GPT-OSS-120B)")
plt.ylabel("Hacking Rate (%)")
plt.xticks(rotation=45)
save_plot("hacking_by_frame")

# Plot 2: Scaling Trend (20B vs 120B in Persona Frame)
plt.figure(figsize=(8, 6))
scaling_df = df[df['frame'] == 'persona_only']
sns.barplot(data=scaling_df, x='model', y='odd_rate_pct', palette='magma')
plt.title("Scaling of Reward Hacking (Persona Frame)")
plt.ylabel("Hacking Rate (%)")
save_plot("scaling_trend")

# Plot 3: Instrument Validation (Rigged vs Baseline)
plt.figure(figsize=(8, 6))
val_df = df[df['frame'].isin(['honest_baseline', 'deceptive_rigged'])]
sns.barplot(data=val_df, x='frame', y='odd_rate_pct', hue='model')
plt.title("Positive Control: Rigged Deception vs Baseline")
plt.ylabel("Hacking Rate (%)")
save_plot("positive_control_validation")