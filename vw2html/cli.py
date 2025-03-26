import argparse
import logging
import multiprocessing
import os
import re
import shutil
import sys
import tomllib

import vw2html

LOG = logging.getLogger()
XDG_CONFIG_HOME = os.getenv('XDG_CONFIG_HOME',
                                os.path.expanduser('~/.config'))
CONF_PATH = os.path.join(XDG_CONFIG_HOME, 'vw2html.toml')
RE_CSS_URL = re.compile(r'url\([\'"]?([^\'"]*)[\'"]?\)')


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
    # usually it's desired to use async for gaining advantage of multicore
    # processors, but for debugging it might be better to turn it off and make
    # conversion sequentially
    convert_async: bool = True

    # converter specific defaults
    # force recreate/convert all wiki files passed to the converter
    force = False

    def __init__(self, args):

        # Read config and update class attributes accordingly.
        self.read_config(args.config, args.source)

        # Default template to put contents in case there is no default
        # template found. If not provided by the commandline, this are the
        # default template fields:
        # %title% - to be replaced by filename by default, if exists on the
        #           page, will be placed instead
        # %date% - used for placing date
        # %root_path% - root path of the generated content - / by default
        # %wiki_path% - unused
        # %content% - where generated content goes
        self._template = ('<html><head><title>VimWiki</title>'
                          '<link rel="Stylesheet" type="text/css" '
                          'href="%root_path%%css%"></head>'
                          '<body>%content%</body></html>')
        self._template_fname = None
        self._sources = []
        self.assets = []
        self.update(args)

    def update(self, args):
        LOG.debug("Updating arguments")
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
            LOG.info("Path `%s' exists. Contents will be overwriten.",
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
        LOG.debug("Using configuration:\n"
                  "  path: %s\n"
                  "  path_html: %s\n"
                  "  index: %s\n"
                  "  ext: %s\n"
                  "  template_path: %s\n"
                  "  template_default: %s\n"
                  "  template_ext: %s\n"
                  "  css_name: %s\n"
                  "  convert_async: %s\n", self.path, self.path_html,
                  self.index, self.ext, self.template_path,
                  self.template_default, self.template_ext, self.css_name,
                  self.convert_async)

    def _apply_data_to_template(self, html_obj):
        # calculate %root_path% for nested in subdirectories content
        relpath = os.path.relpath(os.path.dirname(html_obj.wiki_fname),
                                  start=self.path)
        root_path = ''
        if relpath != '.':
            root_path = '../'.join(['' for _ in
                                    range(len(relpath.split('/')) + 1)])

        # read template
        template = self.get_template_contents(html_obj.template)

        # replace placeholders
        html = template.replace('%content%', html_obj.html)
        html = html.replace('%root_path%', root_path)
        html = html.replace('%title%', html_obj.title)
        if self.css_name:
            html = html.replace('%css%', os.path.basename(self.css_name))
        return html.replace('%date%', html_obj.date)

    def get_template_contents(self, template=None):
        if template:
            path = os.path.join(self.template_path, template
                                + self.template_ext)
            if not os.path.exists(path):
                LOG.error('Error loading template "%s", ignoring.',
                          template)
                return ""
            with open(path) as fobj:
                return fobj.read()

        if not any([self._template_fname and os.path.exists(self.
                                                            _template_fname)]):
            return self._template

        with open(self._template_fname) as fobj:
            return fobj.read()

    def copy_css_assets(self):
        with open(self.css_name) as fobj:
            css = fobj.read().split('\n')

        assets = []
        for line in css:
            if urls := RE_CSS_URL.findall(line):
                assets.extend(urls)

        if not assets:
            return

        assets = set(assets)  # remove duplicates
        for asset in assets:
            dirname = os.path.relpath(os.path.join(self.path,
                                                   os.path.dirname(asset)),
                                      start=self.path)
            src_fname = os.path.join(self.path, dirname,
                                     os.path.basename(asset))
            if not os.path.exists(src_fname):
                continue
            outdir = os.path.join(self.path_html, dirname)
            os.makedirs(outdir, exist_ok=True)
            shutil.copy(src_fname, outdir)
            # calculate output direcotry

    def convert(self):
        # copy css file
        LOG.info("Starting conversion. Using `%s' as an output directory",
                 self.path_html)
        if self.css_name:
            shutil.copy(self.css_name, self.path_html)
            self.copy_css_assets()
            # TODO: copy assets from CSS too

        # run conversion sequentially
        if not self.convert_async:
            for filepath in self._sources:
                self._convert(filepath)
            return 0

        # or use async pool
        try:
            with multiprocessing.Pool() as p:
                try:
                    result = p.map_async(self._convert, tuple(self._sources))
                    result.get(10)  # wait up to ten seconds for convertion
                                    # to finish

                except multiprocessing.context.TimeoutError:
                    LOG.error("Processing files took abnormally long, still "
                              "trying to finish the process, you might use "
                              "Ctrl+C to abort the conversion")
                    wait_time = 1
                    while True:
                        try:
                            result.get(wait_time)
                            break
                        except multiprocessing.context.TimeoutError:
                            wait_time *= 2
                            LOG.error("Still trying… waiting another %s "
                                      "seconds", wait_time)
                            continue
            return 0
        except KeyboardInterrupt:
            LOG.error("Interrupted, conversion is not complete")
            return 1

    def _convert(self, filepath):
        wiki_obj = vw2html.html.VimWiki2Html(filepath, self.path,
                                             self.path_html, self.assets)
        source_mtime = 1
        dest_mtime = 0
        try:
            source_mtime = os.stat(filepath).st_mtime
            dest_mtime = os.stat(wiki_obj.html_fname).st_mtime
        except OSError:
            pass

        #time.sleep(0.5)
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

    def read_config(self, config_file, source):
        potential_path = None
        if self.path:
            potential_path = self.path
        if source:
            source = abspath(source)
            if not os.path.isdir(source):
                source = os.path.dirname(source)
            potential_path = source

        try:
            with open(config_file, "rb") as fobj:
                toml = tomllib.load(fobj)
        except (OSError, ValueError):
            LOG.error("Exception on reading config file '%s'. Ignoring.",
                      config_file)
            return

        legal_keys = ["css_name", "ext", "index", "path_html",
                      "template_default", "template_default", "template_ext",
                      "template_path", 'path', 'force', 'convert_async']

        conf_dict = {}
        if potential_path:
            for confsection in toml.get('vimwiki', []):
                if not confsection.get('path'):
                    continue
                path = abspath(confsection['path'])
                if potential_path == path:
                    conf_dict = confsection
                    break
        if conf_dict:
            for key in legal_keys:
                if key in conf_dict:
                    if key in ['css_name', 'path', 'path_html',
                               'template_path']:
                        setattr(self, key, abspath(conf_dict[key]))
                    else:
                        setattr(self, key, conf_dict[key])
        elif toml.get('vimwiki') and toml['vimwiki'] and toml['vimwiki'][0]:
            # just get the first one
            conf_dict = toml['vimwiki'][0]
            for key in legal_keys:
                if key in conf_dict:
                    if key in ['css_name', 'path', 'path_html',
                               'template_path']:
                        setattr(self, key, abspath(conf_dict[key]))
                    else:
                        setattr(self, key, conf_dict[key])


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

def get_verbose(verbose_level, quiet_level):
    """
    Change verbosity level. Default level is warning.
    """

    level = logging.WARNING

    if quiet_level:
        level = logging.ERROR
        if quiet_level > 1:
            # Only critical messages are displayed
            level = logging.CRITICAL

    if verbose_level:
        level = logging.INFO
        if verbose_level > 1:
            level = logging.DEBUG

    return level


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('-v', '--verbose',  action='count', default=0,
                        help='be verbose. Adding more "v" will increase '
                        'verbosity')
    parser.add_argument('-q', '--quiet',  action='count', default=0,
                        help='suppress output. Adding more "q" will decrease '
                        'messages visibility')
    parser.add_argument('-V', '--version', action='version',
                        version=vw2html.__version__)
    parser.add_argument('source', nargs="?", type=_validate_file_or_dir,
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

    args = parser.parse_args()
    logging.basicConfig(level=get_verbose(args.verbose, args.quiet),
                        format='%(levelname)s: %(message)s')

    return args


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
