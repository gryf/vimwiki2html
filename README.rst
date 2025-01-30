============
vimwiki2html
============

VimWiki2HTML is a python implementation for converting `VimWiki`_ default
syntax into html.

Motivation
----------

I wanted to have some more control over how HTML files are generated and how
asset files are treated. Also in some really large files, I've noticed
``Vimwiki2HTML`` can be really slow. Currently I have around 750 wiki files.
Some of them are pretty small, yet some of them are complicated, full of
tables, code blocks and lists. Below is a simple benchmark I've done to convert
whole wiki collection into html using vimwiki ``VimwikiAll2HTML`` command:

.. code:: console

   $ time vim -s s

   real	2m33,027s
   user	2m17,865s
   sys	0m6,750s
   $ cat s
   :VimwikiIndex
   :VimwikiAll2HTML
   :q!

Two and a half minutes.

Let see how Python implementation performs. Currently it have most of features
I need (see the functionality coverage below):

.. code:: console

   $ time vw2html
   html.py:703: WARNING: Image "p.png" have no schema
   html.py:720: WARNING: File `p.png' doesn't exists, ignoring
   html.py:715: WARNING: File `../../images/vimwiki_logo.png' pointing outside of wiki root, ignoring
   html.py:703: WARNING: Image "images/allegro/nz9_t.jpg" have no schema
   html.py:703: WARNING: Image "Nerd Font" have no schema
   html.py:720: WARNING: File `Nerd Font' doesn't exists, ignoring

   real	0m0,873s
   user	0m0,683s
   sys	0m0,182s

Besides some basic info/warning about potential issues, it took less than
second. That also includes copying asset files into destination.


Requirements
------------

The only requirement is Python 3.11 or higher.

Installation
------------

Currently the only option is to install it using virtualenv:

.. code:: console

   $ python -m venv .venv
   $ . .venv/bin/activate
   (.venv) $ pip install .


Usage
-----

Just use the ``vw2html`` command to convert selected file or directory.

You might also use configuration file placed under a file
``$XDG_CONFIG_HOME/vw2html.toml`` for tweaking program behaviour. All the
possible options are listed below:

.. code:: toml

   [[vimwiki]]
   # Directory to the vimwiki root path. Can contain ~/ or env variables.
   path = ''
   # Directory to the output path. Can contain ~/ or env variables. if not
   # provided it will be created as adding _html suffix for whatever directory 
   # is set on path.
   path_html = ''
   # Main file without extension. Usually index.
   index = 'index'
   # Extension for wiki files.
   ext = '.wiki'
   # Path to templates. If not specified, wiki path will be used.
   template_path = ''
   # Default template without extension.
   template_default = 'default'
   # Default template extension.
   template_ext = '.tpl'
   # Absolute path to the css stylesheet.
   css_name = ''

As for css file, there is default one which comes with VimWiki and is located
in `vimwiki/autoload/vimwiki/style.css` although due to different way and
locations of installing vim plugins, it will need to be specifically set either
in config file, or passed to the ``vw2html`` command via ``-s`` parameter.

To use ``vw2html`` without bothering about providing anything via commandline,
it's as easy as:

.. code:: toml

   [[vimwiki]]
   path = /path/to/vimwiki
   css_name = /path/to/css/file.css

And that's it. Other paths will be assumed or calculated using wiki path, or
using defaults, so in this case:

- ``path_html`` will become ``/path/to/vimwiki_html``
- ``ext`` will be ``.wiki``
- ``template_path`` will be ``/path/to/vimwiki``
- ``template_default`` will be ``default``
- ``template_ext`` will be ``.tpl``
- ``css_name`` will be ``/path/to/css/file.css``.

in other words:

- root wiki: ``path/to/vimwiki``
- html output: ``path/to/vimwiki_html``
- default template file: ``path/to/vimwiki/default.tpl``
- and css file: ``/path/to/css/file.css``

Wiki path is needed even for single wiki file, as it is used for gathering all
needed pieces like templates, stylesheet and assets.

Another thing is, you can have multiple vimwiki configs in single file, i.e.:

.. code:: toml

   [[vimwiki]]
   path = /path/to/vimwiki
   css_name = /path/to/css/file.css

   [[vimwiki]]
   path = ~/vimwiki
   css_name = /path/to/another/css/file.css

and whenever you call ``vw2html`` command with single file or whole wiki
directory, it will search for matching root in available configs and use
appropriate one.


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

  - code blocks can be colored using ``{{{type=foo``` or ``{{{foo`` where "foo"
    is the lexer recognized by the pygments_

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

  - Css - this one is undocumented as well, and allows to add css filename.
    Note, that css file will be copied to the root of vimwiki regardless of
    it's placement on filesystem

- Links

  - Diary
  - wikilinks (absolute/relative/plain/anchors)
  - external links (local/remote/bare)

  - transclusion links (or, image tags, as no other are supported on vimwiki)
    even those which have no schema (VimWiki docs doesn't mention those, yet
    it's simply working)

  - raw links (or bare)

- Tables

  - tables with headers
  - columns and rows spanning

What's not:

- Links:

  - interwiki links
  - wiki and local links are messed up at the moment, all of them are at the
    same level (i.e. *root* level, TBD)

- Lists:

  - which start with roman number (i.e. ``i``, ``x``, ``mc``, ``I``, ``X``,
    ``MC``)
  - which start with letters (i.e. ``a``, ``b``, ``z``, ``A``, ``B``, ``Z``)
  - VimWiki parser produce invalid item lists - no closing item tags for both
    kind of the lists (``<ul>`` and ``<ol>``).
  - With the list defined like below (overindented lists, and another dedented
    list):

    .. code::

       paragraph

         * some list item (which is inednted)
         * another item

       * another list

    ``Vimwiki2HTML`` will generate two lists, or rather list and a dangling
    item in a ``<li>`` tag. OTOH in such case ``vw2html`` will generate two
    lists properly on the same level - output may differ visually.

  - interpretation of items like:

    .. code::

       paragraph

       * some list item
       * another item

       * last item

    will produce two separate lists, not like in VimWiki html parser single
    list with second item having swallowed empty line.

- Tables

  - no aligning for the columns (``VimWiki2HTML`` doesn't do that either)

- Mathematical formulae (both - inline and block)
- Blockquotes
- Tags
- Explicit html tags (default list is ``b``, ``i``, ``s``, ``u``, ``sub``,
  ``sup``, ``kbd``, ``br`` and ``hr``).
- Escape HTML tags but the one excluded

License
-------

This piece of software is licensed under MIT.


.. _VimWiki: https://github.com/vimwiki/vimwiki
.. _pygments: https://pygments.org
