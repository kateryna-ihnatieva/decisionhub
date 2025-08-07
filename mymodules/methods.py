from flask import render_template
import plotly.express as px
import plotly.offline as opy
import pandas as pd
import plotly.graph_objects as go


# Діаграма
def generate_plot(datas, names, percent=True):
    data = {"Alternatives": names, "Global Priorities": datas}
    df = pd.DataFrame(data)

    if percent:
        df["Global Priorities Formatted"] = df["Global Priorities"].apply(
            lambda x: f"{x * 100:.2f}%"
        )
        max_value = max(datas) * 1.1  # Добавляем отступ сверху
    else:
        df["Global Priorities Formatted"] = df["Global Priorities"].apply(
            lambda x: f"{x}" if isinstance(x, int) else f"{x:.3f}"
        )
        max_value = max(datas) * 1.1

    # Цветовая палитра в стиле приложения
    colors = [
        "#66FCF1",  # color-accent
        "#8EE4AF",  # color-link
        "#5CDB95",  # color-link-hover
        "#05386B",  # color-accent-dark
        "#4ECDC4",  # дополнительный оттенок
        "#45B7D1",  # дополнительный оттенок
        "#96CEB4",  # дополнительный оттенок
        "#FECA57",  # дополнительный оттенок
        "#FF9FF3",  # дополнительный оттенок
        "#54A0FF",  # дополнительный оттенок
    ]

    # Создание градиентных цветов для каждой альтернативы
    bar_colors = []
    for i, value in enumerate(datas):
        base_color = colors[i % len(colors)]
        bar_colors.append(base_color)

    # Создание современного графика
    fig = go.Figure()
    # Добавление столбцов с градиентом и эффектами
    fig.add_trace(
        go.Bar(
            x=names,
            y=datas,
            text=df["Global Priorities Formatted"],
            textposition="outside",
            textfont=dict(
                size=14,
                color="#EDF5E1",
                family="Inter, Segoe UI, sans-serif",
            ),
            marker=dict(
                color=bar_colors,
                line=dict(color="rgba(102, 252, 241, 0.3)", width=2),
                # Добавляем эффект свечения через паттерн
                pattern=dict(shape="", bgcolor="rgba(102, 252, 241, 0.1)"),
            ),
            hovertemplate=(
                "<b>%{x}</b><br>" + "Пріоритет: %{text}<br>" + "<extra></extra>"
            ),
            hoverlabel=dict(
                bgcolor="rgba(11, 12, 16, 0.9)",
                bordercolor="#66FCF1",
                font=dict(color="#EDF5E1", family="Inter, sans-serif", size=12),
            ),
        )
    )

    # Настройка макета в стиле приложения
    fig.update_layout(
        # Фон и цвета
        paper_bgcolor="#0B0C10",
        plot_bgcolor="rgba(11, 12, 16, 0.8)",
        # Отступы и размеры
        margin=dict(l=60, r=60, t=80, b=80),
        height=500,
        # Заголовок
        title=dict(
            text="<b>Глобальні пріоритети</b>",
            x=0.5,
            y=0.95,
            font=dict(
                size=24,
                color="#66FCF1",
                family="Inter, Segoe UI, sans-serif",
            ),
        ),
        # Настройка осей
        xaxis=dict(
            title="",
            tickfont=dict(size=13, color="#EDF5E1", family="Inter, sans-serif"),
            gridcolor="rgba(102, 252, 241, 0.1)",
            linecolor="rgba(102, 252, 241, 0.3)",
            tickcolor="rgba(102, 252, 241, 0.3)",
            zeroline=False,
        ),
        yaxis=dict(
            title="",
            tickfont=dict(size=12, color="#EDF5E1", family="Inter, sans-serif"),
            gridcolor="rgba(102, 252, 241, 0.1)",
            linecolor="rgba(102, 252, 241, 0.3)",
            tickcolor="rgba(102, 252, 241, 0.3)",
            zeroline=True,
            zerolinecolor="rgba(102, 252, 241, 0.2)",
            range=[0, max_value],
        ),
        # Убираем легенду
        showlegend=False,
        # Настройка сетки
        xaxis_showgrid=False,
        yaxis_showgrid=True,
        # Анимация при загрузке
        transition_duration=500,
        # Настройка области графика
        # plot_bgcolor="transparent",
    )

    # Форматирование оси Y для процентов
    if percent:
        fig.update_layout(
            yaxis=dict(
                tickformat=".0%",
                tickfont=dict(size=12, color="#EDF5E1", family="Inter, sans-serif"),
                gridcolor="rgba(102, 252, 241, 0.1)",
                linecolor="rgba(102, 252, 241, 0.3)",
                tickcolor="rgba(102, 252, 241, 0.3)",
                zeroline=True,
                zerolinecolor="rgba(102, 252, 241, 0.2)",
                range=[0, max_value],
            )
        )

    # Добавление декоративных элементов
    # Подсветка для лучшей альтернативы
    if datas:
        max_idx = datas.index(max(datas))
        fig.add_shape(
            type="rect",
            x0=max_idx - 0.4,
            y0=0,
            x1=max_idx + 0.4,
            y1=max(datas),
            line=dict(
                color="rgba(102, 252, 241, 0.6)",
                width=3,
            ),
            fillcolor="rgba(102, 252, 241, 0.05)",
            layer="below",
        )

    # Настройка конфигурации графика
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
            "height": 500,
            "width": 800,
            "scale": 2,
        },
    }

    # Преобразование графика в HTML с улучшенными настройками
    plot_html = opy.plot(
        fig,
        auto_open=False,
        output_type="div",
        config=config,
        # div_id="priorities-chart",
        include_plotlyjs="cdn",
    )

    # Добавляем CSS стили для интеграции с приложением
    enhanced_plot_html = f"""
    <div class="chart-container" style="
        background: rgba(11, 12, 16, 0.8);
        border: 1px solid rgba(102, 252, 241, 0.2);
        border-radius: 20px;
        padding: 20px;
        margin: 20px 0;
        backdrop-filter: blur(15px);
        box-shadow: 0 20px 40px rgba(0, 0, 0, 0.3),
                    0 0 0 1px rgba(102, 252, 241, 0.1),
                    inset 0 1px 0 rgba(255, 255, 255, 0.05);
        position: relative;
        overflow: hidden;
    ">
        <div class="chart-header" style="
            text-align: center;
            margin-bottom: 15px;
        ">
            <div class="chart-glow" style="
                position: absolute;
                top: 0;
                left: 0;
                right: 0;
                height: 2px;
                background: linear-gradient(90deg,
                    transparent,
                    rgba(102, 252, 241, 0.5),
                    rgba(142, 228, 175, 0.5),
                    transparent);
            "></div>
        </div>
        {plot_html}
        <style>
            .chart-container .plotly-graph-div {{
                background: transparent !important;
            }}
            .chart-container .main-svg {{
                background: transparent !important;
            }}
            .chart-container .modebar {{
                background: rgba(11, 12, 16, 0.9) !important;
                border-radius: 8px !important;
                border: 1px solid rgba(102, 252, 241, 0.2) !important;
            }}
            .chart-container .modebar-btn path {{
                fill: #66FCF1 !important;
            }}
            .chart-container .modebar-btn:hover {{
                background: rgba(102, 252, 241, 0.1) !important;
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
