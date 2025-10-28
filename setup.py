from setuptools import setup

APP = ['main.py']
DATA_FILES = [
    ('templates', ['templates/index.html', 'templates/preview.html'])
]
OPTIONS = {
    'argv_emulation': False,
    'packages': ['uvicorn', 'fastapi', 'jinja2', 'markdown', 'yaml', 'bs4', 'json', 'uuid', 'os', 'datetime'],
    'includes': ['uvicorn.logging', 'uvicorn.loops', 'uvicorn.loops.auto', 'uvicorn.protocols', 'uvicorn.protocols.http', 'uvicorn.protocols.http.auto', 'uvicorn.protocols.websockets', 'uvicorn.protocols.websockets.auto', 'uvicorn.lifespan', 'uvicorn.lifespan.on'],
    'plist': {
        'CFBundleName': 'MD2PDF',
        'CFBundleDisplayName': 'MD2PDF',
        'CFBundleIdentifier': 'com.md2pdf.app',
        'CFBundleVersion': '1.0.0',
        'CFBundleShortVersionString': '1.0.0',
        'NSHighResolutionCapable': True,
        'LSBackgroundOnly': False,
    },
    'iconfile': None,  # Add icon path if you have one
}

setup(
    app=APP,
    data_files=DATA_FILES,
    options={'py2app': OPTIONS},
    setup_requires=['py2app'],
)
