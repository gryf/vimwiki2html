import os
import unittest
from unittest import mock

from vw2html import cli
from vw2html import html


class TestWikiLink(unittest.TestCase):
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
        self._home = os.environ['HOME']
        os.environ['HOME'] = '/home/foo'

    def tearDown(self):
        os.environ['HOME'] = self._home

    def test_wiki_link(self):
        src = '[[foo]]'
        exp = '<p>\n<a href="foo.html">foo</a>\n</p>'

        self.converter.wiki_contents = src
        self.converter.convert()
        self.assertEqual(self.converter.html, exp)

    def test_relative_wiki_link(self):
        src = '[[../foo]]'
        exp = '<p>\n<a href="../foo.html">../foo</a>\n</p>'

        self.converter.wiki_contents = src
        self.converter.convert()
        self.assertEqual(self.converter.html, exp)

    def test_relative_wiki_link_root(self):
        src = '[[/foo]]'
        exp = '<p>\n<a href="foo.html">/foo</a>\n</p>'

        self.converter.wiki_contents = src
        self.converter.convert()
        self.assertEqual(self.converter.html, exp)

    def test_absolute_wiki_link(self):
        src = '[[///tmp/foo]]'
        exp = '<p>\n<a href="/tmp/foo.html">///tmp/foo</a>\n</p>'

        self.converter.wiki_contents = src
        self.converter.convert()
        self.assertEqual(self.converter.html, exp)

    def test_absolute_directory_wiki_link(self):
        src = '[[///tmp/foo/]]'
        exp = '<p>\n<a href="/tmp/foo/">///tmp/foo/</a>\n</p>'

        self.converter.wiki_contents = src
        self.converter.convert()
        self.assertEqual(self.converter.html, exp)

    def test_anchors(self):
        src = '[[index#The Diary]]'
        exp = '<p>\n<a href="index.html#The Diary">index#The Diary</a>\n</p>'

        self.converter.wiki_contents = src
        self.converter.convert()
        self.assertEqual(self.converter.html, exp)

    def test_raw_url(self):
        src = 'meh https://meh.us foo'
        exp = '<p>\nmeh <a href="https://meh.us">https://meh.us</a> foo\n</p>'

        self.converter.wiki_contents = src
        self.converter.convert()
        self.assertEqual(self.converter.html, exp)

    def test_multiline_url_not_supported(self):
        src = '[[https://meh.us|desc\nfoo]]'
        exp = ('<p>\n[[<a href="https://meh.us|'
               'desc">https://meh.us|desc</a>\nfoo]]\n</p>')

        self.converter.wiki_contents = src
        self.converter.convert()
        self.assertEqual(self.converter.html, exp)

    def test_external_link(self):
        src = '[[file:$HOME/file.txt]]'
        exp = '<p>\n<a href="/home/foo/file.txt">file:$HOME/file.txt</a>\n</p>'

        self.converter.wiki_contents = src
        self.converter.convert()
        self.assertEqual(self.converter.html, exp)

    def test_external_link_with_bracets_in_desc(self):
        src = '[[https://meh.us|[d]esc]]'
        exp = '<p>\n<a href="https://meh.us">[d]esc</a>\n</p>'

        self.converter.wiki_contents = src
        self.converter.convert()
        self.assertEqual(self.converter.html, exp)

    def test_external_link_with_single_arbitrary_attrs(self):
        src = '[[https://meh.us|desc|class="foo"]]'
        exp = '<p>\n<a href="https://meh.us" class="foo">desc</a>\n</p>'

        self.converter.wiki_contents = src
        self.converter.convert()
        self.assertEqual(self.converter.html, exp)

    def test_external_link_with_arbitrary_attrs(self):
        src = '[[https://meh.us|desc|class="foo" data="bar"]]'
        exp = ('<p>\n<a href="https://meh.us" class="foo" data="bar">'
               'desc</a>\n</p>')

        self.converter.wiki_contents = src
        self.converter.convert()
        self.assertEqual(self.converter.html, exp)

# TODO: add tests for transclusions, relative external links and diary
