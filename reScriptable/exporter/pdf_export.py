
from .svg_export import RMToSVG
from .line_reader import RMDocument

import os
import subprocess
import shutil

from io import StringIO

class RMToPDF:
    def __init__(self, doc: RMDocument):
        self.doc = doc

    def write(self, out):
        n_pages = self.doc.content_data['pageCount']
        bg = self.doc.pdf

        to_svg = RMToSVG(self.doc)

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
    doc = RMDocument("/home/ole-magnus/Documents/RemarkableBackup/latest/", "7c712411-d576-4221-b4e5-f36faa016a0e")

    pdf = RMToPDF(doc)

    pdf.write("/home/ole-magnus/Documents/Remarkable/out/pdf_test/test_with_pdf.pdf")
