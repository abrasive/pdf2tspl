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

def pdf2tspl(filename, labelwidth_mm=100, labelheight_mm=150, dpi=203):
    labelwidth = int(round(labelwidth_mm / 25.4 * dpi))
    labelheight = int(round(labelheight_mm / 25.4 * dpi))

    image = convert_pdf_scaled(filename, labelwidth, labelheight)

    paste_x = (labelwidth - image.width) // 2
    paste_y = (labelheight - image.height) // 2
    row_bytes = (image.width + 7) // 8

    command = b"\r\n\r\nSIZE %d mm\r\nCLS\r\nBITMAP %d,%d,%d,%d,0," % (labelwidth_mm, paste_x, paste_y, row_bytes, image.height)
    command += image.data
    command += b"\r\nPRINT 1,1\r\n"
    return command

def print_pdf(filename):
    cmd = pdf2tspl(filename)
    with open("/dev/usb/lp0", "r+b") as prn:
        prn.write(cmd)

if __name__ == "__main__":
    import sys
    print_pdf(sys.argv[1])
