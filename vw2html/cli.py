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

    # converter specific defaults
    # force recreate/convert all wiki files passed to the converter
    force = False

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
        self.update(args)

    def update(self, args):
        # root path
        self.path = args.root if args.root else self.path
        self.path_html = args.output if args.output else self.path_html

        if args.source and os.path.isdir(args.source) and not self.path:
            LOG.info("Assuming provided source directory `%s' is a path to "
                     "whole wiki", args.source)
            self.path = abspath(args.source)

        if not self.path:
            msg = "Root of vimwiki not provided, exiting."
            LOG.error(msg)
            raise ValueError(msg)
        if not os.path.exists(self.path):
            msg = "Provided vimwiki path doesn't exists, exiting."
            LOG.error(msg)
            raise ValueError(msg)

        # output dir
        if not self.path_html:
            self.path_html = self.path + "_html"

        if os.path.exists(self.path_html):
            if not os.path.isdir(self.path_html):
                msg = (f"Path `{self.path_html}' exists and is a file. Cannot "
                       f"proceed.")
                LOG.error(msg)
                raise ValueError(msg)
            LOG.warning("Path `%s' exists. Contents will be overwriten.",
                        self.path_html)
        else:
            os.makedirs(self.path_html)

        # template
        if not self.template_path:
            # assume, template path is the same as wiki path
            self.template_path = self.path

        if args.template:
            self._template_fname = args.template
        elif (self.template_path and
              os.path.exists(os.path.join(self.template_path,
                                          self.template_default +
                                          self.template_ext))):
            self._template_fname = os.path.join(self.template_path,
                                                self.template_default +
                                                self.template_ext)
        else:
            template = os.path.join(self.path, self.template_default +
                                    self.template_ext)
            LOG.info("No template provided, using default: `%s`", template)
            if os.path.exists(template):
                self._template_fname = template
            else:
                LOG.warning("Default template doesn't exists, using builtin.")

        self._template = self.get_template_contents()

        # CSS
        if args.stylesheet:
            self.css_name = args.stylesheet

        if not self.css_name:
            LOG.warning("No CSS file provided, using none.")

        # setting force flag
        self.force = args.force if args.force else self.force

        # source file/dir
        if args.source and os.path.isfile(args.source):
            self._sources.append(args.source)
        else:
            self.scan_for_wiki_files()

    def _apply_data_to_template(self, html_obj):
        # calculate %root_path% for nested in subdirectories content
        relpath = os.path.relpath(os.path.dirname(html_obj.wiki_fname),
                                  start=self.path)
        root_path = ''
        if relpath != '.':
            root_path = '../'.join(['' for _ in
                                    range(len(relpath.split('/')) + 1)])

        # read template
        template = self._template
        if html_obj.template:
            try:
                with open(html_obj.template) as fobj:
                    template = fobj.read()
            except OSError:
                LOG.error('Error loading template "%s", ignoring.',
                          html_obj.template)

        # replace placeholders
        html = template.replace('%content%', html_obj.html)
        html = html.replace('%root_path%', root_path)
        html = html.replace('%title%', html_obj.title)
        html = html.replace('%date%', html_obj.date)
        return html

    def convert(self):
        # copy css file
        LOG.info("Starting conversion. Using `%s' as an output directory",
                 self.path_html)
        if self.css_name:
            shutil.copy(self.css_name, self.path_html)
            # TODO: copy assets from CSS too

        for filepath in self._sources:
            wiki_obj = vw2html.html.VimWiki2Html(filepath, self.path,
                                                 self.path_html, self.assets)
            source_mtime = 1
            dest_mtime = 0
            try:
                source_mtime = os.stat(filepath).st_mtime
                dest_mtime = os.stat(wiki_obj.html_fname).st_mtime
            except OSError:
                pass

            if (source_mtime > dest_mtime) or self.force:
                # convert only when:
                # - conversion is forced
                # - source modify time is newer then destination
                wiki_obj.convert()
                with open(wiki_obj.html_fname, 'w') as fobj:
                    fobj.write(self._apply_data_to_template(wiki_obj))

        return 0

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
    parser.add_argument('-f', '--force', action='store_true', help="Convert "
                        "all files even if source seems unchanged")
    logging.basicConfig(level=logging.DEBUG,
                        format='%(filename)s:%(lineno)d: %(levelname)s: '
                        '%(message)s')

    return parser.parse_args()


def main():
    try:
        args = parse_args()
    except ValueError:
        return 3

    try:
        converter = VimWiki2HTMLConverter(args)
    except ValueError:
        return 4
    return converter.convert()


if __name__ == '__main__':
    sys.exit(main())
