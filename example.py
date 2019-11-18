#!/usr/bin/env python3.7
import pathlib
import time

from hcibenchapi.HCIBenchAPI import HCIBenchAPI

# HCIBench IP and Credential
hcibench_ip = '172.16.27.155'
hcibench_username = 'root'
hcibench_password = 'vmware'
hcibench_tool = 'fio'

# Sample fio file to upload
fio_param_file = 'fio-1vmdk-100ws-4-100rdpct-100randompct-2threads'
fio_param_path = 'data/' + fio_param_file

# Zip file with VDBench executable to upload
vdbench_zip_file = 'vdbench50407.zip'
vdbench_zip_path = 'data/' + vdbench_zip_file

request_body = {
    # Which tool to use (fio/vdbench)
    "tool": 'fio',

    # vCenter IP or hostname
    "vcenterIp": "lab03m01vc01.lab03.vsanpe.vmware.com",

    # vCenter admin username
    "vcenterName": "administrator@vsphere.local",

    # vCenter admin password
    "vcenterPwd": "P@ssword123!",

    # Datacenter Name
    "dcenterName": "lab03-m01-dc",

    # Cluster Name
    "clusterName": "lab03-m01-mgmt01",

    # Resource Pool Name (OPTIONAL)
    "rpName": "",

    # VM Folder Name (OPTIONAL)
    "fdName": "",

    # Network Name (OPTIONAL), if not filled, use "VM Network"
    "networkName": "1284 vm network",

    # set to true if no DHCP in your network, true/false
    "staticEnabled": "false",

    # 172.16, 172.18, ..., 172.31, 192.168 (OPTIONAL), must be specified if staticEnabled set to true
    # Note: 172.17 is excluded because it is used by the internal Docker network.
    "staticIpprefix": "172.28",

    # Name of datastore(s), if you have more datastores to specify, do "datastore1\ndatastor2\ndatastore3
    "dstoreName": "lab03-m01-vsan",

    # Storage policy to use (OPTIONAL) if not specified, the datastores' default policy will be used
    "storagePolicy": "",

    # Set to true if you want to deploy VMs onto particular hosts, true/false
    "deployHost": "false",

    # Specify the hosts you want to deploy your VMs on (OPTIONAL) "host1\nhost2\nhost3"
    "hosts": "",

    # Clear read/write cache/buffer before each test case, only applicable on vSAN, true/false
    "clearCache": "false",

    # ESXi host username, must be specified if clearCache set to true (OPTIONAL)
    "hostName": "root",

    # ESXi host password, must be specified if clearCache set to true (OPTIONAL)
    "hostPwd": "P@ssw0rd123!",

    # Whether reuse the existing guest VMs if applicable, true/false
    "reuseVM": "true",

    # Easy run, only applicable on vSAN, true/false
    "easyRun": "false",

    # Choose one or multiple from 4k70r, 4k100r, 8k50r, 256k0r, must be specified
    # if easyRun set to true e.g. "4k70r,8k50r"
    "workloads": "",

    # Note: If easy run set to true, no need to fill up the following parameters
    # --------------------------------------------------------------------------
    # VM name prefix, no more than 7 chars
    "vmPrefix": "hci-vdb",

    # Number of VMs to deploy
    "vmNum": "20",

    # Number of data disks per VM
    "diskNum": "8",

    # Size(GB) of each data disk
    "diskSize": "20",

    # Where to find workload param files
    "filePath": "/opt/automation/fio-param-files",

    # Test Name, will create a directory /opt/output/results/results20191015144137
    "outPath": "DemoTest",

    # NONE/ZERO/RANDOM
    "warmUp": "RANDOM",

    # Testing time (OPTIONAL)
    "duration": "3600",

    # Whether delete all guest VMs when testing is done, true/false
    "cleanUp": "false",

    # The workload param file name, if not specified, will "USE ALL", for either fio or vdbench
    "selectVdbench": "fio-1vmdk-100ws-4-100rdpct-100randompct-2threads"
}

