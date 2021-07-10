# -*- coding: utf-8 -*-
"""
	Venom Add-on
"""

from datetime import datetime
import inspect
import unicodedata
import xbmc
from resources.lib.modules.control import transPath, setting as getSetting, lang, joinPath, existsPath
from resources.lib.modules import py_tools

LOGDEBUG = xbmc.LOGDEBUG #(0 in 19)  only prints when venom logging set to "Debug"
# ###--from here down methods print when Venom logging set to "Normal".
LOGINFO = xbmc.LOGINFO # (1 in 19)
LOGWARNING = xbmc.LOGWARNING # (2 in 19)
LOGERROR = xbmc.LOGERROR # (3 in 19)
LOGFATAL = xbmc.LOGFATAL # (4 in 19)
LOGNONE = xbmc.LOGNONE # (5 in 19)-not used but listed for int value

debug_list = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'FATAL']
DEBUGPREFIX = '[COLOR red][ Venom: %s ][/COLOR]'
LOGPATH = transPath('special://logpath/')


def log(msg, caller=None, level=LOGINFO):
	debug_enabled = getSetting('debug.enabled') == 'true'
	if not debug_enabled: return
	debug_level = getSetting('debug.level')
	if level == LOGDEBUG and debug_level != '1': return
	debug_location = getSetting('debug.location')
	if isinstance(msg, int): msg = lang(msg) # for strings.po translations
	try:
		if not msg.isprintable(): # ex. "\n" is not a printable character so returns False on those cases
			msg = '%s (NORMALIZED by log_utils.log())' % normalize(msg)
		if isinstance(msg, bytes):
			msg = '%s (ENCODED by log_utils.log())' % (py_tools.ensure_str(msg, errors='replace'))

		if caller is not None and level != LOGERROR:
			func = inspect.currentframe().f_back.f_code
			line_number = inspect.currentframe().f_back.f_lineno
			caller = "%s.%s()" % (caller, func.co_name)
			msg = 'From func name: %s Line # :%s\n                       msg : %s' % (caller, line_number, msg)
		elif caller is not None and level == LOGERROR:
			msg = 'From func name: %s.%s() Line # :%s\n                       msg : %s' % (caller[0], caller[1], caller[2], msg)

		if debug_location == '1':
			log_file = joinPath(LOGPATH, 'venom.log')
			if not existsPath(log_file):
				f = open(log_file, 'w')
				f.close()
			with open(log_file, 'a', encoding='utf-8') as f:
				line = '[%s %s] %s: %s' % (datetime.now().date(), str(datetime.now().time())[:8], DEBUGPREFIX % debug_list[level], msg)
				f.write(line.rstrip('\r\n') + '\n')
				# f.writelines([line1, line2]) ## maybe an option for the 2 lines without using "\n"
		else:
			xbmc.log('%s: %s' % (DEBUGPREFIX % debug_list[level], msg), level)
	except Exception as e:
		import traceback
		traceback.print_exc()
		xbmc.log('[ plugin.video.venom ] log_utils.log() Logging Failure: %s' % (e), LOGERROR)

def error(message=None, exception=True):
	try:
		import sys
		if exception:
			type, value, traceback = sys.exc_info()
			addon = 'plugin.video.venom'
			filename = (traceback.tb_frame.f_code.co_filename)
			filename = filename.split(addon)[1]
			name = traceback.tb_frame.f_code.co_name
			linenumber = traceback.tb_lineno
			errortype = type.__name__
			errormessage = value or value.message
			if str(errormessage) == '': return
			if message: message += ' -> '
			else: message = ''
			message += str(errortype) + ' -> ' + str(errormessage)
			caller = [filename, name, linenumber]
		else:
			caller = None
		del(type, value, traceback) # So we don't leave our local labels/objects dangling
		log(msg=message, caller=caller, level=LOGERROR)
	except Exception as e:
		xbmc.log('[ plugin.video.venom ] log_utils.error() Logging Failure: %s' % (e), LOGERROR)

def normalize(title):
	try:

		xbmc.log('[ plugin.video.venom ] type(title)=%s' % type(title), 1)

		return ''.join(c for c in unicodedata.normalize('NFKD', py_tools.ensure_text(py_tools.ensure_str(title))) if unicodedata.category(c) != 'Mn')
		# return unicodedata.normalize('NFKC', title) # from TMDb Helper
		# return ''.join(c for c in unicodedata.normalize('NFD', title) if unicodedata.category(c) != 'Mn')
		# return u''.join(c for c in unicodedata.normalize('NFKD', ensure_text(title)) if c in printable)

	except:
		error()
		return title