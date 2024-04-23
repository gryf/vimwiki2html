import argparse
import os
import sys
import shutil
import warnings

import vw2html


class VimWiki2HTMLConverter:
    def __init__(self, args):
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
        # XXX: do I need this?
        self._root_path = ''
        # CSS file to be copied/added to the output direcotry. Should be
        # coherent with the template
        self._css_fname = None
        # Source direcotry, aka wiki direcotry, where all wiki/media files are
        # located.
        self._wiki_path = None
        # Source file. It may happen, that user want to convert only single
        # file - this is where it is stored internally.
        self._wiki_filepath = None
        # Output direcotry for the html/css/content files
        self._www_path = None

        self.configure(args)

    def configure(self, args):
        if os.path.isdir(args.source):
            self._wiki_path = os.path.abspath(args.source)
        else:
            self._wiki_filepath = os.path.abspath(args.source)

        self._www_path = args.output

        if args.template:
            with open(args.template) as fobj:
                self._template = fobj.read()

        if args.css:
            self._css_fname = args.css

    def _applay_data_to_template(self, html_obj):
        root_path = '../'.join(['' for _ in range(html_obj.level)])
        template = self._template
        if html_obj.template:
            try:
                with open(html_obj.template) as fobj:
                    template = fobj.read()
            except IOError:
                print(f'Error loading template {html_obj.template}')

        html = template.replace('%content%', html_obj.html)
        html = html.replace('%root_path%', root_path)
        html = html.replace('%title%', html_obj.title)
        html = html.replace('%date%', html_obj.date)
        return html

    def convert(self):
        # copy css file
        if self._css_fname:
            if os.path.isabs(self._css_fname):
                shutil.copy(self._css_fname, self._www_path)
            else:
                os.makedirs(self._www_path, os.path.dirname(self._css_fname))
                shutil.copy(os.path.join(self._wiki_path, self._css_fname),
                            os.path.join(self._www_path, self._css_fname))

        if self._wiki_filepath:
            data = [vw2html.html.s_convert_file(self._wiki_filepath,
                                                self._www_path)]
        else:
            data = []
            for root, dirs, files in os.walk(self._wiki_path):
                for fname in files:
                    data.append(vw2html.html.
                                s_convert_file(os.path.join(root, fname)))

        for obj in data:
            with open(obj.html_fname, 'w') as fobj:
                fobj.write(self._applay_data_to_template(obj))
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
        warnings.warn(f'Path "{path} exists. Content might be removed and/or '
                      f'overwritten.')
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
    parser.add_argument('-t', '--template', help="Template file")
    parser.add_argument('-c', '--css', help="Stylesheet file.")
    return parser.parse_args()


def main():
    args = parse_args()
    converter = VimWiki2HTMLConverter(args)
    return converter.convert()


if __name__ == '__main__':
    sys.exit(main())
