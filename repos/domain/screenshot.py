#!/usr/bin/env python
# To test domain screenshot, the screenshot format is
# hypervisor specific.

import os
import mimetypes

import libvirt

required_params = ('guestname', 'filename',)
optional_params = ('screen',)

last_filename = None

def saver(stream, data, file_):
    return file_.write(data)

def screenshot(params):
    """This method takes a screenshot of a running machine and saves
    it in a filename"""
    ret = 1
    logger = params['logger']

    conn = sharedmod.libvirtobj['conn']
    dom = conn.lookupByName(params['guestname'])

    st = conn.newStream(0)
    screen = params.get('screen', 0)
    mime = dom.screenshot(st, int(screen), 0)

    ext = mimetypes.guess_extension(mime) or '.ppm'
    last_filename = params['filename'] + ext
    f = file(filename, 'w')

    logger.debug('Saving screenshot into %s' % filename)
    st.recvAll(saver, f)
    logger.debug('Mimetype of the file is %s' % mime)

    ret = st.finish()

    return ret

def cleanup(params):
    if last_filename:
        os.remove(last_filename)
