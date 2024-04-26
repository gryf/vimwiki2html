"""
This is translation from vimwiki html export file to python
"""
import datetime
import os
import re


# XXX: remove this
ROOT = os.path.expanduser("~/vimwiki")
OUTPUT_DIR = os.path.expanduser("~/vimwiki_html")

vimwiki_vars = {}


class Generic:
    """
    generic namespace
    """


class Html:
    """
    Represent single wiki file
    """
    re_ph_nohtml = re.compile(r'\n?%nohtml\s*\n')
    re_ph_title = re.compile(r'\n?%title\s(.*)\n')
    re_ph_template = re.compile(r'\n?%template\s(.*)\n')
    re_ph_date = re.compile(r'\n?\s*%date\s(.*)\n')
    re_ml_comment = re.compile(r'%%\+.*?\+%%', flags=re.DOTALL)

    template_ext = 'tpl'

    def __init__(self, wikifname, output_dir, root):
        self.level = 1
        self.root = root
        self.template = None
        self.date = None
        with open(wikifname) as fobj:
            self.wiki_contents = fobj.read()
        self.nohtml = bool(self.re_ph_nohtml.search(self.wiki_contents))
        self._html = ''
        self.wiki_fname = wikifname
        self.output_dir = output_dir
        self.html_fname = os.path.join(output_dir, os.path
                                       .splitext(os.path
                                                 .basename(wikifname))[0] +
                                       '.html')
        self._title = None

    @property
    def title(self):
        if not self._title:
            return os.path.basename(os.path.splitext(self.wiki_fname)[0])
        return self._title

    @property
    def html(self):
        return self._html

    def convert(self):
        # exit early if there is %nohtml placeholder
        if self.nohtml:
            print(f'no content found for {self.wikifile}')
            return

        # do global substitution and removal - remove multiline comments and
        # placeholders
        self._remove_multiline_comments()
        self._find_title()
        self._find_template()
        self._find_date()

        html_struct = s_convert_file_to_lines(self.wiki_contents)
        self._html = '\n'.join(html_struct['html'])

    def _media(self):
        """
        Placeholder for attached media (inline images, link to local images
        and files).
        """

    def _remove_multiline_comments(self):
        """
        Remove comments enclosed %%+ and +%% markings including markins as
        well.
        """
        self.wiki_contents = self.re_ml_comment.sub('', self.wiki_contents)

    def _find_title(self):
        """
        Search for %title placeholder. If found set title and remove the line
        from source wiki.
        """
        result = self.re_ph_title.search(self.wiki_contents)

        if not result:
            return
        self._title = result.groups()[0].strip()
        self.wiki_contents = self.re_ph_title.sub('\n', self.wiki_contents)

    def _find_template(self):
        """
        Search for %template placeholder. If found set it and remove the
        line from source wiki.
        """
        result = self.re_ph_template.search(self.wiki_contents)

        if not result:
            return
        basename = result.groups()[0].strip()
        path = os.path.extsep.join([basename, self.template_ext])
        self.template = os.path.join(self.root, path)
        self.wiki_contents = self.re_ph_template.sub('\n', self.wiki_contents)

    def _find_date(self):
        """
        Search for %date placeholder. If found set it and remove the line from
        source wiki.
        """
        result = self.re_ph_date.search(self.wiki_contents)

        if not result:
            return

        self.date = result.groups()[0].strip()
        self.wiki_contents = self.re_ph_date.sub('\n', self.wiki_contents)

        if not self.date:
            # TODO: support different date formats - another commandline
            # argument?
            # TODO: support TZ for current date
            self.date = datetime.datetime.now().strftime('%Y-%m-%d')


glob = Generic()

s_rxBold = (r'\%(^\|\s\|[[:punct:]]\)\@<=\*\%([^*`[:space:]][^*`]*[^*`'
            r'[:space:]]\|[^*`[:space:]]\)\*\%([[:punct:]]\|\s\|$\)\@=')

# text: _emphasis_ or *emphasis*
s_rxItalic = '\%(^\|\s\|[[:punct:]]\)\@<=_\%([^_`[:space:]][^_`]*[^_`[:space:]]\|[^_`[:space:]]\)_\%([[:punct:]]\|\s\|$\)\@='

# text: $ equation_inline $
s_rxEqIn = '\$[^$`]\+\$'

# text: `code`
s_rxCode = '`[^`]\+`'

# text: ~~deleted text~~
s_rxDelText = '\~\~[^~`]\+\~\~'

# text: ^superscript^
s_rxSuperScript = '\^[^^`]\+\^'

# text: ,,subscript,,
s_rxSubScript = ',,[^,`]\+,,'

# match all the tags in the wiki and replace them, besides defined, simple ones
re_safe_html = re.compile(r'<(\s*/*[^b,i,s,u,sub,sup,kbd,br,hr]*?)>')

def s_root_path(subdir):
    # XXX: not used here - this have nothing to do with the conversion
    return os.path.relpath(ROOT, os.path.join(ROOT, subdir))


def s_syntax_supported():
    return vimwiki#vars#get_wikilocal('syntax') ==? 'default'


def s_remove_blank_lines(lines):
    while len(lines) and lines[-1].strip() == '':
        del lines[-1]


def s_is_web_link(lnk):
    # originally there was regexp for searhing shemas in string; looking for
    # parts of the string should be faster - check that
    #re_schema = re.compile(r'^\%(https://\|http://\|www.\|ftp://\|'
    #                       r'file://\|mailto:\)')
    #return re_schema.match(lnk)
    for schema in ('https://', 'http://', 'www.', 'ftp://', 'file://',
                   'mailto'):
        if schema in lnk.lower():
            return 1
    return 0


def s_is_img_link(lnk):
    # originally there was regexp for searhing shemas in string; looking for
    # parts of the string should be faster - check that
    #re_schema = re.compile(r'\.\%(png\|jpg\|gif\|jpeg\)$')
    #return re_schema.match(lnk)
    for ext in ('.png', '.jpg', '.jpeg', '.gif'):
        if ext in lnk.lower():
            return 1
    return 0


