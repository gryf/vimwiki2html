"""
This is kind of translation from vimwiki html export file to python. Well, not
excact translation, for some portion of convertion implementation has been
done from scratch.
"""
import dataclasses
import datetime
import html
import logging
import os
import re
import shutil

try:
    import pygments
    import pygments.formatters
    import pygments.lexers
    import pygments.util
except ImportError:
    pygments = None


LOG = logging.getLogger()


@dataclasses.dataclass
class State:
    para: bool = False
    quote: bool = False
    list_leading_spaces: bool = False
    # [in_math, indent_math]
    math: list[int, str] = dataclasses.field(default_factory=list)
    deflist: bool = False
    lists: list = dataclasses.field(default_factory=list)
    # [last seen header text in this level, number]
    header_ids: list = dataclasses.field(default_factory=list)
    # [][['', 0], ['', 0], ['', 0],
    #                    ['', 0], ['', 0], ['', 0]]


class List:
    def __init__(self, indent, list_type='ul'):
        self.list_type = list_type
        self.indent = indent

    def __lt__(self, other):
        return len(self.indent) < len(other.indent)

    def __le__(self, other):
        return len(self.indent) <= len(other.indent)

    def __eq__(self, other):
        return len(self.indent) == len(other.indent)

    def __ne__(self, other):
        return len(self.indent) != len(other.indent)

    def __gt__(self, other):
        return len(self.indent) > len(other.indent)

    def __ge__(self, other):
        return len(self.indent) >= len(other.indent)


class Cell:
    def __init__(self, text):
        self.rowspan = 1
        self.colspan = 1
        self.text = text
        self.header = False

    def __repr__(self):
        rspan = cspan = ''
        if self.rowspan > 1:
            rspan = f' rowspan="{self.rowspan}"'
        if self.colspan > 1:
            cspan = f' colspan="{self.colspan}"'
        td = 'th' if self.header else 'td'
        return f"<{td}{rspan}{cspan}>{self.text}</{td}>"


class Table:
    def __init__(self):
        self.centered = False
        self.rows = []
        self.first_row_header = False

    def render(self):
        self._scan_table()
        table = '<table class="center">' if self.centered else "<table>"
        index = 0
        if self.first_row_header:
            table += '<thead>\n<tr>'
            for item in self.rows[0]:
                if item is None:
                    continue
                table += f"{item}"
            table += '</tr>\n</thead>'
            index = 1

        table += '<tbody>'
        for row in self.rows[index:]:
            table += '<tr>'
            for item in row:
                if item is None:
                    continue
                table += f'{item}'
            table += '</tr>'
        table += '</tbody>'
        table += '</table>'
        return table

    def add_rows(self, row_list):
        if (all(re_table_header_sep.match(x) for x in row_list) and
            len(self.rows) == 1):
            self.first_row_header = True
            return
        self.rows.append(row_list)

    def _scan_table(self):
        table = [[None for _ in x] for x in self.rows]

        for x, row in enumerate(self.rows):
            for y, item in enumerate(row):
                if item.strip() == '\\/':
                    counter = 0
                    while counter is not None and x - counter >= 0:
                        counter += 1
                        if table[x-counter][y] is None:
                            continue
                        table[x-counter][y].rowspan += 1
                        counter = None
                    continue

                if item.strip() == '>':
                    counter = 0
                    while counter is not None and y - counter >= 0:
                        counter += 1
                        if table[x][y-counter] is None:
                            continue
                        table[x][y-counter].colspan += 1
                        counter = None
                    continue

                c = Cell(item)
                if self.first_row_header and x == 0:
                    c.header = True
                table[x][y] = c
        self.rows = table


re_ph_nohtml = re.compile(r'^\s*%nohtml\s*$', flags=re.MULTILINE)
re_ph_title = re.compile(r'^\s*%title\s(.*)$', flags=re.MULTILINE)
re_ph_template = re.compile(r'^\s*%template\s(.*)$', flags=re.MULTILINE)
re_ph_date = re.compile(r'^\s*%date\s(.*)$', flags=re.MULTILINE)
# re_ph_plainhtml = re.compile(r'^\s*%plainhtml\s(.*)$', flags=re.MULTILINE)

