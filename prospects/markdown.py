from io import StringIO
from functools import partial


def iter_first(iterable):
    first = True
    for item in iterable:
        yield (first, item)
        first = False


def escape(url):
    return url.replace("(", "\\(").replace(")", "\\)")


class Buffer:
    def __init__(self):
        self._inner = StringIO()

    def write(self, text):
        self._inner.write(text)

    def writef(self, fmt: str, *args, **kwargs):
        self._inner.write(fmt.format(*args, **kwargs))

    def text(self):
        return self._inner.getvalue()


class Document:
    def __init__(self):
        self.items = []

    def add(self, item):
        self.items.append(item)

    def render(self):
        b = Buffer()
        for item in self.items:
            if isinstance(item, Element):
                item.render(b)
        return b.text()


class Element:
    def render(self, writer: Buffer):
        pass


class _Heading(Element):
    def __init__(self, text, *, size):
        self.text = text
        self.size = size

    def render(self, w):
        for _ in range(self.size):
            w.write("#")
        w.write(" ")
        w.write(self.text)
        w.write("\n")


H1 = partial(_Heading, size=1)
H2 = partial(_Heading, size=2)
H3 = partial(_Heading, size=3)


class HorizontalRule(Element):
    def __init__(self):
        pass

    def render(self, w):
        w.write("***\n")


class Paragraph(Element):
    def __init__(self, text):
        self.text = text

    def render(self, w):
        w.write(self.text)
        w.write("\n\n")


class Quote(Element):
    def __init__(self, text):
        self.text = text

    def render(self, w):
        w.write("> ")
        w.write(self.text)
        w.write("\n\n")


class Link(Element):
    def __init__(self, text, url):
        self.text = text
        self.url = url

    def render(self, w):
        w.write("[")
        w.write(self.text)
        w.write("](")
        w.write(escape(self.url))
        w.write(")")


class List(Element):
    def __init__(self, items=None, numbered=False):
        if items is None:
            self.items = []
        else:
            self.items = list(items)
        self.numbered = numbered

    def add(self, text: str):
        self.items.append(text)

    def render(self, w):
        w.write("\n")
        for idx, item in enumerate(self.items):
            if self.numbered:
                w.write(str(idx + 1))
                w.write(". ")
            else:
                w.write("* ")
            w.write(item)
            w.write("\n")
        w.write("\n")


class Table(Element):
    def __init__(self):
        self.columns = []
        self.alignments = []
        self.rows = []

    def add_column(self, name, *, align="center"):
        self.columns.append(name)
        self.alignments.append(align.lower())

    def add_columns(self, *columns):
        for col in columns:
            self.add_column(col)

    def add_row(self, *args):
        self.rows.append(tuple(args))

    def render(self, w):
        for first, column in iter_first(self.columns):
            if not first:
                w.write("|")
            w.write(column)
        w.write("\n")

        for first, align in iter_first(self.alignments):
            if not first:
                w.write("|")
            if align == "center":
                w.write(":---:")
            elif align == "left":
                w.write(":---")
            elif align == "right":
                w.write("---:")
            else:
                raise ValueError("invalid value for alignment %s" % align)
        w.write("\n")

        for row in self.rows:
            for first, item in iter_first(row):
                if not first:
                    w.write("|")
                if isinstance(item, Element):
                    item.render(w)
                elif item is None:
                    w.write("-")
                else:
                    w.write(str(item))
            w.write("\n")
        w.write("\n")