#XXX not used
#def s_has_abs_path(fname):
#    if fname =~# '\(^.:\)\|\(^/\)'
#        return 1
#    return 0


def s_find_autoload_file(name):
    # XXX: not used here - this have nothing to do with the conversion
    return os.path.join(ROOT, name)


def s_default_CSS_full_name(path):
    # XXX: not used here - this have nothing to do with the conversion
    return os.path.join(ROOT, 'style.css')


def s_create_default_CSS(path):
    # XXX: provide css file as a copy of original one to the output dir
    #css_full_name = s_default_CSS_full_name(path)
    #if glob(css_full_name) ==? ''
    #    call vimwiki#path#mkdir(fnamemodify(css_full_name, ':p:h'))
    #    default_css = s_find_autoload_file('style.css')
    #    if default_css !=? ''
    #        lines = readfile(default_css)
    #        call writefile(lines, css_full_name)
    #        return 1
    return 0


def s_template_full_name(name):
    # XXX: provide template file path out of vim config
    #name = name
    #if name ==? ''
    #    name = vimwiki#vars#get_wikilocal('template_default')

    ## Suffix Path by a / is not
    #path = vimwiki#vars#get_wikilocal('template_path')
    #if strridx(path, '/') +1 != len(path)
    #    path .= '/'

    #ext = vimwiki#vars#get_wikilocal('template_ext')

    #fname = expand(path . name . ext)

    #if filereadable(fname)
    #    return fname
    #else
    #    return ''
    return ''


def s_get_html_template(template):
    # XXX: not used here - this have nothing to do with the conversion
    lines=[]

    template_name = os.path.join(ROOT, 'default.tpl')
    if template:
        template_name = template_full_name(template)

    with open(template_name) as fobj:
        return fobj.read()


def safe_html_preformatted(line):
    line = line.replace('<', '\&lt;')
    line = line.replace('>', '\&gt;')
    return line


def s_escape_html_attribute(string):
    return string.replace('"', '\&quot;')


def s_safe_html_line(line):
    """
    escape & < > when producing HTML text using g:vimwiki_valid_html_tags for
    exepctions
    """
    line = re_safe_html.sub('&lt;\\1&gt;', line)
    line = line.replace('&', '\&amp;')
    return line


def s_delete_html_files(path):
    # XXX: not used here - this have nothing to do with the conversion
    wiki_fnames = []
    for root, dirs, files in os.walk(ROOT):
        for fname in files:
            if fname.lower().endswith('.wiki'):
                fname = os.path.splitext(fname)[0] + '.html'
                fname = os.path.relpath(fname, ROOT)
                fname = os.path.join(path, fname)
                wiki_fnames.append(fname)
    # XXX: add user html files to excluded list
    # ignore user html files, e.g. search.html,404.html
    #if stridx(vimwiki#vars#get_global('user_htmls'), fnamemodify(fname, ':t')) >= 0
    #          continue

    for root, dirs, files in os.walk(path):
        for fname in files:
            fullpath = os.path.join(root, fname)
            if fullpath in wiki_fnames:
                continue
            # XXX: egazmine, if all seleted files should be removed
            print(f'rm {fullpath}')

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


def s_process_date(placeholders, default_date):
    if placeholders:
        for (type_, param), row, idx in placeholders:
            if type_.lower() == 'date' and param:
                return param
    return default_date


def s_process_title(placeholders, default_title):
    if placeholders:
        for (type_, param), row, idx in placeholders:
            if type_.lower() == 'title' and param:
                return param
    return default_title


def s_is_html_uptodate(wikifile):
    # XXX: not used here - this have nothing to do with the conversion
    tpl_time = -1

    tpl_file = s_template_full_name('')
    if tpl_file != '':
        tpl_time = os.stat(tpl_file).st_mtime

    wikifile = os.path.abspath(os.path.join(ROOT, wikifile))
    wiki_time = os.stat(wikifile).st_mtime

    htmlfile = os.path.join(OUTPUT_DIR, os.path.splitext(wikifile) + '.html')
    html_time = os.stat(htmlfile).st_mtime

    return wiki_time <= html_time and tpl_time <= html_time


def s_parameterized_wikiname(wikifile):
    initial = fnamemodify(wikifile, ':t:r')
    lower_sanitized = tolower(initial)
    substituted = substitute(lower_sanitized, '[^a-z0-9_-]\+','-', 'g')
    substituted = substitute(substituted, '\-\+','-', 'g')
    substituted = substitute(substituted, '^-', '', 'g')
    substituted = substitute(substituted, '-$', '', 'g')
    return substitute(substituted, '\-\+', '-', 'g') + '.html'

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
    return '\(' + s_mid(value, 1) + '\)'


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


def s_tag_code(value):
    retstr = '<code'

    string = s_mid(value, 1)
    match = match(string, '^#[a-fA-F0-9]\{6\}$')

    if match != -1:
        r = eval('0x' + string[1:2])
        g = eval('0x' + string[3:4])
        b = eval('0x' + string[5:6])

        fg_color = 'black' if (((0.299 * r + 0.587 * g + 0.114 * b) / 0xFF) > 0.5) else 'white'

        retstr += " style='background-color:" + string + ';color:' + fg_color + ";'"

    retstr += '>' + safe_html_preformatted(string) + '</code>'
    return retstr


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


def s_tag_remove_internal_link(value):
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


def s_tag_remove_external_link(value):
    ##value = s_mid(value, 1)

    ##line = ''
    ##if s_is_web_link(value)
    ##    lnkElements = split(value)
    ##    head = lnkElements[0]
    ##    rest = join(lnkElements[1:])
    ##    if rest ==? ''
    ##        rest = head
    ##    line = rest
    ##elseif s_is_img_link(value)
    ##    line = '<img src="'.value.'" />'
    ##else
    ##    # [alskfj sfsf] shouldn't be a link. So return it as it was --
    ##    # enclosed in [...]
    ##    line = '['.value.']'
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


def s_process_tags_remove_links(line):
    line = line
    line = s_make_tag(line, '\[\[.\{-}\]\]', 's_tag_remove_internal_link')
    line = s_make_tag(line, '\[.\{-}\]', 's_tag_remove_external_link')
    return line


