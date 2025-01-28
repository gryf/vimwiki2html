import argparse
import logging
import os
import pathlib
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
    # Root path for the wiki, potentially used in templates and it
    # must be set either by configuration, or through commandline.
    path: str = None  # '~/vimwiki'
    # HTML output directory
    path_html: str = ''
    # Main file. Usually index.
    index: str = 'index'
    # Extension for wiki files
    ext: str = '.wiki'
    # Path to templates.
    template_path: str = None  # '~/vimwiki/templates/'
    # Default template without extension.
    template_default: str = 'default'
    # Default template extension.
    template_ext: str = '.tpl'
    # Style file will be copied to path_html
    css_name: str = None # 'style.css'

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
        self._template_fname = None
        self._sources = []
        self.assets = []
        self._update(args)
        self.configure()

    def configure(self):
        if os.path.exists(self.path_html) and not os.path.isdir(self
                                                                .path_html):
            msg = (f"Path `{self.path_html}' exists and is a file. Cannot "
                   f"proceed.")
            raise ValueError(msg)

        if os.path.exists(self.path_html):
            LOG.warning("Path `%s' exists. Contents will be overwriten.",
                        self.path_html)
        else:
            os.makedirs(self.path_html)

        if not (self._template_fname and os.path.exists(self._template_fname)):
            LOG.error("Provided template `%s' doesn't exists. Check your "
                      "config/or parameters", self._template_fname)
            return
        with open(self._template_fname) as fobj:
            self._template = fobj.read()

    def _apply_data_to_template(self, html_obj):
        root_path = '../'.join(['' for _ in range(html_obj.level)])
        template = self._template
        if html_obj.template:
            try:
                with open(html_obj.template) as fobj:
                    template = fobj.read()
            except OSError:
                LOG.error('Error loading template "%s", ignoring.',
                          html_obj.template)

        html = template.replace('%content%', html_obj.html)
        html = html.replace('%root_path%', root_path)
        html = html.replace('%title%', html_obj.title)
        html = html.replace('%date%', html_obj.date)
        return html

    def convert(self):
        # copy css file
        if self.css_name:
            shutil.copy(self.css_name, self.path_html)
            # TODO: copy assets from CSS too

        data = [vw2html.html.convert_file(f, self) for f in self._sources]
        for obj in data:
            with open(obj.html_fname, 'w') as fobj:
                fobj.write(self._apply_data_to_template(obj))
        return 0

    def _update(self, args):
        if args.output:
            self.path_html = abspath(args.output)

        if args.root:
            self.path = abspath(args.root)

        if not self.path:
            msg = "Root of vimwiki not provided, exiting."
            raise ValueError(msg)

        if args.template:
            self._template_fname = abspath(args.template)
        elif (self.template_path and
              os.path.exists(os.path.join(self.path, self.template_path,
                                          self.template_default +
                                          self.template_ext))):
            self._template_fname = os.path.join(self.path, self.template_path,
                                                self.template_default +
                                                self.template_ext)

        if args.stylesheet:
            self.css_name = abspath(args.stylesheet)

        if args.source and os.path.isfile(args.source):
            self._sources.append(args.source)
        else:
            self.scan_for_wiki_files()

    def scan_for_wiki_files(self):
        for root, _, files in os.walk(self.path):
            for fname in files:
                _fname = os.path.join(root, fname)
                if _fname.endswith(self.ext):
                    self._sources.append(_fname)
                else:
                    self.assets.append(_fname)

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
                if key in ['css_name', 'path', 'path_html', 'template_path']:
                    setattr(self, key, abspath(toml[key]))
                else:
                    setattr(self, key, toml[key])


def _validate_file_or_dir(path):
    if path is None:
        path ='.'
    if not os.path.exists(path):
        msg = f"Provided '{path}' doesn't exists."
        raise argparse.ArgumentTypeError(msg)
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
    parser.add_argument('-w', '--source', type=_validate_file_or_dir,
                        help='Wiki file or directory to be recursively scanned'
                        ' for wiki files')
    parser.add_argument('-o', '--output', type=_validate_output,
                        help='Output directory for html files')
    # Assumed, that css and template files are placed within directory
    # contained wiki files when paths are provided as a relative ones. Using
    # absolute paths will override that assumption, although css file in
    # particular will be placed at the root of the output directory.
    parser.add_argument('-r', '--root', help="Root vimwiki directory. This "
                        "one is expected to be provided either from "
                        "commandline or via config file")
    parser.add_argument('-t', '--template', type=_validate_file_or_dir,
                        help="Template file")
    parser.add_argument('-s', '--stylesheet', type=_validate_file_or_dir,
                        help="CSS stylesheet file")
    parser.add_argument('-c', '--config',  type=_validate_file_or_dir,
                        nargs="?", default=CONF_PATH,
                        help="Alternative config file. if not provided it "
                        "will skip loading confoguration")

    logging.basicConfig(level=logging.DEBUG,
                        format='%(filename)s:%(lineno)d: %(levelname)s: '
                        '%(message)s')

    return parser.parse_args()


def main():
    try:
        args = parse_args()
    except (ValueError, ValueError):
        return 3

    converter = VimWiki2HTMLConverter(args)
    return converter.convert()


if __name__ == '__main__':
    sys.exit(main())
