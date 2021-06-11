import subprocess
import sys
import os
import re
import time
from multiprocessing import Pool, Lock
from PyQt5.Qt import QThread, pyqtSignal


class Zipper(QThread):
    progress_value = pyqtSignal(int)
    log_output = pyqtSignal(str)

    def __init__(self, p_path='', crate=1, cpu_core=1, passwd=None):
        super().__init__()
        self.p_path = p_path
        self.crate = crate
        self.cpu_core = cpu_core
        self.passwd = passwd

    @staticmethod
    def scan_dirs(parent_dir):
        sub_dir_name_list = []
        sub_dir_path_list = []
        ld = os.listdir(parent_dir)  # 列出文件夹下所有的目录与文件
        ld.sort()
        for i, name in enumerate(ld):
            path = os.path.join(parent_dir, name)
            if os.path.isdir(path) and name[0] != '.':
                sub_dir_name_list.append(name)
                sub_dir_path_list.append(path)

        return sub_dir_name_list, sub_dir_path_list

    @staticmethod
    def replace_symbols(dirs):
        new_dirs = []
        for d in dirs:
            d = d.replace('[', '\[')
            d = d.replace(']', '\]')
            d = d.replace(' ', '\ ')
            new_dirs.append(d)

        return new_dirs

    @staticmethod
    def remove_prefix(raw_str):
        pattern = r'\[.*?\]'
        return (re.sub(pattern, '', raw_str)).replace(' ', '\ ')

    def run(self):
        raw_dir_names, raw_dir_list = self.scan_dirs(self.p_path)
        new_dir_list = self.replace_symbols(raw_dir_list)
        dir_size = len(new_dir_list)
        p = Pool(self.cpu_core)
        workers = []
        counter = 0
        print(self.cpu_core)
        for i in range(dir_size):
            dir_name, dir_path = raw_dir_names[i], new_dir_list[i]
            dst_zip_name = self.remove_prefix(dir_name) + ".zip"
            process = p.apply_async(compress_dir, args=(dir_path, dst_zip_name, self.crate, self.passwd))
            workers.append(process)

            while True:
                while True:
                    if len(workers) < self.cpu_core and i < dir_size - 1:
                        break
                    if len(workers) == 0 and i == dir_size - 1:
                        break
                    for worker in workers:
                        if worker.get():
                            workers.remove(worker)
                            counter += 1
                            progress = 100 * (counter / dir_size)
                            self.progress_value.emit(round(progress))
                            time.sleep(0.05)
                            break

                if len(workers) < self.cpu_core:
                    if i < dir_size - 1:
                        break
                    else:
                        if len(workers) == 0:
                            break
                        else:
                            continue

        p.close()
        p.join()
        print('ALL DONE!')


def run_shell(shell):
    # stdout=sys.stdout or subprocess.DEVNULL
    cmd = subprocess.Popen(shell, shell=True,
                           stdin=subprocess.PIPE,
                           stdout=subprocess.DEVNULL,
                           stderr=sys.stderr,
                           close_fds=True, bufsize=1,
                           universal_newlines=True)
    while True:
        if subprocess.Popen.poll(cmd) == 0:
            return True


def compress_dir(src_dir, dst_file, level=5, passwd=None):
    # print(f'processing ---> {dst_file}')
    src_name = src_dir.split('/')[-1]
    src_path = '/'.join(src_dir.split('/')[0:-1])
    cmd = "cd " + src_dir + " && cd .. && "
    cmd += "zip -" + str(level) + "r "
    if passwd is not None:
        cmd += "-P\'" + str(passwd) + "\' "
    cmd += str(os.path.join(src_path, dst_file)) + " " + str(src_name)

    return run_shell(cmd)
