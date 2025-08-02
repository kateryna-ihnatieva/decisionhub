from flask import send_file, render_template
from PyPDF2 import PdfReader, PdfWriter
import re
import pdfkit
import os
import tempfile
import plotly.express as px
import plotly.offline as opy
import pandas as pd


# Діаграма
def generate_plot(datas, names, percent=True):
    data = {"Alternatives": names, "Global Priorities": datas}
    df = pd.DataFrame(data)

    # Форматування чисел
    if percent == True:
        df["Global Priorities Formatted"] = df["Global Priorities"].apply(lambda x: f"{x * 100:.2f}%")
    else:
        df["Global Priorities Formatted"] = df["Global Priorities"].apply(
            lambda x: f"{x}" if isinstance(x, int) else f"{x:.3f}")

    # Створення стовбчикової діагарми
    fig = px.bar(df, x="Alternatives", y="Global Priorities", text="Global Priorities Formatted",
                 title="Глобальні пріоритети",
                 labels={"Global Priorities": "Глобальні пріоритети", "Alternatives": "Альтернативи"},
                 hover_data=None)

    fig.update_layout(xaxis=dict(title=None),
                      yaxis=dict(title=None), title=None)

    if percent == True:
        fig.update_layout(yaxis=dict(tickformat=".0%"))

    # Перетворення графіку в HTML
    plot_html = opy.plot(fig, auto_open=False, output_type="div")

    return plot_html


# PDF
def generate_pdf(context, templ):
    # Генеруємо HTML з шаблону та очищуємо його від зайвих стилів
    html_content = render_template(templ, **context)
    html_content = re.sub(r'@media\sprint\s\{.*?\}', '', html_content, flags=re.DOTALL)

    # Добавляем класс pdf-header к заголовку
    html_content = html_content.replace(
        '<header class="p-3 mb-3 border-bottom d-flex justify-content-between align-items-center">',
        '<header class="pdf-header p-3 mb-3 border-bottom d-flex justify-content-between align-items-center">')

    # Створюємо тимчасовий HTML-файл
    with tempfile.NamedTemporaryFile(delete=False, suffix=".html") as temp_html:
        temp_html.write(html_content.encode('utf-8'))

    # Перетворюємо HTML у PDF
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as temp_pdf:
        pdf_options = {
            "enable-local-file-access": "",
            "print-media-type": "",
            "no-background": "",
            "no-images": "",
            "no-header-line": ""
        }
        pdfkit.from_file(temp_html.name, temp_pdf.name, options=pdf_options)

    try:
        # Відкриваємо PDF-файл для підрахунку сторінок
        with open(temp_pdf.name, 'rb') as pdf_file:
            pdf_reader = PdfReader(pdf_file)
            num_pages = len(pdf_reader.pages)

            # Видаляємо зайві сторінки, залишаючи лише необхідну кількість
            if num_pages > 3455:
                output_pdf = PdfWriter()
                for page_num in range(num_pages - 3455):
                    output_pdf.add_page(pdf_reader.pages[page_num])
                with open(temp_pdf.name, 'wb') as output_file:
                    output_pdf.write(output_file)

        # Відправляємо файл користувачу для завантаження
        return send_file(
            temp_pdf.name,
            as_attachment=True,
            download_name="result.pdf",
            mimetype="application/pdf"
        )
    finally:
        # Після завершення роботи видаляємо тимчасові файли
        os.remove(temp_html.name)
        os.remove(temp_pdf.name)


# Функція для додавання об'єкту в базу даних та повернення його ID
def add_object_to_db(db, object_class, **kwargs):
    object_instance = object_class(**kwargs)
    db.session.add(object_instance)
    db.session.commit()
    return object_instance.id
