#!/usr/bin/env python3

import argparse
import sys
import os


def parse_input():
    inpargs = sys.argv[1:]  # input arguments except ./rsync.py
    inpopts = []  # input options
    inpfiles = []  # input source and des files
    for arg in inpargs:
        if arg.startswith('-'):
            inpopts.append(arg)
        else:
            inpfiles.append(arg)
    args_to_parse = inpopts + inpfiles  # handle options and arguments

    parser = argparse.ArgumentParser(usage='./rsync.py [OPTIONS] '
                                           'SRC_FILE DESTINATION',
                                     add_help=False,
                                     conflict_handler='resolve')
    parser.add_argument('files', nargs='+', type=str, help=argparse.SUPPRESS)
    options = parser.add_argument_group('Options')
    options.add_argument('-u', '--update',
                         action='store_true',
                         default=False,
                         help='skip files that are newer on the receiver')
    options.add_argument('-c', '--checksum',
                         action='store_true',
                         default=False,
                         help='skip based on checksum, not mod-time & size')
    options.add_argument('-r', '--recursive',
                         action='store_true',
                         default=False,
                         help='recurse into directories')
    return parser.parse_args(args_to_parse)


def get_permissions(filename):
    # gets mode of file then convert to permissions
    if os.path.islink(filename):
        per = 'l'
        mask = oct(os.lstat(filename).st_mode)[-3:]
    elif os.path.isdir(filename):
        per = 'd'
        mask = oct(os.stat(filename).st_mode)[-3:]
    else:
        per = '-'
        mask = oct(os.stat(filename).st_mode)[-3:]
    per_dict = {
        '0': '---',
        '1': '--x',
        '2': '-w-',
        '3': '-wx',
        '4': 'r--',
        '5': 'r-x',
        '6': 'rw-',
        '7': 'rwx'
    }
    for i in mask:
        per = per + per_dict[i]
    return per


def get_content(filename):
    try:
        file = open(filename, 'r')
        content = file.read()
        file.close()
    except PermissionError:
        print(error_cases('pererr', filename))
    return content


def decide_skip_update(src, des):
    # decides if destination doesn't need to update
    if c_flag:  # skipping not depend on mod-time and size
        return False
    src_mtime = os.stat(src).st_mtime
    des_mtime = os.stat(des).st_mtime
    if src_mtime < des_mtime:  # with --update option, skip if des is newer
        return True if u_flag else False
    elif src_mtime == des_mtime:
        # without -c and -u opts, skip if des has different size or mtime
        if os.stat(src).st_size == os.stat(des).st_size:
            return True
    return False


def update_time_pers(src_file, destination):
    # updates time and permissions
    if os.path.islink(src_file):
        srcstat = os.lstat(src_file)
    else:
        srcstat = os.stat(src_file)
    os.chmod(destination, srcstat.st_mode)
    ns = (srcstat.st_atime, srcstat.st_mtime)
    os.utime(destination, ns, follow_symlinks=False)
    return


def create_new_file(filename):
    # creates an epmty file
    file = os.open(filename, os.O_CREAT)
    os.close(file)
    return


def rewrite(filename, content):
    f = open(filename, 'w')
    f.write(content)
    f.close()
    return


def error_cases(key, filename):
    # handles errors
    error_dict = {
        'direrr': 'rsync: change_dir \"%s//%s\" '
                  'failed: No such file or directory (2)',
        'fileerr': 'rsync: link_stat \"%s/%s\" '
                   'failed: No such file or directory (2)',
        'skipdir': 'skipping directory %s',
        'skipfile': 'skipping non-regular file \"%s\"',
        'pererr': 'rsync: send_files failed to open '
                  '\"%s/%s\": Permission denied (13)',
        'notdir': 'rsync: ERROR: cannot stat '
                  'destination \"%s/%s\": Not a directory (20)'
    }
    if key in ('skipdir', 'skipfile'):
        return error_dict[key] % filename
    else:
        return error_dict[key] % (os.getcwd(), filename)


