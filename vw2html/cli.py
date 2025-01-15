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


@dataclasses.dataclass
class VWConfig:
    root: str = None
    template: str = None
    css: str = None


def abspath(path):
    return os.path.abspath(os.path.expanduser(os.path.expandvars(path)))


def read_conf():
    try:
        with open(CONF_PATH, "rb") as fobj:
            toml = tomllib.load(fobj)
    except (OSError, ValueError):
        LOG.exception("Exception on reading config file %s, ignoring", CONF_PATH)
        return VWConfig()

    return VWConfig(**toml)


class VimWiki2HTMLConverter:
    def __init__(self, args):
        self._conf = read_conf()
        # Template to put contents in. If not provided by the commandline,
        # this is the default
        # template fields:
        # %title% - to be replaced by filename by default, if exists on the
        #           page, will be placed instead
        # %date% - unused
        # %root_path% - root path of the generated content - / by default
        # %wiki_path% - unused
        # %content% - where generated content goes
        self._template = ("<html><head><title>VimWiki</title></head>"
                          "<body>%content%</body></html>")
        # root path for the root of the wiki, potentially used in templates,
        # and is set if provided source is a directory
        self._root = ''
        # CSS file to be copied/added to the output directory. Should be
        # coherent with the template
        self._css = None
        # Source directory, aka wiki directory, where all wiki/media files are
        # located.
        self._wiki_path = None
        # Source file. It may happen, that user want to convert only single
        # file - this is where it is stored internally.
        self._wiki_filepath = None
        # Output directory for the html/css/content files
        self._www_path = None

        self.configure(args)

    def configure(self, args):
        self._root = args.root if args.root else self._conf.root
        if self._root:
            self._root = abspath(self._root)
        template = args.template if args.template else self._conf.template
        if template:
            template = abspath(template)
        self._css = args.css if args.css else self._conf.css
        if self._css:
            self._css = abspath(self._css)

        if os.path.isdir(args.source):
            self._wiki_path = abspath(args.source)
            # calculate root path with directory
            if not self._root:
                self._root = self._wiki_path

        if not template and self._root:
            template = os.path.join(self._root, 'default.tpl')
            if not os.path.exists(template):
                template = None

        if template:
            with open(template) as fobj:
                self._template = fobj.read()

        if not self._css and self._root:
            self._css = os.path.join(self._root, 'style.css')

        if not os.path.isdir(args.source):
            self._wiki_filepath = abspath(args.source)
            if not self._root:
                self._root = abspath(os.path.dirname(args.source))

        self._www_path = abspath(args.output)

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
            fulldname = os.path.abspath(os.path.dirname(self._css))
            dst = self._www_path
            if fulldname != self._root:
                dname = fulldname.replace(self._root)[1:]
                os.makedirs(self._www_path, dname)
                dst = os.path.join(self._www_path, dname)
            shutil.copy(self._css, dst)

        if self._wiki_filepath:
            data = [vw2html.html.convert_file(self._wiki_filepath,
                                              self._www_path, self._root)]
        else:
            data = []
            for root, _, files in os.walk(self._wiki_path):
                for fname in files:
                    data.append(vw2html.html.
                                convert_file(os.path.join(root, fname),
                                             self._www_path,
                                             self._root))

        for obj in data:
            with open(obj.html_fname, 'w') as fobj:
                fobj.write(self._apply_data_to_template(obj))
        return 0


def _validate_file_or_dir(path):
    if not os.path.exists(path):
        raise argparse.ArgumentTypeError(f"Provided '{path}' doesn't exists.")
    return path


def _validate_output(path):
    if os.path.exists(path):
        if not os.path.isdir(path):
            msg = f"Path '{path}' and it's not a directory"
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
    parser.add_argument('-r', '--root', help="Root vimwiki directory")
    parser.add_argument('-t', '--template', help="Template file")
    parser.add_argument('-c', '--css', help="Stylesheet file")

    logging.basicConfig(level=logging.DEBUG,
                        format='%(filename)s:%(lineno)d: %(message)s')

    return parser.parse_args()


def main():
    args = parse_args()
    converter = VimWiki2HTMLConverter(args)
    return converter.convert()


if __name__ == '__main__':
    sys.exit(main())
