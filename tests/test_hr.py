import unittest
from unittest import mock

from vw2html.html import VimWiki2Html


class TestHorizontalRule(unittest.TestCase):
    tpl = '<hr/>'

    def setUp(self):
        # don't read any file
        VimWiki2Html.read_wiki_file = mock.MagicMock(return_value=None)
        self.converter = VimWiki2Html('/tmp/src/foo.wiki', '/tmp/out',
                                      '/tmp/src')

    def test_hr(self):
        src = '-----'
        exp = '<hr />'

        self.converter.wiki_contents = src
        self.converter.convert()
        self.assertEqual(self.converter.html, exp)

    def test_hr_extra_dash(self):
        src = '-----------------------------'
        exp = '<hr />'

        self.converter.wiki_contents = src
        self.converter.convert()
        self.assertEqual(self.converter.html, exp)

    def test_hr_trailing_space(self):
        src = '---- '
        exp = f'<p>\n{src}\n</p>'

        self.converter.wiki_contents = src
        self.converter.convert()
        self.assertEqual(self.converter.html, exp)

    def test_hr_leading_space(self):
        src = ' ----'
        exp = f'<p>\n{src}\n</p>'

        self.converter.wiki_contents = src
        self.converter.convert()
        self.assertEqual(self.converter.html, exp)

    def test_hr_extra_characters(self):
        src = '----foo'
        exp = f'<p>\n{src}\n</p>'

        self.converter.wiki_contents = src
        self.converter.convert()
        self.assertEqual(self.converter.html, exp)

    def test_hr_too_little_dashes(self):
        src = '---'
        exp = f'<p>\n{src}\n</p>'

        self.converter.wiki_contents = src
        self.converter.convert()
        self.assertEqual(self.converter.html, exp)