def s_process_tags_typefaces(line, header_ids):
    line = line
    # Convert line tag by tag
    ##line = s_make_tag(line, s_rxItalic, 's_tag_em')
    ##line = s_make_tag(line, s_rxBold, 's_tag_strong', header_ids)
    ##line = s_make_tag(line, vimwiki#vars#get_wikilocal('rx_todo'), 's_tag_todo')
    ##line = s_make_tag(line, s_rxDelText, 's_tag_strike')
    ##line = s_make_tag(line, s_rxSuperScript, 's_tag_super')
    ##line = s_make_tag(line, s_rxSubScript, 's_tag_sub')
    ##line = s_make_tag(line, s_rxCode, 's_tag_code')
    ##line = s_make_tag(line, s_rxEqIn, 's_tag_eqin')
    ##line = s_make_tag(line, vimwiki#vars#get_syntaxlocal('rxTags'), 's_tag_tags', header_ids)
    return line


def s_process_tags_links(line):
    line = line
    #line = s_make_tag(line, vimwiki#vars#get_syntaxlocal('rxWikiLink'), 's_tag_wikilink')
    #line = s_make_tag(line, vimwiki#vars#get_global('rxWikiIncl'), 's_tag_wikiincl')
    #line = s_make_tag(line, vimwiki#vars#get_syntaxlocal('rxWeblink'), 's_tag_weblink')
    return line


def s_process_inline_tags(line, header_ids):
    line = s_process_tags_links(line)
    line = s_process_tags_typefaces(line, header_ids)
    return line


def s_close_tag_pre(pre, ldest):
    if pre[0]:
        insert(ldest, '</pre>')
        return 0
    return pre


def s_close_tag_math(math, ldest):
    if math[0]:
        insert(ldest, "\\\]")
        return 0
    return math


def s_close_tag_precode(quote, ldest):
    if quote:
        insert(ldest, '</pre></code>')
        return 0
    return quote

def s_close_tag_arrow_quote(arrow_quote, ldest):
    if arrow_quote:
        insert(ldest, '</p></blockquote>')
        return 0
    return arrow_quote

def s_close_tag_para(para, ldest):
    if para:
        ldest.insert('</p>')
        return 0
    return para


def s_close_tag_table(table, ldest, header_ids):
    # The first element of table list is a string which tells us if table should be centered.
    # The rest elements are rows which are lists of columns:
    # ['center',
    #       [ CELL1, CELL2, CELL3 ],
    #       [ CELL1, CELL2, CELL3 ],
    #       [ CELL1, CELL2, CELL3 ],
    # ]
    # And CELLx is: { 'body': 'col_x', 'rowspan': r, 'colspan': c }

    def s_sum_rowspan(table):
        table = table

        # Get max cells
        max_cells = 0
        for row in table[1:]:
            n_cells = len(row)
            if n_cells > max_cells:
                max_cells = n_cells

        # Sum rowspan
        for cell_idx in range(max_cells):
            rows = 1

            for row_idx in range(len(table)-1, 1, -1):
                if cell_idx >= len(table[row_idx]):
                    rows = 1
                    continue

                if table[row_idx][cell_idx].rowspan == 0:
                    rows += 1
                else:  # table[row_idx][cell_idx].rowspan == 1
                    table[row_idx][cell_idx].rowspan = rows
                    rows = 1

    def s_sum_colspan(table):
        for row in table[1:]:
            cols = 1

            for cell_idx in range(len(row)-1, 0, -1):
                if row[cell_idx].colspan == 0:
                    cols += 1
                else:  # row[cell_idx].colspan == 1
                    row[cell_idx].colspan = cols
                    cols = 1

    def s_close_tag_row(row, header, ldest, header_ids):
        ldest.append('<tr>')

        # Set tag element of columns
        if header:
            tag_name = 'th'
        else:
            tag_name = 'td'

        # Close tag of columns
        for cell in row:
            if cell.rowspan == 0 or cell.colspan == 0:
                continue

            if cell.rowspan > 1:
                rowspan_attr = f' rowspan="{cell.rowspan}"'
            else:  # cell.rowspan == 1
                rowspan_attr = ''

            if cell.colspan > 1:
                colspan_attr = f' colspan="{cell.colspan}"'
            else:  # cell.colspan == 1
                colspan_attr = ''

            ldest.append(f'<{tag_name}{rowspan_attr}{colspan_attr}>')
            ldest.append(s_process_inline_tags(cell.body, header_ids))
            ldest.append('</{tag_name}>')

        add(ldest, '</tr>')

    table = table
    ldest = ldest
    if len(table):
        s_sum_rowspan(table)
        s_sum_colspan(table)

        if table[0] == 'center':
            add(ldest, "<table class='center'>")
        else:
            add(ldest, '<table>')

        # Empty lists are table separators.
        # Search for the last empty list. All the above rows would be a table header.
        # We should exclude the first element of the table list as it is a text tag
        # that shows if table should be centered or not.
        head = 0
        for idx in range(len(table)-1, 1, -1):
            if empty(table[idx]):
                head = idx
                break
        if head > 0:
            add(ldest, '<thead>')
            for row in table[1 : head-1]:
                if not empty(filter(row, '!empty(v:val)')):
                    s_close_tag_row(row, 1, ldest, header_ids)
            add(ldest, '</thead>')
            add(ldest, '<tbody>')
            for row in table[head+1 :]:
                s_close_tag_row(row, 0, ldest, header_ids)
            add(ldest, '</tbody>')
        else:
            for row in table[1 :]:
                s_close_tag_row(row, 0, ldest, header_ids)
        add(ldest, '</table>')
        table = []
    return table


def s_close_tag_list(lists, ldest):
    while len(lists):
        item = remove(lists, 0)
        insert(ldest, item[0])


def s_close_tag_def_list(deflist, ldest):
    if deflist:
        insert(ldest, '</dl>')
        return 0
    return deflist


