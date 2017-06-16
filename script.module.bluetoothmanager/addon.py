import xbmcaddon
import xbmcgui
import xbmc
import time
import subprocess
import shlex
import pexpect
import fileinput
from multiprocessing import Process

# Get global paths
addon       = xbmcaddon.Addon()
addonpath = addon.getAddonInfo('path').decode("utf-8")
addonname   = addon.getAddonInfo('name')
desktop = xbmcgui.Window(10000)

# Controls
BUTTON_FOCUS = 1201
BACK_BUTTON = 1202
SETTINGS_BUTTON = 1203
ON_BUTTON = 1204
OFF_BUTTON = 1205
CONNECT_BUTTON = 1206

# Properties
desktop.setProperty('bluetooth','')

# Definitions
ON = True
OFF = False

# Text
WARNING = "$ADDON[script.module.bluetoothmanager 30010]"
CONNECTION = "$ADDON[script.module.bluetoothmanager 30011]"

def replaceLine(filename, old_phrase, new_phrase, quantity):
	for line in fileinput.input(filename, inplace=True): 
      		print line.replace(old_phrase, new_phrase, quantity),
	
def setProperty(bluetooth):
	global desktop

	if bluetooth == ON:
		desktop.setProperty('bluetooth','true')
	elif bluetooth == OFF:
		desktop.setProperty('bluetooth','false')

def check_bluetooth():
	getstate = str.strip(subprocess.check_output("hcitool dev | grep hci0 | tail -n1", shell = True))
	
	if getstate != "":
		getstate = ON
    	else:
		getstate = OFF

    	return getstate

def check_settings():

	if bluetooth == ON:	

		if addon.getSetting('discoverable') == "true":
			run_command("sudo hciconfig hci0 piscan")
		else:
			run_command("sudo hciconfig hci0 noscan")
	
	if addon.getSetting('on_startup') == "true":
		replaceLine("/home/pi/Startup_Scripts/phrase.py", "\"block\"", "\"unblock\"", 1)
	else:
		replaceLine("/home/pi/Startup_Scripts/phrase.py", "\"unblock\"", "\"block\"", 1)
	

def run_command(command):
	process = subprocess.Popen(shlex.split(command), stdout = subprocess.PIPE)

        while True:
                output = process.stdout.readline()

                if output == '' and process.poll() is not None:
                        break

        rc = process.poll()
        return rc

class BluetoothctlError(Exception):
    	"""This exception is raised, when bluetoothctl fails to start."""
	pass

class Bluetoothctl():
	"""A wrapper for bluetoothctl utility."""

	def __init__(self, createChild):
		if createChild:
			self.child = pexpect.spawn('bluetoothctl', echo = False)

	def get_output(self, command, pause = 0):
		"""Run a command in bluetoothctl prompt, return output as a list of lines."""
		self.child.send(command + "\n")
		time.sleep(pause)
		start_failed = self.child.expect(["bluetooth", pexpect.EOF])

		if start_failed:
			raise BluetoothctlError("Bluetoothctl failed after running " + command)

		return self.child.before.split("\r\n")

	def wait_pairing(self):
		"""Reads output till device is paired."""
		while True:
			try:
				out = self.child.readline()
				parse = shlex.split(out)

				if len(parse) > 4:
					if (parse[3] == "Paired:" and parse[4] == "yes") or parse[3] == "Connected:":
						mac_address = parse[2]
						break
					
			except pexpect.TIMEOUT:
				pass
				
		return mac_address

	def trust_device(self, mac_address):
		"""Trust device."""
		try:
			out = self.get_output("trust " + mac_address, 2)
		except BluetoothctlError, e:
			print(e)
			return None

	def connect_device(self, mac_address):
        	"""Try to connect to a device by mac address."""
        	try:
            		out = self.get_output("connect " + mac_address, 2)
        	except BluetoothctlError, e:
            		print(e)
            		return None

	def pair_device(self):
		"""Pair device automatically."""
		self.child = pexpect.spawn('bluetoothctl', echo = False) # only for new process
		mac_address = self.wait_pairing()
		self.trust_device(mac_address)
		self.connect_device(mac_address)	


class MainClass(xbmcgui.WindowXMLDialog):
	bluetooth = OFF

    	def onAction(self, action):
    		pass
	
	def onInit(self):
		global bluetooth

		MainClass.buttonfocus = self.getControl(BUTTON_FOCUS)
		MainClass.button_back = self.getControl(BACK_BUTTON)
		MainClass.button_settings = self.getControl(SETTINGS_BUTTON)
		MainClass.button_on = self.getControl(ON_BUTTON)
		MainClass.button_off = self.getControl(OFF_BUTTON)
		MainClass.button_connect = self.getControl(CONNECT_BUTTON)
		bluetooth = check_bluetooth()
		setProperty(bluetooth)
		check_settings()

	def onClick(self, controlID):
		global bluetooth

		if controlID == BACK_BUTTON:
			time.sleep(0.3)
			self.close()
	
		if controlID == ON_BUTTON:
			self.setFocus(self.buttonfocus)

			if bluetooth == OFF:
				bluetooth = ON
				run_command("sudo rfkill unblock bluetooth")
				#run_command("sudo hcitool hci0 up")

				#if run_command("pulseaudio --check"):
				#	run_command("pulseaudio -D")

				setProperty(bluetooth)

		if controlID == OFF_BUTTON:
			self.setFocus(self.buttonfocus)

			if bluetooth == ON:
				bluetooth = OFF
				run_command("sudo rfkill block bluetooth")
				#run_command("sudo hcitool hci0 down")
				setProperty(bluetooth)

		if controlID == SETTINGS_BUTTON:
			addon.openSettings()
			check_settings()

		if controlID == CONNECT_BUTTON:
			
			if bluetooth == OFF:
				xbmcgui.Dialog().ok(WARNING, "$ADDON[script.module.bluetoothmanager 30004]")
			elif xbmcgui.Dialog().yesno(CONNECTION, "$ADDON[script.module.bluetoothmanager 30008]"):
				ctl = Bluetoothctl(False)
				p = Process(target = ctl.pair_device)
				p.start()
				run_command("sudo hciconfig hci0 piscan")

				while p.is_alive():
					if xbmcgui.Dialog().yesno(CONNECTION, "$ADDON[script.module.bluetoothmanager 30005]", yeslabel = "$ADDON[script.module.bluetoothmanager 30006]", nolabel = "$ADDON[script.module.bluetoothmanager 30007]"): # Abort
						break
					else:
						xbmcgui.Dialog().ok(WARNING, "$ADDON[script.module.bluetoothmanager 30009]")				
				p.terminate()
				run_command("sudo hciconfig hci0 noscan")
				del ctl

	def onFocus(self, controlID):
		pass

	def onControl(self, controlID):
        	pass

mydisplay = MainClass("bluetooth.xml", addonpath, 'default', '720')
mydisplay.doModal()
del mydisplay
