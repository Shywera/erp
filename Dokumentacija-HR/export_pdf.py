# -*- coding: utf-8 -*-
"""
Konvertira sve .docx dokumente u ovoj mapi u .pdf (koristeci instaliran Word).
Pokrenuti: python export_pdf.py
"""

import os
import glob
import win32com.client as win32

OUT_DIR = os.path.dirname(os.path.abspath(__file__))

wdFormatPDF = 17


def main():
    docx_files = sorted(glob.glob(os.path.join(OUT_DIR, "*.docx")))
    if not docx_files:
        print("Nema .docx datoteka u", OUT_DIR)
        return

    word = win32.gencache.EnsureDispatch("Word.Application")
    word.Visible = False
    try:
        for docx_path in docx_files:
            pdf_path = os.path.splitext(docx_path)[0] + ".pdf"
            doc = word.Documents.Open(docx_path)
            try:
                doc.SaveAs(pdf_path, FileFormat=wdFormatPDF)
                print("OK:", os.path.basename(pdf_path))
            finally:
                doc.Close(False)
    finally:
        word.Quit()


if __name__ == "__main__":
    main()
