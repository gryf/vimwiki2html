import argparse
import os
import tempfile
import unittest
from unittest import mock

from vw2html import cli


class TestCliMisc(unittest.TestCase):

    @mock.patch("vw2html.cli.parse_args")
    @mock.patch("vw2html.cli.VimWiki2HTMLConverter")
    def test_main(self, vw2hc, args):
        args.return_value = mock.MagicMock()
        converted = mock.MagicMock()
        obj = vw2hc()
        obj.convert.return_value = converted
        self.assertEqual(cli.main(), converted)

    def test_abspath(self):
        os.environ['FOO'] = '/tmp/bar'
        self.assertEqual('/tmp/foo', cli.abspath("/tmp/bar/../baz/../foo"))
        self.assertEqual('/tmp/foo', cli.abspath("$FOO/../foo"))

    def test__validate_file_or_dir(self):
        fd, fname = tempfile.mkstemp()
        os.close(fd)
        self.assertEqual(cli._validate_file_or_dir(fname), fname)
        os.unlink(fname)
        self.assertRaises(argparse.ArgumentTypeError,
                          cli._validate_file_or_dir, fname)

    def test__validate_outoput(self):
        # assuming, there is no way for creating anything by test user on root
        # tree
        self.assertRaises(argparse.ArgumentTypeError,
                          cli._validate_output, '/foo')

        # and creating files on / tree.
        self.assertRaises(argparse.ArgumentTypeError,
                          cli._validate_output, '/')

        # fname is not a dir
        fd, fname = tempfile.mkstemp()
        os.close(fd)
        self.assertRaises(argparse.ArgumentTypeError,
                          cli._validate_output, fname)
        # fname is a dir
        os.unlink(fname)
        os.makedirs(fname)
        self.assertEqual(cli._validate_output(fname), fname)


class TestCliMain(unittest.TestCase):

    def setUp(self):
        self._orig_conf_path = cli.CONF_PATH
        fd, cli.CONF_PATH = tempfile.mkstemp()
        os.close(fd)
        self._output = tempfile.mkdtemp()
        fd, self._source = tempfile.mkstemp(suffix='.wiki')
        os.close(fd)
        self._source_dir = tempfile.mkdtemp()
        fd, self._template = tempfile.mkstemp(suffix='.tpl')
        os.close(fd)
        fd, self._css = tempfile.mkstemp(suffix='.css')
        os.close(fd)

    def tearDown(self):
        os.unlink(self._source)
        try:
            os.rmdir(self._output)
        except FileNotFoundError:
            pass
        os.rmdir(self._source_dir)
        os.unlink(self._template)
        os.unlink(self._css)
        os.unlink(cli.CONF_PATH)
        cli.CONF_PATH = self._orig_conf_path

    def test_init(self):
        args = argparse.Namespace(root=os.path.dirname(self._source),
                                  template=None, stylesheet=None,
                                  source=self._source, output=self._output,
                                  config=cli.CONF_PATH, force=False)
        vw2hc = cli.VimWiki2HTMLConverter(args)
        self.assertIsInstance(vw2hc, cli.VimWiki2HTMLConverter)
        self.assertEqual(vw2hc.path, os.path.dirname(self._source))
        self.assertEqual(vw2hc._template, '<html><head><title>VimWiki</title>'
                         '<link rel="Stylesheet" type="text/css" '
                         'href="%root_path%%css%" /></head>'
                         '<body>%content%</body></html>')
        self.assertIsNone(vw2hc.css_name)

    def test_read_conf_no_config_no_root(self):
        args = argparse.Namespace(root=None, template=None, stylesheet=None,
                                  source=self._source, output=self._output,
                                  config=cli.CONF_PATH)

        self.assertRaises(ValueError, cli.VimWiki2HTMLConverter, args)

    def test_read_conf_no_config(self):
        args = argparse.Namespace(root=self._source, template=None,
                                  stylesheet=None, source=self._source,
                                  output=self._output, config=cli.CONF_PATH,
                                  force=False)

        conv = cli.VimWiki2HTMLConverter(args)
        self.assertIsInstance(conv, cli.VimWiki2HTMLConverter)
        self.assertEqual(conv.path, self._source)
        self.assertEqual(conv.path_html, self._output)
        self.assertEqual(conv.index, cli.VimWiki2HTMLConverter.index)
        self.assertEqual(conv.ext, cli.VimWiki2HTMLConverter.ext)
        self.assertEqual(conv.template_path, conv.path)
        self.assertEqual(conv.template_default,
                         cli.VimWiki2HTMLConverter.template_default)
        self.assertEqual(conv.template_ext,
                         cli.VimWiki2HTMLConverter.template_ext)
        self.assertIsNone(conv.css_name)

    def test_read_conf_read_good_conf(self):
        args = argparse.Namespace(root=self._source, template=None,
                                  stylesheet=None, source=self._source,
                                  output=self._output, config=cli.CONF_PATH,
                                  force=False)
        with open(cli.CONF_PATH, 'w') as fobj:
            fobj.write('wrong stuff = even more wrong')

        conv = cli.VimWiki2HTMLConverter(args)

        self.assertIsInstance(conv, cli.VimWiki2HTMLConverter)
        self.assertEqual(conv.path,  self._source)
        self.assertEqual(conv.path_html, self._output)
        self.assertEqual(conv.index, cli.VimWiki2HTMLConverter.index)
        self.assertEqual(conv.ext, cli.VimWiki2HTMLConverter.ext)
        self.assertEqual(conv.template_path, conv.path)
        self.assertEqual(conv.template_default,
                         cli.VimWiki2HTMLConverter.template_default)
        self.assertEqual(conv.template_ext,
                         cli.VimWiki2HTMLConverter.template_ext)
        self.assertIsNone(conv.css_name)
