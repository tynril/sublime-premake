import sublime, sublime_plugin

class PremakeCommand(sublime_plugin.WindowCommand):
	def premake(self, args):
		self.window.run_command("exec", {"cmd": ["premake4"] + args})

	def run(self, operation):
		if operation == "generate":
			self.premake(["gmake"])
		elif operation == "clean":
			self.premake(["clean"])
