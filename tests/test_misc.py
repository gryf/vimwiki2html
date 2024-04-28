import unittest
from unittest import mock

from vw2html.html import VimWiki2Html


class TestComments(unittest.TestCase):

    def setUp(self):
        self.converter = VimWiki2Html('/tmp/src/foo.wiki', '/tmp/out',
                                      '/tmp/src')
        # don't read any file
        self.converter.read_wiki_file = mock.MagicMock(return_value=None)

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


class TestTitlePlaceholder(unittest.TestCase):

    def setUp(self):
        self.converter = VimWiki2Html('/tmp/src/foo.wiki', '/tmp/out',
                                      '/tmp/src')
        # don't read any file
        self.converter.read_wiki_file = mock.MagicMock(return_value=None)

    def test_no_title_unset(self):
        src = 'title'

        self.converter.wiki_contents = src
        self.converter.convert()
        # same as filename without path and extension
        self.assertEqual(self.converter.title, 'foo')

    def test_title_unset(self):
        src = '%title'

        self.converter.wiki_contents = src
        self.converter.convert()
        # same as filename without path and extension
        self.assertEqual(self.converter.title, 'foo')

    def test_title_set(self):
        src = '%title bar'

        self.converter.wiki_contents = src
        self.converter.convert()
        self.assertEqual(self.converter.title, 'bar')

    def test_title_fancy(self):
        src = '\n       %title    My great Title!\nand stuff'

        self.converter.wiki_contents = src
        self.converter.convert()
        self.assertEqual(self.converter.title, 'My great Title!')


class TestNoHtmlPlaceholder(unittest.TestCase):

    def setUp(self):
        # don't read any file
        self.converter = VimWiki2Html('/tmp/src/foo.wiki', '/tmp/out',
                                      '/tmp/src')

    def test_nohtml_set(self):
        src = '%nohtml'

        mock_open = mock.mock_open(read_data=src)
        with mock.patch("builtins.open", mock_open):
            self.converter.convert()
        self.assertTrue(self.converter.nohtml)

    def test_nohtml_fancy(self):
        src = '\n           %nohtml              \n'

        mock_open = mock.mock_open(read_data=src)
        with mock.patch("builtins.open", mock_open):
            self.converter.convert()
        self.assertTrue(self.converter.nohtml)
