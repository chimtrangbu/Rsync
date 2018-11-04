#!/usr/bin/env python3

import argparse
import os
import difflib


parser = argparse.ArgumentParser(usage='./rsync.py [OPTIONS] SRC DES',
                                 conflict_handler='resolve')
parser.add_argument('SRC_FILE', type=str, help=argparse.SUPPRESS)
parser.add_argument('DESTINATION', type=str, help=argparse.SUPPRESS)
options = parser.add_argument_group('Options')
options.add_argument('-u', '--update', action='store_true', default=False,
                     help='skip files that are newer on the receiver')
options.add_argument('-c', '--checksum', action='store_true', default=False,
                     help='skip based on checksum, not mod-time & size')
options.add_argument('-h', '--help', action='store_true', default=False,
                     help='show this help (-h is --help only if used alone)')

args = parser.parse_args()

if args.help:
    parser.print_help()


# __________________________
# print(args)  # Namespace(DESTINATION='b', SRC_FILE='a', \
#  checksum=False, help=True, update=False)
# stat = os.stat(args.SRC_FILE)  #os.stat_result(st_mode=33197, \
#  st_ino=20581831, st_dev=2051, st_nlink=1, st_uid=2126, st_gid=2001, \
#  st_size=6, st_atime=1540536978, st_mtime=1540374675, st_ctime=1540374675)


try:
    f = open(args.SRC_FILE, 'r')
    lines1 = f.readlines()
    f.close()
    lines1 = ''.join(lines1).splitlines()
    # try:
    #     f = open(args.DESTINATION, 'r')
    #     lines2 = f.readlines()
    #     f.close()
    #     lines2 = ''.join(lines2).splitlines()
    #     diffs = difflib.unified_diff(lines1, lines2, fromfile=args.SRC_FILE,\
    #                                tofile=args.DESTINATION, lineterm='', n=0)
    #     # ...
    # except FileNotFoundError:
    #     f = open(args.DESTINATION, 'a')
    #     for line in lines1:
    #         f.write(line + '\n')
    #     f.close()
    f = open(args.DESTINATION, 'w')
    for line in lines1:
        f.write(line + '\n')
    f.close()
except FileNotFoundError:
    print('rsync: link_stat ' + args.SRC_FILE + ' failed: No such file...')
    # if not os.path.exists(args.SRC_FILE):
    #     rsync: link_stat "/home/hm..." failed: No such file or directory (2)

# ______________________________main()______________________________
if not os.path.isfile(args.SRC_FILE):
    print('rsync: link_stat ' + args.SRC_FILE + ' failed: No such file...')
elif args.DESTINATION == args.SRC_FILE:
    print('skipping non-regular file ' + args.SRC_FILE)
else:
    src_file = os.open(args.SRC_FILE, os.O_RDONLY)
    src_content = os.read(src_file, 1024)
    os.close(src_file)
    # src_content = ''.join(src_content).splitlines()
    if not os.path.exists(args.DESTINATION):
        des_file = os.open(args.DESTINATION, os.O_CREAT)
        os.close(des_file)
        des_content = ''
    elif os.path.isdir(args.DESTINATION):
        src_in_des = args.DESTINATION + '/' + args.SRC_FILE
        if os.path.isfile(src_in_des):
            # check size and mtime to decide if des needs to be updates
            # get content of file
            des_file = os.open(src_in_des, os.O_RDWR)
            des_content = os.read(des_file, 1024)
            os.close(des_file)
            # des_content = ''.join(des_content).splitlines()
        else:
            des_file = os.open(src_in_des, os.O_CREAT)
            os.close(des_file)
            des_content = ''
    else:
        # check size and mtime to decide if des needs to be updates
        # get content of file
        des_file = os.open(args.DESTINATION, os.O_RDWR)
        des_content = os.read(des_file, 1024)
        os.close(des_file)
        # des_content = ''.join(des_content).splitlines()

    # if SRC had a hardlink:
    if os.stat(args.SRC_FILE).st_nlink > 1:
        os.unlink(args.DESTINATION)
        os.link(args.SRC_FILE, args.DESTINATION)

    # elif SRC had a symlink:
    elif os.path.islink(args.SRC_FILE):
        sl = os.readlink(args.SRC_FILE)
        os.unlink(args.DESTINATION)
        os.symlink(sl, args.DESTINATION)
    else:
        # if des_content == '':
            # rewrite des
            # os.sendfile()
        # change permission
        mod = os.stat(args.SRC_FILE).st_mode
        os.chmod(args.DESTINATION, mod)
        # change times
        at = os.stat(args.SRC_FILE).st_atime
        mt = os.stat(args.SRC_FILE).st_mtime
        ns = (at, mt)
        # os.open(args.DESTINATION, )
        os.utime(args.DESTINATION, ns, follow_symlinks=False)