def check_filenames(src_file, destination):
    # handles cases of filenames, returns destination as name of a file
    if not os.path.exists(src_file):
        if src_file.endswith('/'):
            print(error_cases('direrr', src_file[:-1]))
        else:
            print(error_cases('fileerr', src_file))
    if destination.endswith('/'):
        if os.path.isfile(destination[:-1]):
            print(error_cases('notdir', destination))
            return
        else:
            destination = destination[:-1]
            if not os.path.exists(destination):
                os.mkdir(destination)
    if os.path.isdir(src_file):
        if not r_flag:
            if src_file.endswith('/'):
                src_name = '.'
            elif '/' in src_file:
                src_name = src_file.split('/')[-1]
            else:
                src_name = src_file
            print(error_cases('skipdir', src_name))
    elif os.path.isfile(src_file):
        if '/' in src_file:
            src_name = src_file.split('/')[-1]
        else:
            src_name = src_file
        if os.path.isdir(destination):
            des_name = destination + '/' + src_name
        else:
            des_name = destination
        if not os.path.isfile(des_name):
            create_new_file(des_name)
        elif decide_skip_update(src_file, des_name):
            return
        return des_name


def check_links(src_file, destination):
    # function checks if src file is hardlink or symlink
    # creats a new destination keeping hard/symlink, returns True
    if os.stat(src_file).st_nlink > 1:
        os.unlink(destination)
        os.link(src_file, destination)
        return True
    elif os.path.islink(src_file):
        if os.readlink(src_file) == destination:
            print(error_cases('skipfile', src_file))
        sl = os.readlink(src_file)
        os.unlink(destination)
        os.symlink(sl, destination)
        update_time_pers(src_file, destination)
        return True
    # if src file isn't, does nothing and returns False
    return False


def change_content(src_file, destination):
    try:  # compares contents of 2 files and changes des following src
        src = os.open(src_file, os.O_RDONLY)
        des = os.open(destination, os.O_RDWR)
        pos = 0
        while pos < os.stat(src_file).st_size:
            os.lseek(src, pos, 0)
            s = os.read(src, 1)
            os.lseek(des, pos, 0)
            d = os.read(des, 1)
            if d != s:
                os.lseek(des, pos, 0)
                os.write(des, s)
            pos = pos + 1
        os.close(src)
        os.close(des)
    except PermissionError:  # if des can't be able to write
        os.remove(destination)
        create_new_file(destination)
        src_content = get_content(src_file)
        rewrite(destination, src_content)
        update_time_pers(src_file, destination)
    return


def rsync_single_file(src_file, destination):
    # synchronizes 2 files
    try:
        src_content = get_content(src_file)
        if not check_links(src_file, destination):
            if os.stat(destination).st_size == 0 or \
                    os.stat(destination).st_size > os.stat(src_file).st_size:
                rewrite(destination, src_content)
                update_time_pers(src_file, destination)
            else:
                change_content(src_file, destination)
                update_time_pers(src_file, destination)
    except BaseException:
        pass
    return


def create_dir(dir_name):
    names = dir_name.split('/')
    cur = ''
    pos = 0
    n = len(names)
    while pos < n:
        cur = cur + names[pos] + '/'
        if not os.path.isdir(cur):
            os.mkdir(cur)
        pos += 1
    return cur[:-1]


def rsync_single_dir(src, des):
    # synchronizes 2 dirs
    if not src.endswith('/'):
        temp = src.split('/')[-1]
        des_name = create_dir(des + '/' + temp)
    else:
        des_name = des
    scan = os.scandir(src)
    for e in scan:
        if src.endswith('/'):
            src_file = src + e.name
        else:
            src_file = src + '/' + e.name
        rsync_two_args(src_file, des_name)
    return


def rsync_two_args(src, des):
    if r_flag and os.path.isdir(src):
        if not os.path.exists(des):
            create_dir(des)
        elif os.path.isfile(des):
            sys.exit('ERROR: destination must be a directory '
                     'when copying more than 1 file')
        rsync_single_dir(src, des)
    else:
        destination = check_filenames(src, des)
        rsync_single_file(src, destination)
    return


def main():
    if nfiles == 1:
        file = args.files[0]
        if os.path.exists(file):
            print(get_permissions(file), '\t\t', str(os.stat(file).st_size))
            sys.exit()
        else:
            sys.exit(error_cases('fileerr', file))
    elif nfiles == 2:
        rsync_two_args(args.files[0], args.files[1])
    else:
        destination = args.files.pop()
        sourses = args.files
        if os.path.isfile(destination):
            sys.exit('ERROR: destination must be a directory '
                     'when copying more than 1 file')
        else:
            for src_file in sourses:
                rsync_two_args(src_file, destination)


if __name__ == '__main__':
    args = parse_input()
    nfiles = len(args.files)
    u_flag = args.update
    c_flag = args.checksum
    r_flag = args.recursive
    main()
