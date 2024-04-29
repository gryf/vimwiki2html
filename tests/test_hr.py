import unittest
from unittest import mock

from vw2html.html import VimWiki2Html


class TestHorizontalRule(unittest.TestCase):

    def setUp(self):
        self.converter = VimWiki2Html('/tmp/src/foo.wiki', '/tmp/out',
                                      '/tmp/src')
        # don't read any file
        self.converter.read_wiki_file = mock.MagicMock(return_value=None)

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
