"""
Animated Financial & Dividend Growth Visualizer
Author: Waseequr Rahman
"""

from __future__ import annotations

import argparse
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk
from typing import List, Optional

import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import numpy as np
import pandas as pd
from matplotlib.animation import FuncAnimation


DEFAULT_STAGES = [
    {"label": "Phase 1: Early Compounding (2004–2010)", "end_year": 2010, "dividend_milestone": 350},
    {"label": "Phase 2: Dividend Acceleration (2004–2016)", "end_year": 2016, "dividend_milestone": 3200},
    {"label": "Phase 3: Institutional Scale (2004–2020)", "end_year": 2020, "dividend_milestone": 14800},
    {"label": "Phase 4: Full Horizon (2004–2024)", "end_year": 2024, "dividend_milestone": 38500},
]


def load_or_generate_dataset(csv_path: Optional[Path] = None) -> pd.DataFrame:
    if csv_path and csv_path.exists():
        df = pd.read_csv(csv_path)
        cols = [c.lower().strip() for c in df.columns]
        df.columns = cols
        if "year" in cols and ("portfolio_value" in cols or "value" in cols):
            if "value" in cols and "portfolio_value" not in cols:
                df = df.rename(columns={"value": "portfolio_value"})
            if "annual_dividend" not in df.columns:
                df["annual_dividend"] = (df["portfolio_value"] * 0.028).round(2)
            return df.sort_values("year").reset_index(drop=True)

    years = np.arange(2004, 2025)
    rates = np.linspace(0.14, 0.31, len(years))
    vals = [1000.0]
    for r in rates[:-1]:
        vals.append(round(vals[-1] * (1.0 + r), 2))
    divs = [round(v * 0.028, 2) for v in vals]
    return pd.DataFrame({"year": years, "portfolio_value": vals, "annual_dividend": divs})


class FinancialGrowthVisualizer:
    """Interactive Tkinter + Matplotlib animated financial trajectory & dividend analyzer."""

    def __init__(self, df: pd.DataFrame) -> None:
        self.df = df
        self.current_stage_idx = 0

    def render_static_snapshot(self, output_path: Path) -> None:
        """Render a publication-grade 2-panel dashboard snapshot to PNG."""
        plt.style.use("seaborn-v0_8-whitegrid" if "seaborn-v0_8-whitegrid" in plt.style.available else "default")
        fig, (ax1, ax2) = plt.subplots(
            2, 1, figsize=(10.5, 6.4), gridspec_kw={"height_ratios": [2.3, 1.1]}, sharex=True
        )
        fig.patch.set_facecolor("#0F172A")
        for ax in (ax1, ax2):
            ax.set_facecolor("#1E293B")
            for spine in ax.spines.values():
                spine.set_color("#334155")
            ax.tick_params(colors="#CBD5E1", labelsize=9.5)
            ax.grid(color="#334155", linestyle="--", linewidth=0.6, alpha=0.7)

        years = self.df["year"].to_numpy()
        vals = self.df["portfolio_value"].to_numpy()
        divs = self.df["annual_dividend"].to_numpy()

        # Panel 1: Portfolio Equity Curve + Milestone Thresholds
        ax1.plot(years, vals, color="#38BDF8", linewidth=2.8, marker="o", markersize=4.5, label="Cumulative Portfolio Value ($)")
        ax1.fill_between(years, vals, color="#38BDF8", alpha=0.14)

        cagr = ((vals[-1] / vals[0]) ** (1 / max(1, len(years) - 1)) - 1) * 100
        ax1.set_title(
            f"Multi-Stage Investment & Dividend Compounding Trajectory  |  CAGR: {cagr:.1f}%",
            color="#F8FAFC",
            fontsize=12.5,
            fontweight="bold",
            pad=12,
        )
        ax1.set_ylabel("Portfolio Value (USD)", color="#E2E8F0", fontsize=10, fontweight="bold")
        ax1.yaxis.set_major_formatter(mticker.StrMethodFormatter("${x:,.0f}"))

        # Annotate peak
        ax1.annotate(
            f"Peak: ${vals[-1]:,.0f}",
            xy=(years[-1], vals[-1]),
            xytext=(years[-5], vals[-1] * 0.88),
            arrowprops={"arrowstyle": "->", "color": "#38BDF8", "lw": 1.4},
            color="#F8FAFC",
            fontsize=9.5,
            fontweight="bold",
            bbox={"boxstyle": "round,pad=0.35", "facecolor": "#0284C7", "edgecolor": "#38BDF8"},
        )
        ax1.legend(loc="upper left", facecolor="#0F172A", edgecolor="#334155", labelcolor="#F8FAFC")

        # Panel 2: Annual Dividend Cashflow Bars
        ax2.bar(years, divs, color="#10B981", width=0.62, alpha=0.88, label="Annual Dividend Payout ($)")
        ax2.set_xlabel("Fiscal Year", color="#E2E8F0", fontsize=10, fontweight="bold")
        ax2.set_ylabel("Annual Dividend", color="#E2E8F0", fontsize=10, fontweight="bold")
        ax2.yaxis.set_major_formatter(mticker.StrMethodFormatter("${x:,.0f}"))
        ax2.set_xticks(years[::2])
        ax2.legend(loc="upper left", facecolor="#0F172A", edgecolor="#334155", labelcolor="#F8FAFC")

        plt.tight_layout()
        fig.savefig(output_path, dpi=180, facecolor=fig.get_facecolor())
        plt.close(fig)

    def launch_animated_chart(self) -> None:
        fig, ax = plt.subplots(figsize=(9, 5.5))
        line, = ax.plot([], [], color="#0284C7", lw=2.5, label="Portfolio Value ($)")
        ax.yaxis.set_major_formatter(mticker.StrMethodFormatter("${x:,.0f}"))

        def update(frame: int):
            stage = DEFAULT_STAGES[self.current_stage_idx]
            stage_df = self.df[self.df["year"] <= stage["end_year"]]
            n_rows = max(2, int(len(stage_df) * ((frame + 1) / 100.0)))
            sub = stage_df.iloc[:n_rows]

            line.set_data(sub["year"], sub["portfolio_value"])
            ax.set_xlim(int(self.df["year"].min()), int(stage["end_year"]) + 1)
            ax.set_ylim(0, float(sub["portfolio_value"].max()) * 1.25)
            ax.set_title(stage["label"], fontweight="bold")
            ax.set_xlabel("Year")
            ax.set_ylabel("Portfolio Value (USD)")

            if frame == 99 and self.current_stage_idx < len(DEFAULT_STAGES) - 1:
                self.current_stage_idx += 1
            return (line,)

        _ani = FuncAnimation(fig, update, frames=100, interval=45, blit=False, repeat=True)
        plt.show()


