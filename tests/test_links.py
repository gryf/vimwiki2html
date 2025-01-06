import unittest
from unittest import mock

from vw2html.html import VimWiki2Html

"""
  [[This is a link]]
With description: >
  [[This is a link source|Description of the link]]

Wiki files don't need to be in the root directory of your wiki, you can put
them in subdirectories as well: >
  [[projects/Important Project 1]]
To jump from that file back to the index file, use this link: >
  [[../index]]
or: >
  [[/index]]
The latter works because wiki links starting with "/" are considered to be
absolute to the wiki root directory, that is, the link [[/index]] always opens
the file /path/to/your/wiki/index.wiki, no matter in which subdirectory you
are currently in.

If you want to use an absolute path to a wiki page on your local filesystem,
you can prefix the path with // >
  [[//absolute_path]]
For example: >
  [[///tmp/in_root_tmp]]
  [[//~/in_home_dir]]
  [[//$HOME/in_home_dir]]
In a wiki with the default wiki extension, this link: >
  [[///tmp/foo]]
Links to the file: >
  /tmp/foo.wiki

Links to subdirectories inside the wiki directory are also supported. They
end with a "/": >
  [[a subdirectory/|Other files]]
Use |g:vimwiki_dir_link| to control the behavior when opening directories.

Typing wikilinks can be simplified by using Vim's omni completion (see
|compl-omni|) like so: >
  [[ind<C-X><C-O>
which opens up a popup menu with all the wiki files starting with "ind".

When |vimwiki-option-maxhi| equals 1, a distinct highlighting style is used to
identify wikilinks whose targets are not found.

Interwiki~

If you maintain more than one wiki, you can create interwiki links between
them by adding a numbered prefix "wikiX:" in front of a link: >
  [[wiki1:This is a link]]
or: >
  [[wiki1:This is a link source|Description of the link]]

The number behind "wiki" is in the range 0..N-1 and identifies the destination
wiki in |g:vimwiki_list|.

Named interwiki links are also supported in the format "wn.name:link" >
  [[wn.My Name:This is a link]]
or: >
  [[wn.MyWiki:This is a link source|Description of the link]]

See |vimwiki-option-name| to set a per wiki name.

Diary~

The "diary:" scheme is used to link to diary entries: >
  [[diary:2012-03-05]]

Anchors~

A wikilink, interwiki link or diary link can be followed by a '#' and the name
of an anchor.  When opening a link, the cursor jumps to the anchor. >
  [[Todo List#Tomorrow|Tasks for tomorrow]]

To jump inside the current wiki file you can omit the file: >
  [[#Tomorrow]]

See |vimwiki-anchors| for how to set an anchor.

Raw URLs~

Raw URLs are also supported: >
  https://github.com/vimwiki/vimwiki.git
  mailto:habamax@gmail.com
  ftp://vim.org

External files~

The "file:" and "local:" schemes allow you to directly link to arbitrary
resources using absolute or relative paths: >
  [[file:/home/somebody/a/b/c/music.mp3]]
  [[file:C:/Users/somebody/d/e/f/music.mp3]]
  [[file:~/a/b/c/music.mp3]]
  [[file:../assets/data.csv|Important Data]]
  [[local:C:/Users/somebody/d/e/f/music.mp3]]
  [[file:/home/user/documents/|Link to a directory]]

These links are opened with the system command, i.e. !xdg-open (Linux), !open
(Mac), or !start (Windows).  To customize this behavior, see
|VimwikiLinkHandler|.

In Vim, "file:" and "local:" behave the same, i.e. you can use them with both
relative and absolute links. When converted to HTML, however, "file:" links
will become absolute links, while "local:" links become relative to the HTML
output directory. The latter can be useful if you copy your HTML files to
another computer.
To customize the HTML conversion of links, see |VimwikiLinkConverter|.

Transclusion (Wiki-Include) Links~

Links that use "{{" and "}}" delimiters signify content that is to be
included into the HTML output, rather than referenced via hyperlink.

Wiki-include URLs may use any of the supported schemes, may be absolute or
relative, and need not end with an extension.

The primary purpose for wiki-include links is to include images.

Transclude from a local URL: >
  {{file:../../images/vimwiki_logo.png}}
or from a universal URL: >
  {{https://raw.githubusercontent.com/vimwiki/vimwiki/master/doc/splash.png}}

Transclude image with alternate text: >
  {{https://raw.githubusercontent.com/vimwiki/vimwiki/master/doc/splash.png|Vimwiki}}
in HTML: >
  <img src="https://raw.githubusercontent.com/vimwiki/vimwiki/master/doc/splash.png"
  alt="Vimwiki"/>

Transclude image with alternate text and some style: >
  {{https://.../vimwiki_logo.png|cool stuff|style="width:150px;height:120px;"}}
in HTML: >
  <img src="https://raw.githubusercontent.com/vimwiki/vimwiki/master/doc/splash.png"
  alt="cool stuff" style="width:150px; height:120px"/>

Transclude image _without_ alternate text and with a CSS class: >
  {{https://.../vimwiki_logo.png||class="center flow blabla"}}
in HTML: >
  <img src="https://raw.githubusercontent.com/vimwiki/vimwiki/master/doc/splash.png"
  alt="" class="center flow blabla"/>

A trial feature allows you to supply your own handler for wiki-include links.
See |VimwikiWikiIncludeHandler|.

Thumbnail links~
>
Thumbnail links are constructed like this: >
  [[https://someaddr.com/bigpicture.jpg|{{https://someaddr.com/thumbnail.jpg}}]]

in HTML: >
  <a href="https://someaddr.com/ ... /.jpg">
  <img src="https://../thumbnail.jpg /></a>
"""

