"""
Sphinx configuration
"""
import os
import sys
sys.path.insert(0, os.path.abspath('..'))

project = 'The Bot on Duty'
copyright = '2024, Your Name'
author = 'Your Name'

extensions = [
    'sphinx.ext.autodoc',
    'sphinx.ext.napoleon',
    'sphinx.ext.viewcode',
    'sphinx.ext.intersphinx',
    'sphinx.ext.todo',
    'myst_parser'
]

templates_path = ['_templates']
exclude_patterns = ['_build', 'Thumbs.db', '.DS_Store']

html_theme = 'sphinx_rtd_theme'
html_static_path = ['_static']

# Настройки для autodoc
autodoc_member_order = 'bysource'
autodoc_typehints = 'description'
autodoc_typehints_format = 'short'

# Настройки для intersphinx
intersphinx_mapping = {
    'python': ('https://docs.python.org/3', None),
    'aiogram': ('https://docs.aiogram.dev/en/latest/', None),
}

# Настройки для todo
todo_include_todos = True 