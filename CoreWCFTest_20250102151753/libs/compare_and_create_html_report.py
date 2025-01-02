import json
import os
from datetime import datetime

# File paths
base_dir = os.environ.get("AGENT_BUILDDIRECTORY", ".").strip('"')
performance_test_name = os.environ.get("PerformanceTestName", "DefaultTestName").strip('"')

# Define the base directory and test name
test_dir = os.path.join(base_dir, f"{performance_test_name}Test")

# Update file paths based on new locations
baseline_file = os.path.join(test_dir, "json", "baseline.json")
latest_file = os.path.join(test_dir, "charts", "Dashboard", "statistics.json")

# Path for HTML report
html_report = os.path.join(test_dir, "comparison_report.html")

# Print paths for verification
print(f"Baseline File: {baseline_file}")
print(f"Latest Results File: {latest_file}")
print(f"HTML Report: {html_report}")

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

def get_comparison_class(baseline_value, latest_value, threshold, lower_is_better=True):
    """Determine CSS class based on metric comparison."""
    diff = latest_value - baseline_value
    if abs(diff) <= threshold:
        return "neutral"
    if lower_is_better:
        return "better" if diff < 0 else "worse"
    return "better" if diff > 0 else "worse"

def generate_html_report(baseline_data, latest_data, comparison_issues):
    """Generate HTML comparison report with styling."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    html_content = [
        "<!DOCTYPE html>",
        "<html>",
        "<head>",
        "<style>",
        "body { font-family: Arial, sans-serif; margin: 20px; }",
        ".better { color: green; background-color: #e6ffe6; }",
        ".worse { color: red; background-color: #ffe6e6; }",
        ".neutral { color: black; background-color: #f2f2f2; }",
        "table { border-collapse: collapse; width: 100%; margin-bottom: 20px; }",
        "th, td { border: 1px solid #ddd; padding: 12px; text-align: left; }",
        "th { background-color: #4CAF50; color: white; }",
        ".issues { margin-top: 20px; padding: 10px; border: 1px solid #ddd; }",
        ".timestamp { color: #666; font-size: 0.9em; margin-bottom: 20px; }",
        "</style>",
        "</head>",
        "<body>",
        "<h1>Performance Comparison Report</h1>",
        f'<div class="timestamp">Generated on: {timestamp}</div>',
        "<h2>Metrics Comparison</h2>",
        "<table>",
        "<tr>",
        "<th>Label</th>",
        "<th>Metric</th>",
        "<th>Baseline</th>",
        "<th>Latest</th>",
        "<th>Difference</th>",
        "</tr>"
    ]

    baseline_metrics = {metric["label"]: metric for metric in baseline_data.get("metrics", [])}
    latest_metrics = {metric["label"]: metric for metric in latest_data.get("metrics", [])}

    metrics_to_compare = [
        ("Response Time (ms)", "averageResponseTime", response_time_threshold, True),
        ("Error Rate", "errorRate", error_rate_threshold, True),
        ("Throughput (rps)", "throughput", throughput_threshold, False)
    ]

    for label, baseline_metric in baseline_metrics.items():
        if label in latest_metrics:
            latest_metric = latest_metrics[label]
            
            for metric_name, metric_key, threshold, lower_is_better in metrics_to_compare:
                baseline_value = baseline_metric[metric_key]
                latest_value = latest_metric[metric_key]
                diff = latest_value - baseline_value
                css_class = get_comparison_class(baseline_value, latest_value, threshold, lower_is_better)
                
                html_content.extend([
                    f'<tr class="{css_class}">',
                    f"<td>{label}</td>",
                    f"<td>{metric_name}</td>",
                    f"<td>{baseline_value:.2f}</td>",
                    f"<td>{latest_value:.2f}</td>",
                    f"<td>{diff:+.2f}</td>",
                    "</tr>"
                ])

    html_content.append("</table>")

    if comparison_issues:
        html_content.extend([
            '<div class="issues">',
            "<h2>Identified Issues</h2>",
            "<ul>"
        ])
        for issue in comparison_issues:
            html_content.append(f"<li>{issue}</li>")
        html_content.extend(["</ul>", "</div>"])

    html_content.extend(["</body>", "</html>"])

    with open(html_report, 'w') as f:
        f.write("\n".join(html_content))

def compare_metrics(baseline, latest):
    """Compare baseline and latest metrics and return any issues."""
    issues = []
    baseline_metrics = {metric["label"]: metric for metric in baseline.get("metrics", [])}
    latest_metrics = {metric["label"]: metric for metric in latest.get("metrics", [])}

    for label, baseline_metric in baseline_metrics.items():
        if label in latest_metrics:
            latest_metric = latest_metrics[label]

            response_time_diff = abs(latest_metric["averageResponseTime"] - baseline_metric["averageResponseTime"])
            if response_time_diff > response_time_threshold:
                issues.append(
                    f"{label}: Response time deviation too high ({latest_metric['averageResponseTime']} ms vs {baseline_metric['averageResponseTime']} ms)."
                )

            error_rate_diff = abs(latest_metric["errorRate"] - baseline_metric["errorRate"])
            if error_rate_diff > error_rate_threshold:
                issues.append(
                    f"{label}: Error rate deviation too high ({latest_metric['errorRate']} vs {baseline_metric['errorRate']})."
                )

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
        baseline_data = load_json(baseline_file)
        latest_data = load_json(latest_file)
        comparison_issues = compare_metrics(baseline_data, latest_data)
        generate_html_report(baseline_data, latest_data, comparison_issues)
        print(f"HTML report generated: {html_report}")

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
