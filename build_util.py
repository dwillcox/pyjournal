from __future__ import print_function
import calendar
import os
import sys

import shell_util

def stripextension(fpath):
    """
    Given a file name, strip the extension and return its base name.
    """
    return '.'.join(os.path.basename(fpath).split('.')[:-1])

def get_appendices(nickname, defs):

    app_dir = "{}/journal-{}/entries/appendices/".format(defs[nickname]["working_path"], nickname)

    app = []
    if os.path.isdir(app_dir):
        for t in os.listdir(app_dir):
            if t.endswith(".tex") or t.endswith(".md"):
                app.append(stripextension(t))
    return app

def md_to_tex(mdpath):
    """
    Given a path specifying a markdown file, use pandoc to
    generate a tex file by the same name (modulo extension)
    in the same directory for building the journal.
    Returns the path of the new tex file.
    """
    tbase = stripextension(mdpath)
    ttex  = tbase + '.tex'
    ftex  = os.path.join(os.path.dirname(mdpath), ttex)
    cmd   = "pandoc --from=markdown --output={} {}".format(ftex, mdpath)
    shell_util.run(cmd)
    return ftex

def build(nickname, defs, show=0):

    entry_dir = "{}/journal-{}/entries/".format(defs[nickname]["working_path"], nickname)

    entries = []
    years = []

    # get the list of directories in entries/
    for d in os.listdir(entry_dir):
        if d.endswith("appendices"):
            continue

        if os.path.isdir(entry_dir + d):
            entries.append(d)

            y, m, d = d.split("-")
            if not y in years:
                years.append(y)


    os.chdir(entry_dir)

    years.sort()
    entries.sort()

    # years are chapters
    try: f = open("chapters.tex", "w")
    except:
        sys.exit("ERROR: unable to create chapters.tex")


    for y in years:
        f.write("\\chapter{{{}}}\n".format(y))
        f.write("\\input{{entries/{}.tex}}\n\n".format(y))

    # now do the appendices
    f.write("\\appendix\n")

    app_dir = "{}/journal-{}/entries/appendices/".format(defs[nickname]["working_path"], nickname)

    if os.path.isdir(app_dir):
        for t in os.listdir(app_dir):
            if t.endswith(".tex"):
                # Find out if there is a markdown file by the same base-name
                # and if there is, then defer to it.
                tmd = stripextension(t) + '.md'
                if not os.path.isfile(os.path.join(app_dir, tmd)):
                    ttex = t
                else:
                    continue
            elif t.endswith(".md"):
                # Process Markdown with Pandoc to LaTeX
                tpath = os.path.join(app_dir, t)
                ttex = os.path.basename(md_to_tex(tpath))
            else:
                continue
            f.write("\\input{{entries/appendices/{}}}\n\n".format(ttex))
    f.close()


    # within each year, months are sections
    for y in years:

        try: f = open("{}.tex".format(y), "w")
        except:
            sys.exit("ERROR: unable to create chapters.tex")

        current_month = None
        current_day = None

        for e in entries:
            ytmp, m, d = e.split("-")
            if not ytmp == y:
                continue

            if not m == current_month:
                f.write("\\section{{{}}}\n".format(calendar.month_name[int(m)]))
                current_month = m

            tex = []
            for t in os.listdir(e):
                if t.endswith(".tex"):
                    # Find out if there is a markdown file by the same base-name
                    # and if there is, then defer to it.
                    tmd = stripextension(t) + '.md'
                    if not os.path.isfile(os.path.join(os.getcwd(), e, tmd)):
                        tex.append(t)
                elif t.endswith(".md"):
                    # Use Pandoc to convert Markdown to LaTeX
                    tpath = os.path.join(os.getcwd(), e, t)
                    ftex  = md_to_tex(tpath)
                    tex.append(os.path.basename(ftex))

            tex.sort()
            for t in tex:
                if not d == current_day:
                    f.write("\\subsection{{{} {}}}\n".format(calendar.month_name[int(m)], d))
                    current_day = d

                f.write("\\HRule\\\\ \n")
                idx = t.rfind(".tex")
                tout = t[:idx].replace("_", " ")
                f.write("{{\\bfseries {{\sffamily {} }} }}\\\\[0.5em] \n".format(tout))
                f.write("\\input{{entries/{}/{}}}\n\n".format(e, t))
                f.write("\\vskip 2em\n")

            f.write("\n")

        f.close()


    # now do the latexing to get the PDF
    build_dir = "{}/journal-{}/".format(defs[nickname]["working_path"], nickname)
    os.chdir(build_dir)

    stdout, stderr, rc = shell_util.run("pdflatex --halt-on-error journal.tex")
    stdout, stderr, rc = shell_util.run("pdflatex --halt-on-error journal.tex")
    stdout, stderr, rc = shell_util.run("makeindex journal")
    stdout, stderr, rc = shell_util.run("pdflatex --halt-on-error journal.tex")
    stdout, stderr, rc = shell_util.run("pdflatex --halt-on-error journal.tex")

    # if we were not successful, then the PDF is not produced
    # note: pdflatex does not seem to use stderr at all
    pdf = os.path.normpath("{}/journal.pdf".format(build_dir))
    if os.path.isfile(pdf):
        print("journal is located at {}".format(pdf))
    else:
        print(stdout)
        print("There were LaTeX errors")
        print("Check the source in {}/entries/".format(build_dir))
        print("be sure to 'git commit' to store any fixes")
        sys.exit()


    # show it in a PDF viewer
    if show == 1:
        os.system("evince {} &".format(pdf))
