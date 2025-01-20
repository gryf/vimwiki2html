import argparse
import dataclasses
import logging
import os
import shutil
import sys
import tomllib

import vw2html

LOG = logging.getLogger()
XDG_CONFIG_HOME = os.getenv('XDG_CONFIG_HOME',
                                os.path.expanduser('~/.config'))
CONF_PATH = os.path.join(XDG_CONFIG_HOME, 'vw2html.toml')


def abspath(path: str) -> str:
    return os.path.abspath(os.path.expanduser(os.path.expandvars(path)))


class VimWiki2HTMLConverter:
    # Root path for the wiki, potentially used in templates and is set if
    # provided source is a directory. If single file is provided, path
    # must be set either by configuration, or through commandline.
    path: str = None  # '~/vimwiki'
    # HTML output directory
    path_html: str = ''
    # Main file. Usually index. If no other index is found, it will be
    # renamed to index anyway.
    index: str = 'index'
    # Extension for wiki files
    ext: str = '.wiki'
    # Path to templates. If not specified, will be deducted from the wiki
    # path and defaults to 'templates' directory within
    template_path: str = None  # '~/vimwiki/templates/'
    # Default template without extension.
    template_default: str = 'default'
    # Default template extension.
    template_ext: str = '.tpl'
    # Default CSS file. Note, that it differ from VimWiki behavior, as it
    # means a relative to vimwiki path location, or it might be provided
    # as absolute path not necessary within vimwiki path.
    #
    # Style file will be copied to path_html, including all media (images).
    css_name: str = 'style.css'

    def __init__(self, args):

        # Read config and update class attributes accordingly.
        self.read_config(args.config)

        # Default template to put contents in case there is no default
        # template found. If not provided by the commandline, this are the
        # default template fields:
        # %title% - to be replaced by filename by default, if exists on the
        #           page, will be placed instead
        # %date% - used for placing date
        # %root_path% - root path of the generated content - / by default
        # %wiki_path% - unused
        # %content% - where generated content goes
        self._template = ("<html><head><title>VimWiki</title></head>"
                          "<body>%content%</body></html>")

        # Source files. If single file provided it will be a single item on
        # that list, otherwise provided directory will be scanned for files.
        self._sources = []
        # Assets path with association as fname -> filepath
        self._assets = {}

        self._update(args)
        self.configure()

    def configure(self):
        if not (self.template_path and os.path.exists(self.template_path)):
            LOG.error("Provided template `%s' doesn't exists. Check your "
                      "config/or parameters", self.template_path)
            return
        with open(self.template_path) as fobj:
            self._template = fobj.read()

    def _apply_data_to_template(self, html_obj):
        root_path = '../'.join(['' for _ in range(html_obj.level)])
        template = self._template
        if html_obj.template:
            try:
                with open(html_obj.template) as fobj:
                    template = fobj.read()
            except OSError:
                LOG.exception('Error loading template "%s"', html_obj.template)

        html = template.replace('%content%', html_obj.html)
        html = html.replace('%root_path%', root_path)
        html = html.replace('%title%', html_obj.title)
        html = html.replace('%date%', html_obj.date)
        return html

    def convert(self):
        # copy css file
        if self._css:
            fulldname = os.path.dirname(self._css)
            dst = self._www_path
            if fulldname != self._root:
                dname = fulldname.replace(self._root)[1:]
                os.makedirs(self._www_path, dname)
                dst = os.path.join(self._www_path, dname)
            shutil.copy(self._css, dst)
            # TODO: copy assets from CSS too

        data = [vw2html.html.convert_file(f, self.path_html, self.path)
                for f in self._source]
        for obj in data:
            with open(obj.html_fname, 'w') as fobj:
                fobj.write(self._apply_data_to_template(obj))
        return 0

    def _update(self, args):
        self.path_html = abspath(args.output)
        if args.root:
            self.path = abspath(args.root)

        if not self.path:
            raise ValueError("Root of vimwiki not provided, exiting.")

        if args.template:
            if args.template.endswith(self.template_ext):
                self.template_path = abspath(args.template)
            else:
                self.template_path = args.template + self.template_ext

            if os.path.exists(args.template_path):
                self.template_path = abspath(self.template_path)
            else:
                self.template_path = None
                LOG.error("Provided template path `%s' does not exist",
                          args.template)
        elif os.path.exists(os.path.join(self.path, self.template_default +
                                         self.template_ext)):
            self.template_path = os.path.join(self.path,
                                              self.template_default +
                                              self.template_ext)

        if args.stylesheet:
            css = abspath(args.stylesheet)
            if os.path.exists(css):
                self.css_name = css
            elif self.path and os.path.exists(os.path.join(self.path,
                                                           args.stylesheet)):
                self.css_name = abspath(os.path.join(self.path,
                                                     args.stylesheet))

        if not os.path.exists(self.css_name):
            LOG.error("Provided stylesheet path `%s' does not exist",
                      self.css_name)
            self.css_name = None

        if os.path.isfile(args.source):
            self._sources.append(args.source)
        else:
            self.scan_for_wiki_files()

    def scan_for_wiki_files(self):
        for root, _, files in os.walk(self._wiki_path):
            for fname in files:
                _fname = os.path.join(root, fname)
                if _fname.endswith(self.ext):
                    self._assets.append(_fname)
                else:
                    self._sources.append(_fname)

    def read_config(self, config_file):
        try:
            with open(config_file, "rb") as fobj:
                toml = tomllib.load(fobj)
        except (OSError, ValueError):
            LOG.exception("Exception on reading config file '%s'. Ignoring.",
                          config_file)
            return

        legal_keys = ["css_name", "ext", "index", "path_html",
                      "template_default", "template_default", "template_ext",
                      "template_path", 'path']

        for key in legal_keys:
            if toml.get(key):
                setattr(self, key, toml[key])


