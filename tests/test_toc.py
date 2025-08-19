import unittest
from unittest import mock

from vw2html import cli
from vw2html import html


class TestTableOfContents(unittest.TestCase):

    @mock.patch.multiple('vw2html.cli.VimWiki2HTMLConverter',
                        update=mock.MagicMock(return_value=None),
                        read_config=mock.MagicMock(return_value=None))
    def setUp(self):
        conf = cli.VimWiki2HTMLConverter(mock.MagicMock())
        conf.path = '/tmp/wiki'
        conf.path_html = '/tmp/wiki_html'
        conf.skip_toc_level = 0
        self.converter = html.VimWiki2Html('/tmp/wiki/foo.wiki', conf)
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

    def test_toc_without_headers(self):
        src = '%toc\n'
        self.converter.wiki_contents = src
        self.converter.convert()
        self.assertEqual(self.converter.html, '')

class TestTableOfContentsFirstLevel(unittest.TestCase):

    @mock.patch.multiple('vw2html.cli.VimWiki2HTMLConverter',
                        update=mock.MagicMock(return_value=None),
                        read_config=mock.MagicMock(return_value=None))
    def setUp(self):
        conf = cli.VimWiki2HTMLConverter(mock.MagicMock())
        conf.path = '/tmp/wiki'
        conf.path_html = '/tmp/wiki_html'
        conf.skip_toc_level = 1
        self.converter = html.VimWiki2Html('/tmp/wiki/foo.wiki', conf)
        # don't read any file
        self.converter.read_wiki_file = mock.MagicMock(return_value=None)

    def test_toc_without_items_on_first_level(self):
        src = '%toc\n\n=foo=\n==bar==\n'
        exp = ('<p>\n<nav>\n'
               '<ul><li><a href="#bar">bar</a></li>\n</ul>\n'
               '</nav>\n</p>\n\n'
               '<h1 id="foo"><a href="#foo">foo</a></h1>\n\n'
               '<h2 id="bar"><a href="#bar">bar</a></h2>\n')

        self.converter.wiki_contents = src
        self.converter.convert()
        self.assertEqual(self.converter.html, exp)

class TestTableOfContentsSecondLevel(unittest.TestCase):

    @mock.patch.multiple('vw2html.cli.VimWiki2HTMLConverter',
                        update=mock.MagicMock(return_value=None),
                        read_config=mock.MagicMock(return_value=None))
    def setUp(self):
        conf = cli.VimWiki2HTMLConverter(mock.MagicMock())
        conf.path = '/tmp/wiki'
        conf.path_html = '/tmp/wiki_html'
        conf.skip_toc_level = 2
        self.converter = html.VimWiki2Html('/tmp/wiki/foo.wiki', conf)
        # don't read any file
        self.converter.read_wiki_file = mock.MagicMock(return_value=None)

    def test_toc_without_items_on_first_level(self):
        src = '%toc\n\n=foo=\n==bar==\n===baz==='
        exp = ('<p>\n<nav>\n'
               '<ul><li><a href="#baz">baz</a></li>\n</ul>\n'
               '</nav>\n</p>\n\n'
               '<h1 id="foo"><a href="#foo">foo</a></h1>\n\n'
               '<h2 id="bar"><a href="#bar">bar</a></h2>\n\n'
               '<h3 id="baz"><a href="#baz">baz</a></h3>\n')

        self.converter.wiki_contents = src
        self.converter.convert()
        self.assertEqual(self.converter.html, exp)
