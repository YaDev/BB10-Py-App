import os
import sys
import re
import traceback
import py_compile
import shutil
import tokenize
import imp
import marshal
import builtins
import errno
from modulefinder import ModuleFinder
from py_compile import PyCompileError


'''
INITIAL_FILE => the main file which creates and runs App script
PROJECT_PY_FOLDER_PATH => The path to "py" directory in your Momentics IDE project's directory
VIRTUAL_ENV_PATH => The path to python virtual environment 
'''
#####################################################
INITIAL_FILE = "initializer.py"
#####################################################
PROJECT_PY_FOLDER_PATH = r"C:\Users\<USER_NAME>\momentics-workspace\<PROJECT_NAME>\py"
#####################################################
VIRTUAL_ENV_PATH = os.path.join(os.getcwd(), "venv")
#####################################################

# The current project's directory
CURRENT_DIR = os.getcwd()
# The magic string value used to recognize byte-compiled code
MAGIC = imp.get_magic()


class PyFile:
    def __init__(self, file_path: str, base: str, pyc_path: str):
        self.file_path = file_path
        self.base = base
        self.pyc_path = pyc_path


def compile_py(file: PyFile):
    with tokenize.open(file.file_path) as f:
        try:
            timestamp = int(os.fstat(f.fileno()).st_mtime)
        except AttributeError:
            timestamp = int(os.stat(file.file_path).st_mtime)
        codestring = f.read()
    try:
        codeobject = builtins.compile(codestring, file.base, 'exec',
                                      dont_inherit=True)
    except Exception as err:
        py_exc = PyCompileError(err.__class__, err, file)
        sys.stderr.write(py_exc.msg + '\n')
        return
    try:
        dirname = os.path.dirname(file.pyc_path)
        if dirname:
            os.makedirs(dirname)
    except OSError as error:
        if error.errno != errno.EEXIST:
            raise
    with open(file.pyc_path, 'wb') as fc:
        fc.write(b'\0\0\0\0')
        py_compile.wr_long(fc, timestamp)
        marshal.dump(codeobject, fc)
        fc.flush()
        fc.seek(0, 0)
        fc.write(MAGIC)
    return file.pyc_path


def clean_compile(file: PyFile):
    if os.path.exists(PROJECT_PY_FOLDER_PATH):
        if os.path.exists(file.file_path):
            if os.path.isfile(file.file_path):
                try:
                    compile_py(file)
                except BaseException:
                    print("Error-> Failed to compile the file:", file.file_path, "\n\n", traceback.format_exc())
            else:
                print("Error-> invalid file's path : ", file.file_path)
        else:
            print("Error-> file does not exist : ", file.file_path)
    else:
        print("Error-> the project's py folder does not exist : ", PROJECT_PY_FOLDER_PATH)


def clean_output_dir() -> bool:
    if os.path.exists(PROJECT_PY_FOLDER_PATH):
        try:
            shutil.rmtree(PROJECT_PY_FOLDER_PATH)
            os.makedirs(PROJECT_PY_FOLDER_PATH)
            return True
        except BaseException:
            print("Failed to clean or create the project's py folder", "\n\n", traceback.format_exc())
            return False
    else:
        try:
            os.makedirs(PROJECT_PY_FOLDER_PATH)
            return True
        except BaseException:
            print("Failed to create the project's py folder", "\n\n", traceback.format_exc())
            return False


if __name__ == '__main__':
    finder = ModuleFinder()
    finder.run_script(INITIAL_FILE)
    local_files = [os.path.join(os.getcwd(), INITIAL_FILE)]
    packages_files = []
    py_files_list = []
    for _, mod in finder.modules.items():
        if mod.__file__:
            if VIRTUAL_ENV_PATH in mod.__file__:
                if "site-packages" in VIRTUAL_ENV_PATH:
                    packages_files.append(mod.__file__)
            elif CURRENT_DIR in mod.__file__:
                local_files.append(mod.__file__)
    for file in local_files:
        base_path = file.replace(os.getcwd() + os.sep, "")
        compiled_file = base_path + "c"
        compiled_file = os.path.join(PROJECT_PY_FOLDER_PATH, compiled_file)
        py_files_list.append(PyFile(file_path=file, base=base_path, pyc_path=compiled_file))

    for file in packages_files:
        base_path = re.sub(r".*[\\|/]site-packages[\\|/]", "", file)
        compiled_file = base_path + "c"
        compiled_file = os.path.join(PROJECT_PY_FOLDER_PATH, compiled_file)
        py_files_list.append(PyFile(file_path=file, base=base_path, pyc_path=compiled_file))

    if not clean_output_dir():
        print("You must create the project's 'py' folder or delete all its files and sub-folders")

    for py_file in py_files_list:
        clean_compile(py_file)