def s_process_tag_pre(line, pre):
    lines = []
    processed = 0
    open_match = re.match(r'^(\s*){{{([^\(}}}\)]*)\s*$', line)
    closed_match = re.match(r'^\s*}}}\s*$', line)
    if not pre[0] and open_match:
        block_type = open_match.group()[1].strip()
        indent = len(open_match.group()[0])
        if block_type:
            lines.append(f'<pre {block_type}>')
        else:
            lines.append('<pre>')
        pre = [1, indent]
        processed = 1
    elif pre[0] and closed_match:
        pre = [0, 0]
        lines.append('</pre>')
        processed = 1
    elif pre[0]:
        processed = 1
        lines.append(safe_html_preformatted(line))
    return [processed, lines, pre]


def s_process_tag_math(line, math):
    # math is the list of [is_in_math, indent_of_math]
    lines = []
    math = math
    processed = 0
    if not math[0] and line == 'dupa':  # '^\s*{{\$[^\(}}$\)]*\s*$'
        css_class = matchstr(line, 'dupa')  # składanie regexpów w lodcie /o\ '{{$\zs.*$')
        #FIXME css_class cannot be any string!
        css_class = substitute(css_class, '\s\+$', '', 'g')
        # store the environment name in a global variable in order to close the
        # environment properly
        s_current_math_env = matchstr(css_class, '^%\zs\S\+\ze%')
        if s_current_math_env:
            add(lines, substitute(css_class, '^%\(\S\+\)%', '\\begin{\1}', ''))
        elif css_class:
            add(lines, "\\\[".css_class)
        else:
            add(lines, "\\\[")
        math = [1, len(matchstr(line, 'asd'))] # no weź. '^\s*\ze{{\$'))]
        processed = 1
    elif math[0] and line == 'dupa': # '^\s*}}\$\s*$'
        math = [0, 0]
        if s_current_math_env:
            add(lines, "\\end{" + s_current_math_env + '}')
        else:
            add(lines, "\\\]")
        processed = 1
    elif math[0]:
        processed = 1
        add(lines, substitute(line, '^\s\{' + math[1] + '}', '', ''))
    return [processed, lines, math]


def s_process_tag_precode(line, quote):
    # Process indented precode
    lines = []
    line = line
    quote = quote
    processed = 0

    # Check if start
    ##if line =~# '^\s\{4,}'
    ##    line = substitute(line, '^\s*', '', '')
    ##    if !quote
    ##    # Check if must decrease level
    ##        line = '<pre><code>' . line
    ##        quote = 1
    ##    processed = 1
    ##    call add(lines, line)

    ### Check if end
    ##elseif quote
    ##    call add(lines, '</code></pre>')
    ##    quote = 0

    return [processed, lines, quote]

def s_process_tag_arrow_quote(line, arrow_quote):
    lines = []
    arrow_quote = arrow_quote
    processed = 0
    line = line

    # Check if must increase level
    ##if line =~# '^' . repeat('\s*&gt;', arrow_quote + 1)
    ##    # Increase arrow_quote
    ##    while line =~# '^' . repeat('\s*&gt;', arrow_quote + 1)
    ##        call add(lines, '<blockquote>')
    ##        call add(lines, '<p>')
    ##        arrow_quote .= 1

    ##    # Treat & Add line
    ##    stripped_line = substitute(line, '^\%(\s*&gt;\)\+', '', '')
    ##    if stripped_line =~# '^\s*$'
    ##        call add(lines, '</p>')
    ##        call add(lines, '<p>')
    ##    call add(lines, stripped_line)
    ##    processed = 1

    ### Check if must decrease level
    ##elseif arrow_quote > 0
    ##    while line !~# '^' . repeat('\s*&gt;', arrow_quote - 1)
    ##        call add(lines, '</p>')
    ##        call add(lines, '</blockquote>')
    ##        arrow_quote -= 1
    return [processed, lines, arrow_quote]