def launch_gui() -> None:
    root = tk.Tk()
    root.title("Animated Financial & Dividend Growth Visualizer")
    root.geometry("460x260")
    root.configure( padx=16, pady=16)

    state = {"df": load_or_generate_dataset()}
    status_var = tk.StringVar(value="Loaded default 20-year compounding dataset (2004–2024).")

    ttk.Label(
        root,
        text="Financial & Dividend Growth Visualizer",
        font=("Segoe UI", 13, "bold"),
    ).pack(pady=(0, 8))

    def on_upload() -> None:
        fp = filedialog.askopenfilename(filetypes=[("CSV files", "*.csv")])
        if fp:
            state["df"] = load_or_generate_dataset(Path(fp))
            status_var.set(f"Loaded {Path(fp).name} ({len(state['df'])} rows).")

    def on_animate() -> None:
        vis = FinancialGrowthVisualizer(state["df"])
        vis.launch_animated_chart()

    def on_export_png() -> None:
        fp = filedialog.asksaveasfilename(
            defaultextension=".png",
            filetypes=[("PNG Image", "*.png")],
            initialfile="portfolio_growth_dashboard.png",
        )
        if fp:
            vis = FinancialGrowthVisualizer(state["df"])
            vis.render_static_snapshot(Path(fp))
            messagebox.showinfo("Export Complete", f"Saved high-DPI dashboard chart to:\n{fp}")

    btn_frame = ttk.Frame(root)
    btn_frame.pack(pady=12, fill=tk.X)
    ttk.Button(btn_frame, text="1. Load Custom CSV", command=on_upload).pack(fill=tk.X, pady=3)
    ttk.Button(btn_frame, text="2. Launch Live Multi-Stage Animation", command=on_animate).pack(fill=tk.X, pady=3)
    ttk.Button(btn_frame, text="3. Export High-DPI Dashboard PNG", command=on_export_png).pack(fill=tk.X, pady=3)

    ttk.Label(root, textvariable=status_var, wraplength=420).pack(pady=8)
    root.mainloop()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Animated Financial & Dividend Growth Visualizer")
    parser.add_argument("--csv", help="Optional CSV input file", default=None)
    parser.add_argument("--export-png", help="Render static high-DPI dashboard snapshot and exit", default=None)
    args = parser.parse_args()

    dataset = load_or_generate_dataset(Path(args.csv) if args.csv else None)
    if args.export_png:
        FinancialGrowthVisualizer(dataset).render_static_snapshot(Path(args.export_png))
    else:
        launch_gui()
