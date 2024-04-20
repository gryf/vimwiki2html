"""
Vimwiki autoload plugin file
Description: HTML export
Home: https://github.com/vimwiki/vimwiki/
"""


# FIXME: Magics: Why not use the current syntax highlight
# This is due to historical copy paste and laziness of markdown user
# text: *strong*
# default_syntax.rxBold = '\*[^*]\+\*'
s_rxBold = '\%(^\|\s\|[[:punct:]]\)\@<=\*\%([^*`[:space:]][^*`]*[^*`[:space:]]\|[^*`[:space:]]\)\*\%([[:punct:]]\|\s\|$\)\@='

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


def s_root_path(subdir):
    return repeat('../', len(split(a:subdir, '[/\\]')))


def s_syntax_supported():
    return vimwiki#vars#get_wikilocal('syntax') ==? 'default'


def s_remove_blank_lines(lines):
    while !empty(a:lines) && a:lines[-1] =~# '^\s*$'
        call remove(a:lines, -1)


def s_is_web_link(lnk):
    if a:lnk =~# '^\%(https://\|http://\|www.\|ftp://\|file://\|mailto:\)'
        return 1
    return 0


def s_is_img_link(lnk):
    if tolower(a:lnk) =~# '\.\%(png\|jpg\|gif\|jpeg\)$'
        return 1
    return 0


def s_has_abs_path(fname):
    if a:fname =~# '\(^.:\)\|\(^/\)'
        return 1
    return 0


def s_find_autoload_file(name):
    for path in split(&runtimepath, ',')
        fname = path.'/autoload/vimwiki/'.a:name
        match = glob(fname)
        if match !=? ''
            return match
    return ''


def s_default_CSS_full_name(path):
    path = expand(a:path)
    css_full_name = path . vimwiki#vars#get_wikilocal('css_name')
    return css_full_name


def s_create_default_CSS(path):
    css_full_name = s_default_CSS_full_name(a:path)
    if glob(css_full_name) ==? ''
        call vimwiki#path#mkdir(fnamemodify(css_full_name, ':p:h'))
        default_css = s_find_autoload_file('style.css')
        if default_css !=? ''
            lines = readfile(default_css)
            call writefile(lines, css_full_name)
            return 1
    return 0


def s_template_full_name(name):
    name = a:name
    if name ==? ''
        name = vimwiki#vars#get_wikilocal('template_default')

    # Suffix Path by a / is not
    path = vimwiki#vars#get_wikilocal('template_path')
    if strridx(path, '/') +1 != len(path)
        path .= '/'

    ext = vimwiki#vars#get_wikilocal('template_ext')

    fname = expand(path . name . ext)

    if filereadable(fname)
        return fname
    else
        return ''


def s_get_html_template(template):
    # TODO: refactor it!!!
    lines=[]

    if a:template !=? ''
        template_name = s_template_full_name(a:template)
        try
            lines = readfile(template_name)
            return lines
        catch /E484/
            call vimwiki#u#echo('HTML template '.template_name. ' does not exist!')

    default_tpl = s_template_full_name('')

    if default_tpl ==? ''
        default_tpl = s_find_autoload_file('default.tpl')

    lines = readfile(default_tpl)
    return lines


def s_safe_html_preformatted(line):
    line = substitute(a:line,'<','\&lt;', 'g')
    line = substitute(line,'>','\&gt;', 'g')
    return line


def s_escape_html_attribute(string):
    return substitute(a:string, '"', '\&quot;', 'g')


def s_safe_html_line(line):
    # escape & < > when producing HTML text
    # s_lt_pattern, s_gt_pattern depend on g:vimwiki_valid_html_tags
    # and are set in vimwiki#html#Wiki2HTML()
    line = substitute(a:line, '&', '\&amp;', 'g')
    line = substitute(line,s_lt_pattern,'\&lt;', 'g')
    line = substitute(line,s_gt_pattern,'\&gt;', 'g')

    return line


