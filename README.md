# First-party packages 📦 from atopile

This is a monorepo for all the loose packages published by atopile.

Project-specific packages are published from their own repos.

## Development

### Conventions

Package name restrictions:

- kebab-case
- starts with a letter
- "[a-z][0-9\-]+"

- project directories MUST have the same name as the package

- drivers for ICs SHOULD be in the format "<manufacturer-stub>-<part-family>x?". eg ti-bq240x

  - there should be a single "x" on the end if there are multiple variants of the same part family
  - the manufacturer stub should be omitted if the they already do this for ths

- modules and files should be named like "<part-family>x?"

  - "x" is optional if there is only one variant of the part family
  - omit the manufacturer stub from the filename

- components should be named like "<part-id>"

- build names should be:
  - "ref-<name>" for reference designs
  - "test-<name>" for test builds
  - "example-<name>" for example builds
  - if only one IC/set of builds exist in a package, the name can be omitted

### Contributing

- Run pre-commit to fix pre-commit install
