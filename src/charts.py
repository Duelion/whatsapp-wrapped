"""
WhatsApp Chat Charts Module

Generates Plotly charts with a modern dark aesthetic.
"""

from typing import TYPE_CHECKING

import pandas as pd
import plotly.graph_objects as go

if TYPE_CHECKING:
    from .analytics import ChatAnalytics

# Modern dark color palette
COLORS = {
    # Backgrounds
    "background": "#09090b",
    "paper": "#18181b",
    "surface": "#1f1f23",
    # Borders & Grid
    "grid": "#27272a",
    "border": "#3f3f46",
    # Text
    "text": "#fafafa",
    "text_secondary": "#a1a1aa",
    "text_muted": "#71717a",
    # Accents
    "blue": "#3b82f6",
    "green": "#22c55e",
    "amber": "#f59e0b",
    "violet": "#8b5cf6",
    "rose": "#f43f5e",
    "cyan": "#06b6d4",
}

# Accent colors for multi-series charts
ACCENT_COLORS = [
    COLORS["blue"],
    COLORS["violet"],
    COLORS["cyan"],
    COLORS["amber"],
    COLORS["green"],
    COLORS["rose"],
]

# Gradient-like color scales
BLUE_GRADIENT = [
    [0, "rgba(59, 130, 246, 0.1)"],
    [0.5, "rgba(59, 130, 246, 0.5)"],
    [1, "rgba(139, 92, 246, 0.9)"],
]


def get_modern_layout(
    title: str = "",
    xaxis_title: str = "",
    yaxis_title: str = "",
    height: int = 400,
    show_legend: bool = True,
) -> dict:
    """Get the base Plotly layout with modern dark aesthetic."""
    return {
        "template": "plotly_dark",
        "paper_bgcolor": COLORS["paper"],
        "plot_bgcolor": COLORS["background"],
        "font": {
            "family": "Geist, -apple-system, BlinkMacSystemFont, sans-serif",
            "color": COLORS["text"],
            "size": 12,
        },
        "title": {
            "text": title if title else "",
            "font": {"size": 14, "color": COLORS["text_secondary"]},
            "x": 0.02,
            "xanchor": "left",
            "y": 0.98,
            "yanchor": "top",
        },
        "xaxis": {
            "title": xaxis_title,
            "gridcolor": COLORS["grid"],
            "linecolor": COLORS["grid"],
            "tickfont": {"color": COLORS["text_muted"], "size": 11},
            "title_font": {"color": COLORS["text_secondary"], "size": 12},
            "showgrid": True,
            "gridwidth": 1,
            "zeroline": False,
        },
        "yaxis": {
            "title": yaxis_title,
            "gridcolor": COLORS["grid"],
            "linecolor": COLORS["grid"],
            "tickfont": {"color": COLORS["text_muted"], "size": 11},
            "title_font": {"color": COLORS["text_secondary"], "size": 12},
            "showgrid": True,
            "gridwidth": 1,
            "zeroline": False,
        },
        "height": height,
        "margin": {"l": 65, "r": 35, "t": 50, "b": 55},
        "showlegend": show_legend,
        "legend": {
            "bgcolor": "rgba(0,0,0,0)",
            "font": {"color": COLORS["text_muted"], "size": 11},
            "orientation": "h",
            "yanchor": "bottom",
            "y": 1.02,
            "xanchor": "left",
            "x": 0,
        },
        "hoverlabel": {
            "bgcolor": COLORS["surface"],
            "bordercolor": COLORS["border"],
            "font": {"color": COLORS["text"], "size": 12},
        },
    }


def chart_to_html(fig: go.Figure, include_plotlyjs: bool = False) -> str:
    """Convert a Plotly figure to an HTML div string."""
    return fig.to_html(
        include_plotlyjs="cdn" if include_plotlyjs else False,
        full_html=False,
        div_id=None,
        config={
            "displayModeBar": False,
            "responsive": True,
        },
    )


