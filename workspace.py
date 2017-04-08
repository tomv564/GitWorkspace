import sublime_plugin
import sublime
import subprocess


def first_folder(window):
    """
    We only support running one stack-ide instance per window currently,
    on the first folder open in that window.
    """
    if len(window.folders()):
        return window.folders()[0]
    else:
        print("Couldn't determine a root folder in this project")
        return None

def run_command(args, cwd, handler):
    stdout, stderr = None, None

    try:
       if os.name == 'nt':
           startupinfo = subprocess.STARTUPINFO()
           startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
       else:
           startupinfo = None
       proc = subprocess.Popen(
           args=args, cwd=cwd, startupinfo=startupinfo,
           stdout=subprocess.PIPE, stderr=subprocess.PIPE,
           stdin=subprocess.PIPE)
       stdout, stderr = proc.communicate()
    except OSError as error:
       # print out system error message
       print('\'git %s\' failed with \"%s\"' % (
           args[1], error))
    finally:
       handler(stdout.decode('utf-8').strip())


def open_changed(result):
    print(result)

class OpenChangedInGitCommand(sublime_plugin.WindowCommand):
    def run(self):
        working_dir = first_folder(self.window)
        print("folder" + working_dir)
        run_command(working_dir, ['git', 'status'], open_changed)
        #   None    Called when the command is run.

    # def is_enabled():
    #     return True #   bool    Returns True if the command is able to be run at this time. The default implementation simply always returns True.

    # def is_visible():
    #     return True #   bool    Returns True if the command should be shown in the menu at this time. The default implementation always returns True.

    def description():
        return "Workspace: Open all files changed"


# class OpenOnlyChangedCommand(sublime_plugin.WindowCommand):
# OpenStagedCommand
# OpenOnlyStagedCommand