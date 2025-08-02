from flask import render_template
import plotly.express as px
import plotly.offline as opy
import pandas as pd


# Діаграма
def generate_plot(datas, names, percent=True):
    data = {"Alternatives": names, "Global Priorities": datas}
    df = pd.DataFrame(data)

    # Форматування чисел
    if percent == True:
        df["Global Priorities Formatted"] = df["Global Priorities"].apply(
            lambda x: f"{x * 100:.2f}%"
        )
    else:
        df["Global Priorities Formatted"] = df["Global Priorities"].apply(
            lambda x: f"{x}" if isinstance(x, int) else f"{x:.3f}"
        )

    # Створення стовбчикової діагарми
    fig = px.bar(
        df,
        x="Alternatives",
        y="Global Priorities",
        text="Global Priorities Formatted",
        title="Глобальні пріоритети",
        labels={
            "Global Priorities": "Глобальні пріоритети",
            "Alternatives": "Альтернативи",
        },
        hover_data=None,
    )

    fig.update_layout(xaxis=dict(title=None), yaxis=dict(title=None), title=None)

    if percent == True:
        fig.update_layout(yaxis=dict(tickformat=".0%"))

    # Перетворення графіку в HTML
    plot_html = opy.plot(fig, auto_open=False, output_type="div")

    return plot_html


# Функція для додавання об'єкту в базу даних та повернення його ID
def add_object_to_db(db, object_class, **kwargs):
    object_instance = object_class(**kwargs)
    db.session.add(object_instance)
    db.session.commit()
    return object_instance.id
