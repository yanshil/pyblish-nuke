# -*- coding: utf-8 -*-

name = "pyblish_nuke"

version = "0.0.1"

description = "pyblish tools nuke module"

authors = [""]

tools = []

requires = ["pyblish_base"]

build_command = 'rez env python -c "python {root}/rezbuild.py {install}"'

format_version = 2


def commands():
    env.PYTHONPATH.append("{root}")
    env.PYBLISHPLUGINPATH.append("{root}/plugins")
