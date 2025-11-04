import tkinter as tk
from tkinter import ttk, messagebox
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.pyplot as plt
import pandas as pd
import subprocess, os
from datetime import datetime
from modules.analytics_engine import AnalyticsEngine
from modules.logger import AppLogger
from modules.data_processor import DataProcessor

# ============================================================
#  Function: Query local Ollama model (.gguf)
# ============================================================
def analyze_with_ollama(prompt, model="gemma3:4b"):
    """
    Runs a local Ollama model and captures plain text output safely.
    Compatible with models that don't support --format json.
    """
    try:
        print(f"🔹 Using local model: {model}")
        result = subprocess.run(
            ["ollama", "run", model, prompt],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="ignore",
            timeout=120
        )

        response_text = result.stdout.strip()
        if not response_text:
            response_text = "⚠️ No response received from the local model."

        return response_text

    except subprocess.TimeoutExpired:
        return "⚠️ Ollama model timed out (no response within 60 seconds)."
    except Exception as e:
        return f"❌ Ollama error: {e}"


# ============================================================
#  Visualization Window Class
# ============================================================
class VisualizationWindow:
    def __init__(self, master, df):
        self.master = master
        self.df = df
        self.master.title("Visualization Engine (Local AI)")
        self.master.geometry("900x700")
        self.master.configure(bg="#121212")

        os.makedirs("output", exist_ok=True)
        os.makedirs("logs", exist_ok=True)

        style = ttk.Style()
        style.configure("TButton", font=("Segoe UI", 11), padding=8)
        style.configure("TLabel", background="#121212", foreground="white", font=("Segoe UI", 11))

        title = ttk.Label(master, text="Visualize Data — Engine & User", font=("Segoe UI", 16, "bold"))
        title.pack(pady=20)

        btn_frame = tk.Frame(master, bg="#121212")
        btn_frame.pack(pady=10)

        ttk.Button(btn_frame, text="By Engine (LLM)", command=self.visual_by_engine).grid(row=0, column=0, padx=15)
        ttk.Button(btn_frame, text="By Engine (Analytical)", command=self.visual_by_analytical).grid(row=0, column=1, padx=15)
        ttk.Button(btn_frame, text="By User", command=self.visual_by_user).grid(row=0, column=2, padx=15)

        self.output_text = tk.Text(master, wrap="word", height=20, bg="#1E1E1E", fg="white", font=("Consolas", 10))
        self.output_text.pack(padx=15, pady=20, fill="both", expand=True)

    # ============================================================
    #  ENGINE VISUALIZATION (local LLM via Ollama)
    # ============================================================
    def visual_by_engine(self):
        try:
            summary = self.df.describe(include="all").to_string()
            columns = ", ".join(self.df.columns)

            prompt = f"""
            You are a data visualization expert.
            Given this dataset with columns: {columns}
            and the following summary:
            {summary}

            Suggest up to six visualizations that would help understand relationships and trends.
            Format each suggestion in this pattern:
            <chart_type> | <x_column> | <y_column or None> | <reason>
            """

            self.output_text.delete(1.0, tk.END)
            self.output_text.insert(tk.END, "🤖 Analyzing dataset with local AI model... please wait...\n\n")

            output = analyze_with_ollama(prompt, model="gemma3:4b")

            self.output_text.insert(tk.END, output)
            print("\n=== AI Visualization Suggestions ===\n", output)

        except Exception as e:
            messagebox.showerror("Error", f"Engine visualization failed:\n{e}")

    # ============================================================
    #  USER VISUALIZATION (manual)
    # ============================================================
    def visual_by_user(self):
        win = tk.Toplevel(self.master)
        win.title("Custom Visualization")
        win.geometry("500x400")
        win.configure(bg="#121212")

        ttk.Label(win, text="Select X Column:").pack(pady=5)
        x_col = ttk.Combobox(win, values=list(self.df.columns))
        x_col.pack(pady=5)

        ttk.Label(win, text="Select Y Column:").pack(pady=5)
        y_col = ttk.Combobox(win, values=list(self.df.columns))
        y_col.pack(pady=5)

        ttk.Label(win, text="Select Plot Type:").pack(pady=5)
        plot_type = ttk.Combobox(win, values=["line", "bar", "scatter", "pie", "hist"])
        plot_type.pack(pady=5)

        def create_plot():
            try:
                x = x_col.get()
                y = y_col.get()
                plot = plot_type.get()

                if not x or not plot:
                    messagebox.showwarning("Missing Input", "Please select at least X column and Plot Type.")
                    return

                fig, ax = plt.subplots(figsize=(7, 5))
                if plot == "line":
                    self.df.plot(x=x, y=y, kind="line", ax=ax)
                elif plot == "bar":
                    self.df.plot(x=x, y=y, kind="bar", ax=ax)
                elif plot == "scatter":
                    self.df.plot(x=x, y=y, kind="scatter", ax=ax)
                elif plot == "pie":
                    if y:
                        data = self.df.groupby(x)[y].sum()
                        data.plot(kind="pie", ax=ax, autopct="%1.1f%%")
                    else:
                        messagebox.showwarning("Invalid", "Pie chart requires both X and Y columns.")
                        return
                elif plot == "hist":
                    self.df[x].plot(kind="hist", ax=ax, bins=20)

                ax.set_title(f"{plot.title()} Chart of {x} vs {y if y else ''}")
                plt.tight_layout()

                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"output/chart_{plot}_{timestamp}.png"
                fig.savefig(filename)
                print(f"✅ Chart saved: {filename}")

                chart_win = tk.Toplevel(win)
                chart_win.title("Chart")
                chart_win.geometry("700x600")

                canvas = FigureCanvasTkAgg(fig, master=chart_win)
                canvas.get_tk_widget().pack(fill="both", expand=True)
                canvas.draw()

                messagebox.showinfo("Saved", f"Chart saved successfully to:\n{filename}")

            except Exception as e:
                messagebox.showerror("Error", f"Plot failed:\n{e}")

        ttk.Button(win, text="Create Plot", command=create_plot).pack(pady=15)

    # ============================================================
    #  ANALYTICAL ENGINE VISUALIZATION (auto generate & log)
    # ============================================================
    def visual_by_analytical(self):
        try:
            logger = AppLogger("logs/error_log.txt")
            analytics = AnalyticsEngine()
            processor = DataProcessor()

            self.output_text.delete(1.0, tk.END)
            self.output_text.insert(tk.END, "🧠 Analytical Engine — Generating Visualizations...\n\n")

            analysis_info = processor.analyze_columns(self.df)
            generated_files = analytics.generate_and_save_charts(self.df, analysis_info)

            log_text = "=== Analytical Engine Suggestions ===\n"
            if generated_files:
                for path in generated_files:
                    self.output_text.insert(tk.END, f"✅ Saved: {path}\n")
                    log_text += f"✅ Saved: {path}\n"
            else:
                msg = "⚠️ No charts generated.\n"
                self.output_text.insert(tk.END, msg)
                log_text += msg

            # ✅ Save all results in engine_suggestions.txt
            with open("logs/engine_suggestions.txt", "a", encoding="utf-8") as f:
                f.write("\n" + log_text + "\n")

            logger.log_info("visual_by_analytical", f"{len(generated_files)} charts logged successfully.")

        except Exception as e:
            messagebox.showerror("Error", f"Analytical engine failed:\n{e}")
            logger.log_error("visual_by_analytical", str(e))


# ============================================================
#  Test Run (standalone)
# ============================================================
if __name__ == "__main__":
    df = pd.DataFrame({
        "Month": ["Jan", "Feb", "Mar", "Apr", "May"],
        "Sales": [100, 120, 90, 150, 200],
        "Profit": [20, 30, 10, 40, 60]
    })

    root = tk.Tk()
    app = VisualizationWindow(root, df)
    root.mainloop()
