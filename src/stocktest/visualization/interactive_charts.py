"""Interactive chart generation using Plotly for hover capabilities."""

from pathlib import Path

import pandas as pd
import plotly.graph_objects as go


def plot_equity_curve_interactive(
    equity_curve: pd.DataFrame,
    output_path: Path | str | None = None,
    title: str = "Portfolio Performance",
    benchmark_data: pd.DataFrame | None = None,
) -> str:
    """Plot interactive equity curve with hover tooltips.

    Args:
        equity_curve: DataFrame with DatetimeIndex and 'total_value' column
        output_path: Path to save HTML file (None to return HTML string only)
        title: Chart title
        benchmark_data: Optional DataFrame with benchmark values

    Returns:
        HTML string of the chart

    Raises:
        ValueError: If equity_curve is empty or missing required columns
    """
    if equity_curve.empty:
        msg = "Equity curve DataFrame is empty"
        raise ValueError(msg)

    if "total_value" not in equity_curve.columns:
        msg = "Equity curve must have 'total_value' column"
        raise ValueError(msg)

    fig = go.Figure()

    fig.add_trace(
        go.Scatter(
            x=equity_curve.index,
            y=equity_curve["total_value"],
            mode="lines",
            name="Portfolio",
            line={"color": "#2E86AB", "width": 2},
            hovertemplate="<b>%{x|%Y-%m-%d}</b><br>" + "$%{y:,.2f}<br>" + "<extra></extra>",
        )
    )

    if benchmark_data is not None and not benchmark_data.empty:
        if "total_value" not in benchmark_data.columns:
            msg = "Benchmark data must have 'total_value' column"
            raise ValueError(msg)

        fig.add_trace(
            go.Scatter(
                x=benchmark_data.index,
                y=benchmark_data["total_value"],
                mode="lines",
                name="Benchmark",
                line={"color": "#A23B72", "width": 2, "dash": "dash"},
                hovertemplate="<b>%{x|%Y-%m-%d}</b><br>" + "$%{y:,.2f}<br>" + "<extra></extra>",
            )
        )

    fig.update_layout(
        title={
            "text": title,
            "x": 0.5,
            "xanchor": "center",
            "font": {"size": 16, "weight": "bold"},
        },
        xaxis_title="Date",
        yaxis_title="Portfolio Value ($)",
        hovermode="x unified",
        template="plotly_white",
        height=600,
        legend={"yanchor": "top", "y": 0.99, "xanchor": "left", "x": 0.01},
    )

    fig.update_xaxes(showgrid=True, gridwidth=1, gridcolor="rgba(0,0,0,0.1)")
    fig.update_yaxes(showgrid=True, gridwidth=1, gridcolor="rgba(0,0,0,0.1)")

    html = fig.to_html(include_plotlyjs="cdn", full_html=True)

    if output_path:
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(html)

    return html


