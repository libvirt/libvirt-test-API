# Set and show scheduler parameters with flag, such as "--current", "--live"
# and "--config"

import libvirt
from libvirt import libvirtError

from libvirttestapi.src import sharedmod
from libvirttestapi.utils import utils
from xml.dom import minidom
import os
import re

required_params = ('guestname', 'vcpuquota', 'vcpuperiod', 'emulatorperiod',
                   'emulatorquota', 'cpushares', 'flag',)
optional_params = {'iothreadperiod': '',
                   'iothreadquota': '',
                   }

CGROUP_PATH = '/sys/fs/cgroup/cpu,cpuacct/machine.slice/'
CGROUP_RE = 'machine-qemu.*?%s.scope'


def get_cgroup_path(guestname, logger):
    for path in os.listdir(CGROUP_PATH):
        logger.debug("Check" + path)
        logger.debug("Check" + CGROUP_RE % guestname)
        if re.match(CGROUP_RE % guestname, path):
            return CGROUP_PATH + path + "/"
        if re.match(CGROUP_RE % guestname.replace('_', ''), path):
            return CGROUP_PATH + path + "/"
    return False


def get_iothread_path(cgroup_path, logger):
    cmd = "find %s -name 'iothread*'" % cgroup_path.replace("\\", "\\\\")
    status, out = utils.exec_cmd(cmd, shell=True)
    if status:
        logger.error("Failed to get iothread path. out: %s" % out)
        return False

    if len(out) < 1:
        logger.error("iothread path is not exist.")
        return False

    return os.path.basename(out[0])


def check_sched_params_flag(guestname, domobj, sched_params_after, domstate,
                            flags_value):
    """Check scheduler parameters validity after setting
    """

    if (domstate == 1) and ((flags_value == 0) or (flags_value == 1)):
        """While the domain is running and the flag is "--live" or "--current",
           the value can be checked with the cgroup value
           As for the other condition, the value can be checked with the domain
           config xml
        """
        if os.path.exists("/cgroup"):
            """ Add the judgment method, since the cgroup path is different on
                rhel6 and rhel7.
                if the folder cgroup is existed, it means the host os is rhel6,
                if not existed, it means the the host of is rhel7
            """
            cgroup_path = "cat /cgroup/cpu/libvirt/qemu/%s/" % guestname
        else:
            cgroup_path = get_cgroup_path(guestname, logger)
            if not cgroup_path:
                logger.error("cgroup path don't exist.")
                return 1

        if utils.version_compare("libvirt-python", 2, 5, 0, logger):
            iothread_path = get_iothread_path(cgroup_path, logger)
            if not iothread_path:
                return 1

            sched_dicts = {'vcpu_quota': 'vcpu0/cpu.cfs_quota_us',
                           'vcpu_period': 'vcpu0/cpu.cfs_period_us',
                           'emulator_period': 'emulator/cpu.cfs_period_us',
                           'emulator_quota': 'emulator/cpu.cfs_quota_us',
                           'cpu_shares': 'cpu.shares',
                           'iothread_period': '%s/cpu.cfs_period_us' % iothread_path,
                           'iothread_quota': '%s/cpu.cfs_quota_us' % iothread_path}
        else:
            sched_dicts = {'vcpu_quota': 'vcpu0/cpu.cfs_quota_us',
                           'vcpu_period': 'vcpu0/cpu.cfs_period_us',
                           'emulator_period': 'emulator/cpu.cfs_period_us',
                           'emulator_quota': 'emulator/cpu.cfs_quota_us',
                           'cpu_shares': 'cpu.shares'}

        for sched_key in sched_dicts:
            cmd = "cat " + cgroup_path.replace("\\", "\\\\") + sched_dicts[sched_key]
            status, cmd_value = utils.exec_cmd(cmd, shell=True)
            if status:
                logger.error("failed to get ***%s*** value" % sched_key)
                return 1
            sched_dicts[sched_key] = int(cmd_value[0])
            if sched_dicts[sched_key] != sched_params_after[sched_key]:
                logger.error("set scheduler parameters failed")
                return 1

    else:
        guestxml = domobj.XMLDesc(libvirt.VIR_DOMAIN_XML_INACTIVE)
        logger.debug("domain %s config xml :\n%s" % (domobj.name(), guestxml))

        xmlrootnode = minidom.parseString(guestxml)

        if utils.version_compare("libvirt-python", 2, 5, 0, logger):
            sched_dicts = {'vcpu_quota': 'quota', 'vcpu_period': 'period',
                           'emulator_period': 'emulator_period',
                           'emulator_quota': 'emulator_quota',
                           'cpu_shares': 'shares',
                           'iothread_period': 'iothread_period',
                           'iothread_quota': 'iothread_quota'}
        else:
            sched_dicts = {'vcpu_quota': 'quota', 'vcpu_period': 'period',
                           'emulator_period': 'emulator_period',
                           'emulator_quota': 'emulator_quota',
                           'cpu_shares': 'shares'}

        for sched_key in sched_dicts:
            node = xmlrootnode.getElementsByTagName(sched_dicts[sched_key])[0]
            sched_dicts[sched_key] = int(node.childNodes[0].data)
            if sched_dicts[sched_key] != sched_params_after[sched_key]:
                logger.error("set scheduler parameters failed")
                return 1

    logger.info("set scheduler parameters success")
    return 0


