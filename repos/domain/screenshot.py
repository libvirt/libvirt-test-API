#!/usr/bin/env python
# To test domain screenshot, the screenshot format is
# hypervisor specific.

import os
import mimetypes

import libvirt

required_params = ('guestname', 'screen', 'filename')
optional_params = ()

def check_params(params):
    """Verify input parameters"""
    for key in ('guestname', 'screen', 'filename'):
        if key not in params:
            raise KeyError('Missing key %s required for screenshot test' % key)

    params['screen'] = int(params['screen'])
    params['filename'] = os.path.abspath(params['filename'])

def saver(stream, data, file_):
    return file_.write(data)

def screenshot(params):
    """This method takes a screenshot of a running machine and saves
    it in a filename"""
    ret = 1
    try:
        logger = params['logger']

        check_params(params)

        conn = libvirt.open(params['uri'])
        dom = conn.lookupByName(params['guestname'])

        st = conn.newStream(0)
        mime = dom.screenshot(st, params['screen'], 0)

        ext = mimetypes.guess_extension(mime) or '.ppm'
        filename = params['filename'] + ext
        f = file(filename, 'w')

        logger.debug('Saving screenshot into %s' % filename)
        st.recvAll(saver, f)
        logger.debug('Mimetype of the file is %s' % mime)

        ret = st.finish()

    finally:
        # Some error occurred, cleanup
        if 'conn' in locals() and conn.isAlive():
            conn.close()

    return ret
