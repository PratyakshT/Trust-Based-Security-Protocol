import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt

data = {
    "Interactions": [
        "8000", "8000", "8000", "8000",
        "12000", "12000", "12000", "12000",
        "15000", "15000", "15000", "15000"
    ],
    "Metric": [
        "Accuracy", "Precision", "Recall", "F1 Score",
        "Accuracy", "Precision", "Recall", "F1 Score",
        "Accuracy", "Precision", "Recall", "F1 Score"
    ],
    "Value": [
        0.9433, 0.9571, 0.9483, 0.9526,
        0.9458, 0.9577, 0.9449, 0.9512,
        0.9330, 0.9462, 0.9421, 0.9441
    ]
}

df = pd.DataFrame(data)

plt.figure(figsize=(9, 5))

ax = sns.barplot(
    data=df,
    x="Interactions",
    y="Value",
    hue="Metric",
    palette=[
    "#1F77B4",  # Blue
    "#FF7F0E",  # Orange
    "#2CA02C",  # Green
    "#D62728"   # Red
]
)

for container in ax.containers:
    ax.bar_label(container, fmt="%.4f", fontsize=10)

plt.ylabel("Score",fontsize=15)
plt.xlabel("Number of Interactions",fontsize=15)
plt.ylim(0.9, 1)
plt.xticks(fontsize=13)
plt.yticks(fontsize=13)

plt.title("Performance Metrics vs Number of Interactions")

plt.legend(
    title="Metric",
    bbox_to_anchor=(1.02, 1),
    loc="upper left"
)

plt.tight_layout()

plt.savefig("metrics.png", dpi=300, bbox_inches="tight")
plt.show()