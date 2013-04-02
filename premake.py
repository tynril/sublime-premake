import sublime, sublime_plugin
import os
import subprocess
try:
	import json
except ImportError:
	import simplejson as json

class PremakeCommand(sublime_plugin.WindowCommand):
	"""Deal with premake build file generation."""

	def is_enabled(self):
		"""Check if the plugin is enabled in the current context."""
		return os.path.exists(self._get_premake_filepath())

	def run(self, operation):
		"""Called when operating the plugin."""
		if operation == "generate":
			self._run_premake(["gmake"])
		elif operation == "clean":
			self._run_premake(["clean"])
		elif operation == "select_configuration":
			self._select_configuration()
		elif operation == "make":
			self._run_make()
		elif operation == "run":
			print "Not yet implemented."
		else:
			raise RuntimeError("Unknown operation '" + operation + "'.")

	def _run_premake(self, args):
		"""Run the premake4 executable with the given arguments."""
		self.window.run_command("exec", {"cmd": ["premake4", "--file=" + self._get_premake_filepath()] + args})

	def _select_configuration(self):
		"""Provides the user with a list of available configurations."""

		# Ensure there's a makefile available.
		if not os.path.exists(os.path.join(os.path.dirname(self._get_premake_filepath()), "Makefile")):
			sublime.error_message("Please run 'Premake: Generate' prior to choosing a configuration.")
			return

		# Configure the startup infos to hide the console window on Windows.
		startupInfo = None
		if os.name == 'nt':
			startupInfo = subprocess.STARTUPINFO()
			startupInfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW

		# Run "make help" to get configurations list.
		proc = subprocess.Popen(["make", "help"], startupinfo = startupInfo, stderr = subprocess.STDOUT, stdout = subprocess.PIPE, cwd = os.path.dirname(self._get_premake_filepath()))
		retVal = proc.wait()
		if retVal != 0:
			raise RuntimeError("Unable to run make to get configurations list.")

		# Parse the result.
		self.configurations = []
		(out, _) = proc.communicate()
		inConf = False
		for line in out.splitlines():
			if line == "CONFIGURATIONS:":
				inConf = True
				continue
			if inConf:
				if line == "":
					inConf = False
					break
				self.configurations.append(line.strip())

		# Make the user choose.		
		self.window.show_quick_panel(self.configurations, self.__configuration_selected)

	def __configuration_selected(self, configurationIndex):
		"""Called when the user has chosen a configuration."""
		if configurationIndex == -1:
			self.configurations = None
			self.configuration = None
			return

		# Store the configuration to build in memory.
		self.configuration = self.configurations[configurationIndex]
		self.configurations = None

		# Sets the configuration setting in memory as well.
		if len(self.window.views()) > 0:
			projectSettings = self.window.views()[0].settings()
			projectSettings.set("premake_configuration", self.configuration)

		# Look for a project settings file.
		filesList = os.listdir(self.window.folders()[0])
		projFileFound = False
		for projFile in filesList:
			if projFile[-16:] == ".sublime-project":
				projFileFound = True
				break

		# If there's no project file, no way to save the configuration.
		if not projFileFound:
			return
		# Otherwise, let's load it...
		projFilePath = os.path.join(self.window.folders()[0], projFile)
		projFileDesc = open(projFilePath, 'r')
		projJson = json.load(projFileDesc)
		projFileDesc.close()

		# Then update it...
		if 'settings' not in projJson:
			projJson['settings'] = {}
		projJson['settings']['premake_configuration'] = self.configuration

		# And then dump it.
		projFileDesc = open(projFilePath, 'w')
		json.dump(projJson, projFileDesc, indent = 4)
		projFileDesc.close()

	def __load_configuration(self):
		"""Loads the configuration to make from the project file."""
		if len(self.window.views()) > 0:
			projectSettings = self.window.views()[0].settings()
			if projectSettings.has("premake_configuration"):
				self.configuration = projectSettings.get("premake_configuration")

	def _run_make(self):
		"""Run GNU make to build the project."""

		# Loads the configuration.
		self.__load_configuration()

		# Run make on the given configuration, if there's one.
		command = ["make"]
		if self.configuration:
			command += ["config=" + self.configuration]

		self.window.run_command("exec", {"cmd": command, "working_dir": os.path.dirname(self._get_premake_filepath())})

	def _get_premake_filepath(self):
		"""Find the absolute path to the premake build file (not guaranteed to exist)."""
		premakeFile = None

		# If there's at least one view, we can get the settings for the project.
		if len(self.window.views()) > 0:
			projectSettings = self.window.views()[0].settings()
			if projectSettings.has("premake_file"):
				premakeFile = projectSettings.get("premake_file")

		# If we don't have it yet, we load it from the default file.
		if not premakeFile:
			premakeSettings = sublime.load_settings("Premake.sublime-settings")
			premakeFile = premakeSettings.get("premake_file")

		# The name should be defined here, otherwise the default config is screwed.
		if not premakeFile:
			raise RuntimeError("Unable to get 'premake_file' from the settings.")

		# Convert the path to an absolute path, if necessary.
		if not os.path.isabs(premakeFile):
			premakeFile = os.path.abspath(os.path.join(self.window.folders()[0], premakeFile))

		return premakeFile