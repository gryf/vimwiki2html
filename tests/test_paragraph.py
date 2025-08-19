import unittest
from unittest import mock

from vw2html import cli
from vw2html import html


class TestParagraph(unittest.TestCase):

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

    def test_single_paragraph(self):
        src = 'foo'
        exp = '<p>\nfoo\n</p>'

        self.converter.wiki_contents = src
        self.converter.convert()
        self.assertEqual(self.converter.html, exp)

    def test_two_paragraphs(self):
        src = 'foo\n\nfoo'
        # TODO: should be single newline, but meh
        exp = '<p>\nfoo\n</p>\n\n<p>\nfoo\n</p>'

        self.converter.wiki_contents = src
        self.converter.convert()
        self.assertEqual(self.converter.html, exp)

    def test_single_paragraphs_two_lines(self):
        src = 'foo\nfoo'
        exp = '<p>\nfoo\nfoo\n</p>'

        self.converter.wiki_contents = src
        self.converter.convert()
        self.assertEqual(self.converter.html, exp)

