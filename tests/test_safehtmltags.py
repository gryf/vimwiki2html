import unittest
from unittest import mock

from vw2html.html import VimWiki2Html
from vw2html.html import re_safe_html


class TestSafeHTMLTags(unittest.TestCase):

    def setUp(self):
        self.converter = VimWiki2Html('/tmp/src/foo.wiki', '/tmp/wiki',
                                      '/tmp/wiki_html', [])
        # don't read any file
        self.converter.read_wiki_file = mock.MagicMock(return_value=None)

    def test_safe_tags(self):
        # currently there are several hardcoded HTML tags supported in
        # vimwiki. The caveat with that is the list is configurable in vimwiki,
        # and vw2html does nothing about such list.
        tags = str(re_safe_html).split('?!(?:')[1].split('))')[0].split('|')

        for tag in tags:
            src = f'<{tag}>foo</{tag}>'
            exp = f'<p>\n<{tag}>foo</{tag}>\n</p>'

            self.converter.wiki_contents = src
            self.converter.convert()
            self.assertEqual(self.converter.html, exp)
            self.setUp()

    def test_unsafe_tags(self):
        src = '<foobar>foo</foobar>'
        exp = '<p>\n&lt;foobar&gt;foo&lt;/foobar&gt;\n</p>'

        self.converter.wiki_contents = src
        self.converter.convert()
        self.assertEqual(self.converter.html, exp)

    def test_nestetd_safe_unsafe(self):
        src = '<b><x>foo</x> bar</b>'
        exp = '<p>\n<b>&lt;x&gt;foo&lt;/x&gt; bar</b>\n</p>'

        self.converter.wiki_contents = src
        self.converter.convert()
        self.assertEqual(self.converter.html, exp)

    def test_nestetd_unsafe_safe(self):
        src = '<x><center>foo</center> bar</x>'
        exp = '<p>\n&lt;x&gt;<center>foo</center> bar&lt;/x&gt;\n</p>'

        self.converter.wiki_contents = src
        self.converter.convert()
        self.assertEqual(self.converter.html, exp)

    def test_safe_in_table(self):
        src = '| <center>foo</center> bar | ✓ |'
        exp = ('<table><tbody><tr>'
               '<td> <center>foo</center> bar </td>'
               '<td> ✓ </td>'
               '</tr></tbody></table>')
        self.converter.wiki_contents = src
        self.converter.convert()
        self.assertEqual(self.converter.html, exp)

