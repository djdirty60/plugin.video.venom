# -*- coding: utf-8 -*-
"""
	Venom Add-on
"""

from json import dumps as jsdumps
from urllib.parse import quote_plus
from resources.lib.modules.control import dialog, getHighlightColor, yesnoDialog, sleep, condVisibility, setting as getSetting
from resources.lib.windows.base import BaseDialog


class TraktHiddenManagerXML(BaseDialog):
	def __init__(self, *args, **kwargs):
		super(TraktHiddenManagerXML, self).__init__(self, args)
		self.window_id = 2040
		self.results = kwargs.get('results')
		self.total_results = str(len(self.results))
		self.chosen_hide = []
		self.chosen_unhide = []
		self.hide_watched = getSetting('trakt.HiddenManager.hideWatched') == 'true'
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
					chosen_listitem = self.item_list[self.get_position(self.window_id)]
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
					self.chosen_hide, self.chosen_unhide = None, None
					self.close()
				elif focus_id == 2045: # Stop Trailer Playback Button
					self.execute_code('PlayerControl(Stop)')
					sleep(500)
					self.setFocusId(self.window_id)

			elif action in self.context_actions:
				cm = []
				chosen_listitem = self.item_list[self.get_position(self.window_id)]
				source_trailer = chosen_listitem.getProperty('venom.trailer')
				if not source_trailer:
					from resources.lib.modules import trailer
					source_trailer = trailer.Trailer().worker('show', chosen_listitem.getProperty('venom.tvshowtitle'), chosen_listitem.getProperty('venom.year'), None, chosen_listitem.getProperty('venom.imdb'))

				if source_trailer: cm += [('[B]Play Trailer[/B]', 'playTrailer')]
				cm += [('[B]Browse Series[/B]', 'browseSeries')]
				chosen_cm_item = dialog.contextmenu([i[0] for i in cm])
				if chosen_cm_item == -1: return
				cm_action = cm[chosen_cm_item][1]

				if cm_action == 'playTrailer':
					self.execute_code('PlayMedia(%s, 1)' % source_trailer)
					total_sleep = 0
					while True:
						sleep(500)
						total_sleep += 500
						HasVideo = condVisibility('Player.HasVideo')
						if HasVideo or total_sleep >= 3000: break
					if HasVideo:
						self.setFocusId(2045)
						while condVisibility('Player.HasVideo'):
							sleep(1000)
						self.setFocusId(self.window_id)
					else: self.setFocusId(self.window_id)

				if cm_action == 'browseSeries':
					systvshowtitle = quote_plus(chosen_listitem.getProperty('venom.tvshowtitle'))
					year = chosen_listitem.getProperty('venom.year')
					imdb = chosen_listitem.getProperty('venom.imdb')
					tmdb = chosen_listitem.getProperty('venom.tmdb')
					tvdb = chosen_listitem.getProperty('venom.tvdb')
					from resources.lib.modules.control import lang
					if not yesnoDialog(lang(32182), '', ''): return
					self.chosen_hide, self.chosen_unhide = None, None
					self.close()
					sysart = ''
					self.execute_code('ActivateWindow(Videos,plugin://plugin.video.venom/?action=seasons&tvshowtitle=%s&year=%s&imdb=%s&tmdb=%s&tvdb=%s&art=%s,return)' % (
							systvshowtitle, year, imdb, tmdb, tvdb, sysart))

			elif action in self.closing_actions:
				self.chosen_hide, self.chosen_unhide = None, None
				self.close()
		except:
			from resources.lib.modules import log_utils
			log_utils.error()

	def make_items(self):
		def filerWatched():
			if self.hide_watched:
				self.results = [i for i in self.results if i.get('watched_count').get('watched') != i.get('watched_count').get('total')]
		def builder():
			for count, item in enumerate(self.results, 1):
				try:
					listitem = self.make_listitem()
					listitem.setProperty('venom.tvshowtitle', item.get('tvshowtitle'))
					listitem.setProperty('venom.year', str(item.get('year')))
					listitem.setProperty('venom.isHidden', str(item.get('isHidden')))
					listitem.setProperty('venom.isSelected', str(item.get('isHidden')))
					listitem.setProperty('venom.imdb', item.get('imdb'))
					listitem.setProperty('venom.tmdb', item.get('tmdb'))
					listitem.setProperty('venom.tvdb', item.get('tvdb'))
					listitem.setProperty('venom.status', item.get('status'))
					listitem.setProperty('venom.watched_count', '(watched ' + str(item.get('watched_count').get('watched')) + ' of ' + str(item.get('watched_count').get('total')) + ')')
					listitem.setProperty('venom.rating', str(round(float(item.get('rating')), 1)))
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
			filerWatched()
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