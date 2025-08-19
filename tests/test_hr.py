import unittest
from unittest import mock

from vw2html import cli
from vw2html import html


class TestHorizontalRule(unittest.TestCase):

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
