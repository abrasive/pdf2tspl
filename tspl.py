#!/usr/bin/env python3

import tempfile
import subprocess
from PIL import Image

def convert_pdf(pdfname, args=[]):
    pbmfile = tempfile.NamedTemporaryFile(suffix='.pbm')
    subprocess.check_call(["pdftoppm", "-mono", "-singlefile"] + args + [pdfname, pbmfile.name.removesuffix('.pbm')])

    return Image.open(pbmfile)

def convert_pdf_scaled(pdfname, max_width, max_height):
    im = convert_pdf(pdfname)
    aspect = im.size[0] / im.size[1]
    max_aspect = max_width / max_height

    if aspect < max_aspect:
        max_width = int(max_height * aspect) - 1
    else:
        # pdftoppm tends to make it 1px too wide
        max_width -= 1
        max_height = int(max_width / aspect)

    args = ['-scale-to-x', str(max_width), '-scale-to-y', str(max_height)]
    im = convert_pdf(pdfname, args)

    assert im.size[0] <= max_width + 1
    assert im.size[1] <= max_height

    return im

def pdf2tspl(filename, labelwidth_mm=100, labelheight_mm=150, dpi=203):
    labelwidth = int(round(labelwidth_mm / 25.4 * dpi))
    labelheight = int(round(labelheight_mm / 25.4 * dpi))

    image = convert_pdf_scaled(filename, labelwidth, labelheight)

    paste_x = (labelwidth - image.size[0]) // 2
    paste_y = (labelheight - image.size[1]) // 2
    row_bytes = (image.size[0] + 7) // 8

    command = b"\r\n\r\nSIZE %d mm\r\nCLS\r\nBITMAP %d,%d,%d,%d,0," % (labelwidth_mm, paste_x, paste_y, row_bytes, image.size[1])
    command += image.tobytes()
    command += b"\r\nPRINT 1,1\r\n"
    return command

def print_pdf(filename):
    cmd = pdf2tspl(filename)
    with open("/dev/usb/lp0", "r+b") as prn:
        prn.write(cmd)

if __name__ == "__main__":
    import sys
    print_pdf(sys.argv[1])