re_ml_comment = re.compile(r'%%\+.*?\+%%', flags=re.DOTALL)
re_codeblock = re.compile(r'^(\s*){{3}([^\n]*?)(\n.*?)\n^\s*}{3}\s*$',
                          flags=re.MULTILINE | re.DOTALL)
re_hr = re.compile(r'^-{4,}$')
re_header = re.compile(r'^\s*(?P<open_level>[=]+)'
                       r'(?P<title>[^=].*?)'
                       r'(?P<close_level>[=]+)\s*$')
re_bold = re.compile(r'(?:(?<=[^a-zA-Z0-9])|^)\*([^\*\s][^\*]*?[^\s])\*'
                     r'(?![a-zA-Z0-9])')
re_italic = re.compile(r'(?:(?<=[^a-zA-Z0-9])|^)_([^_\s][^_]*?[^\s])_'
                       r'(?![a-zA-Z0-9])')
re_strike = re.compile(r'~{2}([^~]+?)~{2}')
re_subscript = re.compile(r',,([^,`]+),,')
re_superscript = re.compile(r'\^([^\^]+?)\^')
re_comment = re.compile(r'^\s*%%\s.*$')
re_hexcolor = re.compile(r'^(?P<hexcolor>#(?P<red>[a-fA-F0-9]{2})'
                         r'(?P<green>[a-fA-F0-9]{2})'
                         r'(?P<blue>[a-fA-F0-9]{2}))$')
re_code = re.compile(r'`([^`]+?)`')
re_list = re.compile(r'^(\s*)([\*\-#]|[\d]+[\.\)])\s(?:\[([^]])\]\s?)?'
                     r'(.*)$')
re_indented_text = re.compile(r'^(\s+)(.*)$')
# TODO(gryf): make tag list configurable
re_safe_html = re.compile(r'<(\s*/*(?!(?:b|i|u|sub|sup|kbd|br|hr))\w.*?)>')
re_bare_links = re.compile(r'(?<!\w)((?:http:|https:|ftp:|mailto:|www\.)/*[^\s]+)')
re_wiki_links = re.compile(r'\[\[(?P<contents>[^]]+)\]\]')
re_transclusion_links = re.compile(r'(?<!{){{(?P<contents>[^}]+)}}(?!})')
re_bare_links = re.compile(r'(?<!\w)((?:http:|https:|ftp:|mailto:|www\.)/*[^\s]+)')
re_html_links = re.compile(r'\[\[(?P<contents>'
                           r'(?:http:|https:|ftp:|mailto:|www\.)?'
                           r'[^]]*)\]\]')
re_table_header_sep = re.compile(r'\s?:?-+:?\s?')


