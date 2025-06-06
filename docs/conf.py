needs_sphinx = "7.2"
sphinx = "7.2"
extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.autosummary",
    "sphinx.ext.coverage",
    "sphinx.ext.doctest",
    "sphinx.ext.extlinks",
    "sphinx.ext.ifconfig",
    "sphinx.ext.napoleon",
    "sphinx.ext.todo",
    "sphinx.ext.viewcode",
]
source_suffix = ".rst"
master_doc = "index"
project = "emtl"
year = "2024-2025"
author = "Eastmoney Trade Library"
copyright = f"{year}, {author}"
try:
    from pkg_resources import get_distribution

    version = release = get_distribution("emtl").version
except Exception:
    import traceback

    traceback.print_exc()
    version = release = "0.2.6"

pygments_style = "trac"
templates_path = ["."]
extlinks = {
    "issue": ("https://github.com/riiy/emtl/issues/%s", "#%s"),
    "pr": ("https://github.com/riiy/emtl/pull/%s", "PR #%s"),
}

html_theme = "alabaster"
html_theme_options = {
    "githuburl": "https://github.com/riiy/emtl/",
}

html_use_smartypants = True
html_last_updated_fmt = "%b %d, %Y"
html_split_index = False
html_short_title = f"{project}-{version}"

napoleon_use_ivar = True
napoleon_use_rtype = False
napoleon_use_param = False
