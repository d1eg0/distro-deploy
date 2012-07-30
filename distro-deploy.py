#!/usr/bin/python
"""Real-Time Linux installer

Installs a debian distro with the rt kernel patch.
"""
import sys
import getopt
import os
import subprocess
import re

MOUNT_POINT = '/mnt/raptorrt'
PATH_DISTRO= '/media/Dades/Proyectos/Raptor/backup/rt_backup_newboard.tgz'
LOG_FILE = 'log.out'
ERR_LOG_FILE = 'log_err.out'

def clean_logs():
    try:
        subprocess.call(['rm',LOG_FILE])
    except:
        pass
    
    try:
        subprocess.call(['rm',ERR_LOG_FILE])
    except:
        pass

def list_devices():
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
    device_info = dict()

    device_info['label'] = get_label(line)     
    device_info['partition'] = get_partition(line) 
    device_info['device'] = get_device(line) 
    device_info['fstype'] = get_type(line) 
    return device_info

def get_label(line):
    try:
        return re.search(r"LABEL=\"(\w+)?\"",line).group(1)
    except:
        return ''


def get_partition(line):
    try:
        return re.search(r"(\/dev\/\w+)?",line).group(0)
    except:
        return ''


def get_device(line):
    try:
        return re.search(r"(\/dev\/\w+)?[1-9]",line).group(1)
    except:
        return ''


def get_type(line):
    try:
        return re.search(r"TYPE=\"(\w+)?\"",line).group(1)  
    except:
        return ''


def umount_device(device):
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
    device_path = device['partition'][0:len(device['partition'])-1]
    with open(LOG_FILE,'a') as out_log:
        with open(ERR_LOG_FILE,'a') as err_log:
            #fdisk method

            #opts = subprocess.Popen(
            #    ["cat","fdisk.opts"],
            #    stdout=subprocess.PIPE,
            #    stderr=err_log
            #)
            #subprocess.Popen(
            #    ["fdisk",device_path],
            #    stdin=opts.stdout,
            #    stdout=out_log,
            #    stderr=err_log
            #).wait()

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

def deploy_distro():
    with open(LOG_FILE,'a') as out_log:
        with open(ERR_LOG_FILE,'a') as err_log:
            subprocess.Popen(
                ["tar","-zxvf",PATH_DISTRO,"-C",MOUNT_POINT],
                stdout=out_log,
                stderr=err_log
            ).wait()

def update_grub():
    import os
    with open(LOG_FILE,'a') as out_log:
        with open(ERR_LOG_FILE,'a') as err_log:
            subprocess.call(
                ["mount","--bind","/proc","%s%s" %(MOUNT_POINT,"/proc")],
                stdout=out_log,
                stderr=err_log
            ).wait()
            subprocess.call(
                ["mount","--bind","/dev","%s%s" %(MOUNT_POINT,"/dev")],
                stdout=out_log,
                stderr=err_log
            ).wait()
            subprocess.Popen(
                ["chroot",MOUNT_POINT,"update-grub"],
                stdout=out_log,
                stderr=err_log
            ).wait()
            subprocess.call(
                ["umount","%s%s" %(MOUNT_POINT,"/proc")],
                stdout=out_log,
                stderr=err_log
            ).wait()
            subprocess.call(
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
    while 1:
        sure_q = raw_input(
            "\nAll data in %s will be deleted. Are you sure? (y=yes,n=no or q to quit):")
        if sure_q=="y":
            return 2
        elif sure_q=="n":
            return 1
        elif sure_q=="q":
            return 0

def main():
    # parse command line options
    try:
        opts, args = getopt.getopt(sys.argv[1:], "h", ["help"])
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

    clean_logs()
    while 1:
        devices_info = list_devices()
        device_select = raw_input(
            "\nEnter the partition number to format (q to quit):")
        try:
            device_select = int(device_select)-1
            if device_select>=0 and device_select<len(devices_info):
                answ = sure_question()
                if answ==0:
                    #quit
                    return
                elif answ==1:
                    #no format
                    pass
                elif answ==2:
                    #format
                    device = devices_info[device_select]
                    umount_device(device)
                    print 'Formatting device...'
                    format_device("ext3", device)
                    print '\rOk'
                        #umount_device(device)
                        #label_device(device)
                    mount_device(device)
                    #deploy linux rt
                    print 'Deploying linux rt...'
                    deploy_distro()
                    print '\rOk'
                    print 'Updating grub bootloader...'
                    update_grub()
                    print '\rOk'
                    umount_device(device)
                    print "\nProcess finished sucessfull!\n"


                    return

        except:
            #print "Unexpected error:", sys.exc_info()[0]
            if device_select=="q":
                return
            else:
                pass




if __name__ == "__main__":
    main()
