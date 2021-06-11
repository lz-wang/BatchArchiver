import subprocess
import sys
import os
import re
from multiprocessing import Pool


def run_shell(shell):
    # stdout=sys.stdout or subprocess.DEVNULL
    cmd = subprocess.Popen(shell, stdin=subprocess.PIPE, stderr=sys.stderr, close_fds=True,
                           stdout=subprocess.DEVNULL, universal_newlines=True, shell=True, bufsize=1)
    while True:
        if subprocess.Popen.poll(cmd) == 0:
            return True


def compress_dir(src_dir, dst_file, level=5, passwd=None):
    print(f'processing ---> {dst_file}')
    src_name = src_dir.split('/')[-1]
    src_path = '/'.join(src_dir.split('/')[0:-1])
    cmd = "cd " + src_dir + " && cd .. && "
    cmd += "zip -" + str(level) + "r"
    if passwd is not None:
        cmd += " -P\'" + str(passwd) + "\' "
    cmd += str(os.path.join(src_path, dst_file)) + " " + str(src_name)

    run_shell(cmd)


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


def replace_symbols(dirs):
    new_dirs = []
    for d in dirs:
        d = d.replace('[', '\[')
        d = d.replace(']', '\]')
        d = d.replace(' ', '\ ')
        new_dirs.append(d)

    return new_dirs


def remove_prefix(raw_str):
    pattern = r'\[.*?\]'
    return (re.sub(pattern, '', raw_str)).replace(' ', '\ ')


def print_args(name):
    print(name)


if __name__ == '__main__':
    parent_dir = '/Users/lzwang/Downloads/2501-2600'
    raw_dir_names, raw_dir_list = scan_dirs(parent_dir)
    new_dir_list = replace_symbols(raw_dir_list)
    print()
    p = Pool(10)
    for dir_name, dir_path in zip(raw_dir_names, new_dir_list):
        dst_zip_name = remove_prefix(dir_name)+".zip"
        p.apply_async(compress_dir, args=(dir_path, dst_zip_name, 9, 'lzwang'))
    p.close()
    p.join()
    print('All subprocesses done.')
