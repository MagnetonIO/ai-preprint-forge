import re
from app.utils.latex import clean_latex_content, restructure_latex_content


def test_clean_latex_content_removes_code_fences():
    raw = """
```latex
\\documentclass{article}
\\begin{document}
Hello
\\end{document}
```
"""
    cleaned = clean_latex_content(raw)
    assert "```" not in cleaned
    assert "\\documentclass" in cleaned


def test_restructure_latex_content_builds_valid_structure():
    src = """
\\documentclass{article}
\\title{Test Title}
\\author{Author Name}
\\date{2025-01-01}
\\begin{document}
\\section{Intro}
Body text.
\\end{document}
"""
    out = restructure_latex_content(src)

    # Must have one document environment and maketitle when metadata exists
    assert out.count("\\begin{document}") == 1
    assert out.count("\\end{document}") == 1
    assert "\\maketitle" in out
    # Metadata lines preserved
    assert "\\title{" in out and "\\author{" in out and "\\date{" in out
    # Body content retained
    assert "\\section{Intro}" in out and "Body text." in out

