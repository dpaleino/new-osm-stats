#!/bin/sh

for trans in $(ls po/*.po); do
	name=$(basename $trans .po)
	[ -d po/locales/$name/LC_MESSAGES ] || mkdir -p po/locales/$name/LC_MESSAGES
	msgfmt $trans -o po/locales/$name/LC_MESSAGES/messages.mo
done