def s_process_tag_list(line, lists, lstLeadingSpaces):
    def s_add_checkbox(line, rx_list):
        st_tag = '<li>'
        chk = matchlist(line, rx_list)
        if not empty(chk) and len(chk[1]) > 0:
            ##completion = index(vimwiki#vars#get_wikilocal('listsyms_list'), chk[1])
            ##n = len(vimwiki#vars#get_wikilocal('listsyms_list'))
            if completion == 0:
                st_tag = '<li class="done0">'
            ##elseif completion == -1 && chk[1] == vimwiki#vars#get_global('listsym_rejected')
            ##    st_tag = '<li class="rejected">'
            ##elseif completion > 0 && completion < n
            ##    completion = float2nr(round(completion / (n-1.0) * 3.0 + 0.5 ))
            ##    st_tag = '<li class="done'.completion.'">'
        return [st_tag, '']


    in_list = (len(lists) > 0)
    lstLeadingSpaces = lstLeadingSpaces

    # If it is not list yet then do not process line that starts from *bold*
    # text.
    # XXX necessary? in *bold* text, no space must follow the first *
    if not in_list:
        pos = match(line, '^\s*' + s_rxBold)
        if pos != -1:
            return [0, [], lstLeadingSpaces]

    ##lines = []
    ##processed = 0
    ##checkboxRegExp = '\s*\[\(.\)\]\s*'
    ##maybeCheckboxRegExp = '\%('.checkboxRegExp.'\)\?'

    ##if line =~# '^\s*'.s_bullets.'\s'
    ##    lstSym = matchstr(line, s_bullets)
    ##    lstTagOpen = '<ul>'
    ##    lstTagClose = '</ul>'
    ##    lstRegExp = '^\s*'.s_bullets.'\s'
    ##elseif line =~# '^\s*'.s_numbers.'\s'
    ##    lstSym = matchstr(line, s_numbers)
    ##    lstTagOpen = '<ol>'
    ##    lstTagClose = '</ol>'
    ##    lstRegExp = '^\s*'.s_numbers.'\s'
    ##else
    ##    lstSym = ''
    ##    lstTagOpen = ''
    ##    lstTagClose = ''
    ##    lstRegExp = ''

    ### If we're at the start of a list, figure out how many spaces indented we are so we can later
    ### determine whether we're indented enough to be at the setart of a blockquote
    ##if lstSym !=# ''
    ##    lstLeadingSpaces = strlen(matchstr(line, lstRegExp.maybeCheckboxRegExp))

    ### Jump empty lines
    ##if in_list && line =~# '^$'
    ##    # Just Passing my way, do you mind ?
    ##    [processed, lines, quote] = s_process_tag_precode(line, g:state.quote)
    ##    processed = 1
    ##    return [processed, lines, lstLeadingSpaces]

    ### Can embedded indented code in list (Issue #55)
    ##b_permit = in_list
    ##blockquoteRegExp = '^\s\{' . (lstLeadingSpaces + 2) . ',}[^[:space:]>*-]'
    ##b_match = lstSym ==# '' && line =~# blockquoteRegExp
    ##b_match = b_match || g:state.quote
    ##if b_permit && b_match
    ##    [processed, lines, g:state.quote] = s_process_tag_precode(line, g:state.quote)
    ##    if processed == 1
    ##        return [processed, lines, lstLeadingSpaces]

    ### New switch
    ##if lstSym !=? ''
    ##    # To get proper indent level 'retab' the line -- change all tabs
    ##    # to spaces*tabstop
    ##    line = substitute(line, '\t', repeat(' ', &tabstop), 'g')
    ##    indent = stridx(line, lstSym)

    ##    [st_tag, en_tag] = s_add_checkbox(line, lstRegExp.checkboxRegExp)

    ##    if !in_list
    ##        call add(lists, [lstTagClose, indent])
    ##        call add(lines, lstTagOpen)
    ##    elseif (in_list && indent > lists[-1][1])
    ##        item = remove(lists, -1)
    ##        call add(lines, item[0])

    ##        call add(lists, [lstTagClose, indent])
    ##        call add(lines, lstTagOpen)
    ##    elseif (in_list && indent < lists[-1][1])
    ##        while len(lists) && indent < lists[-1][1]
    ##            item = remove(lists, -1)
    ##            call add(lines, item[0])
    ##    elseif in_list
    ##        item = remove(lists, -1)
    ##        call add(lines, item[0])

    ##    call add(lists, [en_tag, indent])
    ##    call add(lines, st_tag)
    ##    call add(lines, substitute(line, lstRegExp.maybeCheckboxRegExp, '', ''))
    ##    processed = 1

    ##elseif in_list && line =~# '^\s\+\S\+'
    ##    if vimwiki#vars#get_wikilocal('list_ignore_newline')
    ##        call add(lines, line)
    ##    else
    ##        call add(lines, '<br />'.line)
    ##    processed = 1

    ### Close tag
    ##else
    ##    call s_close_tag_list(lists, lines)

    return [processed, lines, lstLeadingSpaces]


def s_process_tag_def_list(line, deflist):
    lines = []
    deflist = deflist
    processed = 0
    matches = matchlist(line, '\(^.*\)::\%(\s\|$\)\(.*\)')
    ##if !deflist && len(matches) > 0
    ##    call add(lines, '<dl>')
    ##    deflist = 1
    ##if deflist && len(matches) > 0
    ##    if matches[1] !=? ''
    ##        call add(lines, '<dt>'.matches[1].'</dt>')
    ##    if matches[2] !=? ''
    ##        call add(lines, '<dd>'.matches[2].'</dd>')
    ##    processed = 1
    ##elseif deflist
    ##    deflist = 0
    ##    call add(lines, '</dl>')
    return [processed, lines, deflist]


def s_process_tag_para(line, para):
    lines = []
    para = para
    processed = 0
    ##if line =~# '^\s\{,3}\S'
    ##    if !para
    ##        call add(lines, '<p>')
    ##        para = 1
    ##    processed = 1
    ##    if vimwiki#vars#get_wikilocal('text_ignore_newline')
    ##        call add(lines, line)
    ##    else
    ##        call add(lines, line.'<br />')
    ##elseif para && line =~# '^\s*$'
    ##    call add(lines, '</p>')
    ##    para = 0
    return [processed, lines, para]


def s_process_tag_h(line, id):
    line = line
    processed = 0
    h_level = 0
    h_text = ''
    h_id = ''

    ##if line =~# vimwiki#vars#get_syntaxlocal('rxHeader')
    ##    h_level = vimwiki#u#count_first_sym(line)
    ##if h_level > 0

    ##    h_text = vimwiki#u#trim(matchstr(line, vimwiki#vars#get_syntaxlocal('rxHeader')))
    ##    h_number = ''
    ##    h_complete_id = ''
    ##    h_id = s_escape_html_attribute(h_text)
    ##    centered = (line =~# '^\s')

    ##    if h_text !=# vimwiki#vars#get_wikilocal('toc_header')

    ##        id[h_level-1] = [h_text, id[h_level-1][1]+1]

    ##        # reset higher level ids
    ##        for level in range(h_level, 5)
    ##            id[level] = ['', 0]

    ##        for l in range(h_level-1)
    ##            h_number .= id[l][1].'.'
    ##            if id[l][0] !=? ''
    ##                h_complete_id .= id[l][0].'-'
    ##        h_number .= id[h_level-1][1]
    ##        h_complete_id .= id[h_level-1][0]

    ##        if vimwiki#vars#get_global('html_header_numbering')
    ##            num = matchstr(h_number,
    ##                        \ '^\(\d.\)\{'.(vimwiki#vars#get_global('html_header_numbering')-1).'}\zs.*')
    ##            if !empty(num)
    ##                num .= vimwiki#vars#get_global('html_header_numbering_sym')
    ##            h_text = num.' '.h_text
    ##        h_complete_id = s_escape_html_attribute(h_complete_id)
    ##        h_part  = '<div id="'.h_complete_id.'">'
    ##        h_part .= '<h'.h_level.' id="'.h_id.'"'
    ##        a_tag = '<a href="#'.h_complete_id.'">'

    ##    else

    ##        h_part = '<div id="'.h_id.'" class="toc">'
    ##        h_part .= '<h'.h_level.' id="'.h_id.'"'
    ##        a_tag = '<a href="#'.h_id.'">'


    ##    if centered
    ##        h_part .= ' class="header justcenter">'
    ##    else
    ##        h_part .= ' class="header">'

    ##    h_text = s_process_inline_tags(h_text, id)

    ##    line = h_part.a_tag.h_text.'</a></h'.h_level.'></div>'

    ##    processed = 1
    return [processed, line]


