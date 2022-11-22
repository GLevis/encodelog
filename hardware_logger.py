import datetime, psutil, platform, os
from subprocess import Popen, PIPE
from asyncio import subprocess

class hardware_logger:
    def __init__(self):
        self.cpu_dict = dict()
        self.gpu_dict = dict()
        self.ram_dict = dict()
        self.vmaf_dict = dict()
        self._running = True

    def get_cpu_log(self):
        return self.cpu_dict
    
    def get_gpu_log(self):
        return self.gpu_dict
    
    def get_ram_log(self):
        return self.ram_dict
    
    def get_gpu_usage(self):
        if platform.system() == "Windows":
            path = os.path.dirname(os.path.realpath(__file__))
            p = Popen(["powershell", 
                        path + "\\gpusage.ps1"], stdout=subprocess.PIPE)
            stdout, stderror = p.communicate()
            output = stdout.decode('UTF-8')
            output = output.rstrip()
            return output

    def terminate(self):
        self._running = False

    def run(self):
        startTime = datetime.datetime.now()
        while self._running:
            cpu_usage = psutil.cpu_percent()
            gpu_usage = self.get_gpu_usage()
            ram_usage = psutil.virtual_memory().percent
            tickTime = datetime.datetime.now()
            duration = tickTime - startTime
            self.cpu_dict[duration] = float(cpu_usage)
            self.gpu_dict[duration] = float(gpu_usage)
            self.ram_dict[duration] = float(ram_usage)
    

    
