import unittest
from unittest import mock

from vw2html.html import VimWiki2Html


class TestParagraph(unittest.TestCase):

    def setUp(self):
        # don't read any file
        VimWiki2Html.read_wiki_file = mock.MagicMock(return_value=None)
        self.converter = VimWiki2Html('/tmp/src/foo.wiki', '/tmp/out',
                                      '/tmp/src')

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

