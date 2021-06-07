# -*- coding: utf-8 -*-

from resources.lib.windows.base import BaseDialog


class TextViewerXML(BaseDialog):
	def __init__(self, *args, **kwargs):
		super(TextViewerXML, self).__init__(self, args)
		self.window_id = 2000
		self.text = kwargs.get('text')
		self.heading = kwargs.get('heading')

	def onInit(self):
		super(TextViewerXML, self).onInit()
		self.set_properties()

	def run(self):
		self.doModal()

	def onAction(self, action):
		if action in self.closing_actions or action in self.selection_actions:
			self.close()

	def set_properties(self):
		self.setProperty('venom.text', self.text)
		self.setProperty('venom.heading', self.heading)