class VimWiki2Html:
    """
    Represent single wiki file
    """
    max_header_level = 6
    # marks are using Unicode Supplementary Private Use Area A in unicode from
    # the end of the set, there is low chance to fill those with custom
    # glyphs, and even so, the sentence od **4** (where asterisk is such
    # symbol and 4 represents any number) is pretty low to exists in written
    # wiki text.
    codeblock_mark = "󿿽󿿽{}󿿽󿿽"
    inline_code_mark = " 󿿼󿿼{}󿿼󿿼"
    links_mark = " 󿿻󿿻{}󿿻󿿻"
    images_mark = "󿿺󿿺{}󿿺󿿺"

    template_ext = 'tpl'

    def __init__(self, wikifname, path, path_html, assets):
        self.assets = assets
        self.root = path
        self.template = None
        self.date = ''
        self.wiki_contents = None
        self.nohtml = False
        self._html = ''
        self._table = False
        self.wiki_fname = wikifname
        self.output_dir = path_html
        self.html_fname = self.get_output_path()
        self._title = None
        self._code_blocks = []
        self._inline_codes = []
        self._links = []
        self._images = []
        self._inline_codes_count = 0
        self._state = State()
        self._line_processed = False
        self._lists = []

    def get_output_path(self):
        # get relative link out of self.root
        path = os.path.relpath(self.wiki_fname, start=self.root)
        outpath = self.output_dir
        if os.path.dirname(path):
            outpath = os.path.join(self.output_dir, os.path.dirname(path))
            os.makedirs(outpath, exist_ok=True)

        return os.path.join(outpath, os.path
                            .splitext(os.path.basename(path))[0] + '.html')

    @property
    def title(self):
        if not self._title:
            return os.path.basename(os.path.splitext(self.wiki_fname)[0])
        return self._title

    @property
    def html(self):
        _html = self._html
        for index, contents in enumerate(self._code_blocks):
            _html = _html.replace(self.codeblock_mark.format(index), contents)
        for index, contents in enumerate(self._inline_codes):
            _html = _html.replace(self.inline_code_mark.format(index),
                                  contents)
        for index, contents in enumerate(self._links):
            _html = _html.replace(self.links_mark.format(index), contents)
        for index, contents in enumerate(self._images):
            _html = _html.replace(self.images_mark.format(index), contents)


        return _html

    def read_wiki_file(self, fname):
        with open(fname) as fobj:
            self.wiki_contents = fobj.read()
        self.nohtml = bool(re_ph_nohtml.search(self.wiki_contents))

    def convert(self):
        self.read_wiki_file(self.wiki_fname)
        # exit early if there is %nohtml placeholder
        if self.nohtml:
            LOG.info("Found nohtml placeholder, ignoring `%s'.",
                     self.wiki_fname)
            return

        # do global substitution and removal - remove multiline comments and
        # placeholders, and separate code blocks.
        self._remove_multiline_comments()
        self._separate_codeblocks()
        self._find_title()
        self._find_template()
        self._find_date()

        converted = self._process_linewise()
        self._html = '\n'.join(converted)

    def _process_linewise(self):
        lsource = self.wiki_contents.split('\n')

        ldest = []

        # current state of converter
        self._state.math = [0, 0]  # [in_math, indent_math]
        self._state.deflist = 0
        # [last seen header text in this level, number]
        self._state.header_ids = [['', 0], ['', 0], ['', 0],
                                  ['', 0], ['', 0], ['', 0]]

        self._previus_line = None
        for line in lsource:
            self._line_processed = False
            list_lines = None
            header = re_header.match(line)
            if header:
                list_lines = self._close_lists()
                if list_lines:
                    ldest.extend(list_lines)
                ldest.append(self._parse_header(header))
                self._previus_line = line
                continue

            if re_comment.match(line):
                # ignore comments
                continue

            if re_hr.match(line):
                list_lines = self._close_lists()
                if list_lines:
                    ldest.extend(list_lines)
                ldest.append('<hr />')
                self._previus_line = line
                continue

            lines = self._parse_line(line)

            ldest.extend(lines)
            self._previus_line = line

        # remove blank lines
        while len(ldest) and ldest[-1].strip() == '':
            del ldest[-1]

        # process end of file
        # close opened tags if any
        lines = []
        close_para(self._state.para, lines)
        lines.extend(self._close_lists())
        ldest.extend(lines)

        return ldest

    def _handle_plainhtml(self, line):
        """
        Allows insertion of plain text to the final html conversion

        for example:

        %plainhtml <div class="mycustomdiv">

        inserts the line with div in current place unchanged into html output.
        Can be used multiple times.

        NOTE: this is undocumented feature/placeholder of the vimwiki
        """
        trigger = '%plainhtml'
        if trigger not in line:
            return

        self._line_processed = True
        lines = []

        # remove the trigger prefix
        pp = line.split(trigger)[1].strip()

        lines.append(pp)
        return lines

    def _handle_paragraph(self, line):
        lines = []
        if line.strip():
            if not self._state.para:
                lines.append('<p>')
                self._state.para = True
            self._line_processed = True
            # default is to ignore newlines (i.e. do not insert <br/> at the
            # end of the line)
            lines.append(line)
        elif self._state.para and line.strip() == '':
            lines.append('</p>')
            self._state.para = False

        return lines

    def _parse_line(self, line):
        res_lines = []
        self._line_processed = False

        lines = self._handle_plainhtml(line)
        if self._line_processed:
            res_lines.extend(lines)
            return res_lines

        line = self._html_escape(line)

        ### tables
        lines = self._handle_tables(line)
        if lines:
            res_lines.extend(lines)
        if self._line_processed:
            return res_lines

        # lists
        lines = self._handle_list(line)
        if self._line_processed:
            res_lines.extend(lines)
            return res_lines

        if lines and self._line_processed:
            res_lines.extend(lines)

        # Paragraphs
        lines = self._handle_paragraph(line)
        if self._line_processed and self._lists:
            res_lines.extend(self._close_lists())

        lines = [self._apply_attrs(x) for x in lines]

        res_lines.extend(lines)

        # add the rest
        if not self._line_processed:
            res_lines.append(line)

        return res_lines

    def _parse_bold(self, line):
        return re_bold.sub(r'<strong>\g<1></strong>', line)

    def _parse_italic(self, line):
        return re_italic.sub(r'<em>\g<1></em>', line)

    def _parse_strikeout(self, line):
        return re_strike.sub(r'<del>\g<1></del>', line)

    def _parse_subscript(self, line):
        return re_subscript.sub(r'<sub><small>\g<1></small></sub>', line)

    def _parse_superscript(self, line):
        return re_superscript.sub(r'<sup><small>\g<1></small></sup>', line)

    def _parse_inline_code(self, line):
        """
        Return code tagged line.

        Check if code matches color in format "#rrggbb" where rr, gg and bb is
        in hexadecimal format, and in that case return colored version of such
        string.
        """

        threshold = 0.5
        style = ''
        match = re_hexcolor.match(line)
        if match:
            color = match.groupdict()
            hexcolor = color['hexcolor']
            red = int(color['red'], 16)
            green = int(color['green'], 16)
            blue = int(color['blue'], 16)

            fg_color = 'white'
            if (0.299 * red + 0.587 * green + 0.114 * blue) / 0xFF > threshold:
                fg_color = 'black'

            style = f" style='background-color:{hexcolor};color:{fg_color};'"

        return f"<code{style}>{line}</code>"

    def _separate_codeblocks(self):
        count = 0
        while True:
            pre = re_codeblock.search(self.wiki_contents)
            if not pre:
                break
            x, y = pre.span()
            indent, lexer, code = pre.groups()
            self._code_blocks.append(self._make_pre(code, lexer))
            self.wiki_contents = (self.wiki_contents[:x] + indent +
                                  self.codeblock_mark.format(count) +
                                  self.wiki_contents[y:])
            count += 1

    def _separate_inline_codes(self, line):
        if codes := re_code.findall(line):
            for code in codes:
                self._inline_codes.append(self._parse_inline_code(code))
                line = re_code.sub(self.inline_code_mark
                                   .format(self._inline_codes_count), line,
                                   count=1)
                self._inline_codes_count += 1

        return line

    def _parse_header(self, line_match):
        open_level, title, close_level = line_match.groups()
        open_level = open_level.strip()
        close_level = close_level.strip()
        if open_level != close_level:
            LOG.warning("Header open level doesn't match close level in `%s`: "
                        "`%s' vs `%s'.", self.wiki_fname, open_level,
                        close_level)
            return line_match.string
        level = len(open_level)
        if level > self.max_header_level:
            LOG.warning("Headers in `%s'cannot exceed `%s` level.",
                        self.wiki_fname, self.max_header_level)
            return line_match.string

        title = _id = line_match["title"].strip()
        title = self._apply_attrs(title)

        return (f'<h{level} id="{_id}">'
                f'<a href="#{_id}">{title}</a>'
                f'</h{level}>\n')

    def _apply_attrs(self, line):
        """
        Apply tags for different attributes.

        Parse markup fdor bold, italic, strikethrough, superscipt, subscript
        and code.
        """
        processed_line = line
        for fn in (self._separate_inline_codes, self._handle_links,
                   self._parse_italic, self._parse_bold, self._parse_strikeout,
                   self._parse_superscript, self._parse_subscript):
            processed_line = fn(processed_line)
        return processed_line

    def _make_pre(self, code, lexer=None):
        """
        Create <pre></pre> tag to contain passed code.
        """
        lexer = lexer.strip()

        if lexer.lower().startswith('type='):
            lexer = lexer.replace('type=', '')

        highlighted = None
        if pygments and lexer:
            highlighted = self._highlight(code, lexer)
        if not highlighted:
            highlighted = ('<pre class="code literal-block">' +
                           html.escape(code) + '</pre>')

        return highlighted

    def _highlight(self, code, lexer):
        """
        Try to syntax highlight code with the pygments.

        If user put in the wiki preformatted block and mark it as python:
            {{{ python
              …
        for support for highlight in this converted only, or:
            {{{ type=py
              …
        for vimwiki syntax (see help), try to use pygments if available to
        colorize the code. It may be whatever lexer pygments supports.

        Although by default vimwiki use file extension is passing to pygments
        to determine the syntax (a temp file with extension taken from
        'type=<extension>' will be passed to pygments), this script will try
        to use whatever direct lexer name passed as bare word
        (not type= attribute).
        """
        if not pygments:
            return None

        try:
            lex = pygments.lexers.get_lexer_by_name(lexer)
        except pygments.util.ClassNotFound:
            return None
        fmt = pygments.formatters.HtmlFormatter(prestyles="code literal-block")
        return pygments.highlight(code, lex, fmt)

    def _media(self):
        """
        Placeholder for attached media (inline images, link to local images
        and files).
        """

    def _remove_multiline_comments(self):
        """
        Remove comments enclosed %%+ and +%% markings including markings as
        well.
        """
        self.wiki_contents = re_ml_comment.sub('', self.wiki_contents)

    def _find_title(self):
        """
        Search for %title placeholder. If found set title and remove the line
        from source wiki.
        """
        result = re_ph_title.search(self.wiki_contents)

        if not result:
            return
        self._title = result.groups()[0].strip()
        self.wiki_contents = re_ph_title.sub('\n', self.wiki_contents)

    def _find_template(self):
        """
        Search for %template placeholder.

        The argument for the %template placeholder should be name of the file
        without a path (root of the vimwiki) and extension (.tpl by defult).
        """
        result = re_ph_template.search(self.wiki_contents)

        if not result:
            return

        self.template = result.groups()[0].strip()
        self.wiki_contents = re_ph_template.sub('\n', self.wiki_contents)

    def _find_date(self):
        """
        Search for %date placeholder. If found set it and remove the line from
        source wiki.
        """
        result = re_ph_date.search(self.wiki_contents)

        if not result:
            return

        self.date = result.groups()[0].strip()
        self.wiki_contents = re_ph_date.sub('\n', self.wiki_contents)

        if not self.date:
            # TODO: support different date formats - another commandline
            # argument?
            # TODO: support TZ for current date
            self.date = datetime.datetime.now().strftime('%Y-%m-%d')

    def _handle_links(self, line):
        # transclusions
        for link in re_transclusion_links.finditer(line):
            img = self._get_img_out_of_string(link.groupdict()['contents'])
            line = re_transclusion_links.sub(self.images_mark
                                             .format(len(self._images)),
                                             line, count=1)
            self._images.append(img)

        # wiki links
        for link in re_html_links.finditer(line):
            link = self._get_link_out_of_string(link.groupdict()['contents'])
            line = re_html_links.sub(self.links_mark.format(len(self._links)),
                                     line, count=1)
            self._links.append(link)

        # wiki links
        for link in re_wiki_links.finditer(line):
            link = self._get_link_out_of_string(link.groupdict()['contents'])
            line = re_wiki_links.sub(self.links_mark.format(len(self._links)),
                                     line, count=1)
            self._links.append(link)

        # bare links
        for link in re_bare_links.finditer(line):
            link = f'<a href="{link.groups()[0]}">{link.groups()[0]}</a>'
            line = re_bare_links.sub(self.links_mark.format(len(self._links)),
                                     line, count=1)
            self._links.append(link)
        return line

    def _get_img_out_of_string(self, string):
        parts = string.split('|')
        if len(parts) == 3:
            if parts[1]:
                template = f'<img src="%s" alt="{parts[1]}" {parts[2]}/>'
            else:
                template = f'<img src="%s" {parts[2]}/>'
        elif len(parts) == 2:
            template = f'<img src="%s" alt="{parts[1]}"/>'
        else:
            template = '<img src="%s"/>'

        dest = parts[0]

        img = None
        for schema in ('file:', 'local:'):
            if str(dest).startswith(schema):
                img = dest[len(schema):]
                break
        if img:
            img = self._copy_asset(img)
            return template % img

        if dest.lower().startswith('http'):
            return template % dest

        LOG.warning("Image `%s' in `%s' have no schema", dest, self.wiki_fname)
        img = self._copy_asset(dest)
        return template % dest

    def _copy_asset(self, img):
        if (img[0].isalpha() and img[1] == ':'):
            # ignore windows FS for now
            return img

        filepath = os.path.relpath(os.path.join(self.root, img),
                                   start=self.root)
        if filepath.startswith('..'):
            LOG.warning("File `%s' pointing outside of wiki root, ignoring",
                        img)
            return img

        if not os.path.exists(os.path.join(self.root, filepath)):
            LOG.warning("File `%s' in `%s' doesn't exists, ignoring", img,
                        self.wiki_fname)
            return img

        fullpath = os.path.join(self.root, filepath)
        outpath = os.path.join(self.output_dir, os.path.dirname(filepath))
        os.makedirs(outpath, exist_ok=True)
        shutil.copy(fullpath, outpath)
        return filepath

    def _get_link_out_of_string(self, string):
        description = None
        if '|' in string:
            target, description = string.split('|', maxsplit=1)
        else:
            target = string
        template = '<a href="%s">%s</a>'
        if not description:
            description = target

        if target.startswith('diary:'):
            return template % (f'diary/{target[6:]}.html', description)

        for schema in ('http:', 'https:', 'ftp:', 'mailto:'):
            if target.startswith(schema):
                # plain url, just return it
                return template % (target, description)

        link = None
        for schema in ('file:', 'local:'):
            if target.startswith(schema):
                link = target[len(schema):]
                break
        if link:
            if not (link[0].isalpha() and link[1] == ':'
                    and os.path.isabs(link)):
                link = os.path.expandvars(os.path.expanduser(link))
                link = os.path.abspath(os.path.join(self.root, link))
                if link in self.assets:
                    link = self._copy_asset(link)
                elif self.root in link:
                    link = os.path.relpath(os.path.join(self.root, link),
                                           start=self.root)
            return template % (link, description)

        # absolute links
        if target.startswith('//'):
            link = os.path.expanduser(os.path.expandvars(target[2:]))
            if link.endswith('/'):
                return template % (link, description)
            return template % (link + '.html', description)

        # relative links for wiki
        if target.startswith('/'):
            if target.endswith('/'):
                return template % (f'{target[1:]}', description)
            return template % (f'{target[1:]}.html', description)

        # wiki links for directories
        if target.endswith('/'):
            return template % (target, description)

        # wiki links for wiki pages
        if not target.endswith('.html'):
            link = f'{target}.html'
            return template % (link, description)

        # bare html links without schema. assuming remote links.
        if target.endswith('.html'):
            return template % (link, description)

        raise ValueError(string)

    def _handle_list(self, line):
        """
        Handle possible list item. Return html line(s) or untouched line.

        Search for a pattern for a list item, or indented line which in case
        of open any list opened.
        """

        def _new_list(indent, html_ltype, html_check, text):
            self._lists.append(List(indent, html_ltype))
            self._line_processed = True
            return f"<{html_ltype}>\n<li{html_check}>\n{text}"

        # prepare regexps for lists
        bullets = ['-', '*']
        numbers = (r'('
                   r'\d+\)|'
                   r'\d+\.|'
                   r'[ivxlcdm]+\)|'
                   r'[IVXLCDM]+\)|'
                   r'[a-z]{1,2}\)|'
                   r'[A-Z]{1,2}\)'
                   ')')

        checkbox_defaults = {'-': 'rejected',
                             ' ': 'done0',
                             '.': 'done1',
                             'o': 'done2',
                             'O': 'done3',
                             'X': 'done4'}

        indent = list_type = checkbox = text = None
        ret_lines = []

        # empty, not indented line
        if not line.strip() and len(line) == 0:
            if self._lists:
                self._line_processed = True
                ret_lines.extend(self._close_lists())
            else:
                ret_lines.append(line)
            return ret_lines

        match = re_list.match(line)

        if not match:
            if not self._lists:
                return
            match = re_indented_text.match(line)
            if not match:
                return
            indent, text = match.groups()
        else:
            indent, list_type, checkbox, text = match.groups()
            html_ltype = 'ul' if list_type in bullets else 'ol'
            html_check = ''
            if checkbox in checkbox_defaults:
                html_check = f' class="{checkbox_defaults[checkbox]}"'

        text = self._apply_attrs(text)

        if not list_type and len(line) and not self._previus_line.strip():
            # close all lists
            ret_lines.extend(self._close_lists())
            self._line_processed = False
            return ret_lines

        if self._lists:
            for _list in reversed(self._lists):
                if len(indent) >= len(_list.indent):
                    index = self._lists.index(_list)
                    break
            else:
                ret_lines.extend(self._close_lists())
                ret_lines.append(_new_list(indent, html_ltype, html_check,
                                           text))
                return ret_lines

            if len(self._lists[index+1:]):
                ret_lines.extend(self._close_lists(index=index))

            if list_type:
                if len(indent) > len(self._lists[-1].indent):
                    self._lists.append(List(indent, html_ltype))
                    ret_lines.append(f"<{html_ltype}>\n"
                                     f"<li{html_check}>\n{text}")
                else:
                    ret_lines.append(f'</li>\n<li{html_check}>\n{text}')
            else:
                ret_lines.append(text)

            self._line_processed = True
            return ret_lines

        # new list
        ret_lines.append(_new_list(indent, html_ltype, html_check, text))
        return ret_lines

    def _close_lists(self, index=None):
        """
        Close selected lists started (not included) from index.
        If index is not provided, close all lists
        """
        if not self._lists:
            ret_lines = []
        elif index is None:
            ret_lines = [f"</li>\n</{o.list_type}>\n"
                         for o in reversed(self._lists)]
            self._lists = []
        else:
            ret_lines = [f"</li>\n</{o.list_type}>\n"
                         for o in reversed(self._lists[index + 1:])]
            self._lists = self._lists[:index + 1]
        return ret_lines

    def _html_escape(self, line):
        line = line.replace('&', '&amp;')
        return re_safe_html.sub('&lt;\\1&gt;', line)

    def _handle_tables(self, line):
        if not re.match(r'^\|.+\|$', line):
            if self._table:
                # close table
                lines = [self._table.render()]
                self._table = False
                #self._line_processed = True
                return lines
            return

        line = self._apply_attrs(line)
        if not self._table:
            self._table = Table()
        # remove first and last |, split it to have contents
        self._table.add_rows(line.strip()[1:-1].split('|'))

        # return empty list, defer rendering of table, when whole table is
        # processed
        self._line_processed = True
        return []


def close_para(para, ldest):
    if para:
        ldest.insert(0, '</p>')
        return 0
    return para
