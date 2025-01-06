============
vimwiki2html
============

VimWiki2HTML is a python implementation for converting `VimWiki`_ default
syntax into html.

Requirements
------------

The only requirement is Python 3.11 or higher.

Installation
------------

TBD

Conversion state
----------------

What's supported:

- Typefaces
  - bold/strong
  - italic/emphasis
  - strikeout/del
  - inline code/monospace
  - superscript
  - subscript
- Headers
- Paragraphs
- Lists
  - Support for unordered lists (``*``, ``-``, ``#``)
  - Support for ordered lists (``1.``, ``2)``)
  - Support for TODO lists (default markings for the items)
- Preformatted text
- Comments
- Horizontal line
- Placeholders
  - Title
  - Date
  - Template
  - Nohtml
  - Plainhtml (this one is undocumented, and allows to add explicit html tags
    which follows that placeholder. It's inline only, which means no span on
    multiple lines, although this placeholder can be repeated several times)
- Links
  - Diary
  - wikilinks (absolute/relative/plain/anchors)
  - external links (local/remote)
  - transclusion links (or, image tags, as no other are supported on vimwiki)
  - raw links (or bare)

What's not:

- Links: interwiki links
- Lists. Note, that html parser from VimWiki produce invalid item lists - no
  closing item tags for both kind of the lists.

  - which start with roman number (i.e. ``i``, ``x``, ``mc``, ``I``, ``X``,
    ``MC``)
  - which start with letters (i.e. ``a``, ``b``, ``z``, ``A``, ``B``, ``Z``)
  - in VimWiki providing indented items and subsequent dedented items like:
    
    .. code:: 
       
       paragraph

         * some list item (which is inednted)
         * another item

       * another list

    will generate two lists, or rather list and a dangling item in a <li> tag.
    This vimwiki2html, parser will generate two lists properly on the same
    level.

  - interpretation of items like:
 
    .. code:: 
       
       paragraph

       * some list item
       * another item

       * last item
   
    will produce two separate lists, not like in VimWiki html parser single
    list with second item having swallowed empty line.

- Tables
- Mathematical formulae (both - inline and block)
- Blockquotes
- Tags
- Explicit html tags (default list is ``b``, ``i``, ``s``, ``u``, ``sub``,
  ``sup``, ``kbd``, ``br`` and ``hr``.
- Escape HTML tags but the one excluded

License
-------

This piece of software is licensed under MIT.


.. _VimWiki: https://github.com/vimwiki/vimwiki
