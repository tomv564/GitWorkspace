import sublime_plugin
import subprocess
import os


def first_folder(window):
    """
    return the first folder open in a window.
    """
    if len(window.folders()):
        return window.folders()[0]
    else:
        print("Couldn't determine a root folder in this project")
        return None


def run_command(cwd, args, handler):
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
        if stdout:
            handler(stdout.decode('utf-8').rstrip())

def open_changed(window, to_open):
    for file in to_open:
        if window.find_open_file(file) is None:
            window.open_file(file)

def only_changed(window, to_open):
    open_changed(window, to_open)
    close_not_changed(window, to_open)

def close_not_changed(window, to_keep):
    for view in window.views():
        if view.file_name() and not view.is_dirty():
            if view.file_name() not in to_keep:
                print(view.file_name() + " not in " + str(to_keep))
                view.close()


class OpenChangedInGitCommand(sublime_plugin.WindowCommand):
    def __init__(self, window):
        sublime_plugin.WindowCommand.__init__(self, window);
        self.project_root_dir = first_folder(window)
        run_command(self.project_root_dir, ["git", "rev-parse", "--show-toplevel"], lambda output: self.parse_git_root(output))

    def parse_git_root(self, output):
        normalized_path = os.path.normpath(output)
        print("GitWorkspace git root:" + normalized_path)
        self.git_root_dir = normalized_path

    def run(self, query, only):
        # print("folder" + project_root_dir)

        def parse_line(line):
            (index, worktree, file_path) = (line[0], line[1], line[3:])
            return (index, worktree, os.path.join(self.git_root_dir, os.path.normpath(file_path)))

        def parse_filter_and_dispatch(output, predicate, handler):
            print(output)
            entries = filter(predicate, map(parse_line, output.split('\n')))
            full_paths = list(map(lambda e: e[2], entries))
            handler(full_paths)

        def is_staged(entry):
            return entry[0] in ['M', 'A', 'R', 'C']

        def is_changed(entry):
            return is_staged(entry) or entry[1] in ['M', '?']

        def is_conflict(entry):
            return (entry[0] + entry[1]) in ['U.', '.U', 'DD', 'AA']
            # see http://stackoverflow.com/questions/13893763/how-to-ask-git-if-the-repository-is-in-a-conflict-stage

        cmd = ['git', 'status', '--porcelain']
        if query == "changed":
            predicate = is_changed
        elif query == "staged":
            predicate = is_staged
        elif query == "conflicts":
            predicate = is_conflict
        else:
            print("Unknown query: " + query)

        if only:
            handler = lambda file_paths: only_changed(self.window, file_paths)
        else:
            handler = lambda file_paths: open_changed(self.window, file_paths)

        run_command(self.project_root_dir, cmd,
                    lambda response: parse_filter_and_dispatch(response, predicate, handler))