param_body = {
    # Number of disks will be tested against, 1+ integer, has to be equal or less than diskNum in request_body
    "diskNum": "8",

    # Workingset, 1-100 integer
    "workSet": "100",

    # Number of threads per VMDK, 1+ integer
    "threadNum": "4",

    # Blocksize, "4k", "8k", "1024k"...
    "blockSize": "4k",

    # Read percentage, 0-100 integer
    "readPercent": "70",

    # Random percentage, 0-100 integer
    "randomPercent": "100",

    # IO Rate limitaion per VM, 1+ integer (OPTIONAL)
    "ioRate": "",

    # Testing time in seconds, 1+ integer
    "testTime": "600",

    # Warmup time in seconds, 1+ integer (OPTIONAL)
    "warmupTime": "120",

    # Reporting interval time, 1+ integer (OPTIONAL)
    "intervalTime": "",

    # Which tool to use (fio/vdbench)
    "tool": 'fio'
}

print('Starting HCIBench Example\n--------------------------------------------------------\n')

print("1. Creating HCIBenchAPI object\n",
      "  Host: %s\n" % hcibench_ip,
      "  Username: %s\n" % hcibench_username,
      "  Password: %s\n" % hcibench_password,
      "  Tool: %s\n" % hcibench_tool)
hcib = HCIBenchAPI(hcibench_ip, hcibench_username, hcibench_password, hcibench_tool)

print("2. Kill testing")
status, data = hcib.kill_testing()
print("   Status: %s\n" % status,
      "  Data: %s\n" % data)

print("3. Uploading FIO parameter file\n",
      "  Path: %s" % fio_param_path)
if pathlib.Path(fio_param_path).exists():
    status, data = hcib.upload_param_file(fio_param_path)
    print("   Status: %s\n" % status,
          "  Data: %s\n" % data)
else:
    print ("   FIO parameter file does not exist, skipping\n")


print("4. Getting FIO parameter files")
print("   Data: %s\n" % hcib.get_param_files('fio'))

print("5. Deleting FIO test parameters\n"
      "   Filename: %s" % fio_param_file)
status, data = hcib.delete_param_file(fio_param_file, 'fio')
print("   Status: %s\n" % status,
      "  Data: %s\n" % data)

print("6. Getting FIO parameter files")
print("   Data: %s\n" % hcib.get_param_files('fio'))

print("7. Uploading VDBench zip file\n"
      "   Path: %s" % vdbench_zip_path)
if pathlib.Path(vdbench_zip_path).exists():
    status, data = hcib.upload_vdbench_zip(vdbench_zip_path)
    print("   Status: %s\n" % status,
          "  Data: %s\n" % data)
else:
    print ("   VDBench zip file does not exist, skipping\n")

print("8. Generate parameter file")
status, data = hcib.generate_param_file(param_body)
print("   Status: %s\n" % status,
      "  Data: %s" % data)
print("   Test Name: %s\n" % HCIBenchAPI.get_param_filename(param_body))

print("9. Configure HCIBench")
status, data = hcib.configure_hcibench(request_body)
print("   Status: %s\n" % status,
      "  Data: %s\n" % data)

print("10. Reading HCIBench configuration\n"
      "    Data: %s\n" % hcib.read_hcibench_config())

print("11. Deleting worker VM")
status, data = hcib.cleanup_vms()
print("    Status: %s\n" % status,
      "   Data: %s\n" % data)

print("12. Perform prevalidation ")
status, data = hcib.prevalidation()
print("     Status: %s\n" % status,
      "    Result:\n%s\n" % data)

if status:
    print("13. Starting Test")
    status, data = hcib.start_testing()
    print("   Status: %s\n" % status,
          "  Data: %s" % data)

    print("13.1 Waiting for test completion")
    while not hcib.is_test_finished():
        status = hcib.read_test_status()
        print("   Status: %s\n" % status)
        time.sleep(180)

print("Sample complete")
