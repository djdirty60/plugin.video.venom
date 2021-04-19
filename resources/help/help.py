# -*- coding: utf-8 -*-
"""
	Venom Add-on
"""

from resources.lib.modules import control

venom_path = control.addonPath(control.addonId())
venom_version = control.addonVersion(control.addonId())

def get(file):
	helpFile = control.joinPath(venom_path, 'resources', 'help', file + '.txt')
	r = open(helpFile)
	text = r.read()
	r.close()
	control.dialog.textviewer('[COLOR red]Venom[/COLOR] -  v%s - %s' % (venom_version, file), text)