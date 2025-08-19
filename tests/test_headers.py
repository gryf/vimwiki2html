import unittest
from unittest import mock

from vw2html import cli
from vw2html import html


class TestHeaders(unittest.TestCase):

    @mock.patch.multiple('vw2html.cli.VimWiki2HTMLConverter',
                        update=mock.MagicMock(return_value=None),
                        read_config=mock.MagicMock(return_value=None))
    def setUp(self):
        conf = cli.VimWiki2HTMLConverter(mock.MagicMock())
        conf.path = '/tmp/wiki'
        conf.path_html = '/tmp/wiki_html'
        self.converter = html.VimWiki2Html('/tmp/wiki/foo.wiki', conf)
        # don't read any file
        self.converter.read_wiki_file = mock.MagicMock(return_value=None)

    def test_h1(self):
        src = '=foo='
        exp = '<h1 id="foo"><a href="#foo">foo</a></h1>\n'

        self.converter.wiki_contents = src
        self.converter.convert()
        self.assertEqual(self.converter.html, exp)

    def test_h_multiline(self):
        src = '=tit\nle='
        exp = '<p>\n=tit\nle=\n</p>'

        self.converter.wiki_contents = src
        self.converter.convert()
        self.assertEqual(self.converter.html, exp)

    def test_h_extra_spaces(self):
        src = '===    title ==='
        exp = '<h3 id="title"><a href="#title">title</a></h3>\n'

        self.converter.wiki_contents = src
        self.converter.convert()
        self.assertEqual(self.converter.html, exp)

    def test_h6(self):
        src = '====== title ======'
        exp = '<h6 id="title"><a href="#title">title</a></h6>\n'

        self.converter.wiki_contents = src
        self.converter.convert()
        self.assertEqual(self.converter.html, exp)

    def test_h2_equal_in_title(self):
        src = '== ti==tle =='
        exp = '<h2 id="ti==tle"><a href="#ti==tle">ti==tle</a></h2>\n'

        self.converter.wiki_contents = src
        self.converter.convert()
        self.assertEqual(self.converter.html, exp)

    def test_h7(self):
        src = "======= title ======="
        exp = src

        self.converter.wiki_contents = src
        self.converter.convert()
        self.assertEqual(self.converter.html, exp)

    def test_unbalanced_equals_in_header(self):
        src = "===== title ===="
        exp = src

        self.converter.wiki_contents = src
        self.converter.convert()
        self.assertEqual(self.converter.html, exp)

    def test_attrs_in_header(self):
        self.maxDiff = None
        title = "header with _italic_ *bold* ~~and crossed~~"
        src = f"== {title} =="
        exp = (f'<h2 id="{title}"><a href="#{title}">header with '
               f'<em>italic</em> <strong>bold</strong> <del>and '
               f'crossed</del></a></h2>\n')

        self.converter.wiki_contents = src
        self.converter.convert()
        self.assertEqual(self.converter.html, exp)
