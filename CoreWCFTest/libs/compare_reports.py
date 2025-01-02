import json
import os

# File paths
base_dir = os.environ.get("AGENT_BUILDDIRECTORY", ".").strip('"')
performance_test_name = os.environ.get("PerformanceTestName", "DefaultTestName").strip('"')

# Create clean file paths using os.path.join
test_dir = os.path.join(base_dir, f"{performance_test_name}Test")
# Update file paths based on new locations
baseline_file = os.path.join(test_dir, "json", "baseline.json")
latest_file = os.path.join(test_dir, "charts", "Dashboard", "statistics.json")

# Thresholds for comparison
response_time_threshold = 10  # in milliseconds
error_rate_threshold = 0.01   # 1%
throughput_threshold = 5      # requests per second

def load_json(file_path):
    """Load JSON data from a file."""
    try:
        with open(file_path, 'r') as file:
            return json.load(file)
    except FileNotFoundError:
        raise FileNotFoundError(f"File not found: {file_path}")
    except json.JSONDecodeError as e:
        raise ValueError(f"Error decoding JSON in file {file_path}: {e}")

def compare_metrics(baseline, latest):
    """Compare baseline and latest metrics and return any issues."""
    issues = []
    baseline_metrics = {metric["label"]: metric for metric in baseline.get("metrics", [])}
    latest_metrics = {metric["label"]: metric for metric in latest.get("metrics", [])}

    for label, baseline_metric in baseline_metrics.items():
        if label in latest_metrics:
            latest_metric = latest_metrics[label]

            # Check response time
            response_time_diff = abs(latest_metric["averageResponseTime"] - baseline_metric["averageResponseTime"])
            if response_time_diff > response_time_threshold:
                issues.append(
                    f"{label}: Response time deviation too high ({latest_metric['averageResponseTime']} ms vs {baseline_metric['averageResponseTime']} ms)."
                )

            # Check error rate
            error_rate_diff = abs(latest_metric["errorRate"] - baseline_metric["errorRate"])
            if error_rate_diff > error_rate_threshold:
                issues.append(
                    f"{label}: Error rate deviation too high ({latest_metric['errorRate']} vs {baseline_metric['errorRate']})."
                )

            # Check throughput
            throughput_diff = abs(latest_metric["throughput"] - baseline_metric["throughput"])
            if throughput_diff > throughput_threshold:
                issues.append(
                    f"{label}: Throughput deviation too high ({latest_metric['throughput']} rps vs {baseline_metric['throughput']} rps)."
                )
        else:
            issues.append(f"{label}: Missing in latest results.")

    return issues

def main():
    """Main script execution."""
    print(f"Base directory: {base_dir}")
    print(f"Performance test name: {performance_test_name}")
    print(f"Test directory: {test_dir}")
    print(f"Baseline file: {baseline_file}")
    print(f"Latest file: {latest_file}")

    try:
        # Load data
        baseline_data = load_json(baseline_file)
        latest_data = load_json(latest_file)

        # Compare data
        comparison_issues = compare_metrics(baseline_data, latest_data)

        # Output results
        if comparison_issues:
            print("Comparison Issues Found:")
            for issue in comparison_issues:
                print(f" - {issue}")
        else:
            print("All metrics are within acceptable thresholds.")
    except Exception as e:
        print(f"An error occurred during execution: {e}")

if __name__ == "__main__":
    main()
