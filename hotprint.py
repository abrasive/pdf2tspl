#!/usr/bin/env python3

import tempfile
import subprocess
from PIL import Image, ImageOps

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

    assert im.size[0] <= max_width
    assert im.size[1] <= max_height

    return im

def label_to_command(image, labelwidth=810, labelheight=1200):
    "Centre the image on the label and generate a print command"
    assert im.size[0] <= labelwidth
    assert im.size[1] <= labelheight

    paste_x = (labelwidth - im.size[0]) // 2
    paste_y = (labelheight - im.size[1]) // 2
    row_bytes = (im.size[0] + 7) // 8

    command = b"CLS\r\nBITMAP %d,%d,%d,%d,0," % (paste_x, paste_y, row_bytes, im.size[1])
    command += image.tobytes()
    command += b"\r\nPRINT 1,1\r\nSOUND 3,200\r\n"
    return command


im = convert_pdf_scaled("test.pdf", 800, 1200)
cmd = label_to_command(im)
with open("/dev/usb/lp0", "r+b") as prn:
    prn.write(cmd)
