# -*- coding: utf-8 -*-
"""
	Venom Add-on
"""

from resources.lib.modules import control

venom_path = control.addonPath(control.addonId())
venom_version = control.getVenomVersion()
changelogfile = control.joinPath(venom_path, 'changelog.txt')


def get():
	r = open(changelogfile)
	text = r.read()
	r.close()
	control.dialog.textviewer('[COLOR red]Venom[/COLOR] -  v%s - ChangeLog' % venom_version, text)