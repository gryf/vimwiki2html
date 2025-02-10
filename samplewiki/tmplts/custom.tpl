<!DOCTYPE html>
<html>
    <head>
        <title>Custom template: %title%</title>
        <style>
body {
 margin:0;
 padding:0;
 background:#152515;
 color:#eafaea;
 font-size:16px;
 line-height:1.5;
 font-family:Monaco,bitstream vera sans mono,lucida console,Terminal,monospace
}
article, footer {
 width:90%;
 max-width:1000px;
 margin:0 auto
}
section {
 display:block;
 margin:0 0 20px
}
li {
 line-height:1.4
}
header {
 background:rgba(0,0,0,.1);
 border-bottom:1px dashed #b5e853;
 padding:20px;
 margin:0 0 40px
}
.header-links {
 text-align:center
}
.header-link {
 display:inline
}
header h1 {
 font-size:24px;
 line-height:1.5;
 margin:0;
 text-align:center;
 font-weight:700;
 font-family:Monaco,bitstream vera sans mono,lucida console,Terminal,monospace;
 text-shadow:0 1px 1px rgba(0,0,0,.1),0 0 5px rgba(181,232,83,.1),0 0 10px rgba(181,232,83,.1);
 letter-spacing:-1px;
 -webkit-font-smoothing:antialiased
}
header h2 {
 font-size:18px;
 font-weight:300;
}
#main_content {
 width:100%;
 -webkit-font-smoothing:antialiased
}
section img {
 max-width:100%
}
h1,
h2,
h3,
h4,
h5,
h6 {
 font-weight:400;
 font-family:Monaco,bitstream vera sans mono,lucida console,Terminal,monospace;
 letter-spacing:-.03em;
 text-shadow:0 1px 1px rgba(0,0,0,.1),0 0 5px rgba(181,232,83,.1),0 0 10px rgba(181,232,83,.1);
 margin:0 0 20px
}
#main_content h1 {
 font-size:30px
}
#main_content h2 {
 font-size:24px
}
#main_content h3 {
 font-size:18px
}
#main_content h4 {
 font-size:14px
}
#main_content h5 {
 font-size:12px;
 text-transform:uppercase;
 margin:0 0 5px
}
#main_content h6 {
 font-size:12px;
 text-transform:uppercase;
 color:#999;
 margin:0 0 5px
}
footer {
 height:50px;
 line-height:50px;
 text-align:center
}
        </style>
    </head>
    <body>
        <header>
            <div>
                <div class="header-links">
                    <a href="%root_path%index.html"><h2 class="header-link">index</h2></a>
                    <a href="%root_path%headers.html"><h2 class="header-link">headers</h2></a>
                    <a href="%root_path%code.html"><h2 class="header-link">code</h2></a>
                    <a href="%root_path%hr.html"><h2 class="header-link">hr</h2></a>
                    <a href="%root_path%paragraph.html"><h2 class="header-link">para</h2></a>
                    <a href="%root_path%attributes.html"><h2 class="header-link">attr</h2></a>
                    <a href="%root_path%misc.html"><h2 class="header-link">misc</h2></a>
                    <a href="%root_path%lists.html"><h2 class="header-link">lists</h2></a>
                    <a href="%root_path%links.html"><h2 class="header-link">links</h2></a>
                    <a href="%root_path%tables.html"><h2 class="header-link">tables</h2></a>
                </div>
            </div>
        </header>
        <article class="content">
            %content%
        </article>
        <footer>
            <span>
                <b>Last updated on %date%</b>
            </span>
        </footer>
    </body>
</html>
