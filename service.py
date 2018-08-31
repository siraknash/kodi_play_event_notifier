#!/usr/bin/python
# -*- coding: utf-8 -*-

#//////////////////////////////////////////////////////////////////////////
#/ This program is free software: you can redistribute it and/or modify
#/ it under the terms of the GNU General Public License as published by
#/ the Free Software Foundation, either version 3 of the License, or
#/ (at your option) any later version.
#/ 
#/ This program is distributed in the hope that it will be useful,
#/ but WITHOUT ANY WARRANTY; without even the implied warranty of
#/ MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#/ GNU General Public License for more details.
#/ 
#/ You should have received a copy of the GNU General Public License
#/ along with this program.  If not, see <https://www.gnu.org/licenses/>.
#//////////////////////////////////////////////////////////////////////////

import xbmc
import xbmcaddon
import socket


PEVT_HOST_NAME = 'localhost'
PEVT_HOST_PORT = 9595

PEVT_ADDON_NAME = xbmcaddon.Addon().getAddonInfo('name')


def _log(log_txt):
	lt = '%s: %s' % (PEVT_ADDON_NAME, log_txt)
	xbmc.log(msg = lt, level = xbmc.LOGNOTICE)


#
# Main Class
#
class PlayEventNotifier:
	def __init__(self):
		try:
			addr = socket.gethostbyname(PEVT_HOST_NAME)

		except socket.gaierror, err:
			_log('Cannot resolve hostname: [%s]' % PEVT_HOST_NAME)
			return

		port = PEVT_HOST_PORT

		_log('Using host [%s:%i]' % (addr, port))
		self.Player = PlayEventHandler(addr = addr, port = port)
		self._daemon()

	def _daemon(self):
		# Loop until request to terminate
		while not xbmc.Monitor().abortRequested():
			self.Player._update()

			if xbmc.Monitor().waitForAbort(0.75):
				break

#
# Derived from xbmc.Player, handles player events
#
class PlayEventHandler(xbmc.Player):
	STATE_STOPPED = '.'
	STATE_PLAYING = '>'
	STATE_PAUSED = ','

	def __init__(self, addr, port):
		self._sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
		self._addr = addr
		self._port = port

		xbmc.Player.__init__(self)

		self._state = self.STATE_STOPPED
		self._file_name = ""
		self._file_time = 0.0

		# A file is playing, initialize file name and file time
		if xbmc.getCondVisibility('Player.HasMedia'):
			self._file_name = self.getPlayingFile()
			self._file_time = self.getTime()

			# Determine current playing/paused state
			if xbmc.getCondVisibility('Player.Playing'):
				self._state = self.STATE_PLAYING
			else:
				self._state = self.STATE_PAUSED

		self._update()

	def _update(self):
		self._file_name = self.getPlayingFile()
		self._file_time = self.getTime()

		# Message format: "<state>|<file_time_seconds>|<file_name>|"
		msg = str(self._state) + '|' +  str(self._file_time) + '|' + str(self._file_name) + '|'
		self._send_message(msg)

	def onPlayBackStarted(self):
		self._state = self.STATE_PLAYING
		self._update()
		_log('onPlayBackStarted: file [%s]  time: [%f]' % (self._file_name, self._file_time))

	def onPlayBackResume(self):
		# Resume from pause, treat just a play start
		self.onPlayBackStarted()

	def onPlayBackStopped(self):
		self._state == self.STATE_STOPPED
		self._update()
		_log('onPlayBackStopped')

	def onPlayBackEnded(self):
		# Same as playback stopped
		self.onPlayBackStopped()

	def onPlayBackSeek(self, time, offset):
		# Treat seek as just a time update
		self._update()
		_log('onPlayBackSeek: file [%s]  time: [%f]' % (self._file_name, self._file_time))

	def onPlayBackSeekChapter(self, chapter):
		# Same as normal seek
		self._onPlayBackSeek()

	def onPlayBackPaused(self):
		self._state = self.STATE_PAUSED
		self._update()
		_log('onPlayBackPaused: file [%s]  time: [%f]' % (self._file_name, self._file_time))

	def onPlayBackSpeedChanged(self, speed):
		# Treat non-1x speed as paused, 1x speed as resumed
		if speed == 1:
			self.onPlayBackResume()
		else:
			self.onPlayBackPaused()

	#
	# Messaage sender
	#
	def _send_message(self, msg):
		self._sock.sendto(msg, (self._addr, self._port))

#######################################

_log('Service started.')
PlayEventNotifier()
_log('Service terminating.')

#######################################

