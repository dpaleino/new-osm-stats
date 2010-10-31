#!/bin/sh

pybabel extract -F po/babel.cfg . -o po/osmstats.pot \
	--msgid-bugs-address=d.paleino@gmail.com \
	--copyright-holder='David Paleino <d.paleino@gmail.com>' \

sed -i "s/PROJECT/osmstats/g" po/osmstats.pot
sed -i "s/VERSION/0.1/g" po/osmstats.pot

for trans in $(ls po/*.po); do
	msgmerge --update $trans po/osmstats.pot
done
