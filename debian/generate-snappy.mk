#!/usr/bin/make -f

SNAPPY ?= /tmp/chromium-snappy/apps/chromium

all: $(SNAPPY)/meta/package.yaml $(SNAPPY)/meta/readme.md

DEB_HOST_ARCH ?= $(shell arch)

$(SNAPPY)/meta/package.yaml: 
$(SNAPPY)/meta/package.yaml:
	@dpkg-parsechangelog |sed \
		-e '/^Source: / { s/^Source: .*/name: chromium/; p }' \
		-e '/^Maintainer: / { s/^Maintainer: /vendor: /; p }' \
		-e '/^ chromium-browser (/ { s/^ chromium-browser (\(.*\)) .*/version: \1/; p }' \
		-e d >$@
	@echo "architecture: $(DEB_HOST_ARCH)" >>$@
	@echo "icon: meta/chromium.svg" >>$@
	@echo "binaries:" >>$@
	@echo "  - name: chromium" >>$@
	@echo "description: safe, fast web browser; open-source version of Chrome" >>$@
	@echo "  A safe, fast, and stable way for all Internet users to experience the web." >>$@
	@echo >>$@

$(SNAPPY)/meta/readme.md:
	@echo "chromium" >$@
	@echo "========" >>$@
	@echo >>$@
	@echo "A safe, fast, and stable way for all Internet users to experience the web." >>$@
