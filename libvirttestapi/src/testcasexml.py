import os

from . import exception
from ..utils import log
from ..utils import utils


def populate_xml_file(file_path, case_params, optional_params):

    text = ''
    if os.path.exists(file_path):
        fh = open(file_path, 'r')
        text = fh.read()
        fh.close()
    else:
        raise exception.FileDoesNotExist("xml file %s doesn't exist" % file_path)

    # replace the params that in testcase.conf first
    for (key, value) in list(case_params.items()):
        if key == 'logger':
            continue

        key = key.upper()
        text = text.replace(key, value)

    # relace the optional params that defined in testcase.py
    for (key, value) in list(optional_params.items()):
        if key == 'xml':
            continue

        key = key.upper()
        if value is None:
            value = ''

        text = text.replace(key, str(value))

    case_params['xml'] = text
    return case_params

def xml_file_to_str(proxy_obj, mod_case, case_params):
    """ get xml string from xml file in case_params
        return a new case_params with the string in it
    """
    optional_params = proxy_obj.get_testcase_params(mod_case)[1]

    if "xml" in case_params:
        file_name = case_params.pop('xml')
    elif "xml" in optional_params:
        if optional_params['xml'] is None:
            return None
        else:
            file_name = optional_params['xml']
    else:
        return None
    # If file_name is not absolute path, that means
    # the file is in repos/*/xmls/
    # if it is absolute use it directly
    if not os.path.isabs(file_name):
        mod = mod_case.split(':')[0]
        file_name = os.path.basename(file_name)
        base_path = utils.get_base_path()
        file_path = os.path.join(base_path, 'xmls', mod, file_name)
    else:
        file_path = file_name

    populate_xml_file(file_path, case_params, optional_params)
