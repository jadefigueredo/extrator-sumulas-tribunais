"""End to end through pdfplumber with a PDF generated on the fly."""

from fpdf import FPDF

from sumulas.models import DocumentLink
from sumulas.pdf import pdf_to_text
from sumulas.tribunais.tjpa import TJPA


def make_pdf(lines: list[str]) -> bytes:
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Helvetica", size=11)
    for line in lines:
        pdf.multi_cell(0, 6, line, new_x="LMARGIN", new_y="NEXT")
    return bytes(pdf.output())


def test_pdf_text_feeds_the_parser():
    data = make_pdf(
        [
            "Súmula nº 07 (Res.020/2012 - DJ. Nº 5131/2012, 16/10/2012)",
            "Não padece do vício de inconstitucionalidade o disposto no art. 310, "
            "inciso II, do CPP, com redação dada pela Lei nº 12.403/2011.",
        ]
    )

    text = pdf_to_text(data)
    sumula = TJPA().parse(text, DocumentLink(url="https://exemplo/7.pdf", label=""))

    assert sumula.numero == 7
    assert sumula.resolucao == "Res. 020/2012"
    assert sumula.data_publicacao == "2012-10-16"
    assert sumula.enunciado.endswith("Lei nº 12.403/2011.")
