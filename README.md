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

We welcome contributions! Here's how you can help:

1. Fork the repository
2. Create a new branch for your changes
   ```bash
   git checkout -b feature/your-feature-name
   ```
3. Make your changes
4. Install and run pre-commit hooks to ensure code quality
   ```bash
   pre-commit install
   pre-commit run --all-files
   ```
5. Commit your changes with clear, descriptive commit messages
6. Push to your fork
7. Open a Pull Request with a clear description of your changes

Please ensure your PR:

- Follows the package naming conventions above
- Includes appropriate tests if adding new functionality
- Has all pre-commit checks passing
- Has a clear description of the changes

### Building Packages

To build all packages in the repository, use the `build-all.sh` script:

```bash
# Build all packages
./build-all.sh

# Build all packages with specific flags (e.g., --frozen)
./build-all.sh --frozen
```

The script will attempt to build each package and provide a summary report of successes and failures.
