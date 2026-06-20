import os
from importlib.machinery import SourceFileLoader


HERE = os.path.dirname(__file__)
APP = os.path.abspath(os.path.join(HERE, '..', 'dira-nuriot'))
build = SourceFileLoader('build_html', os.path.join(APP, 'build_html.py')).load_module()


def test_build_contains_management_modules():
    build.main()
    with open(os.path.join(APP, 'index.html'), encoding='utf-8') as handle:
        html = handle.read()
    required = [
        'מצב מערכת ונתונים',
        'נתוני שוק רשמיים',
        'comparables-table',
        'cash-monthly-needed',
        'reno-track-table',
        'defects-table',
        'export-state',
        'update_status',
    ]
    for marker in required:
        assert marker in html