class TestWikiLink(unittest.TestCase):
    def setUp(self):
        self.converter = VimWiki2Html('/tmp/src/foo.wiki', '/tmp/out',
                                      '/tmp/src')
        # don't read any file
        self.converter.read_wiki_file = mock.MagicMock(return_value=None)

    def test_wiki_link(self):
        src = '[[foo]]'
        exp = '<p>\n<a href="foo.html">foo</a>\n</p>'

        self.converter.wiki_contents = src
        self.converter.convert()
        self.assertEqual(self.converter.html, exp)

    def test_relative_wiki_link(self):
        src = '[[../foo]]'
        exp = '<p>\n<a href="../foo.html">../foo</a>\n</p>'

        self.converter.wiki_contents = src
        self.converter.convert()
        self.assertEqual(self.converter.html, exp)

    def test_relative_wiki_link_root(self):
        src = '[[/foo]]'
        exp = '<p>\n<a href="foo.html">/foo</a>\n</p>'

        self.converter.wiki_contents = src
        self.converter.convert()
        self.assertEqual(self.converter.html, exp)

    def test_absolute_wiki_link(self):
        src = '[[///tmp/foo]]'
        exp = '<p>\n<a href="/tmp/foo.html">///tmp/foo</a>\n</p>'

        self.converter.wiki_contents = src
        self.converter.convert()
        self.assertEqual(self.converter.html, exp)

    def test_absolute_directory_wiki_link(self):
        src = '[[///tmp/foo/]]'
        exp = '<p>\n<a href="/tmp/foo/">///tmp/foo/</a>\n</p>'

        self.converter.wiki_contents = src
        self.converter.convert()
        self.assertEqual(self.converter.html, exp)

    def test_anchors(self):
        src = '[[index#The Diary]]'
        exp = '<p>\n<a href="index#The Diary.html">index#The Diary</a>\n</p>'

        self.converter.wiki_contents = src
        self.converter.convert()
        self.assertEqual(self.converter.html, exp)

    def test_raw_url(self):
        src = 'meh https://meh.us foo'
        exp = '<p>\nmeh <a href="https://meh.us">https://meh.us</a> foo\n</p>'

        self.converter.wiki_contents = src
        self.converter.convert()
        self.assertEqual(self.converter.html, exp)

    def test_multiline_url_not_supported(self):
        src = '[[https://meh.us|desc\nfoo]]'
        exp = ('<p>\n[[<a href="https://meh.us|'
               'desc">https://meh.us|desc</a>\nfoo]]\n</p>')

        self.converter.wiki_contents = src
        self.converter.convert()
        self.assertEqual(self.converter.html, exp)

    def test_external_link(self):
        src = '[[file:$HOME/file.txt]]'
        exp = ('<p>\n<a href="/tmp/src/home/gryf/file.txt">'
               'file:$HOME/file.txt</a>\n</p>')

        self.converter.wiki_contents = src
        self.converter.convert()
        self.assertEqual(self.converter.html, exp)

# TODO: dodać testy dla transclusions, relatywnych linków zewnętrzny, diary
