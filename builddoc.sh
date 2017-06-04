#!/usr/bin/env bash
mkdir -p doc
raml2html -i src/raml/nikoniko.raml -o doc/nikoniko.html
echo doc/nikoniko.html created
