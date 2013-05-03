#!/usr/bin/python
"""Distro-Deploy

Deploys a linux distro in a Flash memory. Creates a partition table and a ext3
filesystem. Set partition bootable flag on. Finally, updates the grub
configuration.

Usage:

    distro-deploy.py --input=rt_distro.tgz
"""
import sys
import getopt
import os
import subprocess
import re


#default mount point (DON'T CHANGE)
MOUNT_POINT = '/mnt/raptorrt'

#process output log file
LOG_FILE = 'log.out'
#process errors log file
ERR_LOG_FILE = 'log_err.out'

def clean_logs():
    """Delete log files
    """
    try:
        subprocess.call(['rm',LOG_FILE])
    except:
        pass
    
    try:
        subprocess.call(['rm',ERR_LOG_FILE])
    except:
        pass

def list_devices():
    """Get storage devices ids and list them.
    """
    devices_info = list()
    with open(ERR_LOG_FILE,'a') as err_log:
        devices = subprocess.Popen(
            ["blkid"],
            stdout=subprocess.PIPE,
            stderr=err_log
        )
        devices.wait()

    device_id = 1;
    for line in devices.stdout.readlines():
        device_info = parse_device_info(line)
        print '\t[%d] label:%s dev:%s fstype:%s' % (
            device_id,device_info['label'],device_info['partition'],device_info['fstype'])
        devices_info.append(device_info)
        device_id = device_id + 1

    return devices_info


def parse_device_info(line):
    """Parses line device info.
    """
    device_info = dict()

    device_info['label'] = get_label(line)     
    device_info['partition'] = get_partition(line) 
    device_info['device'] = get_device(line) 
    device_info['fstype'] = get_type(line) 
    return device_info

def get_label(line):
    """Gets label field from line device info.
    """
    try:
        return re.search(r"LABEL=\"(\w+)?\"",line).group(1)
    except:
        return ''


def get_partition(line):
    """Gets partition path from line device info.
    """
    try:
        return re.search(r"(\/dev\/\w+)?",line).group(0)
    except:
        return ''


def get_device(line):
    """Gets device path from line device info.
    """
    try:
        return re.search(r"(\/dev\/\w+)?[1-9]",line).group(1)
    except:
        return ''


def get_type(line):
    """Gets filesystem type from line device info.
    """
    try:
        return re.search(r"TYPE=\"(\w+)?\"",line).group(1)  
    except:
        return ''


def umount_device(device):
    """Umounts device and deletes mount point.
    """
    with open(LOG_FILE,'a') as out_log:
        with open(ERR_LOG_FILE,'a') as err_log:
            subprocess.Popen(
                ["umount",device['partition']],
                stdout=out_log,
                stderr=err_log
            ).wait()
            try:
                subprocess.Popen(
                    ["rm","-rf",MOUNT_POINT],
                    stdout=out_log,
                    stderr=err_log
                ).wait()
            except:
                pass

def mount_device(device):
    """Creates MOUNT_POINT dir and mounts the device in,
    """
    with open(LOG_FILE,'a') as out_log:
        with open(ERR_LOG_FILE,'a') as err_log:
            subprocess.Popen(
                ["mkdir",MOUNT_POINT],
                stdout=out_log,
                stderr=err_log
            ).wait()
            subprocess.Popen(
                ["mount",device['partition'],MOUNT_POINT],
                stdout=out_log,
                stderr=err_log
            ).wait()

def format_device(fstype, device):
    """Creates table partition and the filesystem fstype on device.
    """
    device_path = device['partition'][0:len(device['partition'])-1]
    with open(LOG_FILE,'a') as out_log:
        with open(ERR_LOG_FILE,'a') as err_log:
            #sfdisk method

            #create partition table
            #one partition with all available space
            opts = subprocess.Popen(
                ["echo","0,,L"],
                stdout=subprocess.PIPE,
                stderr=err_log
            )
            subprocess.Popen(
                ["sfdisk",device['device']],
                stdin=opts.stdout,
                stdout=out_log,
                stderr=err_log
            ).wait()
            #make the partition booteable
            subprocess.Popen(
                ["sfdisk",device['device'],"-A","1"],
                stdout=out_log,
                stderr=err_log
            ).wait()
            #create filesystem
            subprocess.Popen(
                ["mkfs","-t",fstype,device['partition']],
                stdout=out_log,
                stderr=err_log
            ).wait()