def _validate_file_or_dir(path):
    if not os.path.exists(path):
        raise argparse.ArgumentTypeError(f"Provided '{path}' doesn't exists.")
    return path


def _validate_output(path):
    if os.path.exists(path):
        if not os.path.isdir(path):
            msg = f"Path '{path}' exists and it's not a directory"
            raise argparse.ArgumentTypeError(msg)
        LOG.warning('Path "%s" exists. Content might be removed and/or '
                    'overwritten.', path)
        try:
            test_fn = os.path.join(path, 'test.txt')
            with open(test_fn, 'w') as fobj:
                fobj.write('test')
            os.unlink(test_fn)
        except (PermissionError, OSError) as exc:
            msg = f"Cannot access '{path}': {exc.strerror}."
            raise argparse.ArgumentTypeError(msg)
    else:
        try:
            os.makedirs(path)
        except (PermissionError, OSError) as exc:
            msg = f"Cannot create '{path}': {exc.strerror}."
            raise argparse.ArgumentTypeError(msg)
    return path


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('-v', '--version', action='version',
                        version=vw2html.__version__)
    parser.add_argument('source', type=_validate_file_or_dir,
                        help='Wiki file or directory to be recursively scanned'
                        ' for wiki files')
    parser.add_argument('output', type=_validate_output,
                        help='Output directory for html files')
    # Assumed, that css and template files are placed within directory
    # contained wiki files when paths are provided as a relative ones. Using
    # absolute paths will override that assumption, although css file in
    # particular will be placed at the root of the output directory.
    parser.add_argument('-r', '--root', help="Root vimwiki directory. This "
                        "one is expected to be provided either from "
                        "commandline or via config file")
    parser.add_argument('-t', '--template', help="Template file")
    parser.add_argument('-s', '--stylesheet', help="CSS stylesheet file")
    parser.add_argument('-c', '--config', nargs="?", default=CONF_PATH,
                        help="Alternative config file. if not provided it "
                        "will skip loading confoguration")

    logging.basicConfig(level=logging.DEBUG,
                        format='%(filename)s:%(lineno)d: %(message)s')

    return parser.parse_args()


def main():
    try:
        args = parse_args()
    except ValueError:
        return 3

    converter = VimWiki2HTMLConverter(args)
    return converter.convert()


if __name__ == '__main__':
    sys.exit(main())
