import unittest
from unittest import mock

from vw2html import html

from vw2html import cli


class TestTable(unittest.TestCase):

    @mock.patch.multiple('vw2html.cli.VimWiki2HTMLConverter',
                        update=mock.MagicMock(return_value=None),
                        read_config=mock.MagicMock(return_value=None))

    def setUp(self):
        conf = cli.VimWiki2HTMLConverter(mock.MagicMock())
        conf.path = '/tmp/wiki'
        conf.path_html = '/tmp/wiki_html'
        self.converter = html.VimWiki2Html('/tmp/src/foo.wiki', conf)
        # don't read any file
        self.converter.read_wiki_file = mock.MagicMock(return_value=None)

    def test_table_align(self):
        src = '\n'.join(['| foo | bar | baz |',
                         '|---| :-: | -:    |',
                         '|1 |2 |3|'])
        exp = ('<table>'
               '<thead>\n'
               '<tr>'
               '<th> foo </th>'
               '<th class="cell-center"> bar </th>'
               '<th class="cell-right"> baz </th>'
               '</tr>\n'
               '</thead>'
               '<tbody>'
               '<tr>'
               '<td>1 </td>'
               '<td class="cell-center">2 </td>'
               '<td class="cell-right">3</td>'
               '</tr>'
               '</tbody>'
               '</table>')

        self.converter.wiki_contents = src
        self.converter.convert()
        self.assertEqual(self.converter.html, exp)

    def test_table_align2(self):
        src = '\n'.join(['|foo|bar|baz|',
                         '|---|:-----:|---:|',
                         '|1|2|3|'])
        exp = ('<table>'
               '<thead>\n'
               '<tr>'
               '<th>foo</th>'
               '<th class="cell-center">bar</th>'
               '<th class="cell-right">baz</th>'
               '</tr>\n'
               '</thead>'
               '<tbody>'
               '<tr>'
               '<td>1</td>'
               '<td class="cell-center">2</td>'
               '<td class="cell-right">3</td>'
               '</tr>'
               '</tbody>'
               '</table>')

        self.converter.wiki_contents = src
        self.converter.convert()
        self.assertEqual(self.converter.html, exp)

    def test_table_align3(self):
        src = '\n'.join(['|    foo | bar      |baz        |',
                         '|---        |           :-----:|       ---:   |',
                         '|1|2|3|'])
        exp = ('<table>'
               '<thead>\n'
               '<tr>'
               '<th>    foo </th>'
               '<th class="cell-center"> bar      </th>'
               '<th class="cell-right">baz        </th>'
               '</tr>\n'
               '</thead>'
               '<tbody>'
               '<tr>'
               '<td>1</td>'
               '<td class="cell-center">2</td>'
               '<td class="cell-right">3</td>'
               '</tr>'
               '</tbody>'
               '</table>')

        self.converter.wiki_contents = src
        self.converter.convert()
        self.assertEqual(self.converter.html, exp)