def s_process_tag_hr(line):
    line = line
    processed = 0
    #if line =~# '^-----*$'
    #    line = '<hr />'
    #    processed = 1
    return [processed, line]


def s_process_tag_table(line, table, header_ids):
    def s_table_empty_cell(value):
        cell = {}

        #if value =~# '^\s*\\/\s*$'
        #    cell.body        = ''
        #    cell.rowspan = 0
        #    cell.colspan = 1
        #elseif value =~# '^\s*&gt;\s*$'
        #    cell.body        = ''
        #    cell.rowspan = 1
        #    cell.colspan = 0
        #elseif value =~# '^\s*$'
        #    cell.body        = '&nbsp;'
        #    cell.rowspan = 1
        #    cell.colspan = 1
        #else
        #    cell.body        = value
        #    cell.rowspan = 1
        #    cell.colspan = 1

        return cell

    def s_table_add_row(table, line):
        #if empty(table)
        #    if line =~# '^\s\+'
        #        row = ['center', []]
        #    else
        #        row = ['normal', []]
        #else
        #    row = [[]]
        return row

    table = table
    lines = []
    processed = 0

    #if vimwiki#tbl#is_separator(line)
    #    call extend(table, s_table_add_row(table, line))
    #    processed = 1
    #elseif vimwiki#tbl#is_table(line)
    #    call extend(table, s_table_add_row(table, line))

    #    processed = 1
    #    # cells = split(line, vimwiki#tbl#cell_splitter(), 1)[1: -2]
    #    cells = vimwiki#tbl#get_cells(line)
    #    call map(cells, 's_table_empty_cell(v:val)')
    #    call extend(table[-1], cells)
    #else
    #    table = s_close_tag_table(table, lines, header_ids)
    return [processed, lines, table]


