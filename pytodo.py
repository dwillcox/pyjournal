#!/usr/bin/env python3

from __future__ import print_function

import argparse
try: import ConfigParser as configparser                                        
except ImportError:                                                             
    import configparser
import os
import sys

import entry_util
import git_util

if __name__ == "__main__":

    parser = argparse.ArgumentParser()

    subparsers = parser.add_subparsers(help="commands", dest="command")

    # the show command
    show_parser = subparsers.add_parser("show", help="show a list in an editor")
    show_parser.add_argument("list-name", help="the name of the todo list to show",
                             nargs="?", default=None, type=str)

    # the cat command
    cat_parser = subparsers.add_parser("cat", help="display a list in the terminal (no editing)")
    cat_parser.add_argument("list-name", help="the name of the todo list to show",
                             nargs="?", default=None, type=str)

    # the init command
    init_parser = subparsers.add_parser("init", help="initialize a todo collection")
    init_parser.add_argument("master-path",
                             help="path where we will store the master (bare) git repo",
                             nargs=1, default=None, type=str)
    init_parser.add_argument("working-path",
                             help="path where we will store the working directory (clone of bare repo)",
                             nargs="?", default=None, type=str)

    # the connect command
    connect_parser = subparsers.add_parser("connect", help="create a local working copy of a remote todo collection")
    connect_parser.add_argument("remote-git-repo", help="the full path to the remote '.git' bare repo",
                                nargs=1, default=None, type=str)
    connect_parser.add_argument("working-path", help="the (local) path where we will store the working directory",
                                nargs=1, default=None, type=str)

    # the add command
    add_parser = subparsers.add_parser("add", help="add a new todo list to the collection")
    add_parser.add_argument("list-name", help="the name of the new todo list",
                            nargs=1, default=None, type=str)

    # the rename command
    rename_parser = subparsers.add_parser("rename", help="rename a list")
    rename_parser.add_argument("old-name", help="the existing name of the todo list",
                            nargs=1, default=None, type=str)
    rename_parser.add_argument("new-name", help="the new name of the todo list",
                            nargs=1, default=None, type=str)

    # the list command
    list_parser = subparsers.add_parser("list", help="list available todo lists")

    # the push command
    push_parser = subparsers.add_parser("push", help="push local changes to the master repo")

    # the push command
    pull_parser = subparsers.add_parser("pull", help="pull remote changes to the local todo collection")

    # the mark-default command
    make_default_parser = subparsers.add_parser("make-default",
                                                help="make a list the default for showing")
    make_default_parser.add_argument("list-name", help="the name of the todo list",
                            nargs=1, default=None, type=str)

    args = vars(parser.parse_args())


    # parse the .pytodorc file -- store the results in a dictionary
    defs = {}
    defs["param_file"] = os.path.expanduser("~") + "/.pytodorc"
    defs["default_list"] = None

    if os.path.isfile(defs["param_file"]):
        cp = configparser.ConfigParser()
        cp.optionxform = str
        cp.read(defs["param_file"])

        if not "main" in cp.sections():
            sys.exit("ERROR: no lists initialized")

        # main -- there is only one working directory/master repo for
        # all lists
        defs["working_path"] = cp.get("main", "working_path")
        defs["master_repo"] = cp.get("main", "master_repo")
        if "default_list" in cp.options("main"):
            defs["default_list"] = cp.get("main", "default_list")


    # take the appropriate action
    action = args["command"]

    if action == "show" or action == "cat":
        list_name = args["list-name"]

        if list_name == None:
            if defs["default_list"] == None:
                sys.exit("ERROR: no list specified")
            else:
                list_name = defs["default_list"]

        if action == "show":
            entry_util.show(list_name, defs)
        else:
            entry_util.cat(list_name, defs)

    elif action == "init":
        master_path = args["master-path"][0]

        if "working-path" in args.keys():
            working_path = args["working-path"]  # when using "?" argparse doesn't make this a list
        else:
            working_path = master_path

        master_path = os.path.normpath(os.path.expanduser(master_path))
        working_path = os.path.normpath(os.path.expanduser(working_path))

        git_util.init_todo(master_path, working_path, defs)

    elif action == "connect":
        master_repo = args["remote-git-repo"][0]
        working_path = args["working-path"][0]

        working_path = os.path.normpath(os.path.expanduser(working_path))

        git_util.connect_todo(master_repo, working_path, defs)

    elif action == "add":
        list_name = args["list-name"][0]
        entry_util.add_list(list_name, defs)

    elif action == "rename":
        old_name = args["old-name"][0]
        new_name = args["new-name"][0]        
        entry_util.rename_list(old_name, new_name, defs)

    elif action == "list":
        entry_util.tlist(defs)

    elif action == "make-default":
        cp.set("main", "default_list", args["list-name"][0])
        with open(defs["param_file"], "w") as config_file:
            cp.write(config_file)

    elif action == "push":
        git_util.push(defs)

    elif action == "pull":
        git_util.pull(defs)

    else:
        sys.exit("you should not have gotten here -- invalid action")