def plot_drawdown_interactive(
    equity_curve: pd.DataFrame,
    output_path: Path | str | None = None,
    title: str = "Portfolio Drawdown",
) -> str:
    """Plot interactive drawdown chart with hover tooltips.

    Args:
        equity_curve: DataFrame with DatetimeIndex and 'total_value' column
        output_path: Path to save HTML file (None to return HTML string only)
        title: Chart title

    Returns:
        HTML string of the chart

    Raises:
        ValueError: If equity_curve is empty or missing required columns
    """
    if equity_curve.empty:
        msg = "Equity curve DataFrame is empty"
        raise ValueError(msg)

    if "total_value" not in equity_curve.columns:
        msg = "Equity curve must have 'total_value' column"
        raise ValueError(msg)

    running_max = equity_curve["total_value"].cummax()
    drawdown = ((equity_curve["total_value"] - running_max) / running_max) * 100

    fig = go.Figure()

    fig.add_trace(
        go.Scatter(
            x=equity_curve.index,
            y=drawdown,
            mode="lines",
            name="Drawdown",
            fill="tozeroy",
            line={"color": "#E63946", "width": 2},
            fillcolor="rgba(230, 57, 70, 0.3)",
            hovertemplate="<b>%{x|%Y-%m-%d}</b><br>" + "%{y:.1f}%<br>" + "<extra></extra>",
        )
    )

    fig.update_layout(
        title={
            "text": title,
            "x": 0.5,
            "xanchor": "center",
            "font": {"size": 16, "weight": "bold"},
        },
        xaxis_title="Date",
        yaxis_title="Drawdown (%)",
        hovermode="x unified",
        template="plotly_white",
        height=600,
        legend={"yanchor": "top", "y": 0.99, "xanchor": "left", "x": 0.01},
    )

    fig.update_xaxes(showgrid=True, gridwidth=1, gridcolor="rgba(0,0,0,0.1)")
    fig.update_yaxes(showgrid=True, gridwidth=1, gridcolor="rgba(0,0,0,0.1)")

    html = fig.to_html(include_plotlyjs="cdn", full_html=True)

    if output_path:
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(html)

    return html


def plot_comparison_interactive(
    results: dict[str, dict],
    output_path: Path | str | None = None,
    title: str = "Portfolio Performance Comparison",
) -> str:
    """Plot interactive comparison of multiple tickers with hover tooltips.

    Args:
        results: Dictionary mapping ticker to result dict with 'equity_curve' key
        output_path: Path to save HTML file (None to return HTML string only)
        title: Chart title

    Returns:
        HTML string of the chart

    Raises:
        ValueError: If results is empty or equity curves are invalid
    """
    if not results:
        msg = "Results dictionary is empty"
        raise ValueError(msg)

    fig = go.Figure()

    colors = [
        "#2E86AB",
        "#A23B72",
        "#F18F01",
        "#C73E1D",
        "#6A994E",
        "#BC4B51",
        "#8D5B4C",
        "#5F0F40",
    ]

    ticker_returns = []
    for ticker, result in results.items():
        equity_curve = result["equity_curve"]
        if not equity_curve.empty and "total_value" in equity_curve.columns:
            initial_value = equity_curve["total_value"].iloc[0]
            final_value = equity_curve["total_value"].iloc[-1]
            total_return = ((final_value / initial_value) - 1) * 100
            ticker_returns.append((ticker, total_return, result))

    ticker_returns.sort(key=lambda x: x[1], reverse=True)

    for idx, (ticker, _total_return, result) in enumerate(ticker_returns):
        equity_curve = result["equity_curve"]

        if equity_curve.empty:
            continue

        if "total_value" not in equity_curve.columns:
            continue

        initial_value = equity_curve["total_value"].iloc[0]
        normalized = (equity_curve["total_value"] / initial_value) * 100

        color = colors[idx % len(colors)]

        fig.add_trace(
            go.Scatter(
                x=equity_curve.index,
                y=normalized,
                mode="lines",
                name=ticker,
                line={"color": color, "width": 2},
                hovertemplate="<b>%{fullData.name}</b>: %{y:.1f}<extra></extra>",
            )
        )

    fig.update_layout(
        title={
            "text": title,
            "x": 0.5,
            "xanchor": "center",
            "font": {"size": 16, "weight": "bold"},
        },
        xaxis_title="Date",
        yaxis_title="Portfolio Value (Initial = 100)",
        hovermode="x unified",
        template="plotly_white",
        height=600,
        legend={"yanchor": "top", "y": 0.99, "xanchor": "right", "x": 0.99},
    )

    fig.update_xaxes(showgrid=True, gridwidth=1, gridcolor="rgba(0,0,0,0.1)")
    fig.update_yaxes(showgrid=True, gridwidth=1, gridcolor="rgba(0,0,0,0.1)")

    html = fig.to_html(include_plotlyjs="cdn", full_html=True)

    if output_path:
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(html)

    return html
