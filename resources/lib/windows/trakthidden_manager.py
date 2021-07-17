# -*- coding: utf-8 -*-
"""
	Venom Add-on
"""

from json import dumps as jsdumps
# from urllib.parse import quote_plus
from resources.lib.modules.control import dialog, getHighlightColor
from resources.lib.windows.base import BaseDialog


class TraktHiddenManagerXML(BaseDialog):
	def __init__(self, *args, **kwargs):
		super(TraktHiddenManagerXML, self).__init__(self, args)
		self.window_id = 2040
		self.results = kwargs.get('results')
		self.total_results = str(len(self.results))
		self.chosen_hide = []
		self.chosen_unhide = []
		self.make_items()
		self.set_properties()

	def onInit(self):
		super(TraktHiddenManagerXML, self).onInit()
		win = self.getControl(self.window_id)
		win.addItems(self.item_list)
		self.setFocusId(self.window_id)

	def run(self):
		self.doModal()
		return (self.chosen_hide, self.chosen_unhide)

	# def onClick(self, controlID):
		# from resources.lib.modules import log_utils
		# log_utils.log('controlID=%s' % controlID)

	def onAction(self, action):
		try:
			if action in self.selection_actions:
				focus_id = self.getFocusId()
				if focus_id == 2040: # listItems
					position = self.get_position(self.window_id)
					chosen_listitem = self.item_list[position]
					tvdb = chosen_listitem.getProperty('venom.tvdb')
					if chosen_listitem.getProperty('venom.isHidden') == 'true':
						if chosen_listitem.getProperty('venom.isSelected') == 'true':
							chosen_listitem.setProperty('venom.isSelected', '')
							self.chosen_unhide.append(tvdb)
						else:
							chosen_listitem.setProperty('venom.isSelected', 'true')
							if tvdb in self.chosen_unhide: self.chosen_unhide.remove(tvdb)
					else:
						if chosen_listitem.getProperty('venom.isSelected') == '':
							chosen_listitem.setProperty('venom.isSelected', 'true')
							self.chosen_hide.append(tvdb)
						else:
							chosen_listitem.setProperty('venom.isSelected', '')
							if tvdb in self.chosen_hide: self.chosen_hide.remove(tvdb)

				elif focus_id == 2041: # OK Button
					self.close()
				elif focus_id == 2042: # Cancel Button

					# from resources.lib.modules import log_utils
					# log_utils.log('self.chosen_hide=%s' % self.chosen_hide)
					# log_utils.log('self.chosen_unhide=%s' % self.chosen_unhide)
					self.chosen_hide, self.chosen_unhide = None, None
					self.close()

			# elif action in self.context_actions:
				# from resources.lib.modules import log_utils
				# chosen_source = self.item_list[self.get_position(self.window_id)]
				# source_trailer = chosen_source.getProperty('venom.trailer')
				# if not source_trailer: return
				# log_utils.log('source_trailer=%s' % source_trailer)
				# cm = [('[B]Play Trailer[/B]', 'playTrailer'),]
				# chosen_cm_item = dialog.contextmenu([i[0] for i in cm])
				# if chosen_cm_item == -1: return
				# return self.execute_code('PlayMedia(%s, 1)' % source_trailer)

			elif action in self.closing_actions:
				self.chosen_hide, self.chosen_unhide = None, None
				self.close()
		except:
			from resources.lib.modules import log_utils
			log_utils.error()

	def make_items(self):
		def builder():
			for count, item in enumerate(self.results, 1):
				try:
					listitem = self.make_listitem()
					listitem.setProperty('venom.tvshowtitle', item.get('tvshowtitle'))
					listitem.setProperty('venom.year', str(item.get('year')))
					listitem.setProperty('venom.isHidden', str(item.get('isHidden')))
					listitem.setProperty('venom.isSelected', str(item.get('isHidden')))
					listitem.setProperty('venom.tvdb', item.get('tvdb'))
					listitem.setProperty('venom.rating', str(round(item.get('rating'), 1)))
					listitem.setProperty('venom.trailer', item.get('trailer'))
					listitem.setProperty('venom.studio', item.get('studio'))
					listitem.setProperty('venom.genre', item.get('genre', ''))
					listitem.setProperty('venom.duration', str(item.get('duration')))
					listitem.setProperty('venom.mpaa', item.get('mpaa'))
					listitem.setProperty('venom.plot', item.get('plot'))
					listitem.setProperty('venom.poster', item.get('poster', ''))
					listitem.setProperty('venom.clearlogo', item.get('clearlogo', ''))
					listitem.setProperty('venom.count', '%02d.)' % count)
					yield listitem
				except:
					from resources.lib.modules import log_utils
					log_utils.error()
		try:
			self.item_list = list(builder())
			self.total_results = str(len(self.item_list))
		except:
			from resources.lib.modules import log_utils
			log_utils.error()

	def set_properties(self):
		try:
			self.setProperty('venom.total_results', self.total_results)
			self.setProperty('venom.highlight.color', getHighlightColor())
		except:
			from resources.lib.modules import log_utils
			log_utils.error()