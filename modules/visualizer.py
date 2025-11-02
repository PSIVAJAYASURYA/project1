import matplotlib.pyplot as plt
import seaborn as sns
import os
from modules.logger import AppLogger
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

class Visualizer:
    def __init__(self, output_dir="output_data"):
        self.logger = AppLogger("logs/error_log.txt")
        self.output_dir = output_dir
        os.makedirs(self.output_dir, exist_ok=True)

    def make_figure(self, spec, df):
        """Return matplotlib Figure for given spec and dataframe."""
        try:
            typ = spec.get('type')
            cols = spec.get('cols', [])
            fig, ax = plt.subplots(figsize=(6,4))
            if typ == 'hist' and len(cols)==1:
                df[cols[0]].dropna().plot(kind='hist', ax=ax)
                ax.set_title(f"Histogram: {cols[0]}")
            elif typ == 'box' and len(cols)==1:
                df[cols[0]].dropna().plot(kind='box', ax=ax)
                ax.set_title(f"Boxplot: {cols[0]}")
            elif typ == 'bar' and len(cols)==1:
                counts = df[cols[0]].value_counts().sort_values(ascending=False)
                counts.plot(kind='bar', ax=ax)
                ax.set_title(f"Bar counts: {cols[0]}")
                ax.set_ylabel("Count")
            elif typ == 'bar_top' and len(cols)==1:
                counts = df[cols[0]].value_counts().nlargest(10)
                counts.plot(kind='bar', ax=ax)
                ax.set_title(f"Top categories: {cols[0]}")
                ax.set_ylabel("Count")
            elif typ == 'line_time' and len(cols)==1:
                col = cols[0]
                numeric = df.select_dtypes(include='number').columns.tolist()
                if col not in df.columns:
                    ax.text(0.5,0.5,"Column missing", ha='center')
                else:
                    if numeric:
                        try:
                            series = df.set_index(col)[numeric[0]].resample('M').mean()
                            series.plot(ax=ax)
                            ax.set_title(f"Time trend ({numeric[0]}) by {col}")
                        except Exception:
                            series = df.set_index(col).resample('M').size()
                            series.plot(ax=ax)
                            ax.set_title(f"Counts over time by {col}")
                    else:
                        series = df.set_index(col).resample('M').size()
                        series.plot(ax=ax)
                        ax.set_title(f"Counts over time by {col}")
            elif typ == 'scatter' and len(cols)==2:
                ax.scatter(df[cols[0]], df[cols[1]])
                ax.set_xlabel(cols[0])
                ax.set_ylabel(cols[1])
                ax.set_title(f"Scatter: {cols[0]} vs {cols[1]}")
            elif typ == 'box_group' and len(cols)==2:
                num, cat = cols
                sns.boxplot(x=cat, y=num, data=df, ax=ax)
                ax.set_title(f"{num} by {cat}")
                ax.tick_params(axis='x', rotation=45)
            else:
                ax.text(0.5, 0.5, f"Unsupported spec {typ}", horizontalalignment='center')
            plt.tight_layout()
            return fig
        except Exception as e:
            self.logger.log_error("Visualizer.make_figure", str(e))
            return None

    def save_figure(self, fig, name):
        try:
            path = os.path.join(self.output_dir, name)
            fig.savefig(path)
            return path
        except Exception as e:
            self.logger.log_error("Visualizer.save_figure", str(e))
            return None

    def show_in_terminal(self, fig):
        try:
            plt.show(block=False)
        except Exception as e:
            self.logger.log_error("Visualizer.show_in_terminal", str(e))

    def embed_in_tk(self, fig, tk_parent):
        try:
            canvas = FigureCanvasTkAgg(fig, master=tk_parent)
            canvas_widget = canvas.get_tk_widget()
            canvas_widget.pack(side='top', padx=5, pady=5)
            canvas.draw()
            return canvas
        except Exception as e:
            self.logger.log_error("Visualizer.embed_in_tk", str(e))
            return None