def create_messages_by_hour_chart(messages_by_hour: pd.Series) -> go.Figure:
    """Create a bar chart showing message distribution by hour with gradient colors."""
    hours = list(range(24))
    values = [messages_by_hour.get(h, 0) for h in hours]

    total = sum(values) if values else 1
    percentages = [(v / total * 100) for v in values]

    # Create gradient from blue (#3b82f6) to cyan (#06b6d4) based on hour position
    n = len(hours)
    colors = []
    for i in range(n):
        ratio = i / max(n - 1, 1)
        # Interpolate: blue (59, 130, 246) -> cyan (6, 182, 212)
        r = int(59 + (6 - 59) * ratio)
        g = int(130 + (182 - 130) * ratio)
        b = int(246 + (212 - 246) * ratio)
        colors.append(f"rgb({r}, {g}, {b})")

    fig = go.Figure()

    fig.add_trace(
        go.Bar(
            x=hours,
            y=values,
            marker={"color": colors, "line": {"width": 0}},
            customdata=percentages,
            hovertemplate="<b>%{x}:00</b>: %{y:,} msgs (%{customdata:.1f}%)<extra></extra>",
        )
    )

    layout = get_modern_layout(
        title="",  # No title - will be added in HTML
        xaxis_title="Hour",
        yaxis_title="Messages",
        show_legend=False,
    )
    layout["xaxis"]["tickmode"] = "array"
    layout["xaxis"]["tickvals"] = list(range(0, 24, 3))
    layout["xaxis"]["ticktext"] = ["12am", "3am", "6am", "9am", "12pm", "3pm", "6pm", "9pm"]
    layout["bargap"] = 0.15

    fig.update_layout(**layout)

    return fig


def create_messages_by_weekday_chart(messages_by_weekday: pd.Series) -> go.Figure:
    """Create a bar chart showing message distribution by day of week with gradient colors."""
    days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    short_days = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
    values = [messages_by_weekday.get(d, 0) for d in days]

    total = sum(values) if values else 1
    percentages = [(v / total * 100) for v in values]

    # Create gradient from violet (#8b5cf6) to rose (#f43f5e) based on day position
    n = len(days)
    colors = []
    for i in range(n):
        ratio = i / max(n - 1, 1)
        # Interpolate: violet (139, 92, 246) -> rose (244, 63, 94)
        r = int(139 + (244 - 139) * ratio)
        g = int(92 + (63 - 92) * ratio)
        b = int(246 + (94 - 246) * ratio)
        colors.append(f"rgb({r}, {g}, {b})")

    fig = go.Figure()

    fig.add_trace(
        go.Bar(
            x=short_days,
            y=values,
            marker={"color": colors, "line": {"width": 0}},
            customdata=percentages,
            hovertemplate="<b>%{x}</b>: %{y:,} msgs (%{customdata:.1f}%)<extra></extra>",
        )
    )

    layout = get_modern_layout(
        title="",  # No title - will be added in HTML
        xaxis_title="Day",
        yaxis_title="Messages",
        show_legend=False,
    )
    layout["bargap"] = 0.25

    fig.update_layout(**layout)

    return fig


def create_timeline_chart(messages_by_date: pd.Series) -> go.Figure:
    """Create a smoothed area chart showing message trend over time."""
    dates = pd.to_datetime(messages_by_date.index)
    values = messages_by_date.values

    # Apply 3-day centered rolling average for smoothing (matches sparklines)
    rolling_avg = pd.Series(values).rolling(window=3, min_periods=1, center=True).mean()

    fig = go.Figure()

    # Single smoothed line with area fill, hover shows actual daily value
    fig.add_trace(
        go.Scatter(
            x=dates,
            y=rolling_avg,
            fill="tozeroy",
            fillcolor="rgba(59, 130, 246, 0.1)",
            line={"color": COLORS["blue"], "width": 2},
            mode="lines",
            name="Trend",
            customdata=values,  # Store actual daily values for hover
            hovertemplate="<b>%{x|%b %d}</b>: %{customdata:,} msgs<extra></extra>",
        )
    )

    layout = get_modern_layout(
        title="",  # No title - will be added in HTML
        xaxis_title="",  # Remove axis title - months are self-explanatory
        yaxis_title="Messages",
        height=350,
        show_legend=False,  # Single trace, no legend needed
    )

    # Generate month ticks for the date range
    min_date = dates.min()
    max_date = dates.max()

    # Create tick values for the 1st of each month in the range
    month_ticks = pd.date_range(
        start=min_date.replace(day=1),
        end=max_date,
        freq="MS",  # Month Start
    )

    # Format as abbreviated month names (Jan, Feb, etc.)
    tick_labels = [d.strftime("%b") for d in month_ticks]

    # Update x-axis with month ticks, slanted for readability
    layout["xaxis"]["tickmode"] = "array"
    layout["xaxis"]["tickvals"] = month_ticks
    layout["xaxis"]["ticktext"] = tick_labels
    layout["xaxis"]["tickangle"] = -45  # Slant for better fit
    layout["margin"]["b"] = 70  # Extra bottom margin for slanted labels

    fig.update_layout(**layout)

    return fig


