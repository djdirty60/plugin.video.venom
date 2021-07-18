# -*- coding: utf-8 -*-
"""
	Venom Add-on
"""

from json import dumps as jsdumps
from resources.lib.modules.control import dialog, getHighlightColor
from resources.lib.modules import tools
from resources.lib.windows.base import BaseDialog


class TraktEpisodeProgressManagerXML(BaseDialog):
	def __init__(self, *args, **kwargs):
		super(TraktEpisodeProgressManagerXML, self).__init__(self, args)
		self.window_id = 2060
		self.results = kwargs.get('results')
		self.total_results = str(len(self.results))
		self.selected_items = []
		self.make_items()
		self.set_properties()

	def onInit(self):
		super(TraktEpisodeProgressManagerXML, self).onInit()
		win = self.getControl(self.window_id)
		win.addItems(self.item_list)
		self.setFocusId(self.window_id)

	def run(self):
		self.doModal()
		return self.selected_items

	# def onClick(self, controlID):
		# from resources.lib.modules import log_utils
		# log_utils.log('controlID=%s' % controlID)

	def onAction(self, action):
		try:
			if action in self.selection_actions:
				focus_id = self.getFocusId()
				if focus_id == 2060: # listItems
					position = self.get_position(self.window_id)
					chosen_listitem = self.item_list[position]
					imdb = chosen_listitem.getProperty('venom.imdb')
					if chosen_listitem.getProperty('venom.isSelected') == 'true':
						chosen_listitem.setProperty('venom.isSelected', '')
						if imdb in str(self.selected_items):
							pos = next((index for (index, d) in enumerate(self.selected_items) if d["imdb"] == imdb), None)
							self.selected_items.pop(pos)
					else:
						chosen_listitem.setProperty('venom.isSelected', 'true')
						imdb = chosen_listitem.getProperty('venom.imdb')
						tvdb = chosen_listitem.getProperty('venom.tvdb')
						season = chosen_listitem.getProperty('venom.season')
						episode = chosen_listitem.getProperty('venom.episode')
						self.selected_items.append({'imdb': imdb, 'tvdb': tvdb, 'season': season, 'episode': episode})
				elif focus_id == 2061: # OK Button
					self.close()
				elif focus_id == 2062: # Cancel Button
					self.selected_items = None
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
				self.selected_items = None
				self.close()
		except:
			from resources.lib.modules import log_utils
			log_utils.error()
			self.close()

	def make_items(self):
		def builder():
			for count, item in enumerate(self.results, 1):
				try:
					listitem = self.make_listitem()
					tvshowtitle = item.get('tvshowtitle')
					listitem.setProperty('venom.tvshowtitle', tvshowtitle)
					listitem.setProperty('venom.year', str(item.get('year')))
					new_date = tools.Time.convert(stringTime=str(item.get('premiered', '')), formatInput='%Y-%m-%d', formatOutput='%m-%d-%Y', zoneFrom='utc', zoneTo='utc')
					listitem.setProperty('venom.premiered', new_date)
					season = str(item.get('season'))
					listitem.setProperty('venom.season', season)
					episode = str(item.get('episode'))
					listitem.setProperty('venom.episode', episode)
					label = '%s  -  %sx%s' % (tvshowtitle, season, episode.zfill(2))
					listitem.setProperty('venom.label', label)
					labelProgress = str(round(float(item['progress'] * 100), 1)) + '%'
					listitem.setProperty('venom.progress', '[' + labelProgress + ']')
					listitem.setProperty('venom.isSelected', '')
					listitem.setProperty('venom.imdb', item.get('imdb'))
					listitem.setProperty('venom.tvdb', item.get('tvdb'))
					listitem.setProperty('venom.rating', str(round(float(item.get('rating')), 1)))
					listitem.setProperty('venom.trailer', item.get('trailer'))
					listitem.setProperty('venom.studio', item.get('studio'))
					listitem.setProperty('venom.genre', str(item.get('genre', '')))
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