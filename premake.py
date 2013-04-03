import sublime, sublime_plugin
import os, re, subprocess, thread, functools
try:
	import json
except ImportError:
	import simplejson as json
execcmd = __import__("exec")

class PremakeCommand(sublime_plugin.WindowCommand):
	"""Deal with premake build file generation."""

	def is_enabled(self):
		"""Check if the plugin is enabled in the current context."""
		return self._get_project_folder() is not None and os.path.exists(self._get_premake_filepath())

	def run(self, operation):
		"""Called when operating the plugin."""
		# Checking if the project is enabled.
		if not self.is_enabled():
			sublime.error_message("Sorry!\nThe Premake plugin needs a project and a premake file to be used.\n")
			self._print_help()
			return

		# Setting the output view.
		self.output_view = self.window.get_output_panel("exec")

		# Processing the operation.
		if operation == "generate":
			self._run_premake(["gmake"])
		elif operation == "clean":
			self._run_premake(["clean"])
		elif operation == "select_configuration":
			self._select_configuration()
		elif operation == "make":
			self._run_make()
		elif operation == "select_run_target":
			self._select_run_target()
		elif operation == "run":
			self._run_executable()
		elif operation == "make_and_run":
			self._run_make(wait = True)
		else:
			raise RuntimeError("Unknown operation '" + operation + "'.")

	def _run_premake(self, args):
		"""Run the premake4 executable with the given arguments."""
		self.window.run_command("exec", {"cmd": ["premake4", "--file=" + self._get_premake_filepath()] + args})

	def _run_make(self, wait = False):
		"""Run GNU make to build the project."""

		sublime.status_message("Running make...")

		# Run make on the given configuration, if there's one.
		command = ["make"]
		configuration = self._get_project_setting("premake_configuration")
		if configuration:
			command += ["config=" + configuration]

		# Use the standard command if we shouldn't wait for the result.
		if not wait:
			self.window.run_command("exec", {"cmd": command, "working_dir": os.path.dirname(self._get_premake_filepath())})
			return

		# Otherwise, run it and wait on it.
		startupInfo = None
		if os.name == 'nt':
			startupInfo = subprocess.STARTUPINFO()
			startupInfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW

		# Run the make subprocess.
		self.makeProc = subprocess.Popen(command, startupinfo = startupInfo, stderr = subprocess.STDOUT, stdout = subprocess.PIPE, cwd = os.path.dirname(self._get_premake_filepath()))

		# Starts a thread to read the standard output.
		if self.makeProc.stdout:
			thread.start_new_thread(self._read_make_stdout, ())

	def _read_make_stdout(self):
		while True:
			data = os.read(self.makeProc.stdout.fileno(), 2**15)

			if data != "":
				sublime.set_timeout(functools.partial(self._append_make_data, data), 0)
			else:
				self.makeProc.stdout.close()
				sublime.set_timeout(functools.partial(self._make_completed), 10)
				break

	def _append_make_data(self, data):
		# Decode the data.
		try:
			str = data.decode("utf-8")
		except:
			str = "[Decode error - output not utf-8]\n"

		# Normalize newlines, Sublime Text always uses a single \n separator
		# in memory.
		str = str.replace('\r\n', '\n').replace('\r', '\n')

		# Show the panel if necessary.
		show_panel_on_build = sublime.load_settings("Preferences.sublime-settings").get("show_panel_on_build", True)
		if show_panel_on_build:
			self.window.run_command("show_panel", {"panel": "output.exec"})

		# Append the text at the end of the view.
		selection_was_at_end = (len(self.output_view.sel()) == 1
			and self.output_view.sel()[0]
				== sublime.Region(self.output_view.size()))
		self.output_view.set_read_only(False)
		edit = self.output_view.begin_edit()
		self.output_view.insert(edit, self.output_view.size(), str)
		if selection_was_at_end:
			self.output_view.show(self.output_view.size())
		self.output_view.end_edit(edit)
		self.output_view.set_read_only(True)

	def _make_completed(self):
		"""Called when the 'make' process has finished running."""

		# Getting the exit code.
		exitCode = self.makeProc.poll()
		self.makeProc = None

		# Running the executable if the build succeeded.
		if exitCode == 0:
			self._run_executable()

	def _run_executable(self):
		"""Run the executable that was built during the last build."""

		# Get the run target.
		self._load_configurations_and_projects()
		runTarget = self._get_project_setting("premake_run_target")

		# If there's none, let's ask the user to select one.
		if not runTarget:
			self.run_target_after_select = True
			self._select_run_target()
		else:
			# Otherwise, let's run it!
			self._run_target(runTarget)

	def _select_run_target(self):
		"""Provides the user with a list of available runnable targets."""
		# Load the data.
		self._load_configurations_and_projects()

		# List all executable targets.
		executablesInfo = []
		for t in self.targets:
			targetInfo = self.target[t]
			if targetInfo['is_executable']:
				executablesInfo.append(targetInfo)

		# Ask the user about those targets.
		self.run_target_candidates = [i['name'] for i in executablesInfo]
		self.window.show_quick_panel(self.run_target_candidates, self._run_target_selected)

	def _run_target_selected(self, runTargetIndex):
		"""Called when the user has chosen a target to run."""
		if runTargetIndex == -1:
			self.run_target_candidates = None
			return

		# We know our build target!
		runTarget = self.run_target_candidates[runTargetIndex]
		self.run_target_candidates = None

		# Updates the project file (if possible).
		self._set_project_setting("premake_run_target", runTarget)

		# Run it if necessary.
		if hasattr(self, 'run_target_after_select') and self.run_target_after_select:
			self.run_target_after_select = False
			self._run_target(runTarget)

	def _run_target(self, target):
		"""Run the given target executable."""
		sublime.status_message("Running target...")
		configuration = self._get_project_setting("premake_configuration")
		execPath = os.path.abspath(os.path.join(os.path.dirname(self._get_premake_filepath()), self.target[target][configuration]['target']))
		self.window.run_command("exec", {"cmd": [execPath]})

	def _select_configuration(self):
		"""Provides the user with a list of available configurations."""

		# Load the underlying data.
		self._load_configurations_and_projects()

		# Make the user choose.		
		self.window.show_quick_panel(self.configurations, self._configuration_selected)

	def _configuration_selected(self, configurationIndex):
		"""Called when the user has chosen a configuration."""
		if configurationIndex == -1:
			self.configurations = None
			return

		# We now our configuration!
		configuration = self.configurations[configurationIndex]
		self.configurations = None

		# Save it to the project file.
		self._set_project_setting("premake_configuration", configuration)

	def _get_project_folder(self):
		folders = self.window.folders()
		if len(folders) == 0:
			return None
		return folders[0]

	def _get_project_file(self):
		filesList = os.listdir(self._get_project_folder())
		projFileFound = False
		for projFile in filesList:
			if projFile[-16:] == ".sublime-project":
				projFileFound = True
				break

		if projFileFound:
			return projFile
		return None

	def _get_project_setting(self, name):
		"""Get a value from the project configuration file."""
		projFile = self._get_project_file()
		if not projFile:
			return None

		projFilePath = os.path.join(self._get_project_folder(), projFile)
		projFileDesc = open(projFilePath, 'r')
		projJson = json.load(projFileDesc)
		projFileDesc.close()

		if 'settings' not in projJson:
			return None
		if name not in projJson['settings']:
			return None
		return projJson['settings'][name]

	def _set_project_setting(self, name, value):
		"""Set a value in the project configuration file."""
		projFile = self._get_project_file()
		if not projFile:
			return

		projFilePath = os.path.join(self._get_project_folder(), projFile)
		projFileDesc = open(projFilePath, 'r')
		projJson = json.load(projFileDesc)
		projFileDesc.close()

		if 'settings' not in projJson:
			projJson['settings'] = {}
		projJson['settings'][name] = value

		# Write the result.
		projFilePath = os.path.join(self._get_project_folder(), projFile)
		projFileDesc = open(projFilePath, 'w')
		json.dump(projJson, projFileDesc, indent = 4)
		projFileDesc.close()

	def _load_configurations_and_projects(self):
		"""Executes 'make' to load configurations and projects list, and parse the makefile to get each target info."""
		# Ensure there's a makefile available.
		if not os.path.exists(os.path.join(os.path.dirname(self._get_premake_filepath()), "Makefile")):
			sublime.error_message("Please generate your makefiles (using 'Premake: Generate') before doing that.")
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
		self.targets = []
		self.target = {}
		(out, _) = proc.communicate()
		inConf = False
		inTar = False
		for line in out.splitlines():
			if line == "CONFIGURATIONS:":
				inConf = True
				continue
			if line == "TARGETS:":
				inTar = True
				continue
			sline = line.strip()
			if inConf:
				if line == "":
					inConf = False
				else:
					self.configurations.append(sline)
			if inTar:
				if line == "":
					inTar = False
				else:
					if sline in ('all (default)', 'clean'):
						continue
					else:
						self.targets.append(sline)
						self.target[sline] = self._load_target_info(sline)

	def _load_target_info(self, target):
		"""Load information about the given target from its makefile."""
		
		# Look for the makefile.
		makeFile = os.path.join(os.path.dirname(self._get_premake_filepath()), target + ".make")
		if not os.path.exists(makeFile):
			sublime.error_message("Please generate your makefiles (using 'Premake: Generate') before doing that.")

		# Preparing the result object.
		info = {'name': target}

		# Parsing it.
		makeFileDesc = open(makeFile, 'r')
		inConfigBlock = False
		configBlockName = None
		while True:
			line = makeFileDesc.readline()
			if line == "":
				break
			line = line.strip()

			# Looking for the configuration switch line.
			result = re.match(r"^ifeq \(\$\(config\),(\w+)\)$", line)
			if result:
				inConfigBlock = True
				configBlockName = result.group(1)
				info[configBlockName] = {}

			# Looking for relevant informations inside the configuration block.
			if inConfigBlock:
				# End of the configuration block.
				if line == "endif":
					inConfigBlock = False
					continue

				# The TARGETDIR configuration info.
				result = re.match(r"^TARGETDIR\s*= ([\$\(\)\w\\/\._-]+)$", line)
				if result:
					info[configBlockName]['target_dir'] = result.group(1)
					continue

				# The TARGET configuration info.
				result = re.match(r"^TARGET\s*= ([\$\(\)\w\\/\._-]+)$", line)
				if result:
					info[configBlockName]['target'] = result.group(1).replace('$(TARGETDIR)', info[configBlockName]['target_dir'])
					continue

				# The LDFLAGS configuration info.
				result = re.match(r"^LDFLAGS\s*\+=(.*)$", line)
				if result:
					info['is_shared'] = '-shared' in result.group(1).split(' ')
					continue

				# The LINKCMD configuration info.
				result = re.match(r"^LINKCMD\s*= \$\(([A-Z]+)\)", line)
				if result:
					info['is_library'] = info['is_shared'] or result.group(1) == 'AR'
					info['is_executable'] = not info['is_library']
					continue
		makeFileDesc.close()

		return info

	def _get_premake_filepath(self):
		"""Find the absolute path to the premake build file (not guaranteed to exist)."""
		premakeFile = None

		# Attempt to load it from the project file.
		premakeFile = self._get_project_setting("premake_file")

		# If we don't have it yet, we load it from the default file.
		if not premakeFile:
			premakeSettings = sublime.load_settings("Premake.sublime-settings")
			premakeFile = premakeSettings.get("premake_file")

		# The name should be defined here, otherwise the default config is screwed.
		if not premakeFile:
			raise RuntimeError("Unable to get 'premake_file' from the settings.")

		# Convert the path to an absolute path, if necessary.
		if not os.path.isabs(premakeFile):
			premakeFile = os.path.abspath(os.path.join(self._get_project_folder(), premakeFile))

		return premakeFile

	def _print_help(self):
		help = \
"""Welcome to the Premake plugin!

To use the Premake plugin, you must:
 - Have a project opened.
     The Premake plugin uses your project settings file to get and store important
     settings, such as the premake build file path.
 - Have a premake build file.
     This file is named "premake4.lua" and is to be saved in the same directory
     than the project settings file. If you want, you can change this path by
     defining the "premake_file" property in your project file, this path will be
     used instead.

Once those this is configured, you can use the Premake plugin to generate the
Makefile for your project, to build one of the project defined in your premake
build file, in the configuration of your choice, and to run it as well, using the
Premake build system which is integrated."""
		self.window.run_command("exec", {"cmd": ["echo", help], "quiet": True})