def create_top_users_chart(top_messagers: list[tuple[str, int]]) -> go.Figure:
    """Create a stylish horizontal bar chart with gradient colors."""
    users = [u[0] for u in top_messagers]
    counts = [u[1] for u in top_messagers]

    total = sum(counts) if counts else 1
    percentages = [(c / total * 100) for c in counts]

    # Reverse for horizontal bar (bottom to top)
    users = users[::-1]
    counts = counts[::-1]
    percentages = percentages[::-1]

    n = len(users)

    # Create gradient colors from blue to violet based on position
    colors = []
    for i in range(n):
        ratio = i / max(n - 1, 1)
        # Interpolate between blue (#3b82f6) and violet (#8b5cf6)
        r = int(59 + (139 - 59) * ratio)
        g = int(130 + (92 - 130) * ratio)
        b = 246  # Both colors have same blue component
        colors.append(f"rgb({r}, {g}, {b})")

    fig = go.Figure()

    fig.add_trace(
        go.Bar(
            x=counts,
            y=users,
            orientation="h",
            marker={
                "color": colors,
                "line": {"width": 0},
            },
            text=[f"{c:,} ({p:.1f}%)" for c, p in zip(counts, percentages, strict=False)],
            textposition="outside",
            textfont={"color": COLORS["text_muted"], "size": 10},
            customdata=percentages,
            hovertemplate="<b>%{y}</b>: %{x:,} msgs (%{customdata:.1f}%)<extra></extra>",
        )
    )

    layout = get_modern_layout(
        title="",  # No title - will be added in HTML
        xaxis_title="Messages",
        yaxis_title="",
        height=50 + 45 * len(users),
        show_legend=False,
    )
    layout["margin"]["l"] = 140
    layout["margin"]["r"] = 80  # More space for percentage labels
    layout["bargap"] = 0.3

    fig.update_layout(**layout)

    return fig


def create_message_types_chart(message_type_counts: pd.Series) -> go.Figure:
    """Create a modern donut chart of message type distribution."""
    # Sort by count descending
    data = message_type_counts.sort_values(ascending=False)

    labels = [label.title() for label in data.index.tolist()]
    values = data.values.tolist()
    total = sum(values)

    # Calculate percentages for conditional display
    percentages = [(v / total * 100) for v in values]

    # Create a vibrant color palette for different message types
    n = len(labels)
    colors = [
        COLORS["blue"],
        COLORS["violet"],
        COLORS["cyan"],
        COLORS["amber"],
        COLORS["green"],
        COLORS["rose"],
    ]
    # Extend color list if needed
    while len(colors) < n:
        colors.extend(ACCENT_COLORS)
    colors = colors[:n]

    # Pull effect for largest slice (emphasis)
    pull = [0.03 if i == 0 else 0 for i in range(n)]

    # Custom text: only show percentage for slices > 5%
    text_labels = [f"{p:.1f}%" if p >= 5 else "" for p in percentages]

    fig = go.Figure()

    fig.add_trace(
        go.Pie(
            labels=labels,
            values=values,
            hole=0.45,  # Slightly smaller donut hole
            pull=pull,
            marker_colors=colors,
            marker_line_color=COLORS["background"],
            marker_line_width=2,
            textposition="inside",
            textinfo="text",
            text=text_labels,
            insidetextorientation="radial",
            textfont={"color": COLORS["text"], "size": 12, "family": "Geist, sans-serif"},
            hovertemplate="<b>%{label}</b>: %{value:,} (%{percent})<extra></extra>",
        )
    )

    fig.update_layout(
        template="plotly_dark",
        paper_bgcolor=COLORS["paper"],
        plot_bgcolor=COLORS["background"],
        font={
            "family": "Geist, -apple-system, BlinkMacSystemFont, sans-serif",
            "color": COLORS["text"],
            "size": 12,
        },
        height=400,
        margin={"l": 35, "r": 120, "t": 30, "b": 35},
        showlegend=True,
        legend={
            "bgcolor": "rgba(0,0,0,0)",
            "font": {"color": COLORS["text_muted"], "size": 11},
            "orientation": "v",
            "yanchor": "middle",
            "y": 0.5,
            "xanchor": "left",
            "x": 1.02,
        },
        hoverlabel={
            "bgcolor": COLORS["surface"],
            "bordercolor": COLORS["border"],
            "font": {"color": COLORS["text"], "size": 12},
        },
    )

    return fig


