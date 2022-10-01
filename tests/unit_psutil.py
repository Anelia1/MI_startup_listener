import datetime
import psutil
from prettytable import PrettyTable

########################## Static and accurate methods to make use of ###############################


ls = ['pid', 'username', 'num_threads', 'threads', 'name', 'status']
full_ls = ['pid', 'nice', 'memory_full_info', 'ionice', 'num_threads', 'username', 'num_handles', 'num_ctx_switches', 'connections', 'cpu_affinity', 'create_time', 'memory_info', 'name', 'memory_percent', 'open_files', 'cpu_percent', 'environ', 'io_counters', 'threads', 'cmdline', 'exe', 'status', 'ppid', 'cpu_times', 'memory_maps', 'cwd']


def _active_processes_names():
    return [p.info['name'] for p in psutil.process_iter(ls)]


def _MI_process_info() -> list:
    MI_instances = []
    processes_names = _active_processes_names()
    for p in processes_names:
        #print(p)
        if "MI_app" in p.info['name']:
            #print(p)
            MI_instances.append(p)
    return MI_instances


def test_grab_info():
    for p in psutil.process_iter():
        if "UCL" in p.info['name']:
            print(p.as_dict(attrs=full_ls))


def test_grab_info2():
    for p in psutil.process_iter(ls):
        if "MI_app" in p.info['name']:
            print(p)


def time_created():
    p = psutil.Process
    for p in psutil.process_iter():
        if "MI_app" in p.info['name']:
            p_time = p.create_time()
            formatted_time = datetime.datetime.fromtimetostamp(p_time).strftime("%Y-%m-%d %H:%M:%S")
            print("MI executed on: ", formatted_time)




    #@staticmethod
    #def _MI_process_info():
    #    """
    #    Grab system information about MI
    #    """
    #    MI_instances = []
    #    processes_names = psutil.process_iter([ 'pid', 'name','status', 'exe', 'cmdline'])
    #    for p in processes_names:
    #        if MI_EXE in p.info['name'] or \
    #        p.info['exe'] and os.path.basename(p.info['exe']) == MI_EXE or \
    #            p.info['cmdline'] and p.info['cmdline'][0] == MI_EXE:
    #            MI_instances.append(p)
    #    print(MI_instances)
    #    return MI_instances




def system_info_table():
    """
    Method for visual display of system information
    Not actively used at the moment but has great potential
    (if we do not require fast outputs because psutil is much slower)
    """
    process_table = PrettyTable(['PID', 'PNAME', 'STATUS', 'NUM_THREADS', 'MEMORY(MB)'])
    try:
        for p in psutil.process_iter():
            # oneshot is very fast
            with p.oneshot():
                process_table.add_row([
                    str(p.pid),
                    p.name(),
                    p.status(),
                    p.num_threads(),
                    f'{p.memory_info().rss / 1e6:.3f}'
                    ])
                print(process_table)
    except Exception as e:
        print(e)



def time_MI_process_created():
    """
    Formatted date and time for MI exe trigger
    Not actively used at the moment (added to todo list:)
    """
    p = psutil.Process
    for p in psutil.process_iter():
        if "MI_app" in p.info['name']:
            p_time = p.create_time()
            formatted_time = datetime.datetime.fromtimetostamp(p_time).strftime("%Y-%m-%d %H:%M:%S")
            print("MI executed on: ", formatted_time)



def _active_processes_names():
    """
    Returns a list of the names of running processes 
    on Windows
    """
    return [p.info['name'] for p in psutil.process_iter(['pid', 'name', 'status'])]


########################################################################################