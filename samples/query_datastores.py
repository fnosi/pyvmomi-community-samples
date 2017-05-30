#!/usr/bin/env python
#
# Based on list_dc_datastore_info.py which carries this copyright:
#
# Written by JM Lopez
# GitHub: https://github.com/jm66
# Email: jm@jmll.me
# Website: http://jose-manuel.me
#
# Note: Example code For testing purposes only
#
# This code has been released under the terms of the Apache-2.0 license
# http://opensource.org/licenses/Apache-2.0
#

import atexit
import requests
from tools import cli
from pyVmomi import vim
from pyVim.connect import SmartConnect, Disconnect

import ssl

# disable  urllib3 warnings
if hasattr(requests.packages.urllib3, 'disable_warnings'):
    requests.packages.urllib3.disable_warnings()


def get_args():
    parser = cli.build_arg_parser()
    parser.add_argument('-n', '--name', required=False,
                        help="Name of the Datastore.")
    parser.add_argument('-d', '--datacenter', required=False,
                        help="Filter by Datacenter. If both"
                                " cluster and datacenter are set,"
                                " only datacenter will be used.")
    parser.add_argument('-c', '--cluster', required=False,
                        help="Filter by Cluster. If both"
                                " cluster and datacenter are set,"
                                " only datacenter will be used.")
    parser.add_argument('-m', '--max-free-space', required=False,
                        default=False,
                        action='store_true',
                        help="Show only the multihosted datastore with the most free space")
    parser.add_argument('-v', '--verbose', required=False,
                        default=False,
                        action='store_true',
                        help="Verbose output")
    my_args = parser.parse_args()
    return cli.prompt_for_password(my_args)


def get_obj(content, vimtype, name=None, **kwargs):
    """
    Returns an object based on it's vimtype and name
    """
    obj = None
    obj_container = kwargs.get('container', content.rootFolder)
    container = content.viewManager.CreateContainerView(
        obj_container, vimtype, True)
    if name:
        for c in container.view:
            if c.name == name:
                obj = c
                break
        return obj
    else:
        return container.view


# http://stackoverflow.com/questions/1094841/
def sizeof_fmt(num):
    """
    Returns the human readable version of a file size

    :param num:
    :return:
    """
    for item in ['bytes', 'KB', 'MB', 'GB']:
        if num < 1024.0:
            return "%3.1f%s" % (num, item)
        num /= 1024.0
    return "%3.1f%s" % (num, 'TB')


def print_datastore_info(ds_obj):
    summary = ds_obj.summary
    ds_capacity = summary.capacity
    ds_freespace = summary.freeSpace
    ds_uncommitted = summary.uncommitted if summary.uncommitted else 0
    ds_provisioned = ds_capacity - ds_freespace + ds_uncommitted
    ds_overp = ds_provisioned - ds_capacity
    ds_overp_pct = (ds_overp * 100) / ds_capacity \
        if ds_capacity else 0
    print ""
    print "Name                  : {}".format(summary.name)
    print "URL                   : {}".format(summary.url)
    print "Capacity              : {} GB".format(sizeof_fmt(ds_capacity))
    print "Free Space            : {} GB".format(sizeof_fmt(ds_freespace))
    print "Uncommitted           : {} GB".format(sizeof_fmt(ds_uncommitted))
    print "Provisioned           : {} GB".format(sizeof_fmt(ds_provisioned))
    if ds_overp > 0:
        print "Over-provisioned      : {} GB / {} %".format(
            sizeof_fmt(ds_overp),
            ds_overp_pct)
    print "Hosts                 : {}".format(len(ds_obj.host))
    print "Virtual Machines      : {}".format(len(ds_obj.vm))
    print "Accessible            : {}".format(summary.accessible)
    print "multipleHostAccess    : {}".format(summary.multipleHostAccess)


def main():
    args = get_args()

    ssl_options = ssl.create_default_context(purpose=ssl.Purpose.SERVER_AUTH,
                                            capath=None, cadata=None)
    if args.insecure:
        ssl_options.check_hostname = False
        ssl_options.verify_mode = ssl.CERT_NONE

    # connect to vc
    si = SmartConnect(
        host=args.host,
        user=args.user,
        pwd=args.password,
        port=args.port,
        sslContext=ssl_options)
    # disconnect vc
    atexit.register(Disconnect, si)

    content = si.RetrieveContent()

    # Filter by Cluster - this returns no datastores later, maybe because Datastores
    # are contained inside Datacenters?
    #if args.cluster:
    #    search_container = [vim.ClusterComputeResource]
    if args.datacenter:
        datacenter_name = args.datacenter
        datacenter = get_obj(content, [vim.Datacenter], datacenter_name)
        if datacenter is None:
            print("Datacenter {} not found.".format(datacenter_name))
            return 0
        print("Found Datacenter {}".format(datacenter_name))
        ds_obj_list = get_obj(content, [vim.Datastore], container=datacenter)
    elif args.cluster:
        cluster_name = args.cluster
        cluster = get_obj(content, [vim.ClusterComputeResource], cluster_name)
        if cluster is None:
            print("Cluster {} not found.".format(cluster_name))
            return 0
        print("Found Cluster {}:".format(cluster_name))
        print(cluster.summary)
        #ds_obj_list = get_obj(content, [vim.Datastore], container=cluster)
        ds_obj_list = cluster.datastore
    else:
        ds_obj_list = get_obj(content, [vim.Datastore], args.name)

    max_freeSpace = 0
    choosen_ds = None

    for ds in ds_obj_list:
        if args.verbose:
            print_datastore_info(ds)
        if ds.summary.multipleHostAccess:
            if ds.summary.freeSpace > max_freeSpace:
                max_freeSpace = ds.summary.freeSpace
                choosen_ds = ds

    if args.max_free_space:
        print("\n\n")
        if choosen_ds is None:
            print("No Datastore found")
        else:
            print("Choosen Datastore is:")
            print_datastore_info(choosen_ds)

# start
if __name__ == "__main__":
    main()
