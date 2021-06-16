# -*- coding: utf-8 -*-
# created by Venom (6-13-2021)
"""
	Venom Add-on
"""

import re
try: #Py2
	from urlparse import parse_qs
	from urllib import urlencode
except ImportError: #Py3
	from urllib.parse import parse_qs, urlencode
from resources.lib.debrid import alldebrid
from resources.lib.modules.source_utils import supported_video_extensions
from resources.lib.cloud_scrapers import cloud_utils
from fenomscrapers.modules import source_utils as fs_utils


class source:
	def __init__(self):
		self.priority = 1
		self.language = ['en']

	def movie(self, imdb, title, aliases, year):
		try:
			url = {'imdb': imdb, 'title': title, 'aliases': aliases, 'year': year}
			url = urlencode(url)
			return url
		except:
			return

	def tvshow(self, imdb, tvdb, tvshowtitle, aliases, year):
		try:
			url = {'imdb': imdb, 'tvdb': tvdb, 'tvshowtitle': tvshowtitle, 'aliases': aliases, 'year': year}
			url = urlencode(url)
			return url
		except:
			return

	def episode(self, url, imdb, tvdb, title, premiered, season, episode):
		try:
			if not url: return
			url = parse_qs(url)
			url = dict([(i, url[i][0]) if url[i] else (i, '') for i in url])
			url['title'], url['premiered'], url['season'], url['episode'] = title, premiered, season, episode
			url = urlencode(url)
			return url
		except:
			return

	def sources(self, url, hostDict):
		sources = []
		if not url: return sources
		try:
			data = parse_qs(url)
			data = dict([(i, data[i][0]) if data[i] else (i, '') for i in data])

			title = data['tvshowtitle'] if 'tvshowtitle' in data else data['title']
			title = title.replace('&', 'and').replace('Special Victims Unit', 'SVU')
			aliases = data['aliases']
			episode_title = data['title'] if 'tvshowtitle' in data else None
			self.year = data['year']
			hdlr = 'S%02dE%02d' % (int(data['season']), int(data['episode'])) if 'tvshowtitle' in data else self.year

			self.season = str(data['season']) if 'tvshowtitle' in data else None
			self.episode = str(data['episode']) if 'tvshowtitle' in data else None
			query_list = self.episode_query_list() if 'tvshowtitle' in data else self.year_query_list()
			# log_utils.log('query_list = %s' % query_list)
			cloud_folders = alldebrid.AllDebrid().user_cloud()['magnets']
			cloud_folders = [i for i in cloud_folders if i['statusCode'] == 4]
			if not cloud_folders: return sources
		except:
			from resources.lib.modules import log_utils
			log_utils.error('AD_CLOUD: ')
			return sources

		extras_filter = cloud_utils.extras_filter()
		for folder in cloud_folders:
			try:
				folder_name = folder.get('filename')
				if not cloud_utils.cloud_check_title(title, aliases, folder_name): continue
				files = folder.get('links', '')
				files = [i for i in files if i['filename'].lower().endswith(tuple(supported_video_extensions()))]
				if not files: continue
			except:
				from resources.lib.modules import log_utils
				log_utils.error('AD_CLOUD: ')
				return sources

			for file in files:
				try:
					name = file.get('filename', '')
					path = folder.get('filename', '').lower()
					rt = cloud_utils.release_title_format(name)
					if any(value in rt for value in extras_filter): continue
					if all(not bool(re.search(i, rt)) for i in query_list):
						if 'tvshowtitle' in data:
							season_folder_list = self.season_folder_list()
							if all(not bool(re.search(i, path)) for i in season_folder_list): continue
							episode_list = self.episode_list()
							if all(not bool(re.search(i, rt)) for i in episode_list): continue
						else: continue

					name_info = fs_utils.info_from_name(name, title, self.year, hdlr, episode_title)
					link = file.get('link', '')
					hash = folder.get('hash', '')
					seeders = folder.get('seeders', '')
					quality, info = fs_utils.get_release_quality(name_info, name)
					try:
						dsize, isize = fs_utils.convert_size(file['size'], to='GB')
						info.insert(0, isize)
					except: dsize = 0
					info = ' | '.join(info)

					sources.append({'provider': 'ad_cloud', 'source': 'cloud', 'debrid': 'AllDebrid', 'seeders': seeders, 'hash': hash, 'name': name, 'name_info': name_info,
												'quality': quality, 'language': 'en', 'url': link, 'info': info, 'direct': True, 'debridonly': True, 'size': dsize})
				except:
					from resources.lib.modules import log_utils
					log_utils.error('AD_CLOUD: ')
					return sources
		return sources

	def year_query_list(self):
		return [str(self.year), str(int(self.year)+1), str(int(self.year)-1)]

	def episode_query_list(self):
		return [
				'[.-]%d[.-]%02d[.-]' % (int(self.season), int(self.episode)),
				'[.-]%02d[.-]%02d[.-]' % (int(self.season), int(self.episode)),
				'[.-]%dx%02d[.-]' % (int(self.season), int(self.episode)),
				'[.-]%02dx%02d[.-]' % (int(self.season), int(self.episode)),
				's%de%02d' % (int(self.season), int(self.episode)),
				's%02de%02d' % (int(self.season), int(self.episode)),
				'season%depisode%d' % (int(self.season), int(self.episode)),
				'season%depisode%02d' % (int(self.season), int(self.episode)),
				'season%02depisode%02d' % (int(self.season), int(self.episode))]

	def season_folder_list(self):
		return [
				r'[.-]s\s?%d[/]' % int(self.season),
				r'[.-]s\s?%02d[/]' % int(self.season),
				r'season\s?%d[/]' % int(self.season),
				r'season\s?%02d[/]' % int(self.season)]

	def episode_list(self):
		return [
				'[.-]e%d[.-]' % int(self.episode),
				'[.-]e%02d[.-]' % int(self.episode),
				'[.-]ep%d[.-]' % int(self.episode),
				'[.-]ep%02d[.-]' % int(self.episode),
				'episode[.-]?%d[.-]' % int(self.episode),
				'episode[.-]?%02d[.-]' % int(self.episode)]

	def resolve(self, url):
		try:
			url = alldebrid.AllDebrid().unrestrict_link(url)
			return url
		except:
			from resources.lib.modules import log_utils
			log_utils.error('AD_CLOUD: ')
			return None