"""
This is kind of translation from vimwiki html export file to python
"""
import dataclasses
import datetime
import html
import logging
import os
import re
import shutil
import sys

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
    arrow_quote: bool = False
    list_leading_spaces: bool = False
    # [in_math, indent_math]
    math: list[int, str] = dataclasses.field(default_factory=list)
    table: list = dataclasses.field(default_factory=list)
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

    def __init__(self, wikifname, conf):
        self._conf = conf
        self.level = 1
        self.root = conf.path
        self.template = None
        self.template_path = conf.template_path
        self.date = ''
        self.wiki_contents = None
        self.nohtml = False
        self._html = ''
        self._table = False
        self.wiki_fname = wikifname
        self.output_dir = conf.path_html
        # TODO: There is subdirectory lost. Correlate it with rel_root and
        # wiki root.
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
        self.images_uri = []

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
        self._state.lists = []
        # [last seen header text in this level, number]
        self._state.header_ids = [['', 0], ['', 0], ['', 0],
                                  ['', 0], ['', 0], ['', 0]]

        # TODO(gryf): merge this somehow with html.escape
        # prepare constants for s_safe_html_line()
        # #s_lt_pattern = '<'
        # #s_gt_pattern = '>'
        # defaults: 'b,i,s,u,sub,sup,kbd,br,hr' - those tags should not be
        # touched
        # if vimwiki#vars#get_global('valid_html_tags') !=? ''
        #     tags = "\|".join([x.strip() for x in
        #                       vimwiki_vars.get_global('valid_html_tags')
        #                       .split(',')])
        #     s_lt_pattern = '\c<\%(/\?\%('.tags.'\)\%(\s\{-1}\S\{-}\)\{-}/\?>\)\@!'
        #     s_gt_pattern = '\c\%(</\?\%('.tags.'\)\%(\s\{-1}\S\{-}\)\{-}/\?\)\@<!>'

        self._previus_line = None
        for line in lsource:
            self._line_processed = False
            header = re_header.match(line)
            if header:
                ldest.append(self._parse_header(header))
                self._previus_line = line
                continue

            if re_comment.match(line):
                # ignore comments
                continue

            if re_hr.match(line):
                ldest.append('<hr />')
                self._previus_line = line
                continue

            oldquote = self._state.quote
            lines = self._parse_line(line)

            # Hack: There could be a lot of empty strings before
            # process_tag_precode find out `quote` is over. So we should delete
            # them all. Think of the way to refactor it out.
            if oldquote != self._state.quote:
                remove_blank_lines(ldest)

            ldest.extend(lines)
            self._previus_line = line

        remove_blank_lines(ldest)

        # process end of file
        # close opened tags if any
        lines = []
        close_precode(self._state.quote, lines)
        close_arrow_quote(self._state.arrow_quote, lines)
        close_para(self._state.para, lines)
        close_math(self._state.math, lines)
        # s_close_tag_list(self._state.lists, lines)
        lines.extend(self._close_lists())
        close_def_list(self._state.deflist, lines)
        #close_table(self._state.table, lines, self._state.header_ids)
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
        if len(self._state.table):
            self._state.table = close_table(self._state.table, lines,
                                            self._state.header_ids)
        if self._state.deflist:
            self._state.deflist = close_def_list(self._state.deflist,
                                                 lines)
        if self._state.quote:
            self._state.quote = close_precode(self._state.quote, lines)
        if self._state.arrow_quote:
            self._state.arrow_quote = close_arrow_quote(self._state
                                                        .arrow_quote,
                                                        lines)
        if self._state.para:
            self._state.para = close_para(self._state.para, lines)

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
        if self._line_processed:
            if lines:
                res_lines.extend(lines)
            return res_lines

        # lists
        lines = self._handle_list(line)
        if self._line_processed:
            res_lines.extend(lines)
            return res_lines

        if lines and self._line_processed:
            res_lines.extend(lines)

        ### quotes
        ##if !processed
        ##    [processed, lines, self._state.quote] = s_process_tag_precode(line, self._state.quote)
        ##    if processed && len(self._state.lists)
        ##        call s_close_tag_list(self._state.lists, lines)
        ##    if processed && self._state.deflist
        ##        self._state.deflist = close_def_list(self._state.deflist, lines)
        ##    if processed && self._state.arrow_quote
        ##        self._state.quote = close_arrow_quote(self._state.arrow_quote, lines)
        ##    if processed && len(self._state.table)
        ##        self._state.table = close_table(self._state.table, lines, self._state.header_ids)
        ##    if processed && self._state.math[0]
        ##        self._state.math = close_math(self._state.math, lines)
        ##    if processed && self._state.para
        ##        self._state.para = close_para(self._state.para, lines)

        ##    call extend(res_lines, lines)

        ### arrow quotes
        ##if !processed
        ##    [processed, lines, self._state.arrow_quote] = s_process_tag_arrow_quote(line, self._state.arrow_quote)
        ##    if processed && self._state.quote
        ##        self._state.quote = close_precode(self._state.quote, lines)
        ##    if processed && len(self._state.lists)
        ##        call s_close_tag_list(self._state.lists, lines)
        ##    if processed && self._state.deflist
        ##        self._state.deflist = close_def_list(self._state.deflist, lines)
        ##    if processed && len(self._state.table)
        ##        self._state.table = close_table(self._state.table, lines, self._state.header_ids)
        ##    if processed && self._state.math[0]
        ##        self._state.math = close_math(self._state.math, lines)
        ##    if processed && self._state.para
        ##        self._state.para = close_para(self._state.para, lines)

        ##    call extend(res_lines, lines)

        ### definition lists
        ##if !processed
        ##    [processed, lines, self._state.deflist] = s_process_tag_def_list(line, self._state.deflist)

        ##    call extend(res_lines, lines)


        # Paragraphs
        lines = self._handle_paragraph(line)
        if self._line_processed and self._lists:
            res_lines.extend(self._close_lists())
        if self._line_processed and (self._state.quote or
                                     self._state.arrow_quote):
            self._state.quote = close_precode(True, lines)
        if self._line_processed and self._state.arrow_quote:
            self._state.arrow_quote = close_arrow_quote(self._state
                                                        .arrow_quote,
                                                        lines)
        if self._line_processed and self._state.math[0]:
            self._state.math = close_math(self._state.math, res_lines)
        if self._line_processed and len(self._state.table):
            self._state.table = close_table(self._state.table, res_lines,
                                            self._state.header_ids)

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
            LOG.warning(f"Header open level doesn't match close level: "
                        f"'{open_level}' vs '{close_level}'.")
            return line_match.string
        level = len(open_level)
        if level > self.max_header_level:
            LOG.warning("Headers cannot exceed %s level.",
                        self.max_header_level)
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
        For now it's calculated using self.root as the vimwiki root directory.

        """
        # TODO: change that to use configured template path instead of src
        #       wiki root.
        result = re_ph_template.search(self.wiki_contents)

        if not result:
            return

        template_fname = result.groups()[0].strip() + self._conf.template_ext
        self.template = os.path.join(self._conf.template_path, template_fname)
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
            try:
                link = self._get_link_out_of_string(link.groupdict()['contents'])
            except:
                raise
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

        LOG.warning('Image "%s" have no schema', dest)
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
            LOG.warning("File `%s' doesn't exists, ignoring", img)
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
                if link in self._conf.assets:
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
        if self._table and not line.strip():
            # close table
            lines = [self._table.render()]
            self._table = False
            self._line_processed = True
            return lines

        if not all((line.strip().startswith('|'), line.strip().endswith('|'),
                   len(line.strip()) > 2)):
            return line

        line = self._apply_attrs(line)
        if not self._table:
            self._table = Table()
        # remove first and last |, split it to have contents
        self._table.add_rows(line.strip()[1:-1].split('|'))

        # return empty list, defer rendering of table, when whole table is
        # processed
        self._line_processed = True
        return []


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
        if (all([re_table_header_sep.match(x) for x in row_list]) and
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
                    while counter is not None:
                        counter += 1
                        if x - counter < 0:
                            break
                        if table[x-counter][y] is None:
                            continue
                        table[x-counter][y].rowspan += 1
                        counter = None
                    continue

                if item.strip() == '>':
                    counter = 0
                    while counter is not None:
                        counter += 1
                        if y - counter < 0:
                            break
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


def remove_blank_lines(lines):
    while len(lines) and lines[-1].strip() == '':
        del lines[-1]



def s_is_img_link(lnk):
    # originally there was regexp for searhing shemas in string; looking for
    # parts of the string should be faster - check that
    #re_schema = re.compile(r'\.\%(png\|jpg\|gif\|jpeg\)$')
    #return re_schema.match(lnk)
    for ext in ('.png', '.jpg', '.jpeg', '.gif'):
        if ext in lnk.lower():
            return 1
    return 0


def safe_html_preformatted(line):
    return line.replace('<', '&lt;').replace('>', '&gt;')


def s_escape_html_attribute(string):
    return string.replace('"', '&quot;')


def s_safe_html_line(line):
    """
    escape & < > when producing HTML text using g:vimwiki_valid_html_tags for
    exepctions
    """
    return re_safe_html.sub('&lt;\\1&gt;', line).replace('&', '&amp;')


def s_mid(value, cnt):
    return value[cnt:-cnt]


def s_subst_func(line, regexp, func, *args):
    # Substitute text found by regexp with result of
    # func(matched) function.

    pos = 0
    lines = split(line, regexp, 1)
    res_line = ''
    for line in lines:
        res_line = res_line.line
        matched = matchstr(line, regexp, pos)
        if matched:
            if args and args[0]:
                res_line += func(matched, 1)
            else:
                res_line += func(matched)
        pos = matchend(line, regexp, pos)
    return res_line


def s_parameterized_wikiname(wikifile):
    initial = fnamemodify(wikifile, ':t:r')
    lower_sanitized = tolower(initial)
    substituted = substitute(lower_sanitized, '[^a-z0-9_-]+','-', 'g')
    substituted = substitute(substituted, '-+','-', 'g')
    substituted = substitute(substituted, '^-', '', 'g')
    substituted = substitute(substituted, '-$', '', 'g')
    return substitute(substituted, '-+', '-', 'g') + '.html'

def s_html_insert_contents(html_lines, content):
    lines = []
#    for line in html_lines
#        if line =~# '%content%'
#            parts = split(line, '%content%', 1)
#            if empty(parts)
#                call extend(lines, content)
#            else
#                for idx in range(len(parts))
#                    call add(lines, parts[idx])
#                    if idx < len(parts) - 1
#                        call extend(lines, content)
#        else
#            call add(lines, line)
    return lines


def s_tag_eqin(value):
    # mathJAX wants \( \) for inline maths
    return '(' + s_mid(value, 1) + ')'


def s_tag_em(value):
    return '<em>' + s_mid(value, 1) + '</em>'


def s_tag_strong(value, header_ids):
    text = s_mid(value, 1)
    id = s_escape_html_attribute(text)
    complete_id = ''
    for l in range(6):
        if header_ids[l][0] != '':
            complete_id += header_ids[l][0] + '-'
    if header_ids[5][0] == '':
        complete_id = complete_id[:-2]
    complete_id += '-' + id
    return '<span id="' + s_escape_html_attribute(complete_id) + '"></span><strong id="' + id + '">' + text + '</strong>'


def s_tag_tags(value, header_ids):
    complete_id = ''
    for level in range(6):
        if header_ids[level][0] != '':
            complete_id += header_ids[level][0] + '-'
    if header_ids[5][0] == '':
        complete_id = complete_id[:-2]
    complete_id = s_escape_html_attribute(complete_id)

    result = []
    for tag in value.split(':'):
        id = s_escape_html_attribute(tag)
        add(result, '<span id="' + complete_id + '-' + id + '"></span><span class="tag" id="' + id + '">' + tag + '</span>')
    return join(result)


def s_tag_todo(value):
    return '<span class="todo">' + value + '</span>'


def s_tag_strike(value):
    return '<del>' + s_mid(value, 2) + '</del>'


def s_tag_super(value):
    return '<sup><small>' + s_mid(value, 1) + '</small></sup>'


def s_tag_sub(value):
    return '<sub><small>' + s_mid(value, 2) + '</small></sub>'


def s_incl_match_arg(nn_index):
    #       match n-th ARG within {{URL[|ARG1|ARG2|...]}}
    # *c,d,e),...
    #rx = vimwiki#vars#get_global('rxWikiInclPrefix'). vimwiki#vars#get_global('rxWikiInclUrl')
    #rx = rx . repeat(vimwiki#vars#get_global('rxWikiInclSeparator') .
    #            \ vimwiki#vars#get_global('rxWikiInclArg'), nn_index-1)
    #if nn_index > 0
    #    rx = rx. vimwiki#vars#get_global('rxWikiInclSeparator'). '\zs' .
    #                \ vimwiki#vars#get_global('rxWikiInclArg') . '\ze'
    #rx = rx . vimwiki#vars#get_global('rxWikiInclArgs') .
    #            \ vimwiki#vars#get_global('rxWikiInclSuffix')
    return rx


def s_linkify_link(src, descr):
    #src_str = ' href="'.s_escape_html_attribute(src).'"'
    #descr = vimwiki#u#trim(descr)
    #descr = (descr ==? '' ? src : descr)
    #descr_str = (descr =~# vimwiki#vars#get_global('rxWikiIncl')
    #            \ ? s_tag_wikiincl(descr)
    #            \ : descr)
    return '<a' + src_str + '>' + descr_str + '</a>'


def s_linkify_image(src, descr, verbatim_str):
    #src_str = ' src="'.src.'"'
    #descr_str = (descr !=? '' ? ' alt="'.descr.'"' : '')
    #verbatim_str = (verbatim_str !=? '' ? ' '.verbatim_str : '')
    return '<img' + src_str.descr_str.verbatim_str + ' />'


def s_tag_weblink(value):
    # Weblink Template -> <a href="url">descr</a>
    #str = value
    #url = matchstr(str, vimwiki#vars#get_syntaxlocal('rxWeblinkMatchUrl'))
    #descr = matchstr(str, vimwiki#vars#get_syntaxlocal('rxWeblinkMatchDescr'))
    #line = s_linkify_link(url, descr)
    return line


def s_tag_wikiincl(value):
    # {{imgurl|arg1|arg2}}      -> ???
    # {{imgurl}}                                -> <img src="imgurl"/>
    # {{imgurl|descr|style="A"}} -> <img src="imgurl" alt="descr" style="A" />
    # {{imgurl|descr|class="B"}} -> <img src="imgurl" alt="descr" class="B" />
    # str = value
    # # custom transclusions
    # line = VimwikiWikiIncludeHandler(str)
    # # otherwise, assume image transclusion
    # if line ==? ''
    #     url_0 = matchstr(str, vimwiki#vars#get_global('rxWikiInclMatchUrl'))
    #     descr = matchstr(str, s_incl_match_arg(1))
    #     verbatim_str = matchstr(str, s_incl_match_arg(2))

    #     link_infos = vimwiki#base#resolve_link(url_0)

    #     if link_infos.scheme =~# '\mlocal\|wiki\d\+\|diary'
    #         url = vimwiki#path#relpath(fnamemodify(s_current_html_file, ':h'), link_infos.filename)
    #         # strip the .html extension when we have wiki links, so that the user can
    #         # simply write {{image.png}} to include an image from the wiki directory
    #         if link_infos.scheme =~# '\mwiki\d\+\|diary'
    #             url = fnamemodify(url, ':r')
    #     else
    #         url = link_infos.filename

    #     url = escape(url, '#')
    #     line = s_linkify_image(url, descr, verbatim_str)
    return line


def s_tag_wikilink(value):
    # [[url]]                                       -> <a href="url.html">url</a>
    # [[url|descr]]                         -> <a href="url.html">descr</a>
    # [[url|{{...}}]]                       -> <a href="url.html"> ... </a>
    # [[fileurl.ext|descr]]         -> <a href="fileurl.ext">descr</a>
    # [[dirurl/|descr]]                 -> <a href="dirurl/index.html">descr</a>
    # [[url#a1#a2]]                         -> <a href="url.html#a1-a2">url#a1#a2</a>
    # [[#a1#a2]]                                -> <a href="#a1-a2">#a1#a2</a>
    ## str = value
    ## url = matchstr(str, vimwiki#vars#get_syntaxlocal('rxWikiLinkMatchUrl'))
    ## descr = matchstr(str, vimwiki#vars#get_syntaxlocal('rxWikiLinkMatchDescr'))
    ## descr = vimwiki#u#trim(descr)
    ## descr = (descr !=? '' ? descr : url)

    ## line = VimwikiLinkConverter(url, s_current_wiki_file, s_current_html_file)
    ## if line ==? ''
    ##     link_infos = vimwiki#base#resolve_link(url, s_current_wiki_file)

    ##     if link_infos.scheme ==# 'file'
    ##         # external file links are always absolute
    ##         html_link = link_infos.filename
    ##     elseif link_infos.scheme ==# 'local'
    ##         html_link = vimwiki#path#relpath(fnamemodify(s_current_html_file, ':h'),
    ##                     \ link_infos.filename)
    ##     elseif link_infos.scheme =~# '\mwiki\d\+\|diary'
    ##         # wiki links are always relative to the current file
    ##         html_link = vimwiki#path#relpath(
    ##                     \ fnamemodify(s_current_wiki_file, ':h'),
    ##                     \ fnamemodify(link_infos.filename, ':r'))
    ##         if html_link !~? '\m/$'
    ##             html_link .= '.html'
    ##     else " other schemes, like http, are left untouched
    ##         html_link = link_infos.filename

    ##     if link_infos.anchor !=? ''
    ##         anchor = substitute(link_infos.anchor, '#', '-', 'g')
    ##         html_link .= '#'.anchor
    ##     line = html_link

    ## line = s_linkify_link(line, descr)
    return line


def tag_remove_internal_link(value):
    ##value = s_mid(value, 2)

    ##line = ''
    ##if value =~# '|'
    ##    link_parts = split(value, '|', 1)
    ##else
    ##    link_parts = split(value, '][', 1)

    ##if len(link_parts) > 1
    ##    if len(link_parts) < 3
    ##        style = ''
    ##    else
    ##        style = link_parts[2]
    ##    line = link_parts[1]
    ##else
    ##    line = value
    return line


def s_make_tag(line, regexp, func, *args):
    # Make tags for a given matched regexp.
    # Exclude preformatted text and href links.
    # FIXME
    ##patt_splitter = '\(`[^`]\+`\)\|'.
    ##                                    \ '\('.vimwiki#vars#get_syntaxlocal('rxPreStart').'.\+'.
    ##                                    \ vimwiki#vars#get_syntaxlocal('rxPreEnd').'\)\|'.
    ##                                    \ '\(<a href.\{-}</a>\)\|'.
    ##                                    \ '\(<img src.\{-}/>\)\|'.
    ##                                    \ '\(<pre.\{-}</pre>\)\|'.
    ##                                    \ '\('.s_rxEqIn.'\)'

    ###FIXME FIXME !!! these can easily occur on the same line!
    ###XXX    {{{ }}} ??? obsolete
    ##if '`[^`]\+`' ==# regexp || '{{{.\+}}}' ==# regexp ||
    ##            \ s_rxEqIn ==# regexp
    ##    res_line = s_subst_func(line, regexp, func)
    ##else
    ##    pos = 0
    ##    # split line with patt_splitter to have parts of line before and after
    ##    # href links, preformatted text
    ##    # ie:
    ##    # hello world `is just a` simple <a href="link.html">type of</a> prg.
    ##    # result:
    ##    # ['hello world ', ' simple ', 'type of', ' prg']
    ##    lines = split(line, patt_splitter, 1)
    ##    res_line = ''
    ##    for line in lines
    ##        if 0
    ##            res_line = res_line.s_subst_func(line, regexp, func, 1)
    ##        else
    ##            res_line = res_line.s_subst_func(line, regexp, func)
    ##        res_line = res_line.matchstr(line, patt_splitter, pos)
    ##        pos = matchend(line, patt_splitter, pos)
    return res_line

#def s_process_tags_typefaces(line, header_ids):
#    line = line
#    # Convert line tag by tag
#    ##line = s_make_tag(line, s_rxItalic, 's_tag_em')
#    ##line = s_make_tag(line, s_rxBold, 's_tag_strong', header_ids)
#    ##line = s_make_tag(line, vimwiki#vars#get_wikilocal('rx_todo'), 's_tag_todo')
#    ##line = s_make_tag(line, s_rxDelText, 's_tag_strike')
#    ##line = s_make_tag(line, s_rxSuperScript, 's_tag_super')
#    ##line = s_make_tag(line, s_rxSubScript, 's_tag_sub')
#    ##line = s_make_tag(line, s_rxCode, 's_tag_code')
#    ##line = s_make_tag(line, s_rxEqIn, 's_tag_eqin')
#    ##line = s_make_tag(line, vimwiki#vars#get_syntaxlocal('rxTags'), 's_tag_tags', header_ids)
#    return line
#

#def process_inline_tags(line, header_ids):
#    line = s_process_tags_links(line)
#    line = s_process_tags_typefaces(line, header_ids)
#    return line


def close_math(math, ldest):
    if math[0]:
        insert(ldest, "\\]")
        return 0
    return math


def close_precode(quote, ldest):
    if quote:
        insert(ldest, '</pre></code>')
        return 0
    return quote

def close_arrow_quote(arrow_quote, ldest):
    if arrow_quote:
        insert(ldest, '</p></blockquote>')
        return 0
    return arrow_quote

def close_para(para, ldest):
    if para:
        ldest.insert(0, '</p>')
        return 0
    return para


#def close_table(table, ldest, header_ids):
#    # The first element of table list is a string which tells us if table should be centered.
#    # The rest elements are rows which are lists of columns:
#    # ['center',
#    #       [ CELL1, CELL2, CELL3 ],
#    #       [ CELL1, CELL2, CELL3 ],
#    #       [ CELL1, CELL2, CELL3 ],
#    # ]
#    # And CELLx is: { 'body': 'col_x', 'rowspan': r, 'colspan': c }
#
#    def s_sum_rowspan(table):
#        table = table
#
#        # Get max cells
#        max_cells = 0
#        for row in table[1:]:
#            n_cells = len(row)
#            if n_cells > max_cells:
#                max_cells = n_cells
#
#        # Sum rowspan
#        for cell_idx in range(max_cells):
#            rows = 1
#
#            for row_idx in range(len(table)-1, 1, -1):
#                if cell_idx >= len(table[row_idx]):
#                    rows = 1
#                    continue
#
#                if table[row_idx][cell_idx].rowspan == 0:
#                    rows += 1
#                else:  # table[row_idx][cell_idx].rowspan == 1
#                    table[row_idx][cell_idx].rowspan = rows
#                    rows = 1
#
#    def s_sum_colspan(table):
#        for row in table[1:]:
#            cols = 1
#
#            for cell_idx in range(len(row)-1, 0, -1):
#                if row[cell_idx].colspan == 0:
#                    cols += 1
#                else:  # row[cell_idx].colspan == 1
#                    row[cell_idx].colspan = cols
#                    cols = 1
#
#    def s_close_tag_row(row, header, ldest, header_ids):
#        ldest.append('<tr>')
#
#        # Set tag element of columns
#        if header:
#            tag_name = 'th'
#        else:
#            tag_name = 'td'
#
#        # Close tag of columns
#        for cell in row:
#            if cell.rowspan == 0 or cell.colspan == 0:
#                continue
#
#            if cell.rowspan > 1:
#                rowspan_attr = f' rowspan="{cell.rowspan}"'
#            else:  # cell.rowspan == 1
#                rowspan_attr = ''
#
#            if cell.colspan > 1:
#                colspan_attr = f' colspan="{cell.colspan}"'
#            else:  # cell.colspan == 1
#                colspan_attr = ''
#
#            ldest.append(f'<{tag_name}{rowspan_attr}{colspan_attr}>')
#            ldest.append(process_inline_tags(cell.body, header_ids))
#            ldest.append('</{tag_name}>')
#
#        add(ldest, '</tr>')
#
#    table = table
#    ldest = ldest
#    if len(table):
#        s_sum_rowspan(table)
#        s_sum_colspan(table)
#
#        if table[0] == 'center':
#            add(ldest, "<table class='center'>")
#        else:
#            add(ldest, '<table>')
#
#        # Empty lists are table separators.
#        # Search for the last empty list. All the above rows would be a table header.
#        # We should exclude the first element of the table list as it is a text tag
#        # that shows if table should be centered or not.
#        head = 0
#        for idx in range(len(table)-1, 1, -1):
#            if empty(table[idx]):
#                head = idx
#                break
#        if head > 0:
#            add(ldest, '<thead>')
#            for row in table[1 : head-1]:
#                if not empty(filter(row, '!empty(v:val)')):
#                    s_close_tag_row(row, 1, ldest, header_ids)
#            add(ldest, '</thead>')
#            add(ldest, '<tbody>')
#            for row in table[head+1 :]:
#                s_close_tag_row(row, 0, ldest, header_ids)
#            add(ldest, '</tbody>')
#        else:
#            for row in table[1 :]:
#                s_close_tag_row(row, 0, ldest, header_ids)
#        add(ldest, '</table>')
#        table = []
#    return table
#
#
#def s_close_tag_list(lists, ldest):
#    while len(lists):
#        item = remove(lists, 0)
#        insert(ldest, item[0])
#
#
def close_def_list(deflist, ldest):
    if deflist:
        insert(ldest, '</dl>')
        return 0
    return deflist


#def s_process_tag_pre(line, pre):
#    lines = []
#    processed = 0
#    open_match = re.match(r'^(\s*){{{([^\(}}}\)]*)\s*$', line)
#    closed_match = re.match(r'^\s*}}}\s*$', line)
#    if not pre[0] and open_match:
#        block_type = open_match.group()[1].strip()
#        indent = len(open_match.group()[0])
#        if block_type:
#            lines.append(f'<pre {block_type}>')
#        else:
#            lines.append('<pre>')
#        pre = [1, indent]
#        processed = 1
#    elif pre[0] and closed_match:
#        pre = [0, 0]
#        lines.append('</pre>')
#        processed = 1
#    elif pre[0]:
#        processed = 1
#        lines.append(safe_html_preformatted(line))
#    return processed, lines, pre
#
#
#def s_process_tag_math(line, math):
#    # math is the list of [is_in_math, indent_of_math]
#    lines = []
#    math = math
#    processed = 0
#    if not math[0] and line == 'dupa':  # '^\s*{{\$[^\(}}$\)]*\s*$'
#        css_class = matchstr(line, 'dupa')  # składanie regexpów w lodcie /o\ '{{$\zs.*$')
#        #FIXME css_class cannot be any string!
#        css_class = substitute(css_class, '\s\+$', '', 'g')
#        # store the environment name in a global variable in order to close the
#        # environment properly
#        s_current_math_env = matchstr(css_class, '^%\zs\S\+\ze%')
#        if s_current_math_env:
#            add(lines, substitute(css_class, '^%\(\S\+\)%', '\\begin{\1}', ''))
#        elif css_class:
#            add(lines, "\\\[".css_class)
#        else:
#            add(lines, "\\\[")
#        math = [1, len(matchstr(line, 'asd'))] # no weź. '^\s*\ze{{\$'))]
#        processed = 1
#    elif math[0] and line == 'dupa': # '^\s*}}\$\s*$'
#        math = [0, 0]
#        if s_current_math_env:
#            add(lines, "\\end{" + s_current_math_env + '}')
#        else:
#            add(lines, "\\\]")
#        processed = 1
#    elif math[0]:
#        processed = 1
#        add(lines, substitute(line, '^\s\{' + math[1] + '}', '', ''))
#    return processed, lines, math
#
#
#def s_process_tag_precode(line, quote):
#    # Process indented precode
#    lines = []
#    line = line
#    quote = quote
#    processed = 0
#
#    # Check if start
#    ##if line =~# '^\s\{4,}'
#    ##    line = substitute(line, '^\s*', '', '')
#    ##    if !quote
#    ##    # Check if must decrease level
#    ##        line = '<pre><code>' . line
#    ##        quote = 1
#    ##    processed = 1
#    ##    call add(lines, line)
#
#    ### Check if end
#    ##elseif quote
#    ##    call add(lines, '</code></pre>')
#    ##    quote = 0
#
#    return processed, lines, quote
#
#def s_process_tag_arrow_quote(line, arrow_quote):
#    lines = []
#    arrow_quote = arrow_quote
#    processed = 0
#    line = line
#
#    # Check if must increase level
#    ##if line =~# '^' . repeat('\s*&gt;', arrow_quote + 1)
#    ##    # Increase arrow_quote
#    ##    while line =~# '^' . repeat('\s*&gt;', arrow_quote + 1)
#    ##        call add(lines, '<blockquote>')
#    ##        call add(lines, '<p>')
#    ##        arrow_quote .= 1
#
#    ##    # Treat & Add line
#    ##    stripped_line = substitute(line, '^\%(\s*&gt;\)\+', '', '')
#    ##    if stripped_line =~# '^\s*$'
#    ##        call add(lines, '</p>')
#    ##        call add(lines, '<p>')
#    ##    call add(lines, stripped_line)
#    ##    processed = 1
#
#    ### Check if must decrease level
#    ##elseif arrow_quote > 0
#    ##    while line !~# '^' . repeat('\s*&gt;', arrow_quote - 1)
#    ##        call add(lines, '</p>')
#    ##        call add(lines, '</blockquote>')
#    ##        arrow_quote -= 1
#    return processed, lines, arrow_quote
#
#
#def s_process_tag_list(line, lists, lstLeadingSpaces):
#    def s_add_checkbox(line, rx_list):
#        st_tag = '<li>'
#        chk = matchlist(line, rx_list)
#        if not empty(chk) and len(chk[1]) > 0:
#            ##completion = index(vimwiki#vars#get_wikilocal('listsyms_list'), chk[1])
#            ##n = len(vimwiki#vars#get_wikilocal('listsyms_list'))
#            if completion == 0:
#                st_tag = '<li class="done0">'
#            ##elseif completion == -1 && chk[1] == vimwiki#vars#get_global('listsym_rejected')
#            ##    st_tag = '<li class="rejected">'
#            ##elseif completion > 0 && completion < n
#            ##    completion = float2nr(round(completion / (n-1.0) * 3.0 + 0.5 ))
#            ##    st_tag = '<li class="done'.completion.'">'
#        return [st_tag, '']
#
#
#    in_list = (len(lists) > 0)
#    lstLeadingSpaces = lstLeadingSpaces
#
#    # If it is not list yet then do not process line that starts from *bold*
#    # text.
#    # XXX necessary? in *bold* text, no space must follow the first *
#    #if not in_list:
#    #    pos = match(line, '^\s*' + s_rxBold)
#    #    if pos != -1:
#    #        return [0, [], lstLeadingSpaces]
#
#    lines = []
#    processed = 0
#    checkboxRegExp = '\s*\[\(.\)\]\s*'
#    maybeCheckboxRegExp = '\%(' + checkboxRegExp + '\)\?'
#
#    if line.strip()[0:1] in ['- ', '* ', '# ']:
#        lstSym = matchstr(line, s_bullets)
#        lstTagOpen = '<ul>'
#        lstTagClose = '</ul>'
#        lstRegExp = '^\s*' + s_bullets + '\s'
#    elif re_list_numbers.match(line.strip()[0:1]):
#    #elseif line =~# '^\s*'.s_numbers.'\s'
#        lstSym = matchstr(line, s_numbers)
#        lstTagOpen = '<ol>'
#        lstTagClose = '</ol>'
#        lstRegExp = '^\s*'+s_numbers+'\s'
#    else:
#        lstSym = ''
#        lstTagOpen = ''
#        lstTagClose = ''
#        lstRegExp = ''
#
#    # If we're at the start of a list, figure out how many spaces indented we are so we can later
#    # determine whether we're indented enough to be at the setart of a blockquote
#    if lstSym:  # !=# ''
#        lstLeadingSpaces = strlen(matchstr(line, lstRegExp.maybeCheckboxRegExp))
#
#    # Jump empty lines
#    if in_list and not line:  # =~# '^$'
#        # Just Passing my way, do you mind ?
#        #[processed, lines, quote] = s_process_tag_precode(line, g:self._state.quote)
#        processed = 1
#        return [processed, lines, lstLeadingSpaces]
#
#    # Can embedded indented code in list (Issue #55)
#    b_permit = in_list
#    #blockquoteRegExp = '^\s\{' + (lstLeadingSpaces + 2) + ',}[^[:space:]>*-]'
#    #b_match = lstSym ==# '' && line =~# blockquoteRegExp
#    #b_match = b_match || g:self._state.quote
#    #if b_permit && b_match
#    #    [processed, lines, g:self._state.quote] = s_process_tag_precode(line, g:self._state.quote)
#    #    if processed == 1
#    #        return [processed, lines, lstLeadingSpaces]
#
#    # New switch
#    if lstSym:
#        # To get proper indent level 'retab' the line -- change all tabs
#        # to spaces*tabstop
#        line = substitute(line, '\t', repeat(' ', tabstop), 'g')
#        indent = stridx(line, lstSym)
#
#        [st_tag, en_tag] = s_add_checkbox(line, lstRegExp.checkboxRegExp)
#
#        if not in_list:
#            add(lists, [lstTagClose, indent])
#            add(lines, lstTagOpen)
#        elif in_list and indent > lists[-1][1]:
#            item = remove(lists, -1)
#            add(lines, item[0])
#
#            add(lists, [lstTagClose, indent])
#            add(lines, lstTagOpen)
#        elif in_list and indent < lists[-1][1]:
#            while len(lists) and indent < lists[-1][1]:
#                item = remove(lists, -1)
#                add(lines, item[0])
#        elif in_list:
#            item = remove(lists, -1)
#            add(lines, item[0])
#
#        add(lists, [en_tag, indent])
#        add(lines, st_tag)
#        add(lines, substitute(line, lstRegExp.maybeCheckboxRegExp, '', ''))
#        processed = 1
#
#    elif in_list and line:  # =~# '^\s\+\S\+'
#        add(lines, line)
#        processed = 1
#
#    # Close tag
#    else:
#        s_close_tag_list(lists, lines)
#
#    return processed, lines, lstLeadingSpaces
#
#
#def s_process_tag_def_list(line, deflist):
#    lines = []
#    deflist = deflist
#    processed = 0
#    matches = matchlist(line, '\(^.*\)::\%(\s\|$\)\(.*\)')
#    ##if !deflist && len(matches) > 0
#    ##    call add(lines, '<dl>')
#    ##    deflist = 1
#    ##if deflist && len(matches) > 0
#    ##    if matches[1] !=? ''
#    ##        call add(lines, '<dt>'.matches[1].'</dt>')
#    ##    if matches[2] !=? ''
#    ##        call add(lines, '<dd>'.matches[2].'</dd>')
#    ##    processed = 1
#    ##elseif deflist
#    ##    deflist = 0
#    ##    call add(lines, '</dl>')
#    return processed, lines, deflist
#
#
#def s_process_tag_para(line, para):
#    lines = []
#    processed = 0
#    if line.strip():
#        if not para:
#            lines.append('<p>')
#            para = 1
#        processed = 1
#        # default is to ignore newlines (i.e. do not insert <br/> at the end
#        # of the line)
#        lines.append(line)
#    elif para and line.strip() == '':
#        lines.append('</p>')
#        para = 0
#    return processed, lines, para
#
#
#def s_process_tag_h(line, id):
#    line = line
#    processed = 0
#    h_level = 0
#    h_text = ''
#    h_id = ''
#
#    ##if line =~# vimwiki#vars#get_syntaxlocal('rxHeader')
#    ##    h_level = vimwiki#u#count_first_sym(line)
#    ##if h_level > 0
#
#    ##    h_text = vimwiki#u#trim(matchstr(line, vimwiki#vars#get_syntaxlocal('rxHeader')))
#    ##    h_number = ''
#    ##    h_complete_id = ''
#    ##    h_id = s_escape_html_attribute(h_text)
#    ##    centered = (line =~# '^\s')
#
#    ##    if h_text !=# vimwiki#vars#get_wikilocal('toc_header')
#
#    ##        id[h_level-1] = [h_text, id[h_level-1][1]+1]
#
#    ##        # reset higher level ids
#    ##        for level in range(h_level, 5)
#    ##            id[level] = ['', 0]
#
#    ##        for l in range(h_level-1)
#    ##            h_number .= id[l][1].'.'
#    ##            if id[l][0] !=? ''
#    ##                h_complete_id .= id[l][0].'-'
#    ##        h_number .= id[h_level-1][1]
#    ##        h_complete_id .= id[h_level-1][0]
#
#    ##        if vimwiki#vars#get_global('html_header_numbering')
#    ##            num = matchstr(h_number,
#    ##                        \ '^\(\d.\)\{'.(vimwiki#vars#get_global('html_header_numbering')-1).'}\zs.*')
#    ##            if !empty(num)
#    ##                num .= vimwiki#vars#get_global('html_header_numbering_sym')
#    ##            h_text = num.' '.h_text
#    ##        h_complete_id = s_escape_html_attribute(h_complete_id)
#    ##        h_part  = '<div id="'.h_complete_id.'">'
#    ##        h_part .= '<h'.h_level.' id="'.h_id.'"'
#    ##        a_tag = '<a href="#'.h_complete_id.'">'
#
#    ##    else
#
#    ##        h_part = '<div id="'.h_id.'" class="toc">'
#    ##        h_part .= '<h'.h_level.' id="'.h_id.'"'
#    ##        a_tag = '<a href="#'.h_id.'">'
#
#
#    ##    if centered
#    ##        h_part .= ' class="header justcenter">'
#    ##    else
#    ##        h_part .= ' class="header">'
#
#    ##    h_text = process_inline_tags(h_text, id)
#
#    ##    line = h_part.a_tag.h_text.'</a></h'.h_level.'></div>'
#
#    ##    processed = 1
#    return [processed, line]
#
#
#def process_table(line, table, header_ids):
#    def table_empty_cell(value):
#        cell = {}
#
#        #if value =~# '^\s*\\/\s*$'
#        #    cell.body        = ''
#        #    cell.rowspan = 0
#        #    cell.colspan = 1
#        #elseif value =~# '^\s*&gt;\s*$'
#        #    cell.body        = ''
#        #    cell.rowspan = 1
#        #    cell.colspan = 0
#        #elseif value =~# '^\s*$'
#        #    cell.body        = '&nbsp;'
#        #    cell.rowspan = 1
#        #    cell.colspan = 1
#        #else
#        #    cell.body        = value
#        #    cell.rowspan = 1
#        #    cell.colspan = 1
#
#        return cell
#
#    def table_add_row(table, line):
#        #if empty(table)
#        #    if line =~# '^\s\+'
#        #        row = ['center', []]
#        #    else
#        #        row = ['normal', []]
#        #else
#        #    row = [[]]
#        return row
#
#    table = table
#    lines = []
#    processed = 0
#
#    #if vimwiki#tbl#is_separator(line)
#    #    call extend(table, table_add_row(table, line))
#    #    processed = 1
#    #elseif vimwiki#tbl#is_table(line)
#    #    call extend(table, table_add_row(table, line))
#
#    #    processed = 1
#    #    # cells = split(line, vimwiki#tbl#cell_splitter(), 1)[1: -2]
#    #    cells = vimwiki#tbl#get_cells(line)
#    #    call map(cells, 'table_empty_cell(v:val)')
#    #    call extend(table[-1], cells)
#    #else
#    #    table = close_table(table, lines, header_ids)
#    return [processed, lines, table]


def convert_file(wikifile, conf):
    vwtohtml = VimWiki2Html(wikifile, conf)
    vwtohtml.convert()
    return vwtohtml
