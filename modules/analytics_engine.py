import os
import time
import matplotlib.pyplot as plt
import pandas as pd
from modules.logger import AppLogger


class AnalyticsEngine:
    def __init__(self):
        self.logger = AppLogger("logs/error_log.txt")

    # ============================================================
    # 1️⃣ Summarize Dataset (for reporting)
    # ============================================================
    def summarize(self, df):
        """Return dataset summary with row/column count and stats."""
        try:
            summary = {
                "rows": int(len(df)),
                "columns": int(len(df.columns)),
                "missing_values": df.isnull().sum().to_dict(),
                "numeric_summary": df.describe(include="all").to_dict()
            }
            self.logger.log_info("AnalyticsEngine.summarize", f"Summary generated for {len(df)} rows.")
            return summary
        except Exception as e:
            self.logger.log_error("AnalyticsEngine.summarize", str(e))
            return {}

    # ============================================================
    # 2️⃣ Suggest Suitable Chart Types
    # ============================================================
    def suggest_charts(self, analysis_info, minimum=6):
        """Suggest visualization specs based on column types."""
        try:
            specs = []
            cols = list(analysis_info.keys())

            for col in cols:
                info = analysis_info[col]
                if info["kind"] == "numeric":
                    specs.append({"type": "hist", "cols": [col], "reason": "Numeric distribution"})
                    specs.append({"type": "box", "cols": [col], "reason": "Outliers/Spread"})
                elif info["kind"] == "categorical":
                    if info["unique"] <= 15:
                        specs.append({"type": "bar", "cols": [col], "reason": "Categorical counts"})
                    else:
                        specs.append({"type": "bar_top", "cols": [col], "reason": "Top categories"})
                elif info["kind"] == "datetime":
                    specs.append({"type": "line", "cols": [col], "reason": "Time trend"})

            # numeric correlations (scatter)
            numeric = [c for c, i in analysis_info.items() if i["kind"] == "numeric"]
            for i in range(len(numeric)):
                for j in range(i + 1, len(numeric)):
                    specs.append({"type": "scatter", "cols": [numeric[i], numeric[j]], "reason": "Correlation"})
                    if len(specs) > minimum:
                        break

            # ensure minimum
            while len(specs) < minimum and numeric:
                specs.append({"type": "hist", "cols": [numeric[0]], "reason": "Auto-added"})

            # remove duplicates
            seen, final = set(), []
            for s in specs:
                key = (s["type"], tuple(s["cols"]))
                if key not in seen:
                    seen.add(key)
                    final.append(s)
            return final
        except Exception as e:
            self.logger.log_error("AnalyticsEngine.suggest_charts", str(e))
            return []

    # ============================================================
    # 3️⃣ Generate & Save Charts
    # ============================================================
    def generate_and_save_charts(self, df, analysis_info):
        """Generate visualizations from suggestions and save images."""
        try:
            timestamp = time.strftime("%Y%m%d_%H%M%S")
            output_dir = os.path.join("output", f"analytical_{timestamp}")
            os.makedirs(output_dir, exist_ok=True)

            suggestions = self.suggest_charts(analysis_info)
            saved_paths = []

            for s in suggestions:
                chart_type = s["type"]
                cols = s["cols"]
                try:
                    fig, ax = plt.subplots(figsize=(6, 4))

                    if chart_type == "hist":
                        df[cols[0]].plot(kind="hist", ax=ax, bins=20)
                    elif chart_type == "box":
                        df[cols[0]].plot(kind="box", ax=ax)
                    elif chart_type in ["bar", "bar_top"]:
                        df[cols[0]].value_counts().head(10).plot(kind="bar", ax=ax)
                    elif chart_type == "scatter" and len(cols) == 2:
                        df.plot(kind="scatter", x=cols[0], y=cols[1], ax=ax)
                    elif chart_type == "line" and len(cols) == 1:
                        num_cols = df.select_dtypes(include="number").columns
                        if len(num_cols) > 0:
                            df.plot(x=cols[0], y=num_cols[0], kind="line", ax=ax)

                    ax.set_title(f"{chart_type.title()} — {', '.join(cols)}")
                    plt.tight_layout()

                    save_path = os.path.join(output_dir, f"{chart_type}_{'_'.join(cols)}.png")
                    plt.savefig(save_path)
                    plt.close(fig)

                    saved_paths.append(save_path)
                    self.logger.log_info("Chart Saved", save_path)

                except Exception as e:
                    self.logger.log_error("AnalyticsEngine.generate_chart", f"{chart_type} | {cols} | {e}")

            # ✅ Log saved charts to engine_suggestions.txt
            with open("logs/engine_suggestions.txt", "a", encoding="utf-8") as logf:
                logf.write(f"\n\n=== Analytical Engine — {timestamp} ===\n")
                for p in saved_paths:
                    logf.write(f"✅ Saved: {p}\n")

            return saved_paths

        except Exception as e:
            self.logger.log_error("AnalyticsEngine.generate_and_save_charts", str(e))
            return []
