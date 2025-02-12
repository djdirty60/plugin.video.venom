# -*- coding: utf-8 -*-
"""
	Venom Add-on
"""

from json import dumps as jsdumps
try: #Py2
	from urllib import quote_plus
except ImportError: #Py3
	from urllib.parse import quote_plus
from resources.lib.modules.control import joinPath, transPath, dialog
from resources.lib.modules.source_utils import getFileType
from resources.lib.windows.base import BaseDialog

class SourceResultsXML(BaseDialog):
	def __init__(self, *args, **kwargs):
		super(SourceResultsXML, self).__init__(self, args)
		self.window_id = 2000
		self.results = kwargs.get('results')
		self.total_results = str(len(self.results))
		self.meta = kwargs.get('meta')
		self.info = None
		self.cm = None
		self.make_items()
		self.set_properties()

	def onInit(self):
		super(SourceResultsXML, self).onInit()
		win = self.getControl(self.window_id)
		win.addItems(self.item_list)
		self.setFocusId(self.window_id)

	def run(self):
		self.doModal()
		try: del self.info
		except: pass
		try: del self.cm
		except: pass
		return self.selected

	def onAction(self, action):
		try:
			action_id = action.getId()
			if action_id in self.info_actions:
				chosen_source = self.item_list[self.get_position(self.window_id)]
				chosen_source = chosen_source.getProperty('venom.source_dict')
				syssource = quote_plus(chosen_source)
				self.execute_code('RunPlugin(plugin://plugin.video.venom/?action=sourceInfo&source=%s)' % syssource)
			if action_id in self.selection_actions:
				chosen_source = self.item_list[self.get_position(self.window_id)]
				source = chosen_source.getProperty('venom.source')
				if 'UNCACHED' in source:
					debrid = chosen_source.getProperty('venom.debrid')
					source_dict = chosen_source.getProperty('venom.source_dict')
					link_type = 'pack' if 'package' in source_dict else 'single'
					sysname = quote_plus(self.meta.get('title'))
					if 'tvshowtitle' in self.meta and 'season' in self.meta and 'episode' in self.meta:
						poster = self.meta.get('season_poster') or self.meta.get('poster')
						sysname += quote_plus(' S%02dE%02d' % (int(self.meta['season']), int(self.meta['episode'])))
					elif 'year' in self.meta: sysname += quote_plus(' (%s)' % self.meta['year'])
					try: new_sysname = quote_plus(chosen_source.getProperty('venom.name'))
					except: new_sysname = sysname
					self.execute_code('RunPlugin(plugin://plugin.video.venom/?action=cacheTorrent&caller=%s&type=%s&title=%s&items=%s&url=%s&source=%s&meta=%s)' %
											(debrid, link_type, sysname, quote_plus(jsdumps(self.results)), quote_plus(chosen_source.getProperty('venom.url')), quote_plus(source_dict), quote_plus(jsdumps(self.meta))))
					self.selected = (None, '')
				else:
					self.selected = ('play_Item', chosen_source)
				return self.close()
			elif action_id in self.context_actions:
				chosen_source = self.item_list[self.get_position(self.window_id)]
				source_dict = chosen_source.getProperty('venom.source_dict')
				cm_list = [('[B]Additional Link Info[/B]', 'sourceInfo')]
				if 'cached (pack)' in source_dict:
					cm_list += [('[B]Browse Debrid Pack[/B]', 'showDebridPack')]
				source = chosen_source.getProperty('venom.source')
				if not 'uncached' in source:
					cm_list += [('[B]Download[/B]', 'download')]

				chosen_cm_item = dialog.contextmenu([i[0] for i in cm_list])
				if chosen_cm_item == -1: return

				cm_action = cm_list[chosen_cm_item][1]
				if cm_action == 'sourceInfo':
					self.execute_code('RunPlugin(plugin://plugin.video.venom/?action=sourceInfo&source=%s)' % quote_plus(source_dict))
				elif cm_action == 'showDebridPack':
					debrid = chosen_source.getProperty('venom.debrid')
					name = chosen_source.getProperty('venom.name')
					hash = chosen_source.getProperty('venom.hash')
					self.execute_code('RunPlugin(plugin://plugin.video.venom/?action=showDebridPack&caller=%s&name=%s&url=%s&source=%s)' %
									(quote_plus(debrid), quote_plus(name), quote_plus(chosen_source.getProperty('venom.url')), quote_plus(hash)))
				elif cm_action == 'download':
					sysname = quote_plus(self.meta.get('title'))
					poster = self.meta.get('poster', '')
					if 'tvshowtitle' in self.meta and 'season' in self.meta and 'episode' in self.meta:
						poster = self.meta.get('season_poster') or self.meta.get('poster')
						sysname += quote_plus(' S%02dE%02d' % (int(self.meta['season']), int(self.meta['episode'])))
					elif 'year' in self.meta: sysname += quote_plus(' (%s)' % self.meta['year'])
					try: new_sysname = quote_plus(chosen_source.getProperty('venom.name'))
					except: new_sysname = sysname
					self.execute_code('RunPlugin(plugin://plugin.video.venom/?action=download&name=%s&image=%s&source=%s&caller=sources&title=%s)' %
										(new_sysname, quote_plus(poster), quote_plus(source_dict), sysname))
			elif action in self.closing_actions:
				self.selected = (None, '')
				self.close()
		except:
			from resources.lib.modules import log_utils
			log_utils.error()

	def get_quality_iconPath(self, quality):
		try:
			return joinPath(transPath('special://home/addons/plugin.video.venom/resources/skins/Default/media/resolution'), '%s.png' % quality)
		except:
			from resources.lib.modules import log_utils
			log_utils.error()

	def debrid_abv(self, debrid):
		try:
			d_dict = {'AllDebrid': 'AD', 'Premiumize.me': 'PM', 'Real-Debrid': 'RD'}
			d = d_dict[debrid]
		except:
			from resources.lib.modules import log_utils
			log_utils.error()
			d = ''
		return d

	def make_items(self):
		def builder():
			for count, item in enumerate(self.results, 1):
				try:
					listitem = self.make_listitem()
					quality = item.get('quality', 'SD')
					quality_icon = self.get_quality_iconPath(quality)
					extra_info = item.get('info')
					try:
						size_label = extra_info.split('|', 1)[0]
						if any(value in size_label for value in ['HEVC', '3D']): size_label = ''
					except: size_label = ''

					try: f = ' / '.join(['%s' % info.strip() for info in extra_info.split('|')])
					except: f = ''
					if 'name_info' in item: t = getFileType(name_info=item.get('name_info'))
					else: t = getFileType(url=item.get('url'))
					t = '%s /%s' % (f, t) if (f != '' and f != '0 ' and f != ' ') else t
					if t == '': t = getFileType(url=item.get('url'))
					extra_info = t

					listitem.setProperty('venom.source_dict', jsdumps([item]))
					listitem.setProperty('venom.debrid', self.debrid_abv(item.get('debrid')))
					listitem.setProperty('venom.provider', item.get('provider').upper())
					listitem.setProperty('venom.source', item.get('source').upper())
					listitem.setProperty('venom.seeders', str(item.get('seeders')))
					listitem.setProperty('venom.hash', item.get('hash', 'N/A'))
					listitem.setProperty('venom.name', item.get('name'))
					listitem.setProperty('venom.quality', quality.upper())
					listitem.setProperty('venom.quality_icon', quality_icon)
					listitem.setProperty('venom.url', item.get('url'))
					listitem.setProperty('venom.extra_info', extra_info)
					listitem.setProperty('venom.size_label', size_label)
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
			if self.meta is None: return
			self.setProperty('venom.mediatype', self.meta.get('mediatype', ''))
			self.setProperty('venom.season', str(self.meta.get('season', '')))
			if self.meta.get('season_poster'):	self.setProperty('venom.poster', self.meta.get('season_poster', ''))
			else: self.setProperty('venom.poster', self.meta.get('poster', ''))
			# self.setProperty('venom.fanart', self.meta.get('fanart', ''))
			# self.setProperty('venom.clearart', self.meta.get('clearart', ''))
			self.setProperty('venom.clearlogo', self.meta.get('clearlogo', ''))
			self.setProperty('venom.plot', self.meta.get('plot', ''))
			self.setProperty('venom.year', str(self.meta.get('year', '')))
			self.setProperty('venom.premiered', str(self.meta.get('premiered', '')))
			if self.meta.get('mpaa'): self.setProperty('venom.mpaa', self.meta.get('mpaa'))
			else: self.setProperty('venom.mpaa', 'NA ')
			if self.meta.get('duration'):
				duration = int(self.meta.get('duration')) / 60
				self.setProperty('venom.duration', str(int(duration)))
			else: self.setProperty('venom.duration', 'NA ')
			self.setProperty('venom.total_results', self.total_results)
		except:
			from resources.lib.modules import log_utils
			log_utils.error()