import subprocess
import sys
import os
import re
import time
from multiprocessing import Pool
from PyQt5.Qt import QWidget, pyqtSignal, QApplication
from threading import Thread


class Zipper(QWidget, Thread):
    progress_value = pyqtSignal(int)
    log_output = pyqtSignal(tuple)

    def __init__(self, p_path='', crate=1, cpu_core=1, passwd=None):
        super().__init__()
        self.p_path = p_path
        self.crate = crate
        self.cpu_core = cpu_core
        self.passwd = passwd
        self.p = Pool(self.cpu_core)

    @staticmethod
    def scan_dirs(parent_dir):
        sub_dir_name_list = []
        sub_dir_path_list = []
        ld = os.listdir(parent_dir)  # 列出文件夹下所有的目录与文件
        ld.sort()
        for i, name in enumerate(ld):
            path = os.path.join(parent_dir, name)
            if os.path.isdir(path) and name[0] not in ['.', '_']:
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
        if not os.path.exists(self.p_path):
            self.log_output.emit((True, 'Dir not exist!'))
            return

        raw_dir_names, raw_dir_list = self.scan_dirs(self.p_path)
        if not raw_dir_list:
            self.log_output.emit((True, f'No sub dir found in {self.p_path}'))
            return

        new_dir_list = self.replace_symbols(raw_dir_list)
        dir_size = len(new_dir_list)
        # p = Pool(self.cpu_core)
        workers = []
        counter = 0
        print(self.cpu_core)
        for i in range(dir_size):
            dir_name, dir_path = raw_dir_names[i], new_dir_list[i]
            dst_zip_name = self.remove_prefix(dir_name) + ".zip"
            process = self.p.apply_async(compress_dir, args=(dir_path, dst_zip_name, self.crate, self.passwd))
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
                            self.log_output.emit(worker.get())
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
        self.p.close()
        self.p.join()
        print('ALL DONE!')
        self.log_output.emit((True, 'ALL DONE!'))

    def kill_all(self):
        self.p.terminate()
        self.p.join()
        self.log_output.emit((True, 'User STOP.'))


def run_shell(shell, **kwargs):
    # stdout=sys.stdout or subprocess.DEVNULL
    cmd = subprocess.Popen(shell, shell=True,
                           stdin=subprocess.PIPE,
                           stdout=subprocess.DEVNULL,
                           stderr=sys.stderr,
                           close_fds=True, bufsize=1,
                           universal_newlines=True)
    while True:
        if subprocess.Popen.poll(cmd) == 0:
            return True, kwargs.get('src')


def compress_dir(src_dir, dst_file, level=5, passwd=None):
    # print(f'processing ---> {dst_file}')
    src_name = src_dir.split('/')[-1]
    src_path = '/'.join(src_dir.split('/')[0:-1])
    cmd = "cd " + src_dir + " && cd .. && "
    cmd += "zip -" + str(level) + "r "
    if passwd is not None:
        cmd += "-P\'" + str(passwd) + "\' "
    cmd += str(os.path.join(src_path, dst_file)) + " " + str(src_name)

    return run_shell(cmd, src=src_dir)


if __name__ == "__main__":
    root_path = '/Users/lzwang/Downloads/test/A'
    app = QApplication(sys.argv)
    zp = Zipper(p_path=root_path, crate=5, cpu_core=5, passwd='123')
    zp.start()
    zp.join()
    zp.close()
    app.exec()
