pkgdatadir = get_option('prefix') / get_option('datadir') / meson.project_name()
moduledir = pkgdatadir / 'braus'

python = import('python')

conf = configuration_data()
conf.set('PYTHON', python.find_installation('python3').full_path())
conf.set('VERSION', meson.project_version())
conf.set('localedir', get_option('prefix') / get_option('localedir'))
conf.set('pkgdatadir', pkgdatadir)

configure_file(
  input: 'braus.in',
  output: 'braus',
  configuration: conf,
  install: true,
  install_dir: get_option('bindir'),
)

braus_sources = [
  '__init__.py',
  'main.py',
  'window.py',
  'browser_mappings.py',
  'browser_profiles.py',
  'url_scopes.py',
]

test('url-scopes',
  find_program('python3', required: true),
  args: files('../tests/test_url_scopes.py'),
  suite: 'unit',
)

test('browser-profiles',
  find_program('python3', required: true),
  args: files('../tests/test_browser_profiles.py'),
  suite: 'unit',
)

test('browser-mappings',
  find_program('python3', required: true),
  args: files('../tests/test_browser_mappings.py'),
  suite: 'unit',
)

install_data(braus_sources, install_dir: moduledir)
