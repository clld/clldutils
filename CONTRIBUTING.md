# Contributing to clldutils

## Installing clldutils for development

1. Fork `clld/clldutils`
2. Clone your fork
3. Change into the top-level directory of the clone
4. Install `clldutils` for development (preferably in a separate virtual environment) running
   ```shell
   pip install -r requirements.txt
   ```
5. Make sure the test suite passes:
   ```shell
   pytest
   ```
6. Optionally make sure tests pass on all supported platforms:
   ```shell
   tox -r
   ```

