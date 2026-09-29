"""Visualization and reporting charts for notebooks and figures."""
import matplotlib
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

COLORS = ['#223d60', '#d78c50', '#52958d', '#9381b0']


def style():
    plt.rcParams.update({
        'font.family': 'DejaVu Sans', 'font.size': 10,
        'axes.spines.top': False, 'axes.spines.right': False,
        'axes.labelcolor': '#53647b', 'xtick.color': '#637389', 'ytick.color': '#637389',
        'axes.edgecolor': '#d1dae5', 'figure.facecolor': 'white',
        'axes.titleweight': 'bold', 'axes.titlesize': 14, 'savefig.dpi': 170
    })


def plot_load(d):
    fig, ax = plt.subplots(figsize=(10, 4.2))
    ax.plot(d.date, d.total_load, color=COLORS[0], lw=1.4, label='Reported total load')
    ax.plot(d.date, d.load_mean7, color=COLORS[1], lw=1.7, label='7-observation mean')
    ax.set(ylabel='Children', title='Reported load declined after its December 2023 peak')
    ax.grid(axis='y', alpha=.2)
    ax.legend(frameon=False, loc='upper right')
    fig.autofmt_xdate()
    fig.tight_layout()
    return fig


def plot_flows(d):
    fig, axes = plt.subplots(2, 1, figsize=(10, 5), sharex=True)
    axes[0].plot(d.date, d.transfers, color=COLORS[1], lw=1, label='Transfers out of CBP')
    axes[0].plot(d.date, d.discharges, color=COLORS[2], lw=1, label='HHS discharges')
    axes[0].set_title('Flow balance changes across reporting regimes')
    axes[0].legend(frameon=False, ncol=2)
    axes[0].set_ylabel('Reported flow')
    axes[1].axhline(0, color='#98a8b9', lw=.8)
    axes[1].plot(d.date, d.net_mean7, color=COLORS[0], lw=1.5)
    axes[1].set_ylabel('Net flow, 7-obs mean')
    for ax in axes:
        ax.grid(axis='y', alpha=.2)
    fig.autofmt_xdate()
    fig.tight_layout()
    return fig


def plot_models(models):
    fig, ax = plt.subplots(figsize=(10, 4.1))
    names = [x['model'] for x in models['scores']]
    val = [x['validation']['mae'] for x in models['scores']]
    test = [x['test']['mae'] for x in models['scores']]
    indices = np.arange(len(names))
    ax.bar(indices - .18, val, .34, color=COLORS[0], label='Validation MAE')
    ax.bar(indices + .18, test, .34, color=COLORS[1], label='Test MAE')
    ax.set_xticks(indices, names)
    ax.set_ylabel('Children (lower is better)')
    ax.set_title('Validation selected a local trend over more complex models')
    ax.legend(frameon=False)
    ax.grid(axis='y', alpha=.15)
    fig.tight_layout()
    return fig


def plot_predictions(models):
    d = pd.DataFrame(models['test_predictions'])
    dates = pd.to_datetime(d.date)
    fig, ax = plt.subplots(figsize=(10, 4.1))
    for key, label, color in [('actual', 'Actual HHS care', COLORS[0]),
                              ('selected', 'Selected model', COLORS[1]),
                              ('persistence', 'Persistence', COLORS[2])]:
        ax.plot(dates, d[key], label=label, color=color, lw=1.5 if key == 'actual' else 1.1)
    ax.set(title='Test forecasts use only information available seven days earlier', ylabel='HHS care census')
    ax.legend(frameon=False, ncol=3)
    ax.grid(axis='y', alpha=.2)
    fig.autofmt_xdate()
    fig.tight_layout()
    return fig


def plot_sensitivity(bundle):
    s = pd.DataFrame(bundle['sensitivity'])
    fig, ax = plt.subplots(figsize=(8, 3.6))
    bars = ax.bar(s.rule, s.share_pct, color=[COLORS[2], COLORS[0], COLORS[1]], width=.5)
    ax.bar_label(bars, labels=[f'{v:.1f}%' for v in s.share_pct], padding=4)
    ax.set(ylim=(0, 40), ylabel='Share of eligible observations (%)',
           title='Pressure classification depends on the persistence rule')
    ax.grid(axis='y', alpha=.15)
    fig.tight_layout()
    return fig