def create_hourly_heatmap(hourly_activity_by_user: pd.DataFrame, max_users: int = 15) -> go.Figure:
    """Create a heatmap showing activity by user and hour."""
    # Select top users by total messages
    user_totals = hourly_activity_by_user.sum(axis=1).sort_values(ascending=False)
    top_users = user_totals.head(max_users).index
    data = hourly_activity_by_user.loc[top_users]

    # Normalize per user for better visualization
    data_normalized = data.div(data.max(axis=1), axis=0).fillna(0)

    # Create customdata with absolute values
    customdata = data.values

    fig = go.Figure()

    fig.add_trace(
        go.Heatmap(
            z=data_normalized.values,
            x=list(range(24)),
            y=data.index.tolist(),
            colorscale=[
                [0, COLORS["background"]],
                [0.3, "rgba(59, 130, 246, 0.3)"],
                [0.6, "rgba(59, 130, 246, 0.6)"],
                [1, COLORS["violet"]],
            ],
            showscale=False,
            customdata=customdata,
            hovertemplate="<b>%{y}</b> @ %{x}:00: %{customdata} msgs<extra></extra>",
            xgap=3,  # Add gap between cells
            ygap=3,
        )
    )

    # Calculate height to maintain square cells
    # 24 hours * cell_size, where cell_size should match y-axis spacing
    height = max(300, 80 + 30 * len(top_users))  # Increased cell height for squares

    layout = get_modern_layout(
        title="Activity by User & Hour",
        xaxis_title="Hour",
        yaxis_title="",
        height=height,
        show_legend=False,
    )
    layout["xaxis"]["tickmode"] = "array"
    layout["xaxis"]["tickvals"] = list(range(0, 24, 3))
    layout["xaxis"]["ticktext"] = ["12am", "3am", "6am", "9am", "12pm", "3pm", "6pm", "9pm"]
    layout["margin"]["l"] = 120

    # Force square cells
    layout["yaxis"]["scaleanchor"] = "x"
    layout["yaxis"]["scaleratio"] = 1

    fig.update_layout(**layout)

    return fig


def create_monthly_chart(messages_by_month: pd.Series) -> go.Figure:
    """Create a bar chart showing messages by month."""
    months = messages_by_month.index.tolist()
    values = messages_by_month.values.tolist()

    total = sum(values) if values else 1
    percentages = [(v / total * 100) for v in values]

    # Create gradient based on values
    max_val = max(values) if values else 1
    colors = [f"rgba(139, 92, 246, {0.4 + 0.6 * (v / max_val)})" for v in values]

    fig = go.Figure()

    fig.add_trace(
        go.Bar(
            x=months,
            y=values,
            marker_color=colors,
            marker_line_width=0,
            customdata=percentages,
            hovertemplate="<b>%{x}</b>: %{y:,} msgs (%{customdata:.1f}%)<extra></extra>",
        )
    )

    layout = get_modern_layout(
        title="Monthly Volume",
        xaxis_title="Month",
        yaxis_title="Messages",
        height=300,
        show_legend=False,
    )
    layout["bargap"] = 0.2

    fig.update_layout(**layout)

    return fig