def parse_line(line, state):
    state.para = state.para
    state.quote = state.quote
    state.arrow_quote = state.arrow_quote
    state.list_leading_spaces = state.list_leading_spaces
    state.pre = state.pre[:]
    state.math = state.math[:]
    state.table = state.table[:]
    state.lists = state.lists[:]
    state.deflist = state.deflist
    state.placeholder = state.placeholder
    state.header_ids = state.header_ids

    res_lines = []
    processed = 0

    if not processed:
        # allows insertion of plain text to the final html conversion
        # for example:
        # %plainhtml <div class="mycustomdiv">
        # inserts the line above to the final html file (without %plainhtml
        # prefix)
        trigger = '%plainhtml'
        if trigger in line:
            lines = []
            processed = 1

            # if something precedes the plain text line,
            # make sure everything gets closed properly
            # before inserting plain text. this ensures that
            # the plain text is not considered as
            # part of the preceding structure
            if processed and len(state.table):
                state.table = s_close_tag_table(state.table, lines,
                                                state.header_ids)
            if processed and state.deflist:
                state.deflist = s_close_tag_def_list(state.deflist, lines)
            if processed and state.quote:
                state.quote = s_close_tag_precode(state.quote, lines)
            if processed and state.arrow_quote:
                state.arrow_quote = s_close_tag_arrow_quote(state.arrow_quote,
                                                            lines)
            if processed and state.para:
                state.para = s_close_tag_para(state.para, lines)

            # remove the trigger prefix
            pp = line.split(trigger)[0]

            lines.append(pp)
            res_lines.extend(lines)

    line = s_safe_html_line(line)

    # pres
    if not processed:
        processed, lines, state.pre = s_process_tag_pre(line, state.pre)
        # pre is just fine to be in the list -- do not close list item here.
        # if processed && len(state.lists)
            # call s_close_tag_list(state.lists, lines)
        ##if !processed
        ##    [processed, lines, state.math] = s_process_tag_math(line, state.math)
        ##if processed && len(state.table)
        ##    state.table = s_close_tag_table(state.table, lines, state.header_ids)
        ##if processed && state.deflist
        ##    state.deflist = s_close_tag_def_list(state.deflist, lines)
        ##if processed && state.quote
        ##    state.quote = s_close_tag_precode(state.quote, lines)
        ##if processed && state.arrow_quote
        ##    state.arrow_quote = s_close_tag_arrow_quote(state.arrow_quote, lines)
        ##if processed && state.para
        ##    state.para = s_close_tag_para(state.para, lines)
        ##call extend(res_lines, lines)

    ##if !processed
    ##    if line =~# vimwiki#vars#get_syntaxlocal('comment_regex')
    ##        processed = 1

    # title -- placeholder
    if not processed:
        if line.startswith('%title '):
            title = line[len('%title '):].strip()
            processed = 1
            state.placeholder = ['title', title]

    # date -- placeholder
    ##if not processed:
    ##    if line =~# '\m^\s*%date\%(\s.*\)\?$'
    ##        processed = 1
    ##        param = matchstr(line, '\m^\s*%date\s\+\zs.*')
    ##        state.placeholder = ['date', param]

    ### html template -- placeholder
    ##if !processed
    ##    if line =~# '\m^\s*%template\%(\s.*\)\?$'
    ##        processed = 1
    ##        param = matchstr(line, '\m^\s*%template\s\+\zs.*')
    ##        state.placeholder = ['template', param]


    ### tables
    ##if !processed
    ##    [processed, lines, state.table] = s_process_tag_table(line, state.table, state.header_ids)
    ##    call extend(res_lines, lines)


    ### lists
    ##if !processed
    ##    [processed, lines, state.list_leading_spaces] = s_process_tag_list(line, state.lists, state.list_leading_spaces)
    ##    if processed && state.quote
    ##        state.quote = s_close_tag_precode(state.quote, lines)
    ##    if processed && state.arrow_quote
    ##        state.arrow_quote = s_close_tag_arrow_quote(state.arrow_quote, lines)
    ##    if processed && state.pre[0]
    ##        state.pre = s_close_tag_pre(state.pre, lines)
    ##    if processed && state.math[0]
    ##        state.math = s_close_tag_math(state.math, lines)
    ##    if processed && len(state.table)
    ##        state.table = s_close_tag_table(state.table, lines, state.header_ids)
    ##    if processed && state.deflist
    ##        state.deflist = s_close_tag_def_list(state.deflist, lines)
    ##    if processed && state.para
    ##        state.para = s_close_tag_para(state.para, lines)

    ##    call map(lines, 's_process_inline_tags(v:val, state.header_ids)')

    ##    call extend(res_lines, lines)


    ### headers
    ##if !processed
    ##    [processed, line] = s_process_tag_h(line, state.header_ids)
    ##    if processed
    ##        call s_close_tag_list(state.lists, res_lines)
    ##        state.table = s_close_tag_table(state.table, res_lines, state.header_ids)
    ##        state.pre = s_close_tag_pre(state.pre, res_lines)
    ##        state.math = s_close_tag_math(state.math, res_lines)
    ##        state.quote = s_close_tag_precode(state.quote || state.arrow_quote, res_lines)
    ##        state.arrow_quote = s_close_tag_arrow_quote(state.arrow_quote, lines)
    ##        state.para = s_close_tag_para(state.para, res_lines)

    ##        call add(res_lines, line)


    ### quotes
    ##if !processed
    ##    [processed, lines, state.quote] = s_process_tag_precode(line, state.quote)
    ##    if processed && len(state.lists)
    ##        call s_close_tag_list(state.lists, lines)
    ##    if processed && state.deflist
    ##        state.deflist = s_close_tag_def_list(state.deflist, lines)
    ##    if processed && state.arrow_quote
    ##        state.quote = s_close_tag_arrow_quote(state.arrow_quote, lines)
    ##    if processed && len(state.table)
    ##        state.table = s_close_tag_table(state.table, lines, state.header_ids)
    ##    if processed && state.pre[0]
    ##        state.pre = s_close_tag_pre(state.pre, lines)
    ##    if processed && state.math[0]
    ##        state.math = s_close_tag_math(state.math, lines)
    ##    if processed && state.para
    ##        state.para = s_close_tag_para(state.para, lines)

    ##    call map(lines, 's_process_inline_tags(v:val, state.header_ids)')

    ##    call extend(res_lines, lines)

    ### arrow quotes
    ##if !processed
    ##    [processed, lines, state.arrow_quote] = s_process_tag_arrow_quote(line, state.arrow_quote)
    ##    if processed && state.quote
    ##        state.quote = s_close_tag_precode(state.quote, lines)
    ##    if processed && len(state.lists)
    ##        call s_close_tag_list(state.lists, lines)
    ##    if processed && state.deflist
    ##        state.deflist = s_close_tag_def_list(state.deflist, lines)
    ##    if processed && len(state.table)
    ##        state.table = s_close_tag_table(state.table, lines, state.header_ids)
    ##    if processed && state.pre[0]
    ##        state.pre = s_close_tag_pre(state.pre, lines)
    ##    if processed && state.math[0]
    ##        state.math = s_close_tag_math(state.math, lines)
    ##    if processed && state.para
    ##        state.para = s_close_tag_para(state.para, lines)

    ##    call map(lines, 's_process_inline_tags(v:val, state.header_ids)')

    ##    call extend(res_lines, lines)


    ### horizontal rules
    ##if !processed
    ##    [processed, line] = s_process_tag_hr(line)
    ##    if processed
    ##        call s_close_tag_list(state.lists, res_lines)
    ##        state.table = s_close_tag_table(state.table, res_lines, state.header_ids)
    ##        state.pre = s_close_tag_pre(state.pre, res_lines)
    ##        state.math = s_close_tag_math(state.math, res_lines)
    ##        call add(res_lines, line)


    ### definition lists
    ##if !processed
    ##    [processed, lines, state.deflist] = s_process_tag_def_list(line, state.deflist)

    ##    call map(lines, 's_process_inline_tags(v:val, state.header_ids)')

    ##    call extend(res_lines, lines)


    #" P
    if not processed:
        processed, lines, state.para = s_process_tag_para(line, state.para)
        if processed and len(state.lists):
            s_close_tag_list(state.lists, lines)
        if processed and (state.quote or state.arrow_quote):
            state.quote = s_close_tag_precode(True, lines)
        if processed and state.arrow_quote:
            state.arrow_quote = s_close_tag_arrow_quote(state.arrow_quote,
                                                        lines)
        if processed and state.pre[0]:
            state.pre = s_close_tag_pre(state.pre, res_lines)
        if processed and state.math[0]:
            state.math = s_close_tag_math(state.math, res_lines)
        if processed and len(state.table):
            state.table = s_close_tag_table(state.table, res_lines,
                                            state.header_ids)

        lines = [s_process_inline_tags(x, state.header_ids) for x in lines]

        res_lines.extend(lines)

    # add the rest
    if not processed:
        res_lines.append(line)

    return [res_lines, state]


def s_shellescape(str):
    result = str
    #" This fix CustomWiki2HTML at root dir problem in Windows
    if result[len(result) - 1] == '\\':
        result = result[:-2]
    return shellescape(result)

#def vimwiki#html#CustomWiki2HTML(root_path, path, wikifile, force):
#    call vimwiki#path#mkdir(path)
#    output = system(vimwiki#vars#get_wikilocal('custom_wiki2html'). ' '.
#            \ force. ' '.
#            \ vimwiki#vars#get_wikilocal('syntax'). ' '.
#            \ strpart(vimwiki#vars#get_wikilocal('ext'), 1). ' '.
#            \ s_shellescape(path). ' '.
#            \ s_shellescape(wikifile). ' '.
#            \ s_shellescape(s_default_CSS_full_name(root_path)). ' '.
#            \ (len(vimwiki#vars#get_wikilocal('template_path')) > 1 ?
#            \           s_shellescape(expand(vimwiki#vars#get_wikilocal('template_path'))) : '-'). ' '.
#            \ (len(vimwiki#vars#get_wikilocal('template_default')) > 0 ?
#            \           vimwiki#vars#get_wikilocal('template_default') : '-'). ' '.
#            \ (len(vimwiki#vars#get_wikilocal('template_ext')) > 0 ?
#            \           vimwiki#vars#get_wikilocal('template_ext') : '-'). ' '.
#            \ (len(vimwiki#vars#get_bufferlocal('subdir')) > 0 ?
#            \           s_shellescape(s_root_path(vimwiki#vars#get_bufferlocal('subdir'))) : '-'). ' '.
#            \ (len(vimwiki#vars#get_wikilocal('custom_wiki2html_args')) > 0 ?
#            \           vimwiki#vars#get_wikilocal('custom_wiki2html_args') : '-'))
#    # Print if non void
#    if output !~? '^\s*$'
#        call vimwiki#u#echo(string(output))

