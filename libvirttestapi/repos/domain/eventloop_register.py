# Copyright (C) 2010-2012 Red Hat, Inc.
# This work is licensed under the GNU GPLv2 or later.
import libvirt

from libvirttestapi.utils.events import virEventLoopPureThread

required_params = ()
optional_params = {}


def eventloop_register(params):
    logger = params['logger']

    eventLoop = virEventLoopPureThread(logger)
    eventLoop.regist(libvirt)
    eventLoop.start()

    return 0
