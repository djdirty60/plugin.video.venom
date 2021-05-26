# -*- coding: utf-8 -*-
"""
	Venom Add-on
"""

from modules.settings import skin_location
# from windows.textviewer import TextViewerXML
from resources.lib.windows.textviewer import TextViewerXML
from resources.lib.modules import control
from resources.lib.modules import py_tools

skin_path = control.transPath('special://home/plugin.video.venom')


def show_text(heading, text=None, file=None):
	if file:
		if py_tools.isPY3:
			with open(file, encoding="utf-8") as r: text = r.read()
		else:
			with open(file) as r: text = r.read()
	window = TextViewerXML('textviewer.xml', skin_path, heading=heading, text=text)
	window.run()
	del window