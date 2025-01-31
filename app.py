from flask import Flask, request, jsonify
from PIL import Image
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader
from datetime import datetime, timedelta
import io
import base64

app = Flask(__name__)

def pegar_mes_anterior():
    today = datetime.today()
    first_day_of_current_month = today.replace(day=1)
    last_day_of_last_month = first_day_of_current_month - timedelta(days=1)
    first_day_of_last_month = last_day_of_last_month.replace(day=1)
    return first_day_of_last_month.strftime("%d/%m/%Y"), last_day_of_last_month.strftime("%d/%m/%Y")

def criar_fatura(image_path, invoice_info, items):
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4

    image = Image.open(image_path)
    image_reader = ImageReader(image)
    c.drawImage(image_reader, 0, 0, width=width, height=height, preserveAspectRatio=True, mask='auto')

    text_y_start = height - 283.46

    c.setFont("Helvetica-Bold", 14)
    c.drawString(40, text_y_start, f"Nome: {invoice_info['Nome']}")
    c.drawString(40, text_y_start - 20, f"Data: {invoice_info['Vencimento']}")
    c.drawString(40, text_y_start - 40, f"Endereço: {invoice_info['Endereço']}")
    c.drawString(40, text_y_start - 60, f"Período de Consumo: {invoice_info['Periodo']}")
    c.drawString(40, text_y_start - 80, f"Consumo Total: {invoice_info['Consumo']} kWh")

    c.setLineWidth(1)
    c.line(40, text_y_start - 100, width - 40, text_y_start - 100)

    c.setFont("Helvetica-Bold", 12)
    c.drawString(40, text_y_start - 120, "Descrição")
    c.drawString(300, text_y_start - 120, "Quantidade")
    c.drawString(400, text_y_start - 120, "Preço Unitário")
    c.drawString(500, text_y_start - 120, "Total")

    c.line(40, text_y_start - 125, width - 40, text_y_start - 125)

    c.setFont("Helvetica", 12)
    y = text_y_start - 140
    total = 0
    for item in items:
        c.drawString(40, y, item['Descrição'])
        c.drawString(300, y, str(item['Quantidade']))
        c.drawString(400, y, f"R$ {item['Preço Unitário']:.2f}")
        item_total = item['Quantidade'] * item['Preço Unitário']
        c.drawString(500, y, f"R$ {item_total:.2f}")
        total += item_total
        y -= 20

    c.line(40, y - 10, width - 40, y - 10)

    c.setFont("Helvetica-Bold", 12)
    c.drawString(400, y - 30, "Total Geral:")
    c.drawString(500, y - 30, f"R$ {total:.2f}")

    c.showPage()
    c.save()

    buffer.seek(0)
    return buffer

@app.route('/gerar_fatura', methods=['POST'])
def gerar_fatura():
    data = request.json
    nome = data.get('nome')
    endereco = data.get('endereco')
    cpf = data.get('cpf')
    periodo = data.get('periodo')

    if not nome or not endereco:
        return jsonify({"error": "Os campos 'nome' e 'endereco' são obrigatórios."}), 400

    invoice_info = {
        'Nome': nome,
        'CPF': cpf,
        'Vencimento': datetime.today().strftime("%d/%m/%Y"),
        'Endereço': endereco,
        'Periodo': periodo,
        'Consumo': 250
    }
    items = [
        {'Descrição': 'Tarifa Básica', 'Quantidade': 1, 'Preço Unitário': 30.00},
        {'Descrição': 'Consumo (kWh)', 'Quantidade': 250, 'Preço Unitário': 0.75},
        {'Descrição': 'Taxa de Iluminação Pública', 'Quantidade': 1, 'Preço Unitário': 5.00}
    ]

    image_path = 'img.jpg'
    pdf_buffer = criar_fatura(image_path, invoice_info, items)

    pdf_base64 = base64.b64encode(pdf_buffer.getvalue()).decode('utf-8')
    pdf_data_uri = f"data:application/pdf;base64,{pdf_base64}"

    return jsonify({"value": "fatura.pdf", "key": pdf_data_uri})

if __name__ == '__main__':
    app.run(debug=True)
