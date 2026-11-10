"""Convierte docs/ENTREGA_3.md a .docx (subconjunto de Markdown que usa el documento).

Uso: python scripts/md_a_docx.py [entrada.md] [salida.docx]
Requiere: pip install python-docx
"""
import re
import sys
from pathlib import Path

from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Inches, Pt, RGBColor

RAIZ = Path(__file__).resolve().parents[1]
entrada = Path(sys.argv[1]) if len(sys.argv) > 1 else RAIZ / "docs" / "ENTREGA_3.md"
salida = Path(sys.argv[2]) if len(sys.argv) > 2 else entrada.with_suffix(".docx")

doc = Document()
for seccion in doc.sections:
    seccion.left_margin = seccion.right_margin = Inches(0.8)
    seccion.top_margin = seccion.bottom_margin = Inches(0.8)
estilo = doc.styles["Normal"]
estilo.font.name, estilo.font.size = "Calibri", Pt(10.5)
estilo.element.rPr.rFonts.set(qn("w:eastAsia"), "Calibri")
for nombre, tam, color in (("Heading 1", 20, "1F3864"), ("Heading 2", 15, "2F5496"), ("Heading 3", 12, "1F3864")):
    h = doc.styles[nombre]
    h.font.name, h.font.size, h.font.bold = "Calibri", Pt(tam), True
    h.font.color.rgb = RGBColor.from_string(color)
    h.element.rPr.rFonts.set(qn("w:eastAsia"), "Calibri")


def sombrear(celda, color):
    pr = celda._tc.get_or_add_tcPr()
    sh = OxmlElement("w:shd")
    sh.set(qn("w:val"), "clear")
    sh.set(qn("w:color"), "auto")
    sh.set(qn("w:fill"), color)
    pr.append(sh)


def en_linea(parrafo, texto, tam=None, negrita=False):
    """Agrega texto con **negrita** y `código` en línea."""
    for trozo in re.split(r"(\*\*[^*]+\*\*|`[^`]+`)", texto):
        if not trozo:
            continue
        if trozo.startswith("**"):
            r = parrafo.add_run(trozo[2:-2])
            r.bold = True
        elif trozo.startswith("`"):
            r = parrafo.add_run(trozo[1:-1])
            r.font.name = "Consolas"
            r.font.size = Pt((tam or 10.5) - 1)
            r._element.rPr.rFonts.set(qn("w:eastAsia"), "Consolas")
        else:
            r = parrafo.add_run(trozo)
            r.bold = negrita or None
        if tam and not trozo.startswith("`"):
            r.font.size = Pt(tam)


def tabla(filas):
    encabezado, cuerpo = filas[0], filas[2:]
    n = len(encabezado)
    tam = 7.5 if n >= 7 else 8.5 if n >= 5 else 9.5
    t = doc.add_table(rows=1, cols=n)
    t.style = "Table Grid"
    for i, texto in enumerate(encabezado):
        c = t.rows[0].cells[i]
        sombrear(c, "1E2433")
        p = c.paragraphs[0]
        r = p.add_run(texto.strip().strip("*"))
        r.bold, r.font.size = True, Pt(tam)
        r.font.color.rgb = RGBColor(255, 255, 255)
    for k, fila in enumerate(cuerpo):
        celdas = t.add_row().cells
        for i in range(n):
            texto = fila[i].strip() if i < len(fila) else ""
            if k % 2 == 1:
                sombrear(celdas[i], "EEF2F7")
            en_linea(celdas[i].paragraphs[0], texto, tam=tam)
    doc.add_paragraph()


def partir_fila(linea):
    return [c for c in re.split(r"(?<!\\)\|", linea.strip())[1:-1]]


lineas = entrada.read_text(encoding="utf-8").splitlines()
i = 0
while i < len(lineas):
    linea = lineas[i]
    if linea.startswith("```"):
        bloque = []
        i += 1
        while i < len(lineas) and not lineas[i].startswith("```"):
            bloque.append(lineas[i])
            i += 1
        for texto in bloque:
            p = doc.add_paragraph()
            p.paragraph_format.space_after = Pt(0)
            p.paragraph_format.left_indent = Inches(0.1)
            pPr = p._p.get_or_add_pPr()
            sh = OxmlElement("w:shd")
            sh.set(qn("w:val"), "clear")
            sh.set(qn("w:fill"), "F2F2F2")
            pPr.append(sh)
            r = p.add_run(texto or " ")
            r.font.name, r.font.size = "Consolas", Pt(7.5)
            r._element.rPr.rFonts.set(qn("w:eastAsia"), "Consolas")
        doc.add_paragraph()
    elif linea.startswith("|"):
        filas = []
        while i < len(lineas) and lineas[i].startswith("|"):
            filas.append(partir_fila(lineas[i]))
            i += 1
        tabla(filas)
        continue
    elif linea.startswith("!["):
        m = re.match(r"!\[(.*?)\]\((.*?)\)", linea)
        ruta = (entrada.parent / m.group(2)).resolve()
        doc.add_picture(str(ruta), width=Inches(5.8))
        doc.paragraphs[-1].alignment = WD_ALIGN_PARAGRAPH.CENTER
    elif linea.startswith("### "):
        doc.add_heading(linea[4:], level=3)
    elif linea.startswith("## "):
        doc.add_heading(linea[3:], level=2)
    elif linea.startswith("# "):
        doc.add_heading(linea[2:], level=1)
    elif re.match(r"^\s*- \[[ x]\] ", linea):
        marca = "☒" if "[x]" in linea[:8] else "☐"
        p = doc.add_paragraph()
        p.paragraph_format.left_indent = Inches(0.25 if linea.startswith("   ") else 0.1)
        en_linea(p, f"{marca} " + re.sub(r"^\s*- \[[ x]\] ", "", linea))
    elif re.match(r"^\s*- ", linea):
        p = doc.add_paragraph(style="List Bullet")
        en_linea(p, re.sub(r"^\s*- ", "", linea))
    elif re.match(r"^\s*\d+\. ", linea):
        p = doc.add_paragraph()
        p.paragraph_format.left_indent = Inches(0.25 if linea.startswith("   ") else 0.1)
        en_linea(p, linea.strip())
    elif linea.strip():
        p = doc.add_paragraph()
        p.paragraph_format.space_after = Pt(6)
        en_linea(p, linea.strip())
    i += 1

doc.save(salida)
print("escrito", salida)