def deploy_distro(input_distro):
    """Uncompress targz distro file from PATH_DISTRO to MOUNT_POINT.
    """
    with open(LOG_FILE,'a') as out_log:
        with open(ERR_LOG_FILE,'a') as err_log:
            subprocess.Popen(
                ["tar","-zxvf",input_distro,"-C",MOUNT_POINT],
                stdout=out_log,
                stderr=err_log
            ).wait()

def update_grub(device):
    """Updates grub configuration.
    """
    with open(LOG_FILE,'a') as out_log:
        with open(ERR_LOG_FILE,'a') as err_log:
            subprocess.Popen(
                ["mount","--bind","/proc","%s%s" %(MOUNT_POINT,"/proc")],
                stdout=out_log,
                stderr=err_log
            ).wait()
            #print ["mount","--bind","/dev","%s%s" %(MOUNT_POINT,"/dev")]
            subprocess.Popen(
                ["mount","--bind","/dev","%s%s" %(MOUNT_POINT,"/dev")],
                stdout=out_log,
                stderr=err_log
            ).wait()
            subprocess.Popen(
                ["chroot",MOUNT_POINT,"grub-install %s" % (device['device'])],
                stdout=out_log,
                stderr=err_log
            ).wait()
            subprocess.Popen(
                ["chroot",MOUNT_POINT,"update-grub"],
                stdout=out_log,
                stderr=err_log
            ).wait()
            subprocess.Popen(
                ["umount","%s%s" %(MOUNT_POINT,"/proc")],
                stdout=out_log,
                stderr=err_log
            ).wait()
            subprocess.Popen(
                ["umount","%s%s" %(MOUNT_POINT,"/dev")],
                stdout=out_log,
                stderr=err_log
            ).wait()


def label_device():
    with open(LOG_FILE,'a') as out_log:
        with open(ERR_LOG_FILE,'a') as err_log:
            subprocess.Popen(
                ["e2label",device['partition'],'RAPTORRT'],
                stdout=out_log,
                stderr=err_log
            )


def sure_question():
    """Asks a question to be sure to delete all the data from device.
    """
    while 1:
        sure_q = raw_input(
            "\nAll data in %s will be deleted. Are you sure? (y=yes,n=no or q to quit):")
        if sure_q=="y":
            return 2
        elif sure_q=="n":
            return 1
        elif sure_q=="q":
            return 0


def do_all(device,input_distro):
    """Format device, deploy targz distro file and updates grub configuration.
    """
    #format
    umount_device(device)
    print 'Formatting device...'
    format_device("ext2", device)
    print '\rOk'
        #umount_device(device)
        #label_device(device)
    mount_device(device)
    #deploy linux rt
    print 'Deploying linux rt...'
    deploy_distro(input_distro)
    print '\rOk'
    print 'Updating grub bootloader...'
    update_grub(device)
    print '\rOk'
    umount_device(device)
    print "\nProcess finished sucessfull!\n"


def main():
    # parse command line options
    input_distro = None
    try:
        opts, args = getopt.getopt(sys.argv[1:], "hi", ["help","input="])
    except getopt.error, msg:
        print msg
        print "for help use --help"
        sys.exit(2)

    # process options
    for o, a in opts:
        if o in ("-h", "--help"):
            print __doc__
            sys.exit(0)
            # process arguments
            for arg in args:
                process(arg) # process() is defined elsewhere

        elif o in ("-i", "--input"):
            input_distro = a
     

    if input_distro == None:
        print __doc__
        sys.exit(0)


    clean_logs()
    while 1:
        devices_info = list_devices()
        device_select = raw_input(
            "\nEnter the partition number to format (q to quit):")
        if device_select=="q":
            return
        else:
            try:
                device_select = int(device_select)-1
                if device_select>=0 and device_select<len(devices_info):
                    device = devices_info[device_select]
                    answ = sure_question()
                    if answ==0:
                        #quit
                        return
                    elif answ==1:
                        pass
                    elif answ==2:
                        do_all(device,input_distro)
                        return
                else:
                    print "Wrong device number, try again...\n"
            except ValueError:
                print "Wrong value introduced!\n"



if __name__ == "__main__":
#check root permissions
    if os.geteuid() != 0:
        print "Error: only root can call this script, use sudo instead"
        sys.exit(0)

    main()

