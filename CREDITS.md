# Credits & Copyright

Braus is free software licensed under the GNU General Public License,
version 3 or later ([GPL-3.0-or-later](LICENSE)). Each contributor keeps
the copyright to their own work; the following list documents who created
what, so credit stays with the people whose ideas and code this project
builds on.

## Original author

**Kavya Gokul** ([@properlypurple](https://github.com/properlypurple))
— <https://github.com/properlypurple>

- Created Braus in 2020, wrote the complete original application
  (`src/main.py`, `src/window.py`, `src/browser_mappings.py`, packaging,
  GSettings schema, desktop file)
- Original project: <https://github.com/properlypurple/braus>
- © 2020 Kavya Gokul

In June 2021 the original repository was archived as unmaintained, with
the author's explicit invitation to fork and continue under a new name:
<https://github.com/properlypurple/braus/commit/2d03721>

## Contributors whose work was adopted from the original project

The following ideas and code contributions originate from pull requests on
the original, now-unmaintained repository. They were re-implemented here on
top of the GTK4/libadwaita port (PR [#18](https://github.com/thecodejedi/braus/pull/18)):

### Pavel "GRbit" Griaznov ([@GRbit](https://github.com/GRbit))
— <https://github.com/GRbit>

- Idea and implementation of automatic URL-to-browser mappings
  (the `--set` / `--clear` mechanism) in
  [properlypurple/braus#38](https://github.com/properlypurple/braus/pull/38)
  (open since 2023, unmaintained upstream, first drafted in
  [#28](https://github.com/properlypurple/braus/pull/28) /
  [#32](https://github.com/properlypurple/braus/pull/32))
- The **overwrite semantics** (`--set` replaces an existing mapping for the
  same prefix) and the **`--get-mappings`** command adopted here follow his
  design from that pull request
- © 2021–2023 Pavel Griaznov

### Christian Weiske ([@cweiske](https://github.com/cweiske))
— <https://github.com/cweiske>

- Idea: allow multiple Braus instances
  ([properlypurple/braus#23](https://github.com/properlypurple/braus/pull/23))
- Idea: do not show the "set default browser" banner when Braus is already
  the default
  ([properlypurple/braus#19](https://github.com/properlypurple/braus/pull/19))
- Both behaviors are implemented in this codebase (`NON_UNIQUE` application
  flag, banner visibility check)
- © 2020 Christian Weiske

### Ivan Korniux ([@korniux](https://github.com/korniux))
— <https://github.com/korniux>

- Hotkeys proof-of-concept (number keys launch a browser)
  ([properlypurple/braus#12](https://github.com/properlypurple/braus/pull/12)),
  merged into the original project and present in this fork's history
- Documentation and AUTHORS work
  ([properlypurple/braus#11](https://github.com/properlypurple/braus/pull/11))
- © 2020 Ivan Korniux

## Contributors whose work was adopted from community forks

### Triet Pham ([@trietphm](https://github.com/trietphm))
— <https://github.com/trietphm>

- Idea: hide browsers without icons, and collapse duplicate browser entries
  (same executable installed twice, e.g. snap + deb) in the picker —
  commit [99acad2](https://github.com/trietphm/braus/commit/99acad2)
  in their fork <https://github.com/trietphm/braus>
- Implemented here as `dedupe_browsers()` (keyed on executable and display
  name, refined so distinct profiles are preserved)
- © 2021–2025 Triet Pham

## Maintainer of this fork

**Markus Hoffmann** ([@thecodejedi](https://github.com/thecodejedi))
— <https://github.com/thecodejedi>

- Snap packaging for the original project (merged upstream 2021),
  fork maintenance, and the GTK4/libadwaita modernization
  ([#17](https://github.com/thecodejedi/braus/pull/17)) including the
  upstream contributions above ([#18](https://github.com/thecodejedi/braus/pull/18))
- © 2020–2026 Markus Hoffmann

---

This project is a maintained fork of an abandoned project. If you believe
your contribution is missing from this list, please open an issue at
<https://github.com/thecodejedi/braus/issues>.
