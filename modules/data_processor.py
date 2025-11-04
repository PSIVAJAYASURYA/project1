import pandas as pd
import numpy as np
from modules.logger import AppLogger

pd.options.mode.chained_assignment = None  # suppress warnings


class DataProcessor:
    def __init__(self):
        self.logger = AppLogger("logs/error_log.txt")

    def analyze_columns(self, df):
        """Return summary: inferred kind, missing, unique, and sample values."""
        info = {}
        try:
            for col in df.columns:
                series = df[col]
                missing = int(series.isna().sum())
                unique = int(series.nunique(dropna=True))
                dtype = str(series.dtype)

                # Detect data kind
                kind = "numeric" if pd.api.types.is_numeric_dtype(series) else "categorical"

                # Try to detect datetime
                if series.dropna().shape[0] > 0:
                    sample = series.dropna().astype(str).iloc[:10]
                    import warnings
                    warnings.filterwarnings("ignore", message="Could not infer format", category=UserWarning, module="pandas")
                    parsed = pd.to_datetime(sample, errors="coerce")
                    if parsed.notna().sum() >= len(sample) * 0.6:
                        kind = "datetime"

                info[col] = {
                    "dtype": dtype,
                    "kind": kind,
                    "missing": missing,
                    "unique": unique,
                    "sample_values": series.dropna().astype(str).unique()[:5].tolist(),
                }

            # ✅ Log basic structure summary
            self.logger.log_info("DataProcessor.analyze_columns", f"Columns analyzed: {list(df.columns)}")
            self.logger.log_info("DataProcessor.analyze_columns", f"Detected data kinds: {[info[c]['kind'] for c in info]}")

            return info

        except Exception as e:
            self.logger.log_error("DataProcessor.analyze_columns", str(e))
            return {}

    def clean_data(self, df):
        """Clean dataset: trim strings, detect numeric, fill missing, log stats."""
        try:
            df = df.copy()
            df = df.drop_duplicates(ignore_index=True)

            # Clean text columns
            for col in df.select_dtypes(include=["object"]).columns:
                df[col] = df[col].astype(str).str.strip()
                df[col] = df[col].replace({"": pd.NA, "nan": pd.NA})

            # Detect numeric columns
            for col in df.columns:
                s = df[col].dropna().astype(str)
                if len(s) > 0:
                    numeric_ratio = s.str.match(r"^-?\d+(\.\d+)?$").mean()
                    if numeric_ratio > 0.6:
                        df[col] = pd.to_numeric(df[col], errors="coerce")

            # Detect datetimes
            for col in df.columns:
                if df[col].dtype == object:
                    parsed = pd.to_datetime(df[col], errors="coerce")
                    if parsed.notna().mean() > 0.6:
                        df[col] = parsed

            # Fill missing values
            for col in df.columns:
                if df[col].isna().sum() == 0:
                    continue
                if pd.api.types.is_numeric_dtype(df[col]):
                    median = df[col].median()
                    df[col] = df[col].fillna(median)
                elif pd.api.types.is_datetime64_any_dtype(df[col]):
                    df[col] = df[col].fillna(method="ffill").fillna(method="bfill")
                else:
                    mode = df[col].mode(dropna=True)
                    if not mode.empty:
                        df[col] = df[col].fillna(mode.iloc[0])
                    else:
                        df[col] = df[col].fillna("UNKNOWN")

            # ✅ Log statistical summary
            stats_log = []
            numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
            for col in numeric_cols:
                col_stats = df[col].describe().to_dict()
                stats_log.append(f"Column '{col}': mean={col_stats.get('mean'):.2f}, std={col_stats.get('std'):.2f}, min={col_stats.get('min')}, max={col_stats.get('max')}, median={df[col].median():.2f}")

            categorical_cols = df.select_dtypes(include=["object"]).columns.tolist()
            for col in categorical_cols:
                top_val = df[col].mode()[0] if not df[col].mode().empty else "N/A"
                freq = df[col].value_counts().head(1).values[0] if not df[col].value_counts().empty else 0
                stats_log.append(f"Column '{col}': top='{top_val}', frequency={freq}")

            for entry in stats_log:
                self.logger.log_info("DataProcessor.clean_data.stats", entry)

            self.logger.log_info("DataProcessor.clean_data", "Data cleaned and stats logged successfully.")

            return df

        except Exception as e:
            self.logger.log_error("DataProcessor.clean_data", str(e))
            return df
