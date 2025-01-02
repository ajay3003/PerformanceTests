import json
import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
import os
import logging

# File paths with clean path handling
base_dir = os.environ.get("AGENT_BUILDDIRECTORY", ".").strip('"')
performance_test_name = os.environ.get("PerformanceTestName", "DefaultTestName").strip('"')

# Define the base directory and test name
test_dir = os.path.join(base_dir, f"{performance_test_name}Test")

# Update file paths based on new locations
baseline_file = os.path.join(test_dir, "json", "baseline.json")
latest_file = os.path.join(test_dir, "charts", "Dashboard", "statistics.json")

# Path for Chart report
charts_dir = os.path.join(test_dir, "charts")

# Print paths for verification
print(f"Baseline File: {baseline_file}")
print(f"Latest Results File: {latest_file}")


# Create charts directory
try:
    os.makedirs(charts_dir, exist_ok=True)
    print(f"Charts directory created/verified at: {charts_dir}")
except Exception as e:
    print(f"Failed to create charts directory: {e}")
    raise

# Set up log file path and initialize logging
log_file = os.path.join(charts_dir, 'compare_reports.log')

# Initialize logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler()
    ]
)

def load_json(file_path):
    """Load JSON data from a file."""
    try:
        with open(file_path, 'r') as file:
            return json.load(file)
    except FileNotFoundError:
        logging.error(f"File not found: {file_path}")
        raise FileNotFoundError(f"File not found: {file_path}")
    except json.JSONDecodeError as e:
        logging.error(f"Error decoding JSON in file {file_path}: {e}")
        raise ValueError(f"Error decoding JSON in file {file_path}: {e}")

def prepare_comparison_data(baseline, latest):
    """Prepare comparison data for visualization."""
    data = []
    baseline_metrics = {metric["label"]: metric for metric in baseline.get("metrics", [])}
    latest_metrics = {metric["label"]: metric for metric in latest.get("metrics", [])}

    for label, baseline_metric in baseline_metrics.items():
        if label in latest_metrics:
            latest_metric = latest_metrics[label]
            data.append({
                "Metric": "Average Response Time (ms)",
                "Label": label,
                "Baseline": baseline_metric["averageResponseTime"],
                "Latest": latest_metric["averageResponseTime"]
            })
            data.append({
                "Metric": "Error Rate (%)",
                "Label": label,
                "Baseline": baseline_metric["errorRate"] * 100,
                "Latest": latest_metric["errorRate"] * 100
            })
            data.append({
                "Metric": "Throughput (req/sec)",
                "Label": label,
                "Baseline": baseline_metric["throughput"],
                "Latest": latest_metric["throughput"]
            })
    return pd.DataFrame(data)

def plot_comparison(df):
    """Plot comparison data using bar plots."""
    sns.set(style="whitegrid")
    metrics = df["Metric"].unique()

    for metric in metrics:
        plt.figure(figsize=(12, 6))
        metric_data = df[df["Metric"] == metric]
        melted_data = metric_data.melt(
            id_vars=["Metric", "Label"], var_name="Type", value_name="Value"
        )
        sns.barplot(data=melted_data, x="Label", y="Value", hue="Type", palette="viridis")
        plt.title(f"Comparison of {metric}", fontsize=16)
        plt.ylabel(metric, fontsize=12)
        plt.xlabel("Service", fontsize=12)
        plt.legend(title="Report Type")
        plt.xticks(rotation=45)
        plt.tight_layout()
        
        chart_file = os.path.join(charts_dir, f"{metric.replace(' ', '_').lower()}.png")
        plt.savefig(chart_file)
        plt.close()
        logging.info(f"Generated chart: {chart_file}")

def main():
    """Main function for processing and visualization."""
    logging.info("Starting performance comparison script")
    logging.info(f"Base directory: {base_dir}")
    logging.info(f"Performance test name: {performance_test_name}")
    logging.info(f"Test directory: {test_dir}")
    logging.info(f"Charts directory: {charts_dir}")
    logging.info(f"Baseline file: {baseline_file}")
    logging.info(f"Latest file: {latest_file}")

    try:
        logging.info("Loading baseline and latest data")
        baseline_data = load_json(baseline_file)
        latest_data = load_json(latest_file)

        logging.info("Preparing comparison data")
        comparison_data = prepare_comparison_data(baseline_data, latest_data)

        if not comparison_data.empty:
            logging.info("Generating comparison plots")
            plot_comparison(comparison_data)
            logging.info(f"Charts have been generated in: {charts_dir}")
        else:
            logging.warning("No data available for comparison")
    except Exception as e:
        logging.error(f"An error occurred: {e}")
        raise

if __name__ == "__main__":
    main()
