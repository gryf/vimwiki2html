__version__ = "0.0.1"

from vw2html.parser import Parser


def wiki(text_lines):
    """
    Converts vimwki input, return converted html string.
    """
    par = Parser()
    return par.parse(text_lines)