def sched_params_flag(params):
    """ Change and get the scheduler parameters
    """

    global logger
    logger = params['logger']
    guestname = params['guestname']

    if utils.version_compare("libvirt-python", 2, 5, 0, logger):
        dicts = {'vcpu_quota': int(params['vcpuquota']),
                 'vcpu_period': int(params['vcpuperiod']),
                 'emulator_period': int(params['emulatorperiod']),
                 'emulator_quota': int(params['emulatorquota']),
                 'cpu_shares': int(params['cpushares']),
                 'iothread_period': int(params['iothreadperiod']),
                 'iothread_quota': int(params['iothreadquota'])}
    else:
        dicts = {'vcpu_quota': int(params['vcpuquota']),
                 'vcpu_period': int(params['vcpuperiod']),
                 'emulator_period': int(params['emulatorperiod']),
                 'emulator_quota': int(params['emulatorquota']),
                 'cpu_shares': int(params['cpushares'])}

    flags = params['flag']

    try:
        conn = sharedmod.libvirtobj['conn']
        domobj = conn.lookupByName(guestname)

        domstate = domobj.state(0)[0]
        """virDomainState
           VIR_DOMAIN_NOSTATE = 0
           VIR_DOMAIN_RUNNING = 1
           VIR_DOMAIN_BLOCKED = 2
           VIR_DOMAIN_PAUSED = 3
           VIR_DOMAIN_SHUTDOWN = 4
           VIR_DOMAIN_SHUTOFF = 5
           VIR_DOMAIN_CRASHED = 6
           VIR_DOMAIN_PMSUSPENDED = 7

           please see the following reference link:
           http://libvirt.org/html/libvirt-libvirt.html#virDomainState
        """
        if domstate == libvirt.VIR_DOMAIN_RUNNING:
            logger.info("the state of virtual machine is ***running***")
        elif domstate == libvirt.VIR_DOMAIN_SHUTOFF:
            logger.info("the state of virtual machine is ***shutoff***")
        else:
            logger.error("the state of virtual machine is not running or "
                         "shutoff now, it is out of the check range of this "
                         "script. Please check the domain status.")
            return 1

        """virDomainModificationImpact
           VIR_DOMAIN_AFFECT_CURRENT = 0
           VIR_DOMAIN_AFFECT_LIVE = 1
           VIR_DOMAIN_AFFECT_CONFIG = 2
        """

        if flags == "current":
            flags_value = libvirt.VIR_DOMAIN_AFFECT_CURRENT
        elif flags == "live":
            flags_value = libvirt.VIR_DOMAIN_AFFECT_LIVE
        elif flags == "config":
            flags_value = libvirt.VIR_DOMAIN_AFFECT_CONFIG
        else:
            logger.error("the value of flags is not correct, please check "
                         "the conf file")
            return 1

        sched_type = str(domobj.schedulerType()[0])
        logger.info("the scheduler type is: %s" % sched_type)
        sched_params_original = domobj.schedulerParametersFlags(flags_value)
        logger.info("original scheduler parameters with flag ***%s***: %s" %
                    (flags, sched_params_original))
        logger.info("setting scheduler parameters: %s" % dicts)
        domobj.setSchedulerParametersFlags(dicts, flags_value)
        sched_params_after = domobj.schedulerParametersFlags(flags_value)
        logger.info("current scheduler parameters with flag ***%s***: %s" %
                    (flags, sched_params_after))

        ret = check_sched_params_flag(guestname, domobj, sched_params_after,
                                      domstate, flags_value)

        return ret
    except libvirtError as e:
        logger.error("libvirt call failed: " + str(e))
        return 1
