import unittest
from unittest import mock

from vw2html.html import VimWiki2Html


class TestTextAttrs(unittest.TestCase):

    def setUp(self):
        self.converter = VimWiki2Html('/tmp/wiki/foo.wiki', '/tmp/wiki',
                                      '/tmp/wiki_html', [])
        # don't read any file
        self.converter.read_wiki_file = mock.MagicMock(return_value=None)

    def test_bold(self):
        src = '*foo*'
        exp = '<p>\n<strong>foo</strong>\n</p>'

        self.converter.wiki_contents = src
        self.converter.convert()
        self.assertEqual(self.converter.html, exp)

    def test_double_bold(self):
        src = 'Nullam **adipiscing** ante.'

        exp = '<p>\nNullam *<strong>adipiscing</strong>* ante.\n</p>'

        self.converter.wiki_contents = src
        self.converter.convert()
        self.assertEqual(self.converter.html, exp)

    def test_no_bold_space_before_opening_word(self):
        src = 'Nullam * adipiscing* ante.'

        exp = '<p>\nNullam * adipiscing* ante.\n</p>'

        self.converter.wiki_contents = src
        self.converter.convert()
        self.assertEqual(self.converter.html, exp)

    def test_no_bold_space_before_closing_word(self):
        src = 'Nullam *adipiscing uada *ante.'

        exp = '<p>\nNullam *adipiscing uada *ante.\n</p>'

        self.converter.wiki_contents = src
        self.converter.convert()
        self.assertEqual(self.converter.html, exp)

    def test_bold_followed_by_nobold_with_non_whitespace(self):
        src = 'Nullam *adip*!iscing *uada*ante.'

        exp = '<p>\nNullam <strong>adip</strong>!iscing *uada*ante.\n</p>'

        self.converter.wiki_contents = src
        self.converter.convert()
        self.assertEqual(self.converter.html, exp)

    def test_double_bold_extra_asterisk(self):
        src = 'males *uada *venen *atis'
        exp = ('<p>\nmales *uada *venen *atis\n</p>')

        self.converter.wiki_contents = src
        self.converter.convert()
        self.assertEqual(self.converter.html, exp)

    def test_italic(self):
        src = '_foo_'
        exp = ('<p>\n<em>foo</em>\n</p>')

        self.converter.wiki_contents = src
        self.converter.convert()
        self.assertEqual(self.converter.html, exp)

    def test_double_italic(self):
        src = 'text _italic_ text _italic_ again text'
        exp = ('<p>\ntext <em>italic</em> text <em>italic</em> again '
               'text\n</p>')

        self.converter.wiki_contents = src
        self.converter.convert()
        self.assertEqual(self.converter.html, exp)

    def test_double_italic_extra_underscore(self):
        src = 'text _italic_ text _italic_ again_ text'
        exp = ('<p>\ntext <em>italic</em> text <em>italic</em> again_ '
               'text\n</p>')

        self.converter.wiki_contents = src
        self.converter.convert()
        self.assertEqual(self.converter.html, exp)

    def test_bolditalic(self):
        src = '_*bolditalic*_'
        exp = '<p>\n<em><strong>bolditalic</strong></em>\n</p>'

        self.converter.wiki_contents = src
        self.converter.convert()
        self.assertEqual(self.converter.html, exp)

    def test_italicbold(self):
        src = '*_bolditalic_*'
        exp = '<p>\n<strong><em>bolditalic</em></strong>\n</p>'

        self.converter.wiki_contents = src
        self.converter.convert()
        self.assertEqual(self.converter.html, exp)

    def test_italic_bold_crossed_extra_asterisk(self):
        src = '*_bold* and italic_ *text'
        exp = '<p>\n<strong><em>bold</strong> and italic</em> *text\n</p>'

        self.converter.wiki_contents = src
        self.converter.convert()
        self.assertEqual(self.converter.html, exp)

    def test_strikeout(self):
        src = '~~strikeout~~'
        exp = '<p>\n<del>strikeout</del>\n</p>'

        self.converter.wiki_contents = src
        self.converter.convert()
        self.assertEqual(self.converter.html, exp)

    def test_strikeout_with_extra_tilda(self):
        # IMHO this one doesn't makes sense - the pattern should be:
        # re.compile(r'~{2}([^\s].*?[^\s])~{2}') so that it wont match when
        # spaces exists around ~~ and allows single ~ inside.
        src = '~~ strike~out ~~'
        exp = '<p>\n~~ strike~out ~~\n</p>'

        self.converter.wiki_contents = src
        self.converter.convert()
        self.assertEqual(self.converter.html, exp)

    def test_double_strikeout_with_extra_tilda(self):
        src = '~~strike out~~ and ~~ again~~ text ~'
        exp = '<p>\n<del>strike out</del> and <del> again</del> text ~\n</p>'

        self.converter.wiki_contents = src
        self.converter.convert()
        self.assertEqual(self.converter.html, exp)

    def test_bold_strikeout_crossed(self):
        src = '~~*bold* and crossed out~~ *text~~'
        exp = ('<p>\n<del><strong>bold</strong> and crossed out</del> '
               '*text~~\n</p>')

        self.converter.wiki_contents = src
        self.converter.convert()
        self.assertEqual(self.converter.html, exp)

    def test_nested_attrs(self):
        src = '*bold _italic ~~strikeout~~ no crosed* not bold_ nor italic.'
        exp = ('<p>\n<strong>bold <em>italic <del>strikeout</del> no '
               'crosed</strong> not bold</em> nor italic.\n</p>')

        self.converter.wiki_contents = src
        self.converter.convert()
        self.assertEqual(self.converter.html, exp)

    def test_superscript(self):
        src = 'square^2^'
        exp = ('<p>\nsquare<sup><small>2</small></sup>\n</p>')

        self.converter.wiki_contents = src
        self.converter.convert()
        self.assertEqual(self.converter.html, exp)

    def test_superscript_additional_caret(self):
        src = 'square^^2^^'
        exp = ('<p>\nsquare^<sup><small>2</small></sup>^\n</p>')

        self.converter.wiki_contents = src
        self.converter.convert()
        self.assertEqual(self.converter.html, exp)

    def test_subscript(self):
        src = 'meh,,2,,'
        exp = ('<p>\nmeh<sub><small>2</small></sub>\n</p>')

        self.converter.wiki_contents = src
        self.converter.convert()
        self.assertEqual(self.converter.html, exp)

    def test_subscript_extra_space(self):
        src = 'meh ,, 2 ,,'
        exp = ('<p>\nmeh <sub><small> 2 </small></sub>\n</p>')

        self.converter.wiki_contents = src
        self.converter.convert()
        self.assertEqual(self.converter.html, exp)

    def test_subscript_empty(self):
        src = 'meh ,,,,'
        exp = ('<p>\nmeh ,,,,\n</p>')

        self.converter.wiki_contents = src
        self.converter.convert()
        self.assertEqual(self.converter.html, exp)
