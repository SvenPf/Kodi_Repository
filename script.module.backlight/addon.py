import xbmcaddon
import xbmcgui
import xbmc
import time
from threading import Thread

# Get global paths
addon       = xbmcaddon.Addon()
addonpath = addon.getAddonInfo('path').decode("utf-8")
addonname   = addon.getAddonInfo('name')
desktop = xbmcgui.Window(10000)

# Controls
BRIGHTNESS_SLIDER = 1201
BACK_BUTTON = 1202

# Definitions
BACKLIGHT_FILE = '/sys/class/backlight/rpi_backlight/brightness'
MIN_BRIGHTNESS = 10		#minimum 0 (screen off)
MAX_BRIGHTNESS = 255	#maximum 255
BRIGHTNESS_SCALE = 2.45 #for max:255 min:10
brightness = 0			#in percent
windowopen = False

def check_setting():
	global MIN_BRIGHTNESS, MAX_BRIGHTNESS, BRIGHTNESS_SCALE
	changed = False

	MIN_BRIGHTNESS = int(addon.getSetting('min_brightness'))
	MAX_BRIGHTNESS = int(addon.getSetting('max_brightness'))

	if MIN_BRIGHTNESS > 255:
		MIN_BRIGHTNESS = 255
		changed = True
	elif MIN_BRIGHTNESS < 10:
		MIN_BRIGHTNESS = 10
		changed = True

	if MAX_BRIGHTNESS > 255:
		MAX_BRIGHTNESS = 255
		changed = True
	elif MAX_BRIGHTNESS < 10:
		MAX_BRIGHTNESS = 10
		changed = True

	if MIN_BRIGHTNESS > MAX_BRIGHTNESS:
		tmp = MIN_BRIGHTNESS
		MIN_BRIGHTNESS = MAX_BRIGHTNESS
		MAX_BRIGHTNESS = temp
		changed = True
	elif MIN_BRIGHTNESS == MAX_BRIGHTNESS:
		MIN_BRIGHTNESS = MAX_BRIGHTNESS - 1
		changed = True

	if changed:
		addon.setSetting('min_brightness', str(MIN_BRIGHTNESS))
		addon.setSetting('max_brightness', str(MAX_BRIGHTNESS))

	BRIGHTNESS_SCALE = float(MAX_BRIGHTNESS - MIN_BRIGHTNESS) / 100
	
def get_Brightness():
	file = open(BACKLIGHT_FILE, 'r')

	for line in file:
		if line != "":
			return int(line)

def check_Brightness():
	global brightness, windowopen

	while not windowopen:			#wait for window initialization
		time.sleep(0.5)

	brightness_old = brightness		#get first initialization of brightness

	while windowopen:
		brightness_current = brightness

		if brightness_current != brightness_old:
			brightness_file = int(round(brightness_current * BRIGHTNESS_SCALE + MIN_BRIGHTNESS))

			file = open(BACKLIGHT_FILE, 'w')
			file.write(str(brightness_file))
			file.close()

			brightness_old = brightness_current
		else:
			time.sleep(0.2)

		time.sleep(0.1)

class MainClass(xbmcgui.WindowXMLDialog):

	def onAction(self, action):
		pass
	
	def onInit(self):
		global brightness, windowopen

		check_setting()
		
		MainClass.brightness_slider = self.getControl(BRIGHTNESS_SLIDER)
		MainClass.back_button = self.getControl(BACK_BUTTON)

		brightness = float(get_Brightness() - MIN_BRIGHTNESS) / BRIGHTNESS_SCALE

		MainClass.brightness_slider.setPercent(brightness)
		windowopen = True

	def onClick(self, controlID):
		global brightness, windowopen

		if controlID == BRIGHTNESS_SLIDER:
			brightness = MainClass.brightness_slider.getPercent()

		if controlID == BACK_BUTTON:
			windowopen = False
			time.sleep(0.3)
			self.close()

	def onFocus(self, controlID):
		pass

	def onControl(self, controlID):
		pass


mydisplay = MainClass("backlight.xml", addonpath, 'default', '720')

t1 = Thread(target = check_Brightness)
t1.setDaemon(True)
t1.start()

mydisplay.doModal()
del mydisplay