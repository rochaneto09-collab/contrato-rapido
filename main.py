import os
import re
from pathlib import Path
from datetime import datetime
from fastapi import FastAPI, Form, Request
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.templating import Jinja2Templates
from docxtpl import DocxTemplate
from num2words import num2words
from babel.dates import format_date

try:
    from docx2pdf import convert
    HAS_DOCX2PDF = True
except ImportError:
    HAS_DOCX2PDF = False

app = FastAPI()

# Direciona para a pasta views usando caminho absoluto para evitar erros de diretório
BASE_DIR = Path(__file__).resolve().parent
templates_html = Jinja2Templates(directory=str(BASE_DIR / "views"))

def formatar_cpf(cpf: str) -> str:
    apenas_numeros = re.sub(r'\D', '', cpf)
    if len(apenas_numeros) == 11:
        return f"{apenas_numeros[:3]}.{apenas_numeros[3:6]}.{apenas_numeros[6:9]}-{apenas_numeros[9:]}"
    return cpf

def valor_por_extenso(valor_str: str) -> str:
    if not valor_str:
        return ""
    try:
        valor_limpo = valor_str.replace("R$", "").replace(".", "").replace(",", ".").strip()
        valor_float = float(valor_limpo)
        extenso = num2words(valor_float, lang='pt_BR', to='currency')
        valor_formatado = f"{valor_float:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
        return f"R$ {valor_formatado} ({extenso.capitalize()})"
    except ValueError:
        return valor_str

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates_html.TemplateResponse(
        request=request, 
        name="index.html"
    )

import shutil

@app.post("/gerar-contrato")
async def gerar_contrato(
    modelo_id: str = Form(...),
    formato: str = Form(...),
    contratante_nome: str = Form(...),
    contratante_cpf: str = Form(...),
    contratante_endereco: str = Form(...),
    valor_total: str = Form(...),
    parcela: str = Form(...),
    valor_parcela: str = Form(...),
    data_vencimento: str = Form(...),
    fiador_nome: str = Form(""),
    fiador_cpf: str = Form(""),
    fiador_endereco: str = Form(""),
    veiculo_nome: str = Form(""),
    veiculo_ano: str = Form(""),
    veiculo_placa: str = Form(""),
    veiculo_renavam: str = Form("")
):
    caminho_template = BASE_DIR / "templates" / f"modelo_{modelo_id}.docx"
    
    if not os.path.exists(caminho_template):
        return {"erro": "Modelo de contrato não encontrado."}

    doc = DocxTemplate(caminho_template)

    data_hoje = format_date(datetime.now(), format="d 'de' MMMM 'de' yyyy", locale='pt_BR')

    cpf_contratante_formatado = formatar_cpf(contratante_cpf)
    cpf_fiador_formatado = formatar_cpf(fiador_cpf) if fiador_cpf else ""

    valor_total_formatado = valor_por_extenso(valor_total)
    valor_parcela_formatado = valor_por_extenso(valor_parcela)

    contexto = {
        "contratante_nome": contratante_nome,
        "contratante_cpf": cpf_contratante_formatado,
        "contratante_endereco": contratante_endereco,
        "valor_total": valor_total_formatado,
        "parcela": parcela,
        "valor_parcela": valor_parcela_formatado,
        "data_vencimento": data_vencimento,
        "data_atual": data_hoje,
        "fiador_nome": fiador_nome,
        "fiador_cpf": cpf_fiador_formatado,
        "fiador_endereco": fiador_endereco,
        "veiculo_nome": veiculo_nome,
        "veiculo_ano": veiculo_ano,
        "veiculo_placa": veiculo_placa,
        "veiculo_renavam": veiculo_renavam
    }

    doc.render(contexto)

    pasta_gerados = BASE_DIR / "gerados"
    os.makedirs(pasta_gerados, exist_ok=True)
    caminho_docx_saida = pasta_gerados / "contrato_gerado.docx"
    doc.save(caminho_docx_saida)

    if formato == "docx":
        return FileResponse(
            caminho_docx_saida,
            filename=f"Contrato_{contratante_nome}.docx",
            media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        )
    
    elif formato == "pdf":
        caminho_pdf_saida = pasta_gerados / "contrato_gerado.pdf"
        
        # Verifica se 'soffice' (LibreOffice) está instalado no PATH do sistema
        soffice_path = shutil.which("soffice") or shutil.which("libreoffice")
        
        if soffice_path:
            try:
                import subprocess
                subprocess.run([
                    soffice_path, "--headless", "--convert-to", "pdf",
                    str(caminho_docx_saida), "--outdir", str(pasta_gerados)
                ], check=True)
                
                return FileResponse(
                    caminho_pdf_saida,
                    filename=f"Contrato_{contratante_nome}.pdf",
                    media_type="application/pdf"
                )
            except Exception as e:
                return {"erro": f"Falha na conversão via LibreOffice: {str(e)}"}
        
        # Fallback local para Windows com Word instalado
        elif HAS_DOCX2PDF:
            try:
                convert(str(caminho_docx_saida), str(caminho_pdf_saida))
                return FileResponse(
                    caminho_pdf_saida,
                    filename=f"Contrato_{contratante_nome}.pdf",
                    media_type="application/pdf"
                )
            except Exception as e:
                return {"erro": f"Falha na conversão local: {str(e)}"}
        
        else:
            return {
                "erro": "A conversão para PDF não está disponível no servidor de hospedagem gratuita devido a limitações do ambiente sem LibreOffice/Word. Selecione o formato DOCX para baixar o contrato preenchido."
            }