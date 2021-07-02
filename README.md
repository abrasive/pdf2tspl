# what is this

I bought a cheap label printer for thermal shipping labels. This one is a Hotlabel S8, which appears to be a rebranded Xprinter XP-480B or thereabouts.
These printers speak TSPL, which is yet another printer language, oriented around label production (no surprises there).
It has the rather dubious distinction of being the first one I've seen that includes a BASIC interpreter...

Anyway, the manufacturer includes Windows and Mac drivers, but no Linux ones, so I had to come up with something.
I had a quick look at what it takes to make a CUPS driver; it requires a fair bit of fiddling - more than I have time for.
So this repo contains what I made instead:

1. a tool that takes a PDF and prints it on a label, and
2. a print server that speaks the AppSocket protocol, so you can print to it from CUPS anyway.

# how do I print a thing

You need to have `pdftoppm` on your `PATH` - it's installed by the `poppler` package (at least on my Gentoo system).

Identify the device node for your printer. For my USB printer, it's `/dev/usb/lp0`.

Find the PDF you want to print. Note that at the moment, only the first page is printed. The PDF will be scaled so that the whole thing fits on the label.

Then you can:

```
./pdf2tspl.py file_to_print.pdf /dev/usb/lp0
```

...and hopefully receive a label.

# how do I print a thing with CUPS

If `pdf2tspl.py` is working for you, you can run `appsocket_print_server.py /dev/path/to/your/printer`.

Then, in CUPS:

1. go to Add Printer
2. choose AppSocket/HP JetDirect
3. set the Connection to `socket://hostname`, where `hostname` is the machine running the print server; use `localhost` if you're just running it on the same machine
4. set the name as you wish
5. when prompted for a Make, select Generic
6. when prompted for a Model, select Generic PDF Printer
7. hit Add Printer
8. set the default page size to A6 (for reasonable scaling on 100x150mm labels) and colour mode to Black and White
