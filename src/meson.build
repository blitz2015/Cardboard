pkgdatadir = get_option('prefix') / get_option('datadir') / meson.project_name()
moduledir = pkgdatadir / 'cardboard'

python = import('python')

conf = configuration_data()
conf.set('PYTHON', python.find_installation('python3').full_path())
conf.set('VERSION', meson.project_version())
conf.set('localedir', get_option('prefix') / get_option('localedir'))
conf.set('pkgdatadir', pkgdatadir)

configure_file(
  input: 'cardboard.in',
  output: 'cardboard',
  configuration: conf,
  install: true,
  install_dir: get_option('bindir'),
  install_mode: 'r-xr-xr-x'
)

cardboard_sources = [
  'py/main.py',
  'py/window.py',
  'py/preferences.py',
  'py/catalog.py',
  'py/tab.py',
  'py/entry.py',
  'py/tags.py',
  'py/searches.py',
  'py/favorites.py',
  'py/danbooru.py',
  'py/media.py'
]

install_data(cardboard_sources, install_dir: moduledir)