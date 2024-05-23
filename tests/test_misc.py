import datetime
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

    def test_multiline_comments(self):
        src = ('Pharetra  rhoncus *massa. %%+Cras et* ligula vel '
               'quam\ntristique commodo. Sed est lectus, mollis quis, '
               'lacinia nec,\n\n+%%Vestibulum _ante `ipsum primis %%+in_ '
               'faucibus` orci \nluctus et ultrices posuere cubilia Curae; '
               'Morbi urna dui, \nfermentum quis, feugiat imperdiet, '
               'imperdiet id, +%%sapien.  \n')
        exp = ('<p>\nPharetra  rhoncus *massa. Vestibulum _ante `ipsum primis'
               ' sapien.  \n\n</p>')

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


class TestTemplatePlaceholder(unittest.TestCase):

    def setUp(self):
        # don't read any file
        self.converter = VimWiki2Html('/tmp/src/foo.wiki', '/tmp/out',
                                      '/tmp/src')

    def test_template_without_arg(self):
        src = '%template'

        mock_open = mock.mock_open(read_data=src)
        with mock.patch("builtins.open", mock_open):
            self.converter.convert()
        self.assertIsNone(self.converter.template)

    def test_no_template(self):
        src = 'template'

        mock_open = mock.mock_open(read_data=src)
        with mock.patch("builtins.open", mock_open):
            self.converter.convert()
        self.assertIsNone(self.converter.template)

    def test_custom_template(self):
        src = '\n           %template   bar           \n'

        mock_open = mock.mock_open(read_data=src)
        with mock.patch("builtins.open", mock_open):
            self.converter.convert()
        self.assertEqual(self.converter.template, '/tmp/src/bar.tpl')


class TestDatePlaceholder(unittest.TestCase):

    def setUp(self):
        # don't read any file
        self.converter = VimWiki2Html('/tmp/src/foo.wiki', '/tmp/out',
                                      '/tmp/src')

    def test_no_date(self):
        src = 'date'

        mock_open = mock.mock_open(read_data=src)
        with mock.patch("builtins.open", mock_open):
            self.converter.convert()
        self.assertEqual(self.converter.date, '')

    def test_date_set_to_now(self):
        src = '\n           %date \n'

        mock_open = mock.mock_open(read_data=src)
        with mock.patch("builtins.open", mock_open):
            self.converter.convert()
        self.assertEqual(self.converter.date,
                         datetime.datetime.now().strftime('%Y-%m-%d'))

    def test_date_set_to_date(self):
        src = '\n           %date 1984-06-08   \n'

        mock_open = mock.mock_open(read_data=src)
        with mock.patch("builtins.open", mock_open):
            self.converter.convert()
        self.assertEqual(self.converter.date, '1984-06-08')


class TestPlainHTMLPlaceholder(unittest.TestCase):

    def setUp(self):
        # don't read any file
        self.converter = VimWiki2Html('/tmp/src/foo.wiki', '/tmp/out',
                                      '/tmp/src')

    def test_no_placeholder(self):
        src = 'foo'

        mock_open = mock.mock_open(read_data=src)
        with mock.patch("builtins.open", mock_open):
            self.converter.convert()
        self.assertEqual(self.converter.html, '<p>\nfoo\n</p>')

    def test_placeholder_with_suffix(self):
        src = 'foo %plainhtml <i>bar</i>'

        mock_open = mock.mock_open(read_data=src)
        with mock.patch("builtins.open", mock_open):
            self.converter.convert()
        self.assertEqual(self.converter.html, '<i>bar</i>')

    def test_double_placeholder(self):
        src = '%plainhtml <div>\nmeh\n%plainhtml <i>bar</i>'

        mock_open = mock.mock_open(read_data=src)
        with mock.patch("builtins.open", mock_open):
            self.converter.convert()
        self.assertEqual(self.converter.html,
                         '<div>\n<p>\nmeh\n</p>\n<i>bar</i>')
