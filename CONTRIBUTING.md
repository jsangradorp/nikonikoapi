# CONTRIBUTING

- You **NEED** Python 3.

## Getting started

To start working:

```
virtualenv -p $(which python3) .venv
. .venv/bin/activate
pip install -r requirements.txt
```

To lint the code:

`make check-coding-style` or just `make`

To run the tests:

`make check`

To do both:

`make test`

I recommend you to add the git hook in your working copy so git will run tests
before the actual commit and also ensure you don't decrease test coverage.

`ln -s ../../scripts/git-hooks/pre-commit .git/hooks/pre-commit`
