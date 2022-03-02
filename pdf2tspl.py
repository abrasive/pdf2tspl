#!/usr/bin/env python3

import tempfile
import subprocess
import dataclasses

@dataclasses.dataclass
class Image:
    width: int
    height: int
    data: bytes

def convert_pdf(pdfname, args=[]):
    with tempfile.NamedTemporaryFile(suffix='.pbm') as pbmfile:
        subprocess.check_call(["pdftoppm", "-mono", "-singlefile"] + args + [pdfname, pbmfile.name.removesuffix('.pbm')])

        header = pbmfile.readline()
        if header.strip() != b'P4':
            raise ValueError("unrecognised image format")
        width_height = pbmfile.readline().decode('ascii')
        data = bytes(x ^ 0xff for x in pbmfile.read())

    width, height = map(int, width_height.strip().split())
    return Image(width, height, data)

def convert_pdf_scaled(pdfname, max_width, max_height):
    im = convert_pdf(pdfname)
    aspect = im.width / im.height
    max_aspect = max_width / max_height

    if aspect < max_aspect:
        max_width = int(max_height * aspect) - 1
    else:
        # pdftoppm tends to make it 1px too wide
        max_width -= 1
        max_height = int(max_width / aspect)

    args = ['-scale-to-x', str(max_width), '-scale-to-y', str(max_height)]
    im = convert_pdf(pdfname, args)

    assert im.width <= max_width + 1
    assert im.height <= max_height

    return im

def pdf2tspl(filename, labelwidth_mm=100, labelheight_mm=150, dpi=203.2):
    labelwidth = int(round(labelwidth_mm / 25.4 * dpi))
    labelheight = int(round(labelheight_mm / 25.4 * dpi))

    image = convert_pdf_scaled(filename, labelwidth, labelheight)

    paste_x = (labelwidth - image.width) // 2
    paste_y = (labelheight - image.height) // 2
    row_bytes = (image.width + 7) // 8

    tspl = b"\r\n\r\nSIZE %d mm,%d mm\r\nCLS\r\nBITMAP %d,%d,%d,%d,0," % (labelwidth_mm, labelheight_mm, paste_x, paste_y, row_bytes, image.height)
    tspl += image.data
    tspl += b"\r\nPRINT 1,1\r\n"
    return tspl

if __name__ == "__main__":
    from PyPDF2 import PdfFileWriter, PdfFileReader
    import argparse
    import sys
    parser = argparse.ArgumentParser(description='Convert a PDF to TSPL to send to a label printer.')
    parser.add_argument('pdf_file', help='The PDF to convert.')
    parser.add_argument('tspl_file', help='The file or device to write the TSPL code to. Can be a printer device eg. /dev/usb/lp0, or specify "-" to write to stdout.')

    parser.add_argument('-x', '--width', type=int, default=100, help='The width of the label, in millimetres.')
    parser.add_argument('-y', '--height', type=int, default=150, help='The height of the label, in millimetres.')
    parser.add_argument('-d', '--dpi', type=float, default=203.2, help='Resolution of the printer. Defaults to 8 dots per mm (203.2 dpi)')
    args = parser.parse_args()

    inputpdf = PdfFileReader(open(args.pdf_file, "rb"))

    for i in range(inputpdf.numPages):
        output = PdfFileWriter()
        output.addPage(inputpdf.getPage(i))
        temp_pdf_name = "temp/document-page%s.pdf" % i
        with open(temp_pdf_name, "wb") as outputStream:
            output.write(outputStream)

        tspl = pdf2tspl(temp_pdf_name,
        labelwidth_mm=args.width,
        labelheight_mm=args.height,
        dpi=args.dpi)

        if args.tspl_file == '-':
            sys.stdout.buffer.write(tspl)
        else:
            with open(args.tspl_file, 'wb') as fp:
                fp.write(tspl)