def s_convert_file_to_lines(wiki_contents):
    result = {}

    lsource = wiki_contents.split('\n')

    ldest = []

    # template placeholder
    template_name = ''

    # for table of contents placeholders.
    placeholders = []

    # current state of converter
    state = Generic()
    state.para = 0
    state.quote = 0
    state.arrow_quote = 0
    state.list_leading_spaces = 0
    state.pre = [0, 0]  # [in_pre, indent_pre]
    state.math = [0, 0]  # [in_math, indent_math]
    state.table = []
    state.deflist = 0
    state.lists = []
    state.placeholder = []
    state.header_ids = [['', 0], ['', 0], ['', 0], ['', 0], ['', 0], ['', 0]]
    # [last seen header text in this level, number]

    # Cheat, see cheaters who access me
    glob.state = state

    # prepare constants for s_safe_html_line()
    s_lt_pattern = '<'
    s_gt_pattern = '>'
    # defaults: 'b,i,s,u,sub,sup,kbd,br,hr' - those tags should not be touched
    #if vimwiki#vars#get_global('valid_html_tags') !=? ''
    #    tags = "\|".join([x.strip() for x in
    #                      vimwiki_vars.get_global('valid_html_tags')
    #                      .split(',')])
    #    s_lt_pattern = '\c<\%(/\?\%('.tags.'\)\%(\s\{-1}\S\{-}\)\{-}/\?>\)\@!'
    #    s_gt_pattern = '\c\%(</\?\%('.tags.'\)\%(\s\{-1}\S\{-}\)\{-}/\?\)\@<!>'

    # prepare regexps for lists
    s_bullets = ['-', '*', '#']
    s_numbers = (r'('
                 r'#|\d+\)|'
                 r'\d+\.|'
                 r'[ivxlcdm]+\)|'
                 r'[IVXLCDM]+\)|'
                 r'[a-z]{1,2}\)|'
                 r'[A-Z]{1,2}\)'
                 ')')

    for line in lsource:
        oldquote = state.quote
        lines, state = parse_line(line, state)

        # Hack: There could be a lot of empty strings before
        # process_tag_precode find out `quote` is over. So we should delete
        # them all. Think of the way to refactor it out.
        if oldquote != state.quote:
            s_remove_blank_lines(ldest)

        if state.placeholder:
            if state.placeholder[0].lower() == 'template':
                template_name = state.placeholder[1]
            else:
                placeholders.append([state.placeholder, len(ldest),
                                     len(placeholders)])
            state.placeholder = []

        ldest.extend(lines)

    s_remove_blank_lines(ldest)

    # process end of file
    # close opened tags if any
    lines = []
    s_close_tag_precode(state.quote, lines)
    s_close_tag_arrow_quote(state.arrow_quote, lines)
    s_close_tag_para(state.para, lines)
    s_close_tag_pre(state.pre, lines)
    s_close_tag_math(state.math, lines)
    s_close_tag_list(state.lists, lines)
    s_close_tag_def_list(state.deflist, lines)
    s_close_tag_table(state.table, lines, state.header_ids)
    ldest.extend(lines)

    result['html'] = ldest

    result['template_name'] = template_name

    return result


def s_convert_file(wikifile, output_dir, root):
    html = Html(wikifile, output_dir, root)
    html.convert()
    return html


def vimwiki2html(path_html, wikifile):
    #result = s_convert_file(path_html, vimwiki#path#wikify_path(wikifile))
    if result:
        s_create_default_CSS(path_html)
    return result


def all2html(path_html, force):
    pass

    ## temporarily adjust current_subdir global state variable
    #current_subdir = vimwiki#vars#get_bufferlocal('subdir')
    #current_invsubdir = vimwiki#vars#get_bufferlocal('invsubdir')

    #wikifiles = split(glob(vimwiki#vars#get_wikilocal('path').'**/*'.
    #            \ vimwiki#vars#get_wikilocal('ext')), '\n')
    #for wikifile in wikifiles
    #    wikifile = fnamemodify(wikifile, ':p')

    #    # temporarily adjust 'subdir' and 'invsubdir' state variables
    #    subdir = vimwiki#base#subdir(vimwiki#vars#get_wikilocal('path'), wikifile)
    #    call vimwiki#vars#set_bufferlocal('subdir', subdir)
    #    call vimwiki#vars#set_bufferlocal('invsubdir', vimwiki#base#invsubdir(subdir))

    #    if force || !s_is_html_uptodate(wikifile)
    #        call vimwiki#u#echo('Processing '.wikifile)

    #        call s_convert_file(path_html, wikifile)
    #    else
    #        call vimwiki#u#echo('Skipping '.wikifile)
    ## reset 'subdir' state variable
    #call vimwiki#vars#set_bufferlocal('subdir', current_subdir)
    #call vimwiki#vars#set_bufferlocal('invsubdir', current_invsubdir)

    #created = s_create_default_CSS(path_html)


def s_file_exists(fname):
    return not empty(getftype(expand(fname)))


def s_binary_exists(fname):
    return executable(expand(fname))


def s_get_wikifile_url(wikifile):
    pass
    #return vimwiki#vars#get_wikilocal('path_html') .
        #\ vimwiki#base#subdir(vimwiki#vars#get_wikilocal('path'), wikifile).
        #\ fnamemodify(wikifile, ':t:r').'.html'
