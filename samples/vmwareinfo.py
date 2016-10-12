#!/usr/bin/env python
# VMware vSphere Python SDK
# Copyright (c) 2008-2013 VMware, Inc. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
Python program for listing the vms on an ESX / vCenter host
"""

import atexit

from pyVim import connect
from pyVmomi import vmodl, vim

import tools.cli as cli

import ssl


def print_vm_info(virtual_machine):
    """
    Print information for a particular virtual machine or recurse into a
    folder with depth protection
    """
    summary = virtual_machine.summary
    print("Name       : ", summary.config.name)
    print("Template   : ", summary.config.template)
    print("Path       : ", summary.config.vmPathName)
    print("Guest      : ", summary.config.guestFullName)
    print("Instance UUID : ", summary.config.instanceUuid)
    print("Bios UUID     : ", summary.config.uuid)
    annotation = summary.config.annotation
    if annotation:
        print("Annotation : ", annotation)
    print("State      : ", summary.runtime.powerState)
    if summary.guest is not None:
        ip_address = summary.guest.ipAddress
        tools_version = summary.guest.toolsStatus
        if tools_version is not None:
            print("VMware-tools: ", tools_version)
        else:
            print("Vmware-tools: None")
        if ip_address:
            print("IP         : ", ip_address)
        else:
            print("IP         : None")
    if summary.runtime.question is not None:
        print("Question  : ", summary.runtime.question.text)
    print("")


def main():
    """
    Simple command-line program for listing the virtual machines on a system.
    """

    args = cli.get_args()

    ssl_options = ssl.create_default_context(purpose=ssl.Purpose.SERVER_AUTH,
                                             capath=None, cadata=None)
    if args.insecure:
        ssl_options.check_hostname = False
        ssl_options.verify_mode = ssl.CERT_NONE

    try:
        service_instance = connect.SmartConnect(host=args.host,
                                                user=args.user,
                                                pwd=args.password,
                                                port=int(args.port),
                                                sslContext=ssl_options)

        atexit.register(connect.Disconnect, service_instance)

        content = service_instance.RetrieveContent()

#        print('**** content object: ****')
#        print(dir(content))
#        print('\n**** vim.Datacenter object: ****')
#        print(dir(vim.Datacenter))
#        print('\n**** vim.Datacenter.datastoreFolderobject: ****')
#        print(dir(vim.Datacenter.datastoreFolder))
#        print('\n**** vim.Datastore object: ****')
#        print(dir(vim.Datastore))
#        print('\n**** vim.ResourcePool object: ****')
#        print(dir(vim.ResourcePool))
        print('\n**** vim.VirtualMachine object: ****')
        print(dir(vim.VirtualMachine))
#        print('\n**** content.rootFolder object: ****')
#        print(dir(content.rootFolder))

#        vchtime = service_instance.CurrentTime()

#        object_view = content.ViewManager.CreateContainerView(content.rootFolder, [], True)
#        for obj in object_view.view:
#            print(ojb)

        # Get all performance counters
        perf_dict = {}
        perfList = content.perfManager.perfCounter
        for counter in perfList:
            counter_full = "{}.{}.{}".format(counter.groupInfo.key, counter.nameInfo.key, counter.rollupType)
            perf_dict[counter_full] = counter.key

#        return 0

        container = content.rootFolder  # starting point to look into
        viewType = [vim.VirtualMachine]  # object types to look for
        recursive = True  # whether we should look into it recursively
        containerView = content.viewManager.CreateContainerView(
            container, viewType, recursive)

        children = containerView.view
        for child in children:
            print_vm_info(child)

    except vmodl.MethodFault as error:
        print("Caught vmodl fault : " + error.msg)
        return -1

    return 0

# Start program
if __name__ == "__main__":
    main()