def create_calendar_heatmap(messages_by_date: pd.Series) -> go.Figure:
    """Create a calendar heatmap showing daily message activity in a calendar grid format."""
    from plotly_calplot import calplot

    if len(messages_by_date) == 0:
        # Return empty figure if no data
        fig = go.Figure()
        fig.update_layout(**get_modern_layout(title="", height=290))
        return fig

    # Prepare data as a DataFrame with date and value columns
    df = pd.DataFrame(
        {"date": pd.to_datetime(messages_by_date.index), "value": messages_by_date.values}
    )

    # Create the calendar heatmap using plotly-calplot
    # Optimized for single-year display
    fig = calplot(
        df,
        x="date",
        y="value",
        years_title=False,
        gap=5,  # Increased gap for better visual separation
        name="Messages",
        month_lines_width=2,
        month_lines_color=COLORS["border"],
        colorscale=[
            [0, COLORS["background"]],
            [0.1, "rgba(59, 130, 246, 0.2)"],  # More visible low values
            [0.3, "rgba(59, 130, 246, 0.5)"],
            [0.6, "rgba(59, 130, 246, 0.8)"],
            [0.8, COLORS["blue"]],
            [1, COLORS["violet"]],
        ],
        showscale=False,
        dark_theme=True,  # Enable dark theme if available
    )

    # Apply dark theme styling to match other charts
    fig.update_layout(
        paper_bgcolor=COLORS["paper"],
        plot_bgcolor=COLORS["background"],
        font={
            "family": "Geist, -apple-system, BlinkMacSystemFont, sans-serif",
            "color": COLORS["text"],
            "size": 12,
        },
        title="",  # Remove title - section header already provides context
        height=220,  # Compact height - 7 days don't need much vertical space
        margin={"l": 50, "r": 20, "t": 30, "b": 40},  # Minimal margins
        hoverlabel={
            "bgcolor": COLORS["surface"],
            "bordercolor": COLORS["border"],
            "font": {"color": COLORS["text"], "size": 12},
        },
    )

    # Update all xaxis and yaxis to match dark theme with better readability
    for key in fig.layout:
        if key.startswith("xaxis") or key.startswith("yaxis"):
            axis = fig.layout[key]
            if axis:
                axis.update(
                    gridcolor=COLORS["grid"],
                    linecolor=COLORS["grid"],
                    tickfont={"color": COLORS["text_secondary"], "size": 10},
                    title_font={"color": COLORS["text_secondary"], "size": 11},
                )

    # Customize hover template for cleaner tooltips
    for trace in fig.data:
        if hasattr(trace, "hovertemplate"):
            # Replace the default ugly tooltip with a clean one
            trace.hovertemplate = "<b>%{x|%b %d}</b>: %{z} msgs<extra></extra>"

    return fig


def create_emoji_chart(top_emojis: list[tuple[str, int]], max_emojis: int = 10) -> go.Figure:
    """Create a horizontal bar chart of top emojis with colored ranking labels."""
    emojis = [e[0] for e in top_emojis[:max_emojis]]
    counts = [e[1] for e in top_emojis[:max_emojis]]

    # Colors for ranking numbers (matching medal theme + gradient for rest)
    rank_colors_map = {
        1: "#FFD700",  # Gold
        2: "#C0C0C0",  # Silver
        3: "#CD7F32",  # Bronze
        4: "#f43f5e",  # Rose
        5: "#f59e0b",  # Amber
        6: "#22c55e",  # Green
        7: "#06b6d4",  # Cyan
        8: "#8b5cf6",  # Violet
        9: "#ec4899",  # Pink
        10: "#14b8a6",  # Teal
    }

    # Create ranking labels with medals for top 3
    rankings = []
    rank_medals = []
    rank_colors = []
    for i in range(1, len(emojis) + 1):
        if i == 1:
            rank = "1st"
            medal = "🥇"
        elif i == 2:
            rank = "2nd"
            medal = "🥈"
        elif i == 3:
            rank = "3rd"
            medal = "🥉"
        else:
            rank = f"{i}th"
            medal = f"#{i}"
        rankings.append(rank)
        rank_medals.append(medal)
        rank_colors.append(rank_colors_map.get(i, COLORS["text_muted"]))

    # Reverse for horizontal bar (bottom to top = 10th to 1st)
    emojis = emojis[::-1]
    counts = counts[::-1]
    rankings = rankings[::-1]
    rank_medals = rank_medals[::-1]
    rank_colors = rank_colors[::-1]

    # Create gradient based on position (lighter at bottom, brighter at top)
    n = len(emojis)
    colors = [f"rgba(245, 158, 11, {0.4 + 0.6 * (i / max(n - 1, 1))})" for i in range(n)]

    # Create y-axis labels with just emojis (ranks will be added via annotations)
    y_labels = list(range(n))  # Use numeric positions for precise annotation placement

    fig = go.Figure()

    fig.add_trace(
        go.Bar(
            x=counts,
            y=y_labels,
            orientation="h",
            marker_color=colors,
            marker_line_width=0,
            text=[f"{c:,}" for c in counts],
            textposition="outside",
            textfont={"color": COLORS["text_muted"], "size": 11},
            hovertemplate="%{customdata[1]} %{customdata[0]}: %{x:,} uses<extra></extra>",
            customdata=[[rank, emoji] for rank, emoji in zip(rankings, emojis, strict=False)],
        )
    )

    # Add colored annotations for rankings
    annotations = []
    for i, (medal, emoji, color) in enumerate(zip(rank_medals, emojis, rank_colors, strict=False)):
        annotations.append(
            {
                "x": 0,
                "y": i,
                "xref": "paper",
                "yref": "y",
                "text": f"<b>{medal}</b> {emoji}",
                "showarrow": False,
                "font": {"size": 16, "color": color},
                "xanchor": "right",
                "xshift": -10,
            }
        )

    layout = get_modern_layout(
        title="",  # No title - will be added in HTML
        xaxis_title="Count",
        yaxis_title="",
        height=50 + 38 * len(emojis),
        show_legend=False,
    )
    layout["yaxis"]["tickfont"] = {"size": 16}
    layout["yaxis"]["showticklabels"] = False  # Hide numeric y labels
    layout["margin"]["l"] = 90
    layout["margin"]["t"] = 30
    layout["annotations"] = annotations

    fig.update_layout(**layout)

    return fig


