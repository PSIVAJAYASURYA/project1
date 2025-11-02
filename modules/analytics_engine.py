from modules.logger import AppLogger

class AnalyticsEngine:
    def __init__(self):
        self.logger = AppLogger("logs/error_log.txt")

    def summarize(self, df):
        try:
            summary = {
                "rows": int(len(df)),
                "columns": int(len(df.columns)),
                "missing_values": df.isnull().sum().to_dict(),
                "numeric_summary": df.describe(include='all').to_dict()
            }
            return summary
        except Exception as e:
            self.logger.log_error("AnalyticsEngine.summarize", str(e))
            return {}

    def suggest_charts(self, analysis_info, minimum=6):
        """
        Return a prioritized list of chart specs. Ensure at least `minimum` specs.
        Spec: {'type': 'hist'/'box'/'bar'/'line_time'/'scatter'/'box_group', 'cols': [...], 'reason': str}
        """
        try:
            specs = []
            cols = list(analysis_info.keys())

            # Single-column suggestions
            for col in cols:
                info = analysis_info[col]
                if info['kind'] == 'numeric':
                    specs.append({'type':'hist', 'cols':[col], 'reason':'Numeric distribution'})
                    specs.append({'type':'box', 'cols':[col], 'reason':'Outliers/Spread'})
                elif info['kind'] == 'categorical':
                    if info['unique'] <= 15:
                        specs.append({'type':'bar', 'cols':[col], 'reason':'Categorical counts'})
                    else:
                        specs.append({'type':'bar_top', 'cols':[col], 'reason':'Top categories counts'})
                elif info['kind'] == 'datetime':
                    specs.append({'type':'line_time', 'cols':[col], 'reason':'Time series trend'})

            # Pairwise numeric suggestions (scatter)
            numeric = [c for c,i in analysis_info.items() if i['kind']=='numeric']
            count = 0
            for i in range(len(numeric)):
                for j in range(i+1, len(numeric)):
                    specs.append({'type':'scatter','cols':[numeric[i], numeric[j]], 'reason':'Correlation'})
                    count += 1
                    if count >= 3:
                        break
                if count >= 3:
                    break

            # numeric by categorical
            categorical = [c for c,i in analysis_info.items() if i['kind']=='categorical' and i['unique']<=20]
            if numeric and categorical:
                for num in numeric[:2]:
                    for cat in categorical[:2]:
                        specs.append({'type':'box_group','cols':[num, cat], 'reason':'Numeric by category'})

            # Ensure at least `minimum` specs by repeating or fallback
            idx = 0
            while len(specs) < minimum and idx < len(cols):
                col = cols[idx]
                specs.append({'type':'bar_top' if analysis_info[col]['kind']=='categorical' else 'hist', 'cols':[col], 'reason':'Auto-expanded'})
                idx += 1

            # Trim duplicates (keep order)
            seen = set()
            final = []
            for s in specs:
                key = (s['type'], tuple(s['cols']))
                if key not in seen:
                    seen.add(key)
                    final.append(s)
            return final[:max(minimum, len(final))]
        except Exception as e:
            self.logger.log_error("AnalyticsEngine.suggest_charts", str(e))
            return []