def s_delete_html_files(path):
    htmlfiles = split(glob(a:path.'**/*.html'), '\n')
    for fname in htmlfiles
        # ignore user html files, e.g. search.html,404.html
        if stridx(vimwiki#vars#get_global('user_htmls'), fnamemodify(fname, ':t')) >= 0
            continue

        # delete if there is no corresponding wiki file
        subdir = vimwiki#base#subdir(vimwiki#vars#get_wikilocal('path_html'), fname)
        wikifile = vimwiki#vars#get_wikilocal('path').subdir.
                    \fnamemodify(fname, ':t:r').vimwiki#vars#get_wikilocal('ext')
        if filereadable(wikifile)
            continue

        try
            call delete(fname)
        catch
            call vimwiki#u#error('Cannot delete '.fname)


def s_mid(value, cnt):
    return strpart(a:value, a:cnt, len(a:value) - 2 * a:cnt)


def s_subst_func(line, regexp, func, ...):
    # Substitute text found by regexp with result of
    # func(matched) function.

    pos = 0
    lines = split(a:line, a:regexp, 1)
    res_line = ''
    for line in lines
        res_line = res_line.line
        matched = matchstr(a:line, a:regexp, pos)
        if matched !=? ''
            if a:0
                res_line = res_line.{a:func}(matched, a:1)
            else
                res_line = res_line.{a:func}(matched)
        pos = matchend(a:line, a:regexp, pos)
    return res_line


def s_process_date(placeholders, default_date):
    if !empty(a:placeholders)
        for [placeholder, row, idx] in a:placeholders
            [type, param] = placeholder
            if type ==# 'date' && !empty(param)
                return param
    return a:default_date


def s_process_title(placeholders, default_title):
    if !empty(a:placeholders)
        for [placeholder, row, idx] in a:placeholders
            [type, param] = placeholder
            if type ==# 'title' && !empty(param)
                return param
    return a:default_title


def s_is_html_uptodate(wikifile):
    tpl_time = -1

    tpl_file = s_template_full_name('')
    if tpl_file !=? ''
        tpl_time = getftime(tpl_file)

    wikifile = fnamemodify(a:wikifile, ':p')

    if vimwiki#vars#get_wikilocal('html_filename_parameterization')
        parameterized_wikiname = s_parameterized_wikiname(wikifile)
        htmlfile = expand(vimwiki#vars#get_wikilocal('path_html') .
                    \ vimwiki#vars#get_bufferlocal('subdir') . parameterized_wikiname)
    else
        htmlfile = expand(vimwiki#vars#get_wikilocal('path_html') .
                    \ vimwiki#vars#get_bufferlocal('subdir') . fnamemodify(wikifile, ':t:r').'.html')

    if getftime(wikifile) <= getftime(htmlfile) && tpl_time <= getftime(htmlfile)
        return 1
    return 0

def s_parameterized_wikiname(wikifile):
    initial = fnamemodify(a:wikifile, ':t:r')
    lower_sanitized = tolower(initial)
    substituted = substitute(lower_sanitized, '[^a-z0-9_-]\+','-', 'g')
    substituted = substitute(substituted, '\-\+','-', 'g')
    substituted = substitute(substituted, '^-', '', 'g')
    substituted = substitute(substituted, '-$', '', 'g')
    return substitute(substituted, '\-\+','-', 'g') . '.html'

def s_html_insert_contents(html_lines, content):
    lines = []
    for line in a:html_lines
        if line =~# '%content%'
            parts = split(line, '%content%', 1)
            if empty(parts)
                call extend(lines, a:content)
            else
                for idx in range(len(parts))
                    call add(lines, parts[idx])
                    if idx < len(parts) - 1
                        call extend(lines, a:content)
        else
            call add(lines, line)
    return lines


def s_tag_eqin(value):
    # mathJAX wants \( \) for inline maths
    return '\('.s_mid(a:value, 1).'\)'


def s_tag_em(value):
    return '<em>'.s_mid(a:value, 1).'</em>'


def s_tag_strong(value, header_ids):
    text = s_mid(a:value, 1)
    id = s_escape_html_attribute(text)
    complete_id = ''
    for l in range(6)
        if a:header_ids[l][0] !=? ''
            complete_id .= a:header_ids[l][0].'-'
    if a:header_ids[5][0] ==? ''
        complete_id = complete_id[:-2]
    complete_id .= '-'.id
    return '<span id="'.s_escape_html_attribute(complete_id).'"></span><strong id="'
                \ .id.'">'.text.'</strong>'


def s_tag_tags(value, header_ids):
    complete_id = ''
    for level in range(6)
        if a:header_ids[level][0] !=? ''
            complete_id .= a:header_ids[level][0].'-'
    if a:header_ids[5][0] ==? ''
        complete_id = complete_id[:-2]
    complete_id = s_escape_html_attribute(complete_id)

    result = []
    for tag in split(a:value, ':')
        id = s_escape_html_attribute(tag)
        call add(result, '<span id="'.complete_id.'-'.id.'"></span><span class="tag" id="'
                    \ .id.'">'.tag.'</span>')
    return join(result)


def s_tag_todo(value):
    return '<span class="todo">'.a:value.'</span>'


def s_tag_strike(value):
    return '<del>'.s_mid(a:value, 2).'</del>'


def s_tag_super(value):
    return '<sup><small>'.s_mid(a:value, 1).'</small></sup>'


def s_tag_sub(value):
    return '<sub><small>'.s_mid(a:value, 2).'</small></sub>'


def s_tag_code(value):
    l:retstr = '<code'

    l:str = s_mid(a:value, 1)
    l:match = match(l:str, '^#[a-fA-F0-9]\{6\}$')

    if l:match != -1
        l:r = eval('0x'.l:str[1:2])
        l:g = eval('0x'.l:str[3:4])
        l:b = eval('0x'.l:str[5:6])

        l:fg_color =
                    \ (((0.299 * r + 0.587 * g + 0.114 * b) / 0xFF) > 0.5)
                    \ ? 'black' : 'white'

        l:retstr .=
                    \ " style='background-color:" . l:str .
                    \ ';color:' . l:fg_color . ";'"

    l:retstr .= '>'.s_safe_html_preformatted(l:str).'</code>'
    return l:retstr


def s_incl_match_arg(nn_index):
    #       match n-th ARG within {{URL[|ARG1|ARG2|...]}}
    # *c,d,e),...
    rx = vimwiki#vars#get_global('rxWikiInclPrefix'). vimwiki#vars#get_global('rxWikiInclUrl')
    rx = rx . repeat(vimwiki#vars#get_global('rxWikiInclSeparator') .
                \ vimwiki#vars#get_global('rxWikiInclArg'), a:nn_index-1)
    if a:nn_index > 0
        rx = rx. vimwiki#vars#get_global('rxWikiInclSeparator'). '\zs' .
                    \ vimwiki#vars#get_global('rxWikiInclArg') . '\ze'
    rx = rx . vimwiki#vars#get_global('rxWikiInclArgs') .
                \ vimwiki#vars#get_global('rxWikiInclSuffix')
    return rx


def s_linkify_link(src, descr):
    src_str = ' href="'.s_escape_html_attribute(a:src).'"'
    descr = vimwiki#u#trim(a:descr)
    descr = (descr ==? '' ? a:src : descr)
    descr_str = (descr =~# vimwiki#vars#get_global('rxWikiIncl')
                \ ? s_tag_wikiincl(descr)
                \ : descr)
    return '<a'.src_str.'>'.descr_str.'</a>'


def s_linkify_image(src, descr, verbatim_str):
    src_str = ' src="'.a:src.'"'
    descr_str = (a:descr !=? '' ? ' alt="'.a:descr.'"' : '')
    verbatim_str = (a:verbatim_str !=? '' ? ' '.a:verbatim_str : '')
    return '<img'.src_str.descr_str.verbatim_str.' />'


def s_tag_weblink(value):
    # Weblink Template -> <a href="url">descr</a>
    str = a:value
    url = matchstr(str, vimwiki#vars#get_syntaxlocal('rxWeblinkMatchUrl'))
    descr = matchstr(str, vimwiki#vars#get_syntaxlocal('rxWeblinkMatchDescr'))
    line = s_linkify_link(url, descr)
    return line


def s_tag_wikiincl(value):
    # {{imgurl|arg1|arg2}}      -> ???
    # {{imgurl}}                                -> <img src="imgurl"/>
    # {{imgurl|descr|style="A"}} -> <img src="imgurl" alt="descr" style="A" />
    # {{imgurl|descr|class="B"}} -> <img src="imgurl" alt="descr" class="B" />
    str = a:value
    # custom transclusions
    line = VimwikiWikiIncludeHandler(str)
    # otherwise, assume image transclusion
    if line ==? ''
        url_0 = matchstr(str, vimwiki#vars#get_global('rxWikiInclMatchUrl'))
        descr = matchstr(str, s_incl_match_arg(1))
        verbatim_str = matchstr(str, s_incl_match_arg(2))

        link_infos = vimwiki#base#resolve_link(url_0)

        if link_infos.scheme =~# '\mlocal\|wiki\d\+\|diary'
            url = vimwiki#path#relpath(fnamemodify(s_current_html_file, ':h'), link_infos.filename)
            # strip the .html extension when we have wiki links, so that the user can
            # simply write {{image.png}} to include an image from the wiki directory
            if link_infos.scheme =~# '\mwiki\d\+\|diary'
                url = fnamemodify(url, ':r')
        else
            url = link_infos.filename

        url = escape(url, '#')
        line = s_linkify_image(url, descr, verbatim_str)
    return line


def s_tag_wikilink(value):
    # [[url]]                                       -> <a href="url.html">url</a>
    # [[url|descr]]                         -> <a href="url.html">descr</a>
    # [[url|{{...}}]]                       -> <a href="url.html"> ... </a>
    # [[fileurl.ext|descr]]         -> <a href="fileurl.ext">descr</a>
    # [[dirurl/|descr]]                 -> <a href="dirurl/index.html">descr</a>
    # [[url#a1#a2]]                         -> <a href="url.html#a1-a2">url#a1#a2</a>
    # [[#a1#a2]]                                -> <a href="#a1-a2">#a1#a2</a>
    str = a:value
    url = matchstr(str, vimwiki#vars#get_syntaxlocal('rxWikiLinkMatchUrl'))
    descr = matchstr(str, vimwiki#vars#get_syntaxlocal('rxWikiLinkMatchDescr'))
    descr = vimwiki#u#trim(descr)
    descr = (descr !=? '' ? descr : url)

    line = VimwikiLinkConverter(url, s_current_wiki_file, s_current_html_file)
    if line ==? ''
        link_infos = vimwiki#base#resolve_link(url, s_current_wiki_file)

        if link_infos.scheme ==# 'file'
            # external file links are always absolute
            html_link = link_infos.filename
        elseif link_infos.scheme ==# 'local'
            html_link = vimwiki#path#relpath(fnamemodify(s_current_html_file, ':h'),
                        \ link_infos.filename)
        elseif link_infos.scheme =~# '\mwiki\d\+\|diary'
            # wiki links are always relative to the current file
            html_link = vimwiki#path#relpath(
                        \ fnamemodify(s_current_wiki_file, ':h'),
                        \ fnamemodify(link_infos.filename, ':r'))
            if html_link !~? '\m/$'
                html_link .= '.html'
        else " other schemes, like http, are left untouched
            html_link = link_infos.filename

        if link_infos.anchor !=? ''
            anchor = substitute(link_infos.anchor, '#', '-', 'g')
            html_link .= '#'.anchor
        line = html_link

    line = s_linkify_link(line, descr)
    return line


def s_tag_remove_internal_link(value):
    value = s_mid(a:value, 2)

    line = ''
    if value =~# '|'
        link_parts = split(value, '|', 1)
    else
        link_parts = split(value, '][', 1)

    if len(link_parts) > 1
        if len(link_parts) < 3
            style = ''
        else
            style = link_parts[2]
        line = link_parts[1]
    else
        line = value
    return line


def s_tag_remove_external_link(value):
    value = s_mid(a:value, 1)

    line = ''
    if s_is_web_link(value)
        lnkElements = split(value)
        head = lnkElements[0]
        rest = join(lnkElements[1:])
        if rest ==? ''
            rest = head
        line = rest
    elseif s_is_img_link(value)
        line = '<img src="'.value.'" />'
    else
        # [alskfj sfsf] shouldn't be a link. So return it as it was --
        # enclosed in [...]
        line = '['.value.']'
    return line


def s_make_tag(line, regexp, func, ...):
    # Make tags for a given matched regexp.
    # Exclude preformatted text and href links.
    # FIXME
    patt_splitter = '\(`[^`]\+`\)\|'.
                                        \ '\('.vimwiki#vars#get_syntaxlocal('rxPreStart').'.\+'.
                                        \ vimwiki#vars#get_syntaxlocal('rxPreEnd').'\)\|'.
                                        \ '\(<a href.\{-}</a>\)\|'.
                                        \ '\(<img src.\{-}/>\)\|'.
                                        \ '\(<pre.\{-}</pre>\)\|'.
                                        \ '\('.s_rxEqIn.'\)'

    #FIXME FIXME !!! these can easily occur on the same line!
    #XXX    {{{ }}} ??? obsolete
    if '`[^`]\+`' ==# a:regexp || '{{{.\+}}}' ==# a:regexp ||
                \ s_rxEqIn ==# a:regexp
        res_line = s_subst_func(a:line, a:regexp, a:func)
    else
        pos = 0
        # split line with patt_splitter to have parts of line before and after
        # href links, preformatted text
        # ie:
        # hello world `is just a` simple <a href="link.html">type of</a> prg.
        # result:
        # ['hello world ', ' simple ', 'type of', ' prg']
        lines = split(a:line, patt_splitter, 1)
        res_line = ''
        for line in lines
            if a:0
                res_line = res_line.s_subst_func(line, a:regexp, a:func, a:1)
            else
                res_line = res_line.s_subst_func(line, a:regexp, a:func)
            res_line = res_line.matchstr(a:line, patt_splitter, pos)
            pos = matchend(a:line, patt_splitter, pos)
    return res_line


def s_process_tags_remove_links(line):
    line = a:line
    line = s_make_tag(line, '\[\[.\{-}\]\]', 's_tag_remove_internal_link')
    line = s_make_tag(line, '\[.\{-}\]', 's_tag_remove_external_link')
    return line


def s_process_tags_typefaces(line, header_ids):
    line = a:line
    # Convert line tag by tag
    line = s_make_tag(line, s_rxItalic, 's_tag_em')
    line = s_make_tag(line, s_rxBold, 's_tag_strong', a:header_ids)
    line = s_make_tag(line, vimwiki#vars#get_wikilocal('rx_todo'), 's_tag_todo')
    line = s_make_tag(line, s_rxDelText, 's_tag_strike')
    line = s_make_tag(line, s_rxSuperScript, 's_tag_super')
    line = s_make_tag(line, s_rxSubScript, 's_tag_sub')
    line = s_make_tag(line, s_rxCode, 's_tag_code')
    line = s_make_tag(line, s_rxEqIn, 's_tag_eqin')
    line = s_make_tag(line, vimwiki#vars#get_syntaxlocal('rxTags'), 's_tag_tags', a:header_ids)
    return line


def s_process_tags_links(line):
    line = a:line
    line = s_make_tag(line, vimwiki#vars#get_syntaxlocal('rxWikiLink'), 's_tag_wikilink')
    line = s_make_tag(line, vimwiki#vars#get_global('rxWikiIncl'), 's_tag_wikiincl')
    line = s_make_tag(line, vimwiki#vars#get_syntaxlocal('rxWeblink'), 's_tag_weblink')
    return line


def s_process_inline_tags(line, header_ids):
    line = s_process_tags_links(a:line)
    line = s_process_tags_typefaces(line, a:header_ids)
    return line


def s_close_tag_pre(pre, ldest):
    if a:pre[0]
        call insert(a:ldest, '</pre>')
        return 0
    return a:pre


def s_close_tag_math(math, ldest):
    if a:math[0]
        call insert(a:ldest, "\\\]")
        return 0
    return a:math


def s_close_tag_precode(quote, ldest):
    if a:quote
        call insert(a:ldest, '</pre></code>')
        return 0
    return a:quote

def s_close_tag_arrow_quote(arrow_quote, ldest):
    if a:arrow_quote
        call insert(a:ldest, '</p></blockquote>')
        return 0
    return a:arrow_quote

def s_close_tag_para(para, ldest):
    if a:para
        call insert(a:ldest, '</p>')
        return 0
    return a:para


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
        table = a:table

        # Get max cells
        max_cells = 0
        for row in table[1:]
            n_cells = len(row)
            if n_cells > max_cells
                max_cells = n_cells
            end

        # Sum rowspan
        for cell_idx in range(max_cells)
            rows = 1

            for row_idx in range(len(table)-1, 1, -1)
                if cell_idx >= len(table[row_idx])
                    rows = 1
                    continue

                if table[row_idx][cell_idx].rowspan == 0
                    rows += 1
                else " table[row_idx][cell_idx].rowspan == 1
                    table[row_idx][cell_idx].rowspan = rows
                    rows = 1

    def s_sum_colspan(table):
        for row in a:table[1:]
            cols = 1

            for cell_idx in range(len(row)-1, 0, -1)
                if row[cell_idx].colspan == 0
                    cols += 1
                else "row[cell_idx].colspan == 1
                    row[cell_idx].colspan = cols
                    cols = 1

    def s_close_tag_row(row, header, ldest, header_ids):
        call add(a:ldest, '<tr>')

        # Set tag element of columns
        if a:header
            tag_name = 'th'
        else
            tag_name = 'td'
        end

        # Close tag of columns
        for cell in a:row
            if cell.rowspan == 0 || cell.colspan == 0
                continue

            if cell.rowspan > 1
                rowspan_attr = ' rowspan="' . cell.rowspan . '"'
            else "cell.rowspan == 1
                rowspan_attr = ''
            if cell.colspan > 1
                colspan_attr = ' colspan="' . cell.colspan . '"'
            else "cell.colspan == 1
                colspan_attr = ''

            call add(a:ldest, '<' . tag_name . rowspan_attr . colspan_attr .'>')
            call add(a:ldest, s_process_inline_tags(cell.body, a:header_ids))
            call add(a:ldest, '</'. tag_name . '>')

        call add(a:ldest, '</tr>')

    table = a:table
    ldest = a:ldest
    if len(table)
        call s_sum_rowspan(table)
        call s_sum_colspan(table)

        if table[0] ==# 'center'
            call add(ldest, "<table class='center'>")
        else
            call add(ldest, '<table>')

        # Empty lists are table separators.
        # Search for the last empty list. All the above rows would be a table header.
        # We should exclude the first element of the table list as it is a text tag
        # that shows if table should be centered or not.
        head = 0
        for idx in range(len(table)-1, 1, -1)
            if empty(table[idx])
                head = idx
                break
        if head > 0
            call add(ldest, '<thead>')
            for row in table[1 : head-1]
                if !empty(filter(row, '!empty(v:val)'))
                    call s_close_tag_row(row, 1, ldest, a:header_ids)
            call add(ldest, '</thead>')
            call add(ldest, '<tbody>')
            for row in table[head+1 :]
                call s_close_tag_row(row, 0, ldest, a:header_ids)
            call add(ldest, '</tbody>')
        else
            for row in table[1 :]
                call s_close_tag_row(row, 0, ldest, a:header_ids)
        call add(ldest, '</table>')
        table = []
    return table


def s_close_tag_list(lists, ldest):
    while len(a:lists)
        item = remove(a:lists, 0)
        call insert(a:ldest, item[0])


def s_close_tag_def_list(deflist, ldest):
    if a:deflist
        call insert(a:ldest, '</dl>')
        return 0
    return a:deflist


def s_process_tag_pre(line, pre):
    # pre is the list of [is_in_pre, indent_of_pre]
    #XXX always outputs a single line or empty list!
    lines = []
    pre = a:pre
    processed = 0
    #XXX huh?
    #if !pre[0] && a:line =~# '^\s*{{{[^\(}}}\)]*\s*$'
    if !pre[0] && a:line =~# '^\s*{{{'
        class = matchstr(a:line, '{{{\zs.*$')
        #FIXME class cannot contain arbitrary strings
        class = substitute(class, '\s\+$', '', 'g')
        if class !=? ''
            call add(lines, '<pre '.class.'>')
        else
            call add(lines, '<pre>')
        pre = [1, len(matchstr(a:line, '^\s*\ze{{{'))]
        processed = 1
    elseif pre[0] && a:line =~# '^\s*}}}\s*$'
        pre = [0, 0]
        call add(lines, '</pre>')
        processed = 1
    elseif pre[0]
        processed = 1
        #XXX destroys indent in general!
        #call add(lines, substitute(a:line, '^\s\{'.pre[1].'}', '', ''))
        call add(lines, s_safe_html_preformatted(a:line))
    return [processed, lines, pre]


def s_process_tag_math(line, math):
    # math is the list of [is_in_math, indent_of_math]
    lines = []
    math = a:math
    processed = 0
    if !math[0] && a:line =~# '^\s*{{\$[^\(}}$\)]*\s*$'
        class = matchstr(a:line, '{{$\zs.*$')
        #FIXME class cannot be any string!
        class = substitute(class, '\s\+$', '', 'g')
        # store the environment name in a global variable in order to close the
        # environment properly
        s_current_math_env = matchstr(class, '^%\zs\S\+\ze%')
        if s_current_math_env !=? ''
            call add(lines, substitute(class, '^%\(\S\+\)%', '\\begin{\1}', ''))
        elseif class !=? ''
            call add(lines, "\\\[".class)
        else
            call add(lines, "\\\[")
        math = [1, len(matchstr(a:line, '^\s*\ze{{\$'))]
        processed = 1
    elseif math[0] && a:line =~# '^\s*}}\$\s*$'
        math = [0, 0]
        if s_current_math_env !=? ''
            call add(lines, "\\end{".s_current_math_env.'}')
        else
            call add(lines, "\\\]")
        processed = 1
    elseif math[0]
        processed = 1
        call add(lines, substitute(a:line, '^\s\{'.math[1].'}', '', ''))
    return [processed, lines, math]


def s_process_tag_precode(line, quote):
    # Process indented precode
    lines = []
    line = a:line
    quote = a:quote
    processed = 0

    # Check if start
    if line =~# '^\s\{4,}'
        line = substitute(line, '^\s*', '', '')
        if !quote
        # Check if must decrease level
            line = '<pre><code>' . line
            quote = 1
        processed = 1
        call add(lines, line)

    # Check if end
    elseif quote
        call add(lines, '</code></pre>')
        quote = 0

    return [processed, lines, quote]

def s_process_tag_arrow_quote(line, arrow_quote):
    lines = []
    arrow_quote = a:arrow_quote
    processed = 0
    line = a:line

    # Check if must increase level
    if line =~# '^' . repeat('\s*&gt;', arrow_quote + 1)
        # Increase arrow_quote
        while line =~# '^' . repeat('\s*&gt;', arrow_quote + 1)
            call add(lines, '<blockquote>')
            call add(lines, '<p>')
            arrow_quote .= 1

        # Treat & Add line
        stripped_line = substitute(a:line, '^\%(\s*&gt;\)\+', '', '')
        if stripped_line =~# '^\s*$'
            call add(lines, '</p>')
            call add(lines, '<p>')
        call add(lines, stripped_line)
        processed = 1

    # Check if must decrease level
    elseif arrow_quote > 0
        while line !~# '^' . repeat('\s*&gt;', arrow_quote - 1)
            call add(lines, '</p>')
            call add(lines, '</blockquote>')
            arrow_quote -= 1
    return [processed, lines, arrow_quote]


def s_process_tag_list(line, lists, lstLeadingSpaces):
    def s_add_checkbox(line, rx_list):
        st_tag = '<li>'
        chk = matchlist(a:line, a:rx_list)
        if !empty(chk) && len(chk[1]) > 0
            completion = index(vimwiki#vars#get_wikilocal('listsyms_list'), chk[1])
            n = len(vimwiki#vars#get_wikilocal('listsyms_list'))
            if completion == 0
                st_tag = '<li class="done0">'
            elseif completion == -1 && chk[1] == vimwiki#vars#get_global('listsym_rejected')
                st_tag = '<li class="rejected">'
            elseif completion > 0 && completion < n
                completion = float2nr(round(completion / (n-1.0) * 3.0 + 0.5 ))
                st_tag = '<li class="done'.completion.'">'
        return [st_tag, '']


    in_list = (len(a:lists) > 0)
    lstLeadingSpaces = a:lstLeadingSpaces

    # If it is not list yet then do not process line that starts from *bold*
    # text.
    # XXX necessary? in *bold* text, no space must follow the first *
    if !in_list
        pos = match(a:line, '^\s*' . s_rxBold)
        if pos != -1
            return [0, [], lstLeadingSpaces]

    lines = []
    processed = 0
    checkboxRegExp = '\s*\[\(.\)\]\s*'
    maybeCheckboxRegExp = '\%('.checkboxRegExp.'\)\?'

    if a:line =~# '^\s*'.s_bullets.'\s'
        lstSym = matchstr(a:line, s_bullets)
        lstTagOpen = '<ul>'
        lstTagClose = '</ul>'
        lstRegExp = '^\s*'.s_bullets.'\s'
    elseif a:line =~# '^\s*'.s_numbers.'\s'
        lstSym = matchstr(a:line, s_numbers)
        lstTagOpen = '<ol>'
        lstTagClose = '</ol>'
        lstRegExp = '^\s*'.s_numbers.'\s'
    else
        lstSym = ''
        lstTagOpen = ''
        lstTagClose = ''
        lstRegExp = ''

    # If we're at the start of a list, figure out how many spaces indented we are so we can later
    # determine whether we're indented enough to be at the setart of a blockquote
    if lstSym !=# ''
        lstLeadingSpaces = strlen(matchstr(a:line, lstRegExp.maybeCheckboxRegExp))

    # Jump empty lines
    if in_list && a:line =~# '^$'
        # Just Passing my way, do you mind ?
        [processed, lines, quote] = s_process_tag_precode(a:line, g:state.quote)
        processed = 1
        return [processed, lines, lstLeadingSpaces]

    # Can embedded indented code in list (Issue #55)
    b_permit = in_list
    blockquoteRegExp = '^\s\{' . (lstLeadingSpaces + 2) . ',}[^[:space:]>*-]'
    b_match = lstSym ==# '' && a:line =~# blockquoteRegExp
    b_match = b_match || g:state.quote
    if b_permit && b_match
        [processed, lines, g:state.quote] = s_process_tag_precode(a:line, g:state.quote)
        if processed == 1
            return [processed, lines, lstLeadingSpaces]

    # New switch
    if lstSym !=? ''
        # To get proper indent level 'retab' the line -- change all tabs
        # to spaces*tabstop
        line = substitute(a:line, '\t', repeat(' ', &tabstop), 'g')
        indent = stridx(line, lstSym)

        [st_tag, en_tag] = s_add_checkbox(line, lstRegExp.checkboxRegExp)

        if !in_list
            call add(a:lists, [lstTagClose, indent])
            call add(lines, lstTagOpen)
        elseif (in_list && indent > a:lists[-1][1])
            item = remove(a:lists, -1)
            call add(lines, item[0])

            call add(a:lists, [lstTagClose, indent])
            call add(lines, lstTagOpen)
        elseif (in_list && indent < a:lists[-1][1])
            while len(a:lists) && indent < a:lists[-1][1]
                item = remove(a:lists, -1)
                call add(lines, item[0])
        elseif in_list
            item = remove(a:lists, -1)
            call add(lines, item[0])

        call add(a:lists, [en_tag, indent])
        call add(lines, st_tag)
        call add(lines, substitute(a:line, lstRegExp.maybeCheckboxRegExp, '', ''))
        processed = 1

    elseif in_list && a:line =~# '^\s\+\S\+'
        if vimwiki#vars#get_wikilocal('list_ignore_newline')
            call add(lines, a:line)
        else
            call add(lines, '<br />'.a:line)
        processed = 1

    # Close tag
    else
        call s_close_tag_list(a:lists, lines)

    return [processed, lines, lstLeadingSpaces]


def s_process_tag_def_list(line, deflist):
    lines = []
    deflist = a:deflist
    processed = 0
    matches = matchlist(a:line, '\(^.*\)::\%(\s\|$\)\(.*\)')
    if !deflist && len(matches) > 0
        call add(lines, '<dl>')
        deflist = 1
    if deflist && len(matches) > 0
        if matches[1] !=? ''
            call add(lines, '<dt>'.matches[1].'</dt>')
        if matches[2] !=? ''
            call add(lines, '<dd>'.matches[2].'</dd>')
        processed = 1
    elseif deflist
        deflist = 0
        call add(lines, '</dl>')
    return [processed, lines, deflist]


def s_process_tag_para(line, para):
    lines = []
    para = a:para
    processed = 0
    if a:line =~# '^\s\{,3}\S'
        if !para
            call add(lines, '<p>')
            para = 1
        processed = 1
        if vimwiki#vars#get_wikilocal('text_ignore_newline')
            call add(lines, a:line)
        else
            call add(lines, a:line.'<br />')
    elseif para && a:line =~# '^\s*$'
        call add(lines, '</p>')
        para = 0
    return [processed, lines, para]


def s_process_tag_h(line, id):
    line = a:line
    processed = 0
    h_level = 0
    h_text = ''
    h_id = ''

    if a:line =~# vimwiki#vars#get_syntaxlocal('rxHeader')
        h_level = vimwiki#u#count_first_sym(a:line)
    if h_level > 0

        h_text = vimwiki#u#trim(matchstr(line, vimwiki#vars#get_syntaxlocal('rxHeader')))
        h_number = ''
        h_complete_id = ''
        h_id = s_escape_html_attribute(h_text)
        centered = (a:line =~# '^\s')

        if h_text !=# vimwiki#vars#get_wikilocal('toc_header')

            a:id[h_level-1] = [h_text, a:id[h_level-1][1]+1]

            # reset higher level ids
            for level in range(h_level, 5)
                a:id[level] = ['', 0]

            for l in range(h_level-1)
                h_number .= a:id[l][1].'.'
                if a:id[l][0] !=? ''
                    h_complete_id .= a:id[l][0].'-'
            h_number .= a:id[h_level-1][1]
            h_complete_id .= a:id[h_level-1][0]

            if vimwiki#vars#get_global('html_header_numbering')
                num = matchstr(h_number,
                            \ '^\(\d.\)\{'.(vimwiki#vars#get_global('html_header_numbering')-1).'}\zs.*')
                if !empty(num)
                    num .= vimwiki#vars#get_global('html_header_numbering_sym')
                h_text = num.' '.h_text
            h_complete_id = s_escape_html_attribute(h_complete_id)
            h_part  = '<div id="'.h_complete_id.'">'
            h_part .= '<h'.h_level.' id="'.h_id.'"'
            a_tag = '<a href="#'.h_complete_id.'">'

        else

            h_part = '<div id="'.h_id.'" class="toc">'
            h_part .= '<h'.h_level.' id="'.h_id.'"'
            a_tag = '<a href="#'.h_id.'">'


        if centered
            h_part .= ' class="header justcenter">'
        else
            h_part .= ' class="header">'

        h_text = s_process_inline_tags(h_text, a:id)

        line = h_part.a_tag.h_text.'</a></h'.h_level.'></div>'

        processed = 1
    return [processed, line]


def s_process_tag_hr(line):
    line = a:line
    processed = 0
    if a:line =~# '^-----*$'
        line = '<hr />'
        processed = 1
    return [processed, line]


def s_process_tag_table(line, table, header_ids):
    def s_table_empty_cell(value):
        cell = {}

        if a:value =~# '^\s*\\/\s*$'
            cell.body        = ''
            cell.rowspan = 0
            cell.colspan = 1
        elseif a:value =~# '^\s*&gt;\s*$'
            cell.body        = ''
            cell.rowspan = 1
            cell.colspan = 0
        elseif a:value =~# '^\s*$'
            cell.body        = '&nbsp;'
            cell.rowspan = 1
            cell.colspan = 1
        else
            cell.body        = a:value
            cell.rowspan = 1
            cell.colspan = 1

        return cell

    def s_table_add_row(table, line):
        if empty(a:table)
            if a:line =~# '^\s\+'
                row = ['center', []]
            else
                row = ['normal', []]
        else
            row = [[]]
        return row

    table = a:table
    lines = []
    processed = 0

    if vimwiki#tbl#is_separator(a:line)
        call extend(table, s_table_add_row(a:table, a:line))
        processed = 1
    elseif vimwiki#tbl#is_table(a:line)
        call extend(table, s_table_add_row(a:table, a:line))

        processed = 1
        # cells = split(a:line, vimwiki#tbl#cell_splitter(), 1)[1: -2]
        cells = vimwiki#tbl#get_cells(a:line)
        call map(cells, 's_table_empty_cell(v:val)')
        call extend(table[-1], cells)
    else
        table = s_close_tag_table(table, lines, a:header_ids)
    return [processed, lines, table]


def s_parse_line(line, state):
    state = {}
    state.para = a:state.para
    state.quote = a:state.quote
    state.arrow_quote = a:state.arrow_quote
    state.active_multiline_comment = a:state.active_multiline_comment
    state.list_leading_spaces = a:state.list_leading_spaces
    state.pre = a:state.pre[:]
    state.math = a:state.math[:]
    state.table = a:state.table[:]
    state.lists = a:state.lists[:]
    state.deflist = a:state.deflist
    state.placeholder = a:state.placeholder
    state.header_ids = a:state.header_ids

    res_lines = []
    processed = 0
    line = a:line

    # Handle multiline comments, keeping in mind that they can mutate the
    # current line while not marking as processed in the scenario where some
    # text remains that needs to go through additional processing
    if !processed
        mc_format = vimwiki#vars#get_syntaxlocal('multiline_comment_format')
        mc_start = mc_format.pre_mark
        mc_end = mc_format.post_mark

        # If either start or end is empty, we want to skip multiline handling
        if !empty(mc_start) && !empty(mc_end)
            # If we have an active multiline comment, we prepend the start of the
            # multiline to our current line to make searching easier, knowing that
            # it will be removed using substitute in all scenarios
            if state.active_multiline_comment
                line = mc_start.line

            # Remove all instances of multiline comment pairs (start + end), using
            # a lazy match so that we stop at the first ending multiline comment
            # rather than potentially absorbing multiple
            line = substitute(line, mc_start.'.\{-\}'.mc_end, '', 'g')

            # Check for a dangling multiline comment (comprised only of start) and
            # remove all characters beyond it, also indicating that we are dangling
            mc_start_pos = match(line, mc_start)
            if mc_start_pos >= 0
                # NOTE: mc_start_pos is the byte offset, so should be fine with strpart
                line = strpart(line, 0, mc_start_pos)

            # If we had a dangling multiline comment, we want to flag as such
            state.active_multiline_comment = mc_start_pos >= 0

    if !processed
        # allows insertion of plain text to the final html conversion
        # for example:
        # %plainhtml <div class="mycustomdiv">
        # inserts the line above to the final html file (without %plainhtml prefix)
        trigger = '%plainhtml'
        if line =~# '^\s*' . trigger
            lines = []
            processed = 1

            # if something precedes the plain text line,
            # make sure everything gets closed properly
            # before inserting plain text. this ensures that
            # the plain text is not considered as
            # part of the preceding structure
            if processed && len(state.table)
                state.table = s_close_tag_table(state.table, lines, state.header_ids)
            if processed && state.deflist
                state.deflist = s_close_tag_def_list(state.deflist, lines)
            if processed && state.quote
                state.quote = s_close_tag_precode(state.quote, lines)
            if processed && state.arrow_quote
                state.arrow_quote = s_close_tag_arrow_quote(state.arrow_quote, lines)
            if processed && state.para
                state.para = s_close_tag_para(state.para, lines)

            # remove the trigger prefix
            pp = split(line, trigger)[0]

            call add(lines, pp)
            call extend(res_lines, lines)

    line = s_safe_html_line(line)

    # pres
    if !processed
        [processed, lines, state.pre] = s_process_tag_pre(line, state.pre)
        # pre is just fine to be in the list -- do not close list item here.
        # if processed && len(state.lists)
            # call s_close_tag_list(state.lists, lines)
        if !processed
            [processed, lines, state.math] = s_process_tag_math(line, state.math)
        if processed && len(state.table)
            state.table = s_close_tag_table(state.table, lines, state.header_ids)
        if processed && state.deflist
            state.deflist = s_close_tag_def_list(state.deflist, lines)
        if processed && state.quote
            state.quote = s_close_tag_precode(state.quote, lines)
        if processed && state.arrow_quote
            state.arrow_quote = s_close_tag_arrow_quote(state.arrow_quote, lines)
        if processed && state.para
            state.para = s_close_tag_para(state.para, lines)
        call extend(res_lines, lines)

    if !processed
        if line =~# vimwiki#vars#get_syntaxlocal('comment_regex')
            processed = 1

    # nohtml -- placeholder
    if !processed
        if line =~# '\m^\s*%nohtml\s*$'
            processed = 1
            state.placeholder = ['nohtml']

    # title -- placeholder
    if !processed
        if line =~# '\m^\s*%title\%(\s.*\)\?$'
            processed = 1
            param = matchstr(line, '\m^\s*%title\s\+\zs.*')
            state.placeholder = ['title', param]

    # date -- placeholder
    if !processed
        if line =~# '\m^\s*%date\%(\s.*\)\?$'
            processed = 1
            param = matchstr(line, '\m^\s*%date\s\+\zs.*')
            state.placeholder = ['date', param]

    # html template -- placeholder
    if !processed
        if line =~# '\m^\s*%template\%(\s.*\)\?$'
            processed = 1
            param = matchstr(line, '\m^\s*%template\s\+\zs.*')
            state.placeholder = ['template', param]


    # tables
    if !processed
        [processed, lines, state.table] = s_process_tag_table(line, state.table, state.header_ids)
        call extend(res_lines, lines)


    # lists
    if !processed
        [processed, lines, state.list_leading_spaces] = s_process_tag_list(line, state.lists, state.list_leading_spaces)
        if processed && state.quote
            state.quote = s_close_tag_precode(state.quote, lines)
        if processed && state.arrow_quote
            state.arrow_quote = s_close_tag_arrow_quote(state.arrow_quote, lines)
        if processed && state.pre[0]
            state.pre = s_close_tag_pre(state.pre, lines)
        if processed && state.math[0]
            state.math = s_close_tag_math(state.math, lines)
        if processed && len(state.table)
            state.table = s_close_tag_table(state.table, lines, state.header_ids)
        if processed && state.deflist
            state.deflist = s_close_tag_def_list(state.deflist, lines)
        if processed && state.para
            state.para = s_close_tag_para(state.para, lines)

        call map(lines, 's_process_inline_tags(v:val, state.header_ids)')

        call extend(res_lines, lines)


    # headers
    if !processed
        [processed, line] = s_process_tag_h(line, state.header_ids)
        if processed
            call s_close_tag_list(state.lists, res_lines)
            state.table = s_close_tag_table(state.table, res_lines, state.header_ids)
            state.pre = s_close_tag_pre(state.pre, res_lines)
            state.math = s_close_tag_math(state.math, res_lines)
            state.quote = s_close_tag_precode(state.quote || state.arrow_quote, res_lines)
            state.arrow_quote = s_close_tag_arrow_quote(state.arrow_quote, lines)
            state.para = s_close_tag_para(state.para, res_lines)

            call add(res_lines, line)


    # quotes
    if !processed
        [processed, lines, state.quote] = s_process_tag_precode(line, state.quote)
        if processed && len(state.lists)
            call s_close_tag_list(state.lists, lines)
        if processed && state.deflist
            state.deflist = s_close_tag_def_list(state.deflist, lines)
        if processed && state.arrow_quote
            state.quote = s_close_tag_arrow_quote(state.arrow_quote, lines)
        if processed && len(state.table)
            state.table = s_close_tag_table(state.table, lines, state.header_ids)
        if processed && state.pre[0]
            state.pre = s_close_tag_pre(state.pre, lines)
        if processed && state.math[0]
            state.math = s_close_tag_math(state.math, lines)
        if processed && state.para
            state.para = s_close_tag_para(state.para, lines)

        call map(lines, 's_process_inline_tags(v:val, state.header_ids)')

        call extend(res_lines, lines)

    # arrow quotes
    if !processed
        [processed, lines, state.arrow_quote] = s_process_tag_arrow_quote(line, state.arrow_quote)
        if processed && state.quote
            state.quote = s_close_tag_precode(state.quote, lines)
        if processed && len(state.lists)
            call s_close_tag_list(state.lists, lines)
        if processed && state.deflist
            state.deflist = s_close_tag_def_list(state.deflist, lines)
        if processed && len(state.table)
            state.table = s_close_tag_table(state.table, lines, state.header_ids)
        if processed && state.pre[0]
            state.pre = s_close_tag_pre(state.pre, lines)
        if processed && state.math[0]
            state.math = s_close_tag_math(state.math, lines)
        if processed && state.para
            state.para = s_close_tag_para(state.para, lines)

        call map(lines, 's_process_inline_tags(v:val, state.header_ids)')

        call extend(res_lines, lines)


    # horizontal rules
    if !processed
        [processed, line] = s_process_tag_hr(line)
        if processed
            call s_close_tag_list(state.lists, res_lines)
            state.table = s_close_tag_table(state.table, res_lines, state.header_ids)
            state.pre = s_close_tag_pre(state.pre, res_lines)
            state.math = s_close_tag_math(state.math, res_lines)
            call add(res_lines, line)


    # definition lists
    if !processed
        [processed, lines, state.deflist] = s_process_tag_def_list(line, state.deflist)

        call map(lines, 's_process_inline_tags(v:val, state.header_ids)')

        call extend(res_lines, lines)


    #" P
    if !processed
        [processed, lines, state.para] = s_process_tag_para(line, state.para)
        if processed && len(state.lists)
            call s_close_tag_list(state.lists, lines)
        if processed && (state.quote || state.arrow_quote)
            state.quote = s_close_tag_precode(state.quote || state.arrow_quote, lines)
        if processed && state.arrow_quote
            state.arrow_quote = s_close_tag_arrow_quote(state.arrow_quote, lines)
        if processed && state.pre[0]
            state.pre = s_close_tag_pre(state.pre, res_lines)
        if processed && state.math[0]
            state.math = s_close_tag_math(state.math, res_lines)
        if processed && len(state.table)
            state.table = s_close_tag_table(state.table, res_lines, state.header_ids)

        call map(lines, 's_process_inline_tags(v:val, state.header_ids)')

        call extend(res_lines, lines)


    #" add the rest
    if !processed
        call add(res_lines, line)

    return [res_lines, state]


def s_use_custom_wiki2html():
    custom_wiki2html = vimwiki#vars#get_wikilocal('custom_wiki2html')
    return !empty(custom_wiki2html) &&
                \ (s_file_exists(custom_wiki2html) || s_binary_exists(custom_wiki2html))

def s_shellescape(str):
    result = a:str
    #" This fix CustomWiki2HTML at root dir problem in Windows
    if result[len(result) - 1] ==# '\'
        result = result[:-2]
    return shellescape(result)

def vimwiki#html#CustomWiki2HTML(root_path, path, wikifile, force):
    call vimwiki#path#mkdir(a:path)
    output = system(vimwiki#vars#get_wikilocal('custom_wiki2html'). ' '.
            \ a:force. ' '.
            \ vimwiki#vars#get_wikilocal('syntax'). ' '.
            \ strpart(vimwiki#vars#get_wikilocal('ext'), 1). ' '.
            \ s_shellescape(a:path). ' '.
            \ s_shellescape(a:wikifile). ' '.
            \ s_shellescape(s_default_CSS_full_name(a:root_path)). ' '.
            \ (len(vimwiki#vars#get_wikilocal('template_path')) > 1 ?
            \           s_shellescape(expand(vimwiki#vars#get_wikilocal('template_path'))) : '-'). ' '.
            \ (len(vimwiki#vars#get_wikilocal('template_default')) > 0 ?
            \           vimwiki#vars#get_wikilocal('template_default') : '-'). ' '.
            \ (len(vimwiki#vars#get_wikilocal('template_ext')) > 0 ?
            \           vimwiki#vars#get_wikilocal('template_ext') : '-'). ' '.
            \ (len(vimwiki#vars#get_bufferlocal('subdir')) > 0 ?
            \           s_shellescape(s_root_path(vimwiki#vars#get_bufferlocal('subdir'))) : '-'). ' '.
            \ (len(vimwiki#vars#get_wikilocal('custom_wiki2html_args')) > 0 ?
            \           vimwiki#vars#get_wikilocal('custom_wiki2html_args') : '-'))
    # Print if non void
    if output !~? '^\s*$'
        call vimwiki#u#echo(string(output))

def s_convert_file_to_lines(wikifile, current_html_file):
    result = {}

    # the currently processed file name is needed when processing links
    # yeah yeah, shame on me for using (quasi-) global variables
    s_current_wiki_file = a:wikifile
    s_current_html_file = a:current_html_file

    lsource = readfile(a:wikifile)
    ldest = []

    # nohtml placeholder -- to skip html generation.
    nohtml = 0

    # template placeholder
    template_name = ''

    # for table of contents placeholders.
    placeholders = []

    # current state of converter
    state = {}
    state.para = 0
    state.quote = 0
    state.arrow_quote = 0
    state.active_multiline_comment = 0
    state.list_leading_spaces = 0
    state.pre = [0, 0] " [in_pre, indent_pre]
    state.math = [0, 0] " [in_math, indent_math]
    state.table = []
    state.deflist = 0
    state.lists = []
    state.placeholder = []
    state.header_ids = [['', 0], ['', 0], ['', 0], ['', 0], ['', 0], ['', 0]]
             # [last seen header text in this level, number]

    # Cheat, see cheaters who access me
    g:state = state

    # prepare constants for s_safe_html_line()
    s_lt_pattern = '<'
    s_gt_pattern = '>'
    if vimwiki#vars#get_global('valid_html_tags') !=? ''
        tags = join(split(vimwiki#vars#get_global('valid_html_tags'), '\s*,\s*'), '\|')
        s_lt_pattern = '\c<\%(/\?\%('.tags.'\)\%(\s\{-1}\S\{-}\)\{-}/\?>\)\@!'
        s_gt_pattern = '\c\%(</\?\%('.tags.'\)\%(\s\{-1}\S\{-}\)\{-}/\?\)\@<!>'

    # prepare regexps for lists
    s_bullets = vimwiki#vars#get_wikilocal('rx_bullet_char')
    s_numbers = '\C\%(#\|\d\+)\|\d\+\.\|[ivxlcdm]\+)\|[IVXLCDM]\+)\|\l\{1,2})\|\u\{1,2})\)'

    for line in lsource
        oldquote = state.quote
        [lines, state] = s_parse_line(line, state)

        # Hack: There could be a lot of empty strings before s_process_tag_precode
        # find out `quote` is over. So we should delete them all. Think of the way
        # to refactor it out.
        if oldquote != state.quote
            call s_remove_blank_lines(ldest)

        if !empty(state.placeholder)
            if state.placeholder[0] ==# 'nohtml'
                nohtml = 1
                break
            elseif state.placeholder[0] ==# 'template'
                template_name = state.placeholder[1]
            else
                call add(placeholders, [state.placeholder, len(ldest), len(placeholders)])
            state.placeholder = []

        call extend(ldest, lines)


    result['nohtml'] = nohtml
    if nohtml
        call vimwiki#u#echo("\r".'%nohtml placeholder found', '', 'n')
        return result

    call s_remove_blank_lines(ldest)

    # process end of file
    # close opened tags if any
    lines = []
    call s_close_tag_precode(state.quote, lines)
    call s_close_tag_arrow_quote(state.arrow_quote, lines)
    call s_close_tag_para(state.para, lines)
    call s_close_tag_pre(state.pre, lines)
    call s_close_tag_math(state.math, lines)
    call s_close_tag_list(state.lists, lines)
    call s_close_tag_def_list(state.deflist, lines)
    call s_close_tag_table(state.table, lines, state.header_ids)
    call extend(ldest, lines)

    result['html'] = ldest

    result['template_name'] = template_name
    result['title'] = s_process_title(placeholders, fnamemodify(a:wikifile, ':t:r'))
    result['date'] = s_process_date(placeholders, strftime(vimwiki#vars#get_wikilocal('template_date_format')))
    result['wiki_path'] = strpart(s_current_wiki_file, strlen(vimwiki#vars#get_wikilocal('path')))

    return result

def s_convert_file_to_lines_template(wikifile, current_html_file):
    converted = s_convert_file_to_lines(a:wikifile, a:current_html_file)
    if converted['nohtml'] == 1
        return []
    html_lines = s_get_html_template(converted['template_name'])

    # processing template variables (refactor to a function)
    call map(html_lines, 'substitute(v:val, "%title%", converted["title"], "g")')
    call map(html_lines, 'substitute(v:val, "%date%", converted["date"], "g")')
    call map(html_lines, 'substitute(v:val, "%root_path%", "'.
                \ s_root_path(vimwiki#vars#get_bufferlocal('subdir')) .'", "g")')
    call map(html_lines, 'substitute(v:val, "%wiki_path%", converted["wiki_path"], "g")')

    css_name = expand(vimwiki#vars#get_wikilocal('css_name'))
    css_name = substitute(css_name, '\', '/', 'g')
    call map(html_lines, 'substitute(v:val, "%css%", css_name, "g")')

    rss_name = expand(vimwiki#vars#get_wikilocal('rss_name'))
    rss_name = substitute(rss_name, '\', '/', 'g')
    call map(html_lines, 'substitute(v:val, "%rss%", rss_name, "g")')

    enc = &fileencoding
    if enc ==? ''
        enc = &encoding
    call map(html_lines, 'substitute(v:val, "%encoding%", enc, "g")')

    html_lines = s_html_insert_contents(html_lines, converted['html']) " %contents%

    return html_lines

def s_convert_file(path_html, wikifile):
    done = 0
    root_path_html = a:path_html
    wikifile = fnamemodify(a:wikifile, ':p')
    path_html = expand(a:path_html).vimwiki#vars#get_bufferlocal('subdir')
    htmlfile = fnamemodify(wikifile, ':t:r').'.html'

    if s_use_custom_wiki2html()
        force = 1
        call vimwiki#html#CustomWiki2HTML(root_path_html, path_html, wikifile, force)
        done = 1
        if vimwiki#vars#get_wikilocal('html_filename_parameterization')
            return path_html . s_parameterized_wikiname(htmlfile)
        else
            return path_html.htmlfile

    if s_syntax_supported() && done == 0
        html_lines = s_convert_file_to_lines_template(wikifile, path_html . htmlfile)
        if html_lines == []
            return ''
        call vimwiki#path#mkdir(path_html)

        if g:vimwiki_global_vars['listing_hl'] > 0 && has('unix')
            i = 0
            while i < len(html_lines)
                if html_lines[i] =~# '^<pre .*type=.\+>'
                    type = split(split(split(html_lines[i], 'type=')[1], '>')[0], '\s\+')[0]
                    attr = split(split(html_lines[i], '<pre ')[0], '>')[0]
                    start = i + 1
                    cur = start

                    while html_lines[cur] !~# '^<\/pre>'
                        cur += 1

                    tmp = ('tmp'. split(system('mktemp -p . --suffix=.' . type, 'silent'), 'tmp')[-1])[:-2]
                    call system('echo ' . shellescape(join(html_lines[start : cur - 1], "\n")) . ' > ' . tmp)
                    call system(g:vimwiki_global_vars['listing_hl_command'] . ' ' . tmp  . ' > ' . tmp . '.html')
                    html_out = system('cat ' . tmp . '.html')
                    call system('rm ' . tmp . ' ' . tmp . '.html')
                    i = cur
                    html_lines = html_lines[0 : start - 1] + split(html_out, "\n") + html_lines[cur : ]
                i += 1

        call writefile(html_lines, path_html.htmlfile)
        return path_html . htmlfile

    call vimwiki#u#error('Conversion to HTML is not supported for this syntax')
    return ''


def vimwiki#html#Wiki2HTML(path_html, wikifile):
    result = s_convert_file(a:path_html, vimwiki#path#wikify_path(a:wikifile))
    if result !=? ''
        call s_create_default_CSS(a:path_html)
    return result


def vimwiki#html#WikiAll2HTML(path_html, force):
    if !s_syntax_supported() && !s_use_custom_wiki2html()
        call vimwiki#u#error('Conversion to HTML is not supported for this syntax')
        return

    call vimwiki#u#echo('Saving Vimwiki files ...')
    save_eventignore = &eventignore
    &eventignore = 'all'
    try
        wall
    catch
        # just ignore errors
    &eventignore = save_eventignore

    path_html = expand(a:path_html)
    call vimwiki#path#mkdir(path_html)

    if !vimwiki#vars#get_wikilocal('html_filename_parameterization')
        call vimwiki#u#echo('Deleting non-wiki html files ...')
        call s_delete_html_files(path_html)

    setting_more = &more
    call vimwiki#u#echo('Converting wiki to html files ...')
    setlocal nomore

    # temporarily adjust current_subdir global state variable
    current_subdir = vimwiki#vars#get_bufferlocal('subdir')
    current_invsubdir = vimwiki#vars#get_bufferlocal('invsubdir')

    wikifiles = split(glob(vimwiki#vars#get_wikilocal('path').'**/*'.
                \ vimwiki#vars#get_wikilocal('ext')), '\n')
    for wikifile in wikifiles
        wikifile = fnamemodify(wikifile, ':p')

        # temporarily adjust 'subdir' and 'invsubdir' state variables
        subdir = vimwiki#base#subdir(vimwiki#vars#get_wikilocal('path'), wikifile)
        call vimwiki#vars#set_bufferlocal('subdir', subdir)
        call vimwiki#vars#set_bufferlocal('invsubdir', vimwiki#base#invsubdir(subdir))

        if a:force || !s_is_html_uptodate(wikifile)
            call vimwiki#u#echo('Processing '.wikifile)

            call s_convert_file(path_html, wikifile)
        else
            call vimwiki#u#echo('Skipping '.wikifile)
    # reset 'subdir' state variable
    call vimwiki#vars#set_bufferlocal('subdir', current_subdir)
    call vimwiki#vars#set_bufferlocal('invsubdir', current_invsubdir)

    created = s_create_default_CSS(path_html)
    if created
        call vimwiki#u#echo('Default style.css has been created')
    call vimwiki#u#echo('HTML exported to '.path_html)
    call vimwiki#u#echo('Done!')

    &more = setting_more


def s_file_exists(fname):
    return !empty(getftype(expand(a:fname)))


def s_binary_exists(fname):
    return executable(expand(a:fname))


def s_get_wikifile_url(wikifile):
    return vimwiki#vars#get_wikilocal('path_html') .
        \ vimwiki#base#subdir(vimwiki#vars#get_wikilocal('path'), a:wikifile).
        \ fnamemodify(a:wikifile, ':t:r').'.html'


def vimwiki#html#PasteUrl(wikifile):
    execute 'r !echo file://'.s_get_wikifile_url(a:wikifile)


def vimwiki#html#CatUrl(wikifile):
    execute '!echo file://'.s_get_wikifile_url(a:wikifile)


def s_rss_header():
    title = vimwiki#vars#get_wikilocal('diary_header')
    rss_url = vimwiki#vars#get_wikilocal('base_url') . vimwiki#vars#get_wikilocal('rss_name')
    link = vimwiki#vars#get_wikilocal('base_url')
                \ . vimwiki#vars#get_wikilocal('diary_rel_path')
                \ . vimwiki#vars#get_wikilocal('diary_index') . '.html'
    description = title
    pubdate = strftime('%a, %d %b %Y %T %z')
    header = [
                \ '<?xml version="1.0" encoding="UTF-8" ?>',
                \ '<rss version="2.0" xmlns:atom="http://www.w3.org/2005/Atom">',
                \ '<channel>',
                \ ' <title>' . title . '</title>',
                \ ' <link>' . link . '</link>',
                \ ' <description>' . description . '</description>',
                \ ' <pubDate>' . pubdate . '</pubDate>',
                \ ' <atom:link href="' . rss_url . '" rel="self" type="application/rss+xml" />'
                \ ]
    return header

def s_rss_footer():
    footer = ['</channel>', '</rss>']
    return footer

def s_rss_item(path, title):
    diary_rel_path = vimwiki#vars#get_wikilocal('diary_rel_path')
    full_path = vimwiki#vars#get_wikilocal('path')
                \ . diary_rel_path . a:path . vimwiki#vars#get_wikilocal('ext')
    fname_base = fnamemodify(a:path, ':t:r')
    htmlfile = fname_base . '.html'

    converted = s_convert_file_to_lines(full_path, htmlfile)
    if converted['nohtml'] == 1
        return []

    link = vimwiki#vars#get_wikilocal('base_url')
                \ . diary_rel_path
                \ . fname_base . '.html'
    pubdate = strftime('%a, %d %b %Y %T %z', getftime(full_path))

    item_pre = [' <item>',
                \ '  <title>' . a:title . '</title>',
                \ '  <link>' . link . '</link>',
                \ '  <guid isPermaLink="false">' . fname_base . '</guid>',
                \ '  <description><![CDATA[']
    item_post = [']]></description>',
                \ '  <pubDate>' . pubdate . '</pubDate>',
                \ ' </item>'
                \]
    return item_pre + converted['html'] + item_post

def s_generate_rss(path):
    rss_path = a:path . vimwiki#vars#get_wikilocal('rss_name')
    max_items = vimwiki#vars#get_wikilocal('rss_max_items')

    rss_lines = []
    call extend(rss_lines, s_rss_header())

    captions = vimwiki#diary#diary_file_captions()
    i = 0
    for diary in vimwiki#diary#diary_sort(keys(captions))
        if i >= max_items
            break
        title = captions[diary]['top']
        if title ==? ''
            title = diary
        call extend(rss_lines, s_rss_item(diary, title))
        i += 1

    call extend(rss_lines, s_rss_footer())
    call writefile(rss_lines, rss_path)

def vimwiki#html#diary_rss():
    call vimwiki#u#echo('Saving RSS feed ...')
    path_html = expand(vimwiki#vars#get_wikilocal('path_html'))
    call vimwiki#path#mkdir(path_html)
    call s_generate_rss(path_html)