def create_user_sparkline(daily_activity: pd.Series, user_name: str) -> go.Figure:
    """Create a minimal sparkline chart for user activity over time."""
    # Fill missing dates with 0
    if len(daily_activity) == 0:
        return go.Figure()

    dates = pd.to_datetime(daily_activity.index)
    values = daily_activity.values

    # Apply 3-day rolling average for smoothing
    rolling_avg = pd.Series(values).rolling(window=3, min_periods=1, center=True).mean()

    fig = go.Figure()

    fig.add_trace(
        go.Scatter(
            x=dates,
            y=rolling_avg,
            mode="lines",
            line={
                "color": COLORS["blue"],
                "width": 2,
            },
            fill="tozeroy",
            fillcolor="rgba(59, 130, 246, 0.1)",
            hovertemplate="<b>%{x|%b %d}</b>: %{y:.0f} msgs<extra></extra>",
        )
    )

    # Get start and end months for minimal x-axis labels
    start_month = dates.min().strftime("%b")
    end_month = dates.max().strftime("%b")

    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        height=65,  # Very minimal height like a stock ticker
        margin={"l": 0, "r": 0, "t": 0, "b": 20},
        xaxis={
            "visible": True,
            "showgrid": False,
            "zeroline": False,
            "showticklabels": True,
            "tickmode": "array",
            "tickvals": [dates.min(), dates.max()],
            "ticktext": [start_month, end_month],
            "tickfont": {"color": COLORS["text_muted"], "size": 9},
            "side": "bottom",
        },
        yaxis={
            "visible": False,
            "showgrid": False,
            "zeroline": False,
        },
        showlegend=False,
        hovermode="closest",
    )

    return fig


def create_user_hourly_sparkline(hourly_activity: pd.Series, user_name: str) -> go.Figure:
    """Create a minimal bar sparkline chart showing hourly activity pattern (0-23)."""
    if len(hourly_activity) == 0:
        return go.Figure()

    hours = list(range(24))
    values = [hourly_activity.get(h, 0) for h in hours]

    # Create gradient-like effect with varying opacity
    max_val = max(values) if max(values) > 0 else 1
    colors = [f"rgba(139, 92, 246, {0.3 + 0.7 * (v / max_val)})" for v in values]

    fig = go.Figure()

    fig.add_trace(
        go.Bar(
            x=hours,
            y=values,
            marker_color=colors,
            marker_line_width=0,
            hovertemplate="<b>%{x}:00</b>: %{y} msgs<extra></extra>",
        )
    )

    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        height=65,
        margin={"l": 0, "r": 0, "t": 0, "b": 20},
        xaxis={
            "visible": True,
            "showgrid": False,
            "zeroline": False,
            "showticklabels": True,
            "tickmode": "array",
            "tickvals": [12],
            "ticktext": ["12pm"],
            "tickfont": {"color": COLORS["text_muted"], "size": 9},
            "side": "bottom",
        },
        yaxis={
            "visible": False,
            "showgrid": False,
            "zeroline": False,
        },
        showlegend=False,
        bargap=0.1,
    )

    return fig


