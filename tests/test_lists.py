import unittest
from unittest import mock

from vw2html.html import VimWiki2Html


class TestUL(unittest.TestCase):
    def setUp(self):
        self.converter = VimWiki2Html('/tmp/src/foo.wiki', '/tmp/out',
                                      '/tmp/src')
        # don't read any file
        self.converter.read_wiki_file = mock.MagicMock(return_value=None)

    def test_unsorted_list_single_element(self):
        src = '* foo'
        exp = '<ul>\n<li>\nfoo\n</li>\n</ul>\n'

        self.converter.wiki_contents = src
        self.converter.convert()
        self.assertEqual(self.converter.html, exp)

    def test_unsorted_list_three_elements(self):
        src = '- foo\n- bar\n- baz'
        exp = ('<ul>\n<li>\nfoo\n</li>\n<li>\nbar\n</li>\n'
               '<li>\nbaz\n</li>\n</ul>\n')

        self.converter.wiki_contents = src
        self.converter.convert()
        self.assertEqual(self.converter.html, exp)

    def test_unsorted_nested_list(self):
        src = '# foo\n # bar\n# baz'
        exp = ('<ul>\n<li>\nfoo\n'
               '<ul>\n<li>\nbar\n</li>\n</ul>\n'
               '\n</li>\n<li>\nbaz\n</li>\n</ul>\n')

        self.converter.wiki_contents = src
        self.converter.convert()
        self.assertEqual(self.converter.html, exp)

    def test_unsorted_more_nested_list(self):
        src = '# foo\n # bar\n  # baz\n# meh'
        exp = ('<ul>\n<li>\nfoo\n'
               '<ul>\n<li>\nbar\n'
               '<ul>\n<li>\nbaz\n</li>\n</ul>\n\n</li>\n</ul>\n\n</li>\n'
               '<li>\nmeh\n</li>\n</ul>\n')

        self.converter.wiki_contents = src
        self.converter.convert()
        self.assertEqual(self.converter.html, exp)

    def test_todo_list(self):
        src = '* [ ] foo\n* [.] bar\n'
        exp = ('<ul>\n<li class="done0">\nfoo\n</li>\n'
               '<li class="done1">\nbar\n</li>\n'
               '</ul>\n')

        self.converter.wiki_contents = src
        self.converter.convert()
        self.assertEqual(self.converter.html, exp)

    def test_todo_nested_list(self):
        src = '* [ ] foo\n  * [.] bar\n'
        exp = ('<ul>\n<li class="done0">\nfoo\n'
               '<ul>\n<li class="done1">\nbar\n</li>\n</ul>\n'
               '\n</li>\n</ul>\n')

        self.converter.wiki_contents = src
        self.converter.convert()
        self.assertEqual(self.converter.html, exp)

    def test_todo_invalid_item(self):
        src = '* [ ] foo\n* [z] bar\n'
        exp = ('<ul>\n<li class="done0">\nfoo\n</li>\n'
               '<li>\nbar\n</li>\n'
               '</ul>\n')

        self.converter.wiki_contents = src
        self.converter.convert()
        self.assertEqual(self.converter.html, exp)

    def test_two_lists(self):
        src = '1) foo\n\n1) bar\n'
        exp = ('<ol>\n<li>\nfoo\n</li>\n</ol>\n\n'
               '<ol>\n<li>\nbar\n</li>\n</ol>\n')

        self.converter.wiki_contents = src
        self.converter.convert()
        self.assertEqual(self.converter.html, exp)

    def test_two_indented_lists(self):
        src = 'meh\n\n  3. foo\n1. bar\n'
        exp = ('<p>\nmeh\n\n</p>\n\n<ol>\n<li>\nfoo\n</li>\n</ol>\n\n'
               '<ol>\n<li>\nbar\n</li>\n</ol>\n')

        self.converter.wiki_contents = src
        self.converter.convert()
        self.assertEqual(self.converter.html, exp)

    def test_single_list_separated_by_indent(self):
        src = '2) foo\n1) bar\n   \n4) baz\n'
        exp = ('<ol>\n<li>\nfoo\n</li>\n'
               '<li>\nbar\n\n</li>\n'
               '<li>\nbaz\n</li>\n</ol>\n')

        self.converter.wiki_contents = src
        self.converter.convert()
        self.assertEqual(self.converter.html, exp)
