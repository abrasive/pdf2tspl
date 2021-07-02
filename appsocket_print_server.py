#!/usr/bin/env python3

import pdf2tspl
import socket
import logging
import tempfile
import sys

if len(sys.argv) != 2:
    print("Usage: %s /dev/path/to/printer" % sys.argv[0])
    sys.exit(1)

printer = sys.argv[1]
open(printer, 'wb').close()

logging.basicConfig(level=logging.DEBUG)

UEL = b'\x1b%-12345X'
ENTER_PDF = b'@PJL ENTER LANGUAGE = PDF'

def accept_one_job(sock):
    def read_more_data(data):
        new_data = sock.recv(1048576)
        if not len(new_data):
            logging.error('Received unexpected EOF from client')
            return
        data.extend(new_data)

    def consume_up_to(data, marker):
        while not marker in data:
            read_more_data(data)

        pos = data.index(marker)
        before_marker = data[:pos]
        after_marker = data[pos+len(marker):]
        return before_marker, after_marker

    data = bytearray()

    _, data = consume_up_to(data, UEL)
    _, data = consume_up_to(data, ENTER_PDF)
    pdf_data, _ = consume_up_to(data, UEL)
    pdf_data = pdf_data.lstrip()

    with tempfile.NamedTemporaryFile(suffix=".pdf") as pdffile:
        pdffile.write(pdf_data)
        pdffile.flush()
        tspl = pdf2tspl.pdf2tspl(pdffile.name)

    with open(printer, 'wb') as fp:
        fp.write(tspl)

    logging.info('Job complete')

sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
sock.bind(('0.0.0.0', 9100))
sock.listen()

class ConnectionClosed(Exception):
    pass

while True:
    conn, peer = sock.accept()
    logging.info('New connection from %s' % peer[0])

    try:
        accept_one_job(conn)
    except ConnectionClosed:
        pass
    except Exception as e:
        logging.exception(e)
    finally:
        conn.close()
