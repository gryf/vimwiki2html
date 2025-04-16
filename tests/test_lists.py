import unittest
from unittest import mock

from vw2html.html import VimWiki2Html


class TestULOL(unittest.TestCase):
    def setUp(self):
        self.converter = VimWiki2Html('/tmp/src/foo.wiki', '/tmp/wiki',
                                      '/tmp/wiki_html', [])
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

    def test_sorted_nested_list(self):
        src = '# foo\n # bar\n# baz'
        exp = ('<ol>\n<li>\nfoo\n'
               '<ol>\n<li>\nbar\n</li>\n</ol>\n'
               '\n</li>\n<li>\nbaz\n</li>\n</ol>\n')

        self.converter.wiki_contents = src
        self.converter.convert()
        self.assertEqual(self.converter.html, exp)

    def test_sorted_more_nested_list(self):
        src = '# foo\n # bar\n  # baz\n# meh'
        exp = ('<ol>\n<li>\nfoo\n'
               '<ol>\n<li>\nbar\n'
               '<ol>\n<li>\nbaz\n</li>\n</ol>\n\n</li>\n</ol>\n\n</li>\n'
               '<li>\nmeh\n</li>\n</ol>\n')

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
        exp = ('<p>\nmeh\n</p>\n\n<ol>\n<li>\nfoo\n</li>\n</ol>\n\n'
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


class TestDL(unittest.TestCase):

    def setUp(self):
        self.converter = VimWiki2Html('/tmp/src/foo.wiki', '/tmp/wiki',
                                      '/tmp/wiki_html', [])
        # don't read any file
        self.converter.read_wiki_file = mock.MagicMock(return_value=None)

    def test_simple_definition(self):
        src = 'title:: definition\n'
        exp = '<dl>\n<dt>title</dt>\n<dd>\n<p>definition</p>\n</dd>\n</dl>\n'

        self.converter.wiki_contents = src
        self.converter.convert()
        self.assertEqual(self.converter.html, exp)

    def test_simple_two_lines_definition(self):
        src = ('title:: definition\n'
               '        continuation\n')
        exp = ('<dl>\n<dt>title</dt>\n'
               '<dd>\n<p>definition continuation</p>\n</dd>\n'
               '</dl>\n')

        self.converter.wiki_contents = src
        self.converter.convert()
        self.assertEqual(self.converter.html, exp)

    def test_several_definitions(self):
        src = ('title1:: definition1\n'
               'title2:: definition2\n')
        exp = ('<dl>\n'
               '<dt>title1</dt>\n'
               '<dd>\n<p>definition1</p>\n</dd>\n'
               '<dt>title2</dt>\n'
               '<dd>\n<p>definition2</p>\n</dd>\n'
               '</dl>\n')

        self.converter.wiki_contents = src
        self.converter.convert()
        self.assertEqual(self.converter.html, exp)

    def test_several_definitions_two_lines_definition(self):
        src = ('title1:: definition1\n'
               '         continuation\n'
               'title2:: definition2\n')
        exp = ('<dl>\n'
               '<dt>title1</dt>\n'
               '<dd>\n<p>definition1 continuation</p>\n</dd>\n'
               '<dt>title2</dt>\n'
               '<dd>\n<p>definition2</p>\n</dd>\n'
               '</dl>\n')

        self.converter.wiki_contents = src
        self.converter.convert()
        self.assertEqual(self.converter.html, exp)

    def test_two_paragraphs_in_definition(self):
        src = ('title1:: definition1\n'
               '\n'
               '         continuation\n')
        exp = ('<dl>\n'
               '<dt>title1</dt>\n'
               '<dd>\n<p>definition1</p>\n<p>continuation</p>\n</dd>\n'
               '</dl>\n')

        self.converter.wiki_contents = src
        self.converter.convert()
        self.assertEqual(self.converter.html, exp)
