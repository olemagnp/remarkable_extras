
from .svg_export import RMToSVG
from .line_reader import RMDocument

import os
import subprocess
import shutil
import sys

from io import StringIO

class RMToPDF:
    def __init__(self, doc: RMDocument, width: int = 1404, height: int = 1872):
        self.doc = doc
        self.width = width
        self.height = height

    def get_pdf_size(self, pdf):
        if pdf is not None:
            res = subprocess.run(["pdfinfo", "-box", pdf], capture_output=True, text=True)
            w, h = None, None
            for line in res.stdout.split("\n"):
                nice = line.strip().lower()
                if nice.startswith("mediabox"):
                    data = nice.split()
                    w, h = float(data[-2]), float(data[-1])
            if w is None:
                print("Warning: MediaBox not found in pdfinfo output!", file=sys.stderr)
            else:
                w_frac = self.width / w
                h_frac = self.height / h
                m_frac = min(w_frac, h_frac)

                return round(w * m_frac), round(h * m_frac)
        return self.width, self.height

    def write(self, out):
        os.makedirs(os.path.dirname(out), exist_ok=True)
        n_pages = self.doc.content_data['pageCount']
        bg = self.doc.pdf

        width, height = self.get_pdf_size(bg)

        to_svg = RMToSVG(self.doc, width, height)

        tmp_out_dir = ".rm_pdf_export_tmp"
        to_svg.write(tmp_out_dir, bg is None)

        for i in range(1, n_pages+1):
            proc = subprocess.Popen(['/usr/bin/inkscape', '--without-gui', f'--export-filename={os.path.join(tmp_out_dir, "pdf" + str(i) + ".pdf")}', os.path.join(tmp_out_dir, "p" + str(i) + ".svg")], stderr=subprocess.DEVNULL, stdout=subprocess.DEVNULL)
            proc.communicate()
            if proc.returncode < 0:
                raise OSError(f"Popen return code: {proc.returncode}")

        merged_path = os.path.join(tmp_out_dir, 'merged.pdf')
        proc = subprocess.run(['/usr/bin/pdftk'] + [os.path.join(tmp_out_dir, f"pdf{i}.pdf") for i in range(1, n_pages + 1)] + ['cat', 'output', merged_path])

        if bg is None:
            shutil.copy(merged_path, out)
        else:
            subprocess.run(['/usr/bin/pdftk', bg, 'multistamp', merged_path, 'output', out])

        shutil.rmtree(tmp_out_dir)


if __name__ == "__main__":
    doc = RMDocument("/home/ole-magnus/Documents/RemarkableBackup/.raw/latest/xochitl", "bc1fe071-5655-4d41-b513-3df3b5bd0c00")

    pdf = RMToPDF(doc)

    pdf.write("/home/ole-magnus/Documents/RemarkableBackup/content/Papers/Wang2018_-_Generating_High_Quality_Visible_Images_from_SAR_Images_Using_CNNs.pdf")
