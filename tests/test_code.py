import unittest
from unittest import mock

from vw2html import html


class TestCode(unittest.TestCase):

    def setUp(self):
        # don't read any file
        html.VimWiki2Html.read_wiki_file = mock.MagicMock(return_value=None)
        self.converter = html.VimWiki2Html('/tmp/src/foo.wiki', '/tmp/out',
                                           '/tmp/src')
        html.pygments = mock.MagicMock()

    def test_multiline_pre(self):
        src = '{{{\n*foo*\n}}}'
        exp = '<p>\n<pre class="code literal-block">\n*foo*</pre>\n</p>'

        self.converter.wiki_contents = src
        self.converter.convert()
        self.assertEqual(self.converter.html, exp)

    def test_multiline_pre_highlight(self):
        src = '{{{type=py\nprint("meh")\n}}}'
        retval = "whatever pygments.highlight returns"
        html.pygments.highlight.return_value = retval
        exp = f'<p>\n{retval}\n</p>'

        self.converter.wiki_contents = src
        self.converter.convert()
        self.assertEqual(self.converter.html, exp)

    def test_multiline_pre_indent(self):
        src = '    {{{\n  foo\n    }}}'
        exp = '<p>\n    <pre class="code literal-block">\n  foo</pre>\n</p>'

        self.converter.wiki_contents = src
        self.converter.convert()
        self.assertEqual(self.converter.html, exp)

    def test_multiline_pre_containing_closing(self):
        src = '{{{\nfoo\n}}}x\n}}}'
        exp = '<p>\n<pre class="code literal-block">\nfoo\n}}}x</pre>\n</p>'

        self.converter.wiki_contents = src
        self.converter.convert()
        self.assertEqual(self.converter.html, exp)

    def test_multiline_pre_containing_closing2(self):
        src = '{{{\nfoo\nx }}}\n}}}'
        exp = '<p>\n<pre class="code literal-block">\nfoo\nx }}}</pre>\n</p>'

        self.converter.wiki_contents = src
        self.converter.convert()
        self.assertEqual(self.converter.html, exp)

    def test_multiline_pre_invalid_opening(self):
        src = 'foo {{{\nbar\n}}}'
        exp = '<p>\nfoo {{{\nbar\n}}}\n</p>'

        self.converter.wiki_contents = src
        self.converter.convert()
        self.assertEqual(self.converter.html, exp)

    def test_inline_code(self):
        src = '`foo`'
        exp = '<p>\n<code>foo</code>\n</p>'

        self.converter.wiki_contents = src
        self.converter.convert()
        self.assertEqual(self.converter.html, exp)

    def test_inline_double_code(self):
        src = '`foo` and `bar`'
        exp = '<p>\n<code>foo</code> and <code>bar</code>\n</p>'

        self.converter.wiki_contents = src
        self.converter.convert()
        self.assertEqual(self.converter.html, exp)

    def test_inline_multiline_triple_code(self):
        src = '`foo`, `bar`\nand `baz`'
        exp = ('<p>\n<code>foo</code>, '
               '<code>bar</code>\nand <code>baz</code>\n</p>')

        self.converter.wiki_contents = src
        self.converter.convert()
        self.assertEqual(self.converter.html, exp)

    def test_inline_code_invalid(self):
        src = '`foo` and ```'
        exp = '<p>\n<code>foo</code> and ```\n</p>'

        self.converter.wiki_contents = src
        self.converter.convert()
        self.assertEqual(self.converter.html, exp)

    def test_inline_code_colors_black(self):
        src = '`#000000`'
        exp = ("<p>\n<code style='background-color:#000000;color:white;'>"
               "#000000</code>\n</p>")

        self.converter.wiki_contents = src
        self.converter.convert()
        self.assertEqual(self.converter.html, exp)

    def test_inline_code_colors_white(self):
        src = '`#FFFFFF`'
        exp = ("<p>\n<code style='background-color:#FFFFFF;color:black;'>"
               "#FFFFFF</code>\n</p>")

        self.converter.wiki_contents = src
        self.converter.convert()
        self.assertEqual(self.converter.html, exp)

    def test_inline_code_colors_orange(self):
        src = '`#ff8800`'
        exp = ("<p>\n<code style='background-color:#ff8800;color:black;'>"
               "#ff8800</code>\n</p>")

        self.converter.wiki_contents = src
        self.converter.convert()
        self.assertEqual(self.converter.html, exp)
