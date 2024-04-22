import argparse
import os
import sys
import shutil
import warnings

import vw2html
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
    return 0


if __name__ == '__main__':
    sys.exit(main())
