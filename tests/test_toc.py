import unittest
from unittest import mock

from vw2html.html import VimWiki2Html


class TestTableOfContents(unittest.TestCase):

    def setUp(self):
        self.converter = VimWiki2Html('/tmp/src/foo.wiki', '/tmp/wiki',
                                      '/tmp/wiki_html', [])
        # don't read any file
        self.converter.read_wiki_file = mock.MagicMock(return_value=None)

    def test_toc(self):
        src = '%toc\n\n=foo=\n'
        exp = ('<p>\n<nav>\n'
               '<ul><li><a href="#foo">foo</a></li>\n</ul>\n'
               '</nav>\n</p>\n\n'
               '<h1 id="foo"><a href="#foo">foo</a></h1>\n')

        self.converter.wiki_contents = src
        self.converter.convert()
        self.assertEqual(self.converter.html, exp)

    def test_more_complex(self):
        src = ('%toc\n\n'
               '=foo=\n'
               '=bar=\n'
               '==baz==\n'
               '===lorem===\n'
               '=ipsum=\n')
        exp = ('<p>\n<nav>\n'
               '<ul><li><a href="#foo">foo</a></li>\n'
               '<li><a href="#bar">bar</a>'
               '<ul>\n'
               '<li><a href="#baz">baz</a>'
               '<ul>\n'
               '<li><a href="#lorem">lorem</a></li>\n'
               '</ul>\n'
               '</li>\n'
               '</ul>\n'
               '</li>\n'
               '<li>\n<a href="#ipsum">ipsum</a></li>\n'
               '</ul>\n'
               '</nav>\n</p>\n\n'
               '<h1 id="foo"><a href="#foo">foo</a></h1>\n\n'
               '<h1 id="bar"><a href="#bar">bar</a></h1>\n\n'
               '<h2 id="baz"><a href="#baz">baz</a></h2>\n\n'
               '<h3 id="lorem"><a href="#lorem">lorem</a></h3>\n\n'
               '<h1 id="ipsum"><a href="#ipsum">ipsum</a></h1>\n')

        self.converter.wiki_contents = src
        self.converter.convert()
        self.assertEqual(self.converter.html, exp)
