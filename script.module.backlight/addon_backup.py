import xbmcaddon
import xbmcgui
import xbmc
import time
from multiprocessing import Process, Lock

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

def get_Brightness():
	file = open(BACKLIGHT_FILE, 'r')

	for line in file:
		if line != "":
			return int(line)

def set_Brightness(brightness, lock):
	brightness *= 2.55
	brightness = int(round(brightness))

	if brightness < 30:
		brightness = 30

	lock.acquire()
	file = open(BACKLIGHT_FILE, 'w')
	file.write(str(brightness))
	file.close()
	time.sleep(0.1)
	lock.release()

class MainClass(xbmcgui.WindowXMLDialog):
	porcess = Process()
	lock = Lock()

	def onAction(self, action):
		pass
	
	def onInit(self):
		global process, lock

		MainClass.brightness_slider = self.getControl(BRIGHTNESS_SLIDER)
		MainClass.back_button = self.getControl(BACK_BUTTON)

		process = Process()
		lock = Lock()
		percentage = (float(get_Brightness()) / 255) * 100

		if percentage < 15:
			percentage = 0

		MainClass.brightness_slider.setPercent(percentage)

	def onClick(self, controlID):
		global process

		if controlID == BRIGHTNESS_SLIDER:
			try:
				if not process.is_alive():
					brightness = MainClass.brightness_slider.getPercent()
					process = Process(target = set_Brightness, args = (brightness, lock))
					process.start()			
			except:
				pass

		if controlID == BACK_BUTTON:
			time.sleep(0.3)
			self.close()

	def onFocus(self, controlID):
		pass

	def onControl(self, controlID):
		pass

mydisplay = MainClass("backlight.xml", addonpath, 'default', '720')
mydisplay.doModal()
del mydisplay