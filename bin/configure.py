#!/usr/bin/env python
# -*- coding: utf8 -*-


import os
import sys
import stat
import getopt
import configparser


def usage():
    print("""%s [-h -l] -c cfg -d destination_dir
    -h --help: show help
    -c --cfg: specify configuration file
    -d --directory: specify directory where templates file will be instantiated
    -l --list: only list template file""" % sys.argv[0])


def get_template_files(file_list):
    l = []
    for file in file_list:
        if file.endswith('.tpl'):
            l.append(file)
    return l


def load_config(config_path):
    d = {}
    fullname = ''
    config = configparser.ConfigParser()
    config.optionxform = str
    config.read(config_path)

    cwd = os.getcwd()
    sections = config.sections()
    for section in sections:
        items = config.items(section)
        for item in items:
            if item[0] == 'template':
                fullname = os.path.realpath(cwd + '/' + item[1])
                if fullname not in d:
                    d[fullname] = {}
                else:
                    print("ERROR: found duplicated file: %s" % fullname)
            else:
                d[fullname][item[0]] = item[1]
    return d


def build_template_key(key):
    return '${' + key + '}'


def instantiate_template(config, template):
    t_file = open(template, 'r')
    file_str = t_file.read()
    t_file.close()

    for k, v in config[template].items():
        template_key = build_template_key(k)
        file_str = file_str.replace(template_key, v)

    out_filename = template.replace('.tpl', '')
    o_file = open(out_filename, 'w')
    o_file.write(file_str)
    o_file.close()
    # add exec bit if needed (for shell, python, Perl, ruby)
    if out_filename.endswith('.sh') or out_filename.endswith('.py') or \
            out_filename.endswith('.pl') or out_filename.endswith('.rb'):
        os.chmod(out_filename, stat.S_IRWXU | stat.S_IRWXG | stat.S_IROTH | stat.S_IXOTH)


do_list_template = False
destination_dir = None
cfg_path = None
cfg = None

try:
    opts, args = getopt.getopt(
        sys.argv[1:], "hd:lc:", ['help', 'directory=', 'list', "cfg="])
except getopt.GetoptError as err:
    print(str(err))
    usage()
    sys.exit(1)

for o, a in opts:
    if o in ("-h", "--help"):
        usage()
        sys.exit(0)
    elif o in ("-d", "--directory"):
        destination_dir = a
    elif o in ("-l", "--list"):
        do_list_template = True
    elif o in ("-c", "--cfg"):
        cfg_path = a
    else:
        usage()
        sys.exit(1)

if destination_dir is None:
    usage()
    sys.exit(1)

if cfg_path is None and not do_list_template:
    usage()
    sys.exit(1)

if not do_list_template:
    cfg = load_config(cfg_path)

pre_instantiated_templates = {}

cnt = 1
for root, dirs, files in os.walk(destination_dir):
    for template_file in get_template_files(files):
        template_file = os.path.realpath(os.path.join(root, template_file))

        # list templates only
        if do_list_template:
            print("%2d. template %s" % (cnt, template_file))
            cnt += 1
            continue
        # instantiate template
        else:
            # skip template file which can not be instantiated
            if template_file not in cfg:
                pre_instantiated_templates[template_file] = 1
                continue

            print("%2d. instantiating %s" % (cnt, template_file))
            cnt += 1
            if not do_list_template:
                instantiate_template(cfg, template_file)

if not do_list_template:
    print("pre-instantiated templates:")
    cnt = 1
    for f in pre_instantiated_templates.keys():
        print("%2d. template %s" % (cnt, f))
        cnt += 1
