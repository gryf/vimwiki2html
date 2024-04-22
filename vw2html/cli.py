import argparse
import sys
def _validate_file_or_dir(path):
    return path


def _validate_output(path):
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
