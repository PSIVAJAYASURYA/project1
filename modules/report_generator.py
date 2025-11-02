import os
import json
from datetime import datetime

class ReportGenerator:
    def __init__(self, output_dir="output"):
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)

    def generate_report(self):
        """Collects all chart files from output folder and creates a JSON report."""
        try:
            charts = [f for f in os.listdir(self.output_dir)
                      if f.lower().endswith(('.png', '.jpg', '.jpeg'))]

            report_data = {
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "total_charts": len(charts),
                "charts": charts
            }

            report_name = f"report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            report_path = os.path.join(self.output_dir, report_name)

            with open(report_path, "w") as f:
                json.dump(report_data, f, indent=4)

            print(f"✅ Report generated: {report_path}")
            return report_path

        except Exception as e:
            print(f"❌ Report generation failed: {e}")
            return None
