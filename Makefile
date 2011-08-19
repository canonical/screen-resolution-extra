DOMAIN=screen-resolution-extra

PO_FILES=$(wildcard po/*.po)
DESKTOP_FILES=$(basename $(wildcard */*.desktop.in))

all: po/$(DOMAIN).pot build-mo $(DESKTOP_FILES)

clean:
	rm -rf po/mo/
	rm -f po/$(DOMAIN).pot
	rm -f $(DESKTOP_FILES)

#
# i18n for po/*
#

# update the pot
po/$(DOMAIN).pot:
	cd po; intltool-update -p -g $(DOMAIN)

# merge the new stuff into the po files
merge-po: $(PO_FILES) po/$(DOMAIN.pot)
	cd po; intltool-update -r -g $(DOMAIN)

# create mo from po files
%.mo : %.po
	mkdir -p $(basename $(subst po/,po/mo/,$<))/LC_MESSAGES/ 
	msgfmt $< -o $(basename $(subst po/,po/mo/,$<))/LC_MESSAGES/$(DOMAIN).mo 

# generate all *.mo files
build-mo: $(patsubst %.po,%.mo,$(PO_FILES))

#
# i18n for *.desktop files
#

%.desktop : %.desktop.in
	intltool-merge -d po/ $< $@

.PHONY: all clean build-mo merge-po
