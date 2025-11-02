import pandas as pd
import json
import os
from modules.logger import AppLogger

class FileHandler:
    def __init__(self):
        self.logger = AppLogger("logs/error_log.txt")

    def load_file(self, filepath, sheet_name=None):
        """
        Returns a pandas DataFrame. For Excel with multiple sheets,
        concatenate similar sheets if possible.
        """
        try:
            ext = os.path.splitext(filepath)[1].lower()
            if ext == '.csv':
                df = pd.read_csv(filepath)
            elif ext in ['.xlsx', '.xls']:
                xls = pd.ExcelFile(filepath)
                if sheet_name:
                    df = pd.read_excel(xls, sheet_name=sheet_name)
                else:
                    dfs = [pd.read_excel(xls, sheet_name=sh) for sh in xls.sheet_names]
                    dfs = [d for d in dfs if not d.empty]
                    if len(dfs) == 0:
                        df = pd.DataFrame()
                    elif len(dfs) == 1:
                        df = dfs[0]
                    else:
                        try:
                            df = pd.concat(dfs, ignore_index=True, sort=False)
                        except Exception:
                            df = dfs[0]
            elif ext == '.json':
                with open(filepath, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                df = pd.DataFrame(data)
            else:
                raise ValueError("Unsupported file type")
            return df
        except Exception as e:
            self.logger.log_error("FileHandler.load_file", str(e))
            return None
