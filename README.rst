============
vimwiki2html
============

VimWiki2HTML is a python implementation for converting `VimWiki`_ default
syntax into html.

Motivation
----------

My main motivation is to be able to deploy output of the ``VimwikiAll2HTML`` to
somewhere else, either to use it directly on local filesystem, rsync it to some
of other machines or even expose it via webserver. With that assumption I've
noticed it might be somewhat troublesome with current design especially when
dealing with asset files, which are not stored on ``~/vimwiki_html``, but
rather are simply linked to ``~/vimwiki`` path.

Also in some really large files, I've noticed ``Vimwiki2HTML`` can be really
slow. Currently I have around 750 wiki files.  A lot of them are pretty small,
yet some of them are complex, full of tables, code blocks and lists. Below is a
simple benchmark I've done to convert whole wiki collection into html using
vimwiki ``VimwikiAll2HTML`` command:

.. code:: console

   $ time vim -s script.vim

   real	2m33,027s
   user	2m17,865s
   sys	0m6,750s
   $ cat script.vim
   :VimwikiIndex
   :VimwikiAll2HTML
   :q!

And yes, it took two and a half minutes to build whole wiki as HTML.

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

   real 0m0,428s
   user 0m2,173s
   sys  0m0,608s

Besides some basic info/warning about potential issues and copying all needed
files (including images and linked static non-wiki files), it took less than
second thanks to parallel conversion - although with single thread it still
take under 1 second:

.. code:: console

   real	0m0,873s
   user	0m0,683s
   sys	0m0,182s


Requirements
------------

The only requirement is Python 3.12 or higher.

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
   # If set to false, conversion will execute wiki after wiki. Usefull for
   # debugging.
   convert_async = true

As for css file, there is default one which comes with VimWiki and is located
in `vimwiki/autoload/vimwiki/style.css` although due to different way and
locations of installing vim plugins, it will need to be specifically set either
in config file, or passed to the ``vw2html`` command via ``-s`` parameter.

To use ``vw2html`` without bothering about providing anything via commandline,
it's as easy as:

.. code:: toml

   [[vimwiki]]
   path = "/path/to/vimwiki"

And that's it. Other paths will be assumed or calculated using wiki path, or
using defaults, so in this case:

- ``path_html`` will become ``/path/to/vimwiki_html``
- ``ext`` will be ``.wiki``
- ``template_path`` will be ``/path/to/vimwiki``
- ``template_default`` will be ``default``
- ``template_ext`` will be ``.tpl``
- ``css_name`` will be none

in other words:

- root wiki: ``path/to/vimwiki``
- html output: ``path/to/vimwiki_html``
- default template file: ``path/to/vimwiki/default.tpl``

optionally you can provide CSS file using ``css_name`` with full path to css
file.

Wiki path is needed even for single wiki file, as it is used for gathering all
needed pieces like templates, stylesheet and assets.

Another thing is, you can have multiple vimwiki configs in single file, i.e.:

.. code:: toml

   [[vimwiki]]
   path = "/path/to/vimwiki"

   [[vimwiki]]
   path = "~/vimwiki"

and whenever you call ``vw2html`` command with single file or whole wiki
directory, it will search for matching root in available configs and use
appropriate one.

Templates
---------

Even so templates can be in whatever HTML standard (including raw *tag soup*,
HTML4, XHTML and HTML5), parser used for extracting css and javascript files
origins from Python stdlib, just for simplicity (it might change in the future
with optional dependency on BeautifulSoup - for now it's ``minidom`` parser),
so be careful and close all the tags even if standards like HTML5 permit for
unclosing tags like ``<link>``.

If you place css file(s) into template, you don't have to provide ``css_name``
in the configuration or use ``--stylesheet`` commandline option - all the files
will be gathered from the links and put into destination directory with exact
directory structure like in source vimwiki path. Additionally, assets from CSS
files will be copied as well (namely image files), while JavaScript files will
not be searched for those.

When using no template (i.e. using "default") using external CSS file is
optional as well, although resulting HTML will be pretty raw.

Integration with vim
--------------------

You can use ``vw2html`` with vim for rendering wiki, instead of using
``Vimwiki2HTML`` and/or ``VimwikiAll2HTML``. There are many ways to achieve
that, one of it is to map the keys:

.. code:: vim

   map <F5> :call system("vw2html " . bufname("%"))<CR>
   map <F6> :call system("vw2html")<CR>

so, suppose there is a valid configuration and user hit F5 it will pass current
file to ``vw2html`` and convert it to HTML. F6 on the other hand will execute
``vw2html`` without arguments, which will do the conversion on entire wiki.


Conversion state
----------------

What's supported
''''''''''''''''

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
  - Support for definition lists

    - including multiline paragraph in definition
    - including limited lists support nested within definition

- Preformatted text

  - code blocks can be colored using ``{{{type=foo``` or ``{{{foo`` where "foo"
    is the lexer recognized by the pygments_

- Comments
- Horizontal line
- Placeholders

  - ``%title``
  - ``%date``
  - ``%template``
  - ``%nohtml``

  - ``%plainhtml`` (this one is undocumented, and allows to add explicit html
    tags which follows that placeholder. It's inline only, which means no span
    on multiple lines, although this placeholder can be repeated several times)

  - Template placeholders

    - ``%root_path%``
    - ``%title%``
    - ``%date%``
    - ``%content%``
    - ``%css%`` - this one is undocumented as well, and allows to add css
      filename. Note, that css file will be copied to the root of vimwiki
      regardless of it's placement on filesystem

- Links

  - Diary
  - wikilinks (absolute/relative/plain)
  - external links (local/remote/bare)

  - transclusion links (or, image tags, as no other are supported on vimwiki)
    even those which have no schema (VimWiki docs doesn't mention those, yet
    it's simply working)

  - raw links (or bare)
  - anchor links (implemented differently - only last anchor is taken into
    account - may cause anchors collision)

  - adding arbitrary attributes for the link - i.e.
    ``[[target|descritption|class="foo"]]``. This is addition which doesn't
    exists on VimWiki, but it's nice addition for adding lightbox-ish
    functionality

- Tables

  - tables with headers
  - columns and rows spanning
  - aligning for the columns (``VimWiki2HTML`` doesn't do that)

- Explicit html tags (supported tag list: ``b``, ``i``, ``s``, ``u``, ``sub``,
  ``sup``, ``kbd``, ``br`` and ``hr``).
- Escape other HTML tags

What's not
''''''''''

- Placeholders

  - Template placeholders

    - ``%wiki_path%``

- Links:

  - interwiki links

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

- Mathematical formulae (both - inline and block)
- Blockquotes
- Tags
- Configurable explicit html tags (besides default list)


Most of those are either second priority for implementation or things, which I
have no interested in.


License
-------

This piece of software is licensed under MIT.


.. _VimWiki: https://github.com/vimwiki/vimwiki
.. _pygments: https://pygments.org
