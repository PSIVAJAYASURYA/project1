import tkinter as tk
from tkinter import filedialog, messagebox, ttk, scrolledtext
import os
import json
import pandas as pd
from modules.file_handler import FileHandler
from modules.data_processor import DataProcessor
from modules.analytics_engine import AnalyticsEngine
from modules.visualizer import Visualizer
from modules.report_generator import ReportGenerator
from modules.logger import AppLogger


class StyledButton(tk.Button):
    def __init__(self, parent, text, command=None, color="#00ADEF"):
        super().__init__(
            parent, text=text, command=command, bg=color, fg="white",
            font=("Segoe UI", 12, "bold"), activebackground="#0078D7",
            activeforeground="white", relief="flat", cursor="hand2",
            width=18, height=2, bd=0, highlightthickness=0
        )
        self.default_color = color
        self.bind("<Enter>", lambda e: self.configure(bg="#0099CC"))
        self.bind("<Leave>", lambda e: self.configure(bg=self.default_color))


class Dashboard:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Data Insights Automation Dashboard")
        self.root.geometry("1380x850")
        self.root.configure(bg="#121212")

        # Initialize modules
        self.file_handler = FileHandler()
        self.data_processor = DataProcessor()
        self.analytics = AnalyticsEngine()
        self.visualizer = Visualizer()
        self.reporter = ReportGenerator()
        self.logger = AppLogger("logs/error_log.txt")

        # Data states
        self.df = None
        self.analysis_info = {}
        self.is_cleaned = False

        self.build_main_screen()

    # ============================================================
    #  MAIN UI LAYOUT
    # ============================================================
    def build_main_screen(self):
        title = tk.Label(
            self.root, text="DATA INSIGHTS AUTOMATION DASHBOARD",
            font=("Segoe UI", 22, "bold"), fg="#00ADEF", bg="#121212"
        )
        title.pack(pady=(60, 30))

        button_frame = tk.Frame(self.root, bg="#121212")
        button_frame.pack(pady=10)

        StyledButton(button_frame, "Upload File", self.upload_file, color="#1E88E5").pack(side="left", padx=15)
        StyledButton(button_frame, "Data Clean", self.data_clean, color="#43A047").pack(side="left", padx=15)
        StyledButton(button_frame, "Visual", self.open_visual_window, color="#FFB300").pack(side="left", padx=15)
        StyledButton(button_frame, "Report", self.generate_report, color="#8E24AA").pack(side="left", padx=15)

        ttk.Separator(self.root, orient="horizontal").pack(fill="x", pady=25)
        StyledButton(self.root, "Column Analysis", self.show_column_analysis, color="#00ACC1").pack(pady=(10, 15))

        # Column Analysis Frame
        self.analysis_frame = tk.Frame(self.root, bg="#1E1E1E", bd=1, relief="solid")
        self.analysis_frame.pack_forget()

        tk.Label(self.analysis_frame, text="COLUMN ANALYSIS",
                 bg="#1E1E1E", fg="#00ADEF", font=("Segoe UI", 16, "bold"), pady=10)\
            .pack(fill="x")

        self.analysis_box = scrolledtext.ScrolledText(
            self.analysis_frame, wrap="word", bg="#2B2B2B", fg="white",
            insertbackground="white", font=("Consolas", 11), relief="flat"
        )
        self.analysis_box.pack(fill="both", expand=True, padx=20, pady=10)

        footer = tk.Label(
            self.root, text="Follow the flow → Upload → Data Clean → Visual → Report",
            bg="#121212", fg="#AAAAAA", font=("Segoe UI", 10, "italic")
        )
        footer.pack(side="bottom", pady=10)

    # ============================================================
    #  FILE UPLOAD
    # ============================================================
    def upload_file(self):
        filepath = filedialog.askopenfilename(
            title="Select data file",
            filetypes=[("Excel/CSV/JSON", "*.xlsx;*.xls;*.csv;*.json"), ("All files", "*.*")]
        )
        if filepath:
            self.df = self.file_handler.load_file(filepath)
            if self.df is not None:
                self.is_cleaned = False
                self.analysis_info = {}
                messagebox.showinfo(
                    "Success",
                    f"Loaded: {os.path.basename(filepath)}\nRows: {len(self.df)} | Columns: {len(self.df.columns)}"
                )
            else:
                messagebox.showerror("Error", "Failed to load file. Please check your input.")

    # ============================================================
    #  DATA CLEANING
    # ============================================================
    def data_clean(self):
        if self.df is None:
            messagebox.showwarning("Warning", "Please upload a file first.")
            return
        self.df = self.data_processor.clean_data(self.df)
        self.is_cleaned = True
        self.analysis_info = self.data_processor.analyze_columns(self.df)
        messagebox.showinfo("Data Cleaned", "Data cleaned successfully. You can now visualize or analyze.")

    # ============================================================
    #  OPEN VISUALIZATION WINDOW
    # ============================================================
    def open_visual_window(self):
        if self.df is None:
            messagebox.showwarning("Warning", "Please upload a file first.")
            return
        if not self.is_cleaned:
            messagebox.showwarning("Please clean first", "Clean data before visualization.")
            return
        from gui.visual_window import VisualizationWindow
        VisualizationWindow(self.root, self.df)

    # ============================================================
    #  GENERATE JSON REPORT
    # ============================================================
    def generate_report(self):
        try:
            if self.df is None:
                messagebox.showwarning("Warning", "Please upload a file first.")
                return
            if not self.is_cleaned:
                messagebox.showwarning("Please clean first", "Clean data before generating reports.")
                return

            # ✅ Only numeric columns
            numeric_df = self.df.select_dtypes(include="number")
            if numeric_df.empty:
                messagebox.showinfo("No Numeric Data", "No numeric columns found for reporting.")
                return

            # ✅ Calculate summary stats
            summary = {}
            for col in numeric_df.columns:
                summary[col] = {
                    "mean": float(numeric_df[col].mean()),
                    "median": float(numeric_df[col].median()),
                    "min": float(numeric_df[col].min()),
                    "max": float(numeric_df[col].max()),
                    "std_dev": float(numeric_df[col].std()),
                    "missing_values": int(numeric_df[col].isna().sum())
                }

            # ✅ Save JSON report
            os.makedirs("output", exist_ok=True)
            report_path = os.path.join("output", "numeric_report.json")
            with open(report_path, "w", encoding="utf-8") as f:
                json.dump(summary, f, indent=4)

            self.logger.log_info("Dashboard.generate_report", f"Report saved at {report_path}")
            messagebox.showinfo("Report Generated", f"✅ Numeric summary report saved to:\n{report_path}")

        except Exception as e:
            self.logger.log_error("Dashboard.generate_report", str(e))
            messagebox.showerror("Error", f"Report generation failed:\n{e}")

    # ============================================================
    #  COLUMN ANALYSIS DISPLAY
    # ============================================================
    def show_column_analysis(self):
        if not self.is_cleaned:
            messagebox.showwarning("Warning", "Please clean data first to analyze columns.")
            return

        self.analysis_frame.pack(fill="both", expand=True, padx=60, pady=20)
        self.analysis_box.delete("1.0", tk.END)

        for col, meta in self.analysis_info.items():
            self.analysis_box.insert(tk.END, f"{col}\n", "header")
            self.analysis_box.insert(tk.END, f"  Type: {meta['kind']}\n  Missing: {meta['missing']}\n  Unique: {meta['unique']}\n")
            self.analysis_box.insert(tk.END, f"  Sample: {meta['sample_values']}\n\n")

        self.analysis_box.tag_config("header", foreground="#00ADEF", font=("Consolas", 12, "bold"))

    def run(self):
        self.root.mainloop()


if __name__ == "__main__":
    Dashboard().run()