def create_wordcloud_chart(
    word_frequencies: "pd.Series",
    width: int = 1200,
    height: int = 500,
    max_words: int = 150,
) -> str:
    """
    Create a word cloud visualization as a base64-encoded PNG.

    Uses the project's dark aesthetic with accent colors.

    Args:
        word_frequencies: pd.Series with words as index, counts as values
        width: Image width in pixels
        height: Image height in pixels
        max_words: Maximum number of words to display

    Returns:
        Base64-encoded PNG string (data URI format) or empty string if no data
    """
    import base64
    import random
    from io import BytesIO

    from wordcloud import WordCloud

    if word_frequencies is None or len(word_frequencies) == 0:
        return ""

    # Convert Series to dict for wordcloud
    freq_dict = word_frequencies.head(max_words * 2).to_dict()  # Get extra for filtering

    if not freq_dict:
        return ""

    # Accent colors from the theme (matching ACCENT_COLORS)
    wordcloud_colors = [
        "#3b82f6",  # blue
        "#8b5cf6",  # violet
        "#06b6d4",  # cyan
        "#f59e0b",  # amber
        "#22c55e",  # green
        "#f43f5e",  # rose
    ]

    def color_func(word, font_size, position, orientation, random_state=None, **kwargs):
        """Custom color function using theme accent colors."""
        return random.choice(wordcloud_colors)

    # Create word cloud with dark background
    wc = WordCloud(
        width=width,
        height=height,
        background_color=COLORS["background"],  # #09090b
        color_func=color_func,
        max_words=max_words,
        min_font_size=12,
        max_font_size=120,
        prefer_horizontal=0.8,
        relative_scaling=0.5,
        margin=10,
        mode="RGB",
    )

    # Generate the word cloud
    wc.generate_from_frequencies(freq_dict)

    # Convert to base64 PNG
    buffer = BytesIO()
    wc.to_image().save(buffer, format="PNG", optimize=True)
    buffer.seek(0)
    img_base64 = base64.b64encode(buffer.read()).decode("utf-8")

    return f"data:image/png;base64,{img_base64}"


class ChartCollection:
    """Collection of all charts for a report."""

    def __init__(self, analytics: "ChatAnalytics"):
        """
        Generate all charts from analytics data.

        Args:
            analytics: ChatAnalytics object
        """
        self.messages_by_hour = create_messages_by_hour_chart(analytics.messages_by_hour)
        self.messages_by_weekday = create_messages_by_weekday_chart(analytics.messages_by_weekday)
        self.timeline = create_timeline_chart(analytics.messages_by_date)
        self.top_users = create_top_users_chart(analytics.top_messagers)
        self.message_types = create_message_types_chart(analytics.message_type_counts)
        self.hourly_heatmap = create_hourly_heatmap(analytics.hourly_activity_by_user)
        self.monthly = create_monthly_chart(analytics.messages_by_month)
        self.calendar_heatmap = create_calendar_heatmap(analytics.messages_by_date)

        if analytics.top_emojis_overall:
            self.emojis = create_emoji_chart(analytics.top_emojis_overall)
        else:
            self.emojis = None

        # Word cloud (returns base64 PNG data URI, not Plotly)
        self.wordcloud = create_wordcloud_chart(analytics.word_frequencies)

    def to_html_dict(self, include_plotlyjs_first: bool = True) -> dict[str, str]:
        """Convert all charts to HTML divs."""
        # top_users is the first chart in the document (in "The Voices Behind the Chat" section)
        charts = {
            "top_users": chart_to_html(self.top_users, include_plotlyjs_first),
            "messages_by_hour": chart_to_html(self.messages_by_hour, False),
            "messages_by_weekday": chart_to_html(self.messages_by_weekday, False),
            "timeline": chart_to_html(self.timeline, False),
            "message_types": chart_to_html(self.message_types, False),
            "hourly_heatmap": chart_to_html(self.hourly_heatmap, False),
            "monthly": chart_to_html(self.monthly, False),
            "calendar_heatmap": chart_to_html(self.calendar_heatmap, False),
        }

        if self.emojis:
            charts["emojis"] = chart_to_html(self.emojis, False)
        else:
            charts["emojis"] = ""

        # Word cloud is already a base64 data URI, wrap in img tag
        if self.wordcloud:
            charts["wordcloud"] = (
                f'<img src="{self.wordcloud}" alt="Word Cloud" style="width: 100%; height: auto; border-radius: var(--radius-md);">'
            )
        else:
            charts["wordcloud"] = ""

        return charts
