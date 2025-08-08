import plotly.offline as opy
import pandas as pd
import plotly.graph_objects as go
from typing import List, Optional


def generate_plot(
    datas: List[float],
    names: List[str],
    percent: bool = True,
    title: str = "Глобальні пріоритети",
    color_scheme: str = "modern",
    font_size: int = 13,
    height: int = 550,
    width: Optional[int] = None,
) -> str:
    """
    Generates a modern styled bar chart with enhanced customization options.

    Args:
        datas: List of values to display
        names: List of alternative names
        percent: If True, displays data as percentages
        title: Custom chart title
        color_scheme: Color scheme ('modern', 'vibrant', 'pastel')
        font_size: Base font size for text elements
        height: Chart height in pixels
        width: Chart width in pixels (None for auto-width)

    Returns:
        HTML string containing the chart
    """
    # Input validation
    if not datas or not names or len(datas) != len(names):
        return "<div style='color: #FF6B7D; padding: 20px;'>Помилка: некорректні дані для побудови графіку</div>"

    if len(names) > 20:
        return "<div style='color: #FF6B7D; padding: 20px;'>Помилка: занадто багато альтернатив (максимум 20)</div>"

    # Prepare data
    data = {"Alternatives": names, "Global Priorities": datas}
    df = pd.DataFrame(data)

    # Format values for display
    if percent:
        df["Global Priorities Formatted"] = df["Global Priorities"].apply(
            lambda x: f"{x * 100:.1f}%" if abs(x * 100) >= 0.1 else f"{x * 100:.2f}%"
        )
    else:
        df["Global Priorities Formatted"] = df["Global Priorities"].apply(
            lambda x: f"{x}" if isinstance(x, int) else f"{x:.3f}"
        )

    # Define color schemes
    color_schemes = {
        "modern": [
            "#66FCF1",
            "#8EE4AF",
            "#5CDB95",
            "#4ECDC4",
            "#45B7D1",
            "#96CEB4",
            "#FECA57",
            "#FF9FF3",
            "#54A0FF",
            "#05386B",
        ],
        "vibrant": [
            "#FF2E63",
            "#08D9D6",
            "#FF9F45",
            "#F9ED69",
            "#F08A5D",
            "#B83B5E",
            "#6A2C70",
            "#00B7C2",
            "#4F8A8B",
            "#252A34",
        ],
        "pastel": [
            "#A8DADC",
            "#F4A261",
            "#E76F51",
            "#2A9D8F",
            "#E9C46A",
            "#F4E3B0",
            "#D8A7B1",
            "#B6E2D3",
            "#8ABAD3",
            "#F2E7D5",
        ],
    }

    selected_colors = color_schemes.get(color_scheme, color_schemes["modern"])

    # Create colors for bars
    bar_colors = []
    for i, value in enumerate(datas):
        base_color = selected_colors[i % len(selected_colors)]
        if value < 0:
            hex_color = base_color.lstrip("#")
            rgb = tuple(int(hex_color[i : i + 2], 16) for i in (0, 2, 4))
            bar_colors.append(f"rgba({rgb[0]}, {rgb[1]}, {rgb[2]}, 0.7)")
        else:
            bar_colors.append(base_color)

    # Calculate Y-axis range
    data_min = min(datas)
    data_max = max(datas)

    if percent:
        if data_min < 0:
            max_abs = max(abs(data_min), abs(data_max))
            min_value = -max_abs * 1.1
            max_value = max_abs * 1.1
        else:
            min_value = 0
            max_value = data_max * 1.15
    else:
        range_diff = data_max - data_min
        padding = max(range_diff * 0.1, abs(data_max) * 0.05) if range_diff > 0 else 1
        min_value = data_min - padding
        max_value = data_max + padding

    # Create figure
    fig = go.Figure()

    # Add bars
    fig.add_trace(
        go.Bar(
            x=names,
            y=datas,
            text=df["Global Priorities Formatted"],
            textposition="outside",
            textfont=dict(
                size=font_size,
                color="#EDF5E1",
                family="Inter, -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif",
            ),
            marker=dict(
                color=bar_colors,
                line=dict(color="rgba(102, 252, 241, 0.4)", width=1.5),
                pattern=dict(shape="", bgcolor="rgba(255, 255, 255, 0.03)"),
            ),
            hovertemplate=(
                "<b style='color: #66FCF1;'>%{x}</b><br>"
                "<span style='color: #8EE4AF;'>Значення:</span> %{text}<br>"
                "<span style='color: #8EE4AF;'>Частка:</span> %{y:.3f}<br>"
                "<extra></extra>"
            ),
            hoverlabel=dict(
                bgcolor="rgba(11, 12, 16, 0.95)",
                bordercolor="#66FCF1",
                font=dict(
                    color="#EDF5E1", family="Inter, sans-serif", size=font_size - 1
                ),
            ),
            marker_line_width=1.5,
        )
    )

    # Update layout
    fig.update_layout(
        paper_bgcolor="rgba(11, 12, 16, 0.95)",
        plot_bgcolor="rgba(11, 12, 16, 0.8)",
        margin=dict(l=70, r=60, t=100, b=80),
        height=height,
        width=width,
        title=dict(
            text=f"<b style='color: #66FCF1;'>{title}</b>",
            x=0.5,
            y=0.95,
            xanchor="center",
            yanchor="top",
            font=dict(
                size=font_size + 13,
                color="#66FCF1",
                family="Inter, -apple-system, BlinkMacSystemFont, sans-serif",
            ),
        ),
        xaxis=dict(
            title="",
            tickfont=dict(
                size=font_size - 1, color="#EDF5E1", family="Inter, sans-serif"
            ),
            gridcolor="rgba(102, 252, 241, 0.08)",
            linecolor="rgba(102, 252, 241, 0.3)",
            tickcolor="rgba(102, 252, 241, 0.3)",
            zeroline=False,
            showgrid=False,
            tickangle=-15 if any(len(name) > 12 for name in names) else 0,
        ),
        yaxis=dict(
            title="",
            tickformat=".1%" if percent else ".3f",
            tickfont=dict(
                size=font_size - 2, color="#EDF5E1", family="Inter, sans-serif"
            ),
            gridcolor="rgba(102, 252, 241, 0.12)",
            linecolor="rgba(102, 252, 241, 0.3)",
            tickcolor="rgba(102, 252, 241, 0.3)",
            zeroline=True,
            zerolinecolor="rgba(102, 252, 241, 0.25)",
            zerolinewidth=2,
            range=[min_value, max_value],
            showgrid=True,
        ),
        showlegend=False,
        transition_duration=800,
        transition_easing="cubic-in-out",
        font=dict(
            family="Inter, -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif"
        ),
    )

    # Highlight best alternative
    if datas:
        max_value = max(datas)
        max_indices = [i for i, x in enumerate(datas) if x == max_value]
        for max_idx in max_indices:
            fig.add_shape(
                type="rect",
                x0=max_idx - 0.42,
                y0=min_value,
                x1=max_idx + 0.42,
                y1=max_value if max_value > 0 else 0,
                line=dict(color="rgba(102, 252, 241, 0.4)", width=0),
                fillcolor="rgba(102, 252, 241, 0.06)",
                layer="below",
            )
            fig.add_shape(
                type="rect",
                x0=max_idx - 0.42,
                y0=0 if max_value > 0 else max_value,
                x1=max_idx + 0.42,
                y1=max_value if max_value > 0 else 0,
                line=dict(color="rgba(102, 252, 241, 0.6)", width=2),
                fillcolor="rgba(0, 0, 0, 0)",
                layer="above",
            )

    # Add negative value shading
    if any(x < 0 for x in datas):
        fig.add_shape(
            type="rect",
            x0=-0.5,
            y0=min_value,
            x1=len(names) - 0.5,
            y1=0,
            line=dict(color="rgba(0, 0, 0, 0)", width=0),
            fillcolor="rgba(255, 107, 125, 0.03)",
            layer="below",
        )

    # Configure interactivity
    config = {
        "displayModeBar": True,
        "displaylogo": False,
        "modeBarButtonsToRemove": [
            "zoom2d",
            "pan2d",
            "select2d",
            "lasso2d",
            "zoomIn2d",
            "zoomOut2d",
            "autoScale2d",
            "resetScale2d",
            "hoverClosestCartesian",
            "hoverCompareCartesian",
            "toggleSpikelines",
        ],
        "toImageButtonOptions": {
            "format": "png",
            "filename": "global_priorities_chart",
            "height": height,
            "width": 900 if width is None else width,
            "scale": 2,
        },
        "responsive": True,
    }

    # Generate HTML
    plot_html = opy.plot(
        fig,
        auto_open=False,
        output_type="div",
        config=config,
        include_plotlyjs="cdn",
    )

    # Enhanced HTML wrapper
    enhanced_plot_html = f"""
    <div class="chart-container" style="
        background: rgba(11, 12, 16, 0.85);
        border: 1px solid rgba(102, 252, 241, 0.15);
        border-radius: 25px;
        padding: 25px;
        margin: 30px auto;
        backdrop-filter: blur(20px);
        box-shadow:
            0 25px 50px rgba(0, 0, 0, 0.25),
            0 0 0 1px rgba(102, 252, 241, 0.08),
            inset 0 1px 0 rgba(255, 255, 255, 0.03);
        position: relative;
        overflow: hidden;
        max-width: {width if width else 900}px;
    ">
        <div class="chart-glow" style="
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            height: 2px;
            background: linear-gradient(90deg,
                transparent,
                rgba(102, 252, 241, 0.4),
                rgba(142, 228, 175, 0.4),
                transparent);
        "></div>

        <div class="chart-corner-accent" style="
            position: absolute;
            top: 0;
            right: 0;
            width: 60px;
            height: 60px;
            background: radial-gradient(circle at top right,
                rgba(102, 252, 241, 0.08) 0%,
                transparent 50%);
        "></div>

        {plot_html}

        <style>
            .chart-container .plotly-graph-div {{
                background: transparent !important;
                border-radius: 20px;
            }}
            .chart-container .main-svg {{
                background: transparent !important;
            }}
            .chart-container .modebar {{
                background: rgba(11, 12, 16, 0.9) !important;
                border: 1px solid rgba(102, 252, 241, 0.2) !important;
                border-radius: 10px !important;
                padding: 4px 8px !important;
                backdrop-filter: blur(10px) !important;
            }}
            .chart-container .modebar-btn path {{
                fill: #66FCF1 !important;
                opacity: 0.8 !important;
            }}
            .chart-container .modebar-btn:hover {{
                background: rgba(102, 252, 241, 0.1) !important;
                border-radius: 6px !important;
            }}
            .chart-container .modebar-btn:hover path {{
                opacity: 1 !important;
                filter: drop-shadow(0 0 4px rgba(102, 252, 241, 0.4)) !important;
            }}

            /* Enhanced responsiveness */
            @media (max-width: 768px) {{
                .chart-container {{
                    margin: 20px -10px;
                    border-radius: 20px;
                    padding: 15px;
                    max-width: 100%;
                }}
                .chart-container .plotly-graph-div {{
                    transform: scale(0.95);
                }}
            }}
            @media (max-width: 480px) {{
                .chart-container {{
                    padding: 10px;
                }}
                .chart-container .plotly-graph-div {{
                    transform: scale(0.9);
                }}
            }}
        </style>
    </div>
    """

    return enhanced_plot_html


# Функція для додавання об'єкту в базу даних та повернення його ID
def add_object_to_db(db, object_class, **kwargs):
    object_instance = object_class(**kwargs)
    db.session.add(object_instance)
    db.session.commit()
    return object_instance.id
