pkgdatadir = get_option('prefix') / get_option('datadir') / meson.project_name()
moduledir = pkgdatadir / 'lipi'
gnome = import('gnome')

blueprints = custom_target('blueprints',
  input: files(
    'shortcuts-dialog.blp',
    'window.blp',
    'fonts-view.blp',
    'font-row.blp',
    'sheet-view.blp',
    'sidebar.blp',
    'test-font.blp',
  ),
  output: '.',
  command: [find_program('blueprint-compiler'), 'batch-compile', '@OUTPUT@', '@CURRENT_SOURCE_DIR@', '@INPUT@'],
)

gnome.compile_resources('lipi',
  'lipi.gresource.xml',
  gresource_bundle: true,
  install: true,
  install_dir: pkgdatadir,
  dependencies: blueprints,
)

python = import('python')

conf = configuration_data()
conf.set('PYTHON', python.find_installation('python3').full_path())
conf.set('VERSION', meson.project_version())
conf.set('localedir', get_option('prefix') / get_option('localedir'))
conf.set('pkgdatadir', pkgdatadir)

configure_file(
  input: 'lipi.in',
  output: 'lipi',
  configuration: conf,
  install: true,
  install_dir: get_option('bindir'),
  install_mode: 'rwxr-xr-x'
)

lipi_sources = [
  '__init__.py',
  'main.py',
  'window.py',
  'fonts_manager.py',
  'fonts_view.py',
  'font_model.py',
  'font_row.py',
  'sheet_view.py',
  'sidebar.py',
  'filters.py',
  'test_font.py',
]

install_data(lipi_sources, install_dir: moduledir)
