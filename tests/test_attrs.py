import unittest
from unittest import mock

from vw2html.html import VimWiki2Html


class TestTextAttrs(unittest.TestCase):

    def setUp(self):
        # don't read any file
        VimWiki2Html.read_wiki_file = mock.MagicMock(return_value=None)
        self.converter = VimWiki2Html('/tmp/src/foo.wiki', '/tmp/out',
                                      '/tmp/src')

    def test_bold(self):
        src = '*foo*'
        exp = '<p>\n<strong>foo</strong>\n</p>'

        self.converter.wiki_contents = src
        self.converter.convert()
        self.assertEqual(self.converter.html, exp)

    def test_double_bold(self):
        src = 'males*uada venen*atis maur*is ornare mol*lis velit'
        exp = ('<p>\nmales<strong>uada venen</strong>atis maur<strong>is '
               'ornare mol</strong>lis velit\n</p>')

        self.converter.wiki_contents = src
        self.converter.convert()
        self.assertEqual(self.converter.html, exp)

    def test_double_bold_extra_asterisk(self):
        src = 'males*uada venen*atis maur*is ornare mol*lis ve*lit'
        exp = ('<p>\nmales<strong>uada venen</strong>atis maur<strong>is '
               'ornare mol</strong>lis ve*lit\n</p>')

        self.converter.wiki_contents = src
        self.converter.convert()
        self.assertEqual(self.converter.html, exp)
