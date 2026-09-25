desktop_file = i18n.merge_file(
  input: 'com.properlypurple.braus.desktop.in',
  output: 'com.properlypurple.braus.desktop',
  type: 'desktop',
  po_dir: '../po',
  install: true,
  install_dir: get_option('datadir') / 'applications',
)

desktop_utils = find_program('desktop-file-validate', required: false)
if desktop_utils.found()
  test('Validate desktop file', desktop_utils,
    args: [desktop_file],
  )
endif

metainfo_file = i18n.merge_file(
  input: 'com.properlypurple.braus.metainfo.xml.in',
  output: 'com.properlypurple.braus.metainfo.xml',
  type: 'xml',
  po_dir: '../po',
  install: true,
  install_dir: get_option('datadir') / 'metainfo',
)

appstreamcli = find_program('appstreamcli', required: false)
if appstreamcli.found()
  test('Validate metainfo file', appstreamcli,
    args: ['validate', '--no-net', metainfo_file],
  )
endif

install_data(
  'com.properlypurple.braus.gschema.xml',
  install_dir: get_option('datadir') / 'glib-2.0/schemas',
)

install_data(
  'icons/hicolor/scalable/apps/com.properlypurple.braus.svg',
  install_dir: get_option('datadir') / 'icons/hicolor/scalable/apps',
  rename: 'com.properlypurple.braus.svg',
)

compile_schemas = find_program('glib-compile-schemas', required: false)
if compile_schemas.found()
  test('Validate schema file', compile_schemas,
    args: ['--strict', '--dry-run', meson.current_source_dir()],
  )
endif
