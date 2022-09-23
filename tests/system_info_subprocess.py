import os
import subprocess


def system_info():
    # Test 1
    output = subprocess.check_output(["wmic", "process", "list", "full", "/format:list"])
    output = output.decode("utf-8") 
    wmi_entries = []
    for task in output.strip().split("\r\r\n\r\r\n"):
        wmi_entries.append(dict(e.split("=", 1) for e in task.strip().split("\r\r\n")))
    for row in wmi_entries:
        if row['Name'].startswith('ch') or row['Name'].startswith('MI'):
            print(row)


def subprocess_output():
    # Test 2
    print(subprocess.getoutput('tasklist'))


def os_sys_output():
    # Test 3
    print(os.system('tasklist'))



system_info()