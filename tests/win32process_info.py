from win32api import GetFileVersionInfo, OpenProcess
from win32con import PROCESS_QUERY_INFORMATION, PROCESS_VM_READ
from win32process import EnumProcesses, EnumProcessModules, GetModuleFileNameEx
import pywintypes

def get_executable_desc(path, default=''):
    try:
        language, codepage = GetFileVersionInfo(path, "\\VarFileInfo\\Translation")[0]
        return GetFileVersionInfo(path, "\\StringFileInfo\\{:04x}{:04x}\\FileDescription".format(language, codepage)) or default
    except:
        return default

def get_process_list():
    proc_list = []
    processes = EnumProcesses()
    if not processes:
        return [] 
    for proc in processes:
        try:
            handle = OpenProcess(PROCESS_QUERY_INFORMATION | PROCESS_VM_READ, pywintypes.FALSE, proc)
            modules = EnumProcessModules(handle)
            if not modules:
                continue  
            path = GetModuleFileNameEx(handle, modules[0])
            proc_list.append({"ProcessId": proc, "ExecutablePath": path, "Description": get_executable_desc(path, path)})
        except pywintypes.error as e:
            print(e)

    return proc_list


tasks = get_process_list()
for row in tasks:
    print(row) 
