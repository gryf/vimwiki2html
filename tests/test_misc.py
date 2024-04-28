import unittest
from unittest import mock

from vw2html.html import VimWiki2Html


class TestComments(unittest.TestCase):

    def setUp(self):
        # don't read any file
        VimWiki2Html.read_wiki_file = mock.MagicMock(return_value=None)
        self.converter = VimWiki2Html('/tmp/src/foo.wiki', '/tmp/out',
                                      '/tmp/src')

    def test_comment(self):
        src = '%% foo'
        exp = ''

        self.converter.wiki_contents = src
        self.converter.convert()
        self.assertEqual(self.converter.html, exp)

    def test_space_before_comment(self):
        src = ' %% foo'
        exp = ''

        self.converter.wiki_contents = src
        self.converter.convert()
        self.assertEqual(self.converter.html, exp)

    def test_things_before_comment(self):
        src = 'bar %% foo'
        exp = '<p>\nbar %% foo\n</p>'

        self.converter.wiki_contents = src
        self.converter.convert()
        self.assertEqual(self.converter.html, exp)
