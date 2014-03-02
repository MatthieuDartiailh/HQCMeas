# -*- coding: utf-8 -*-
#==============================================================================
# module : manager_plugin.py
# author : Matthieu Dartiailh
# license : MIT license
#==============================================================================
"""
"""
from configobj import ConfigObj
from textwrap import wrap


def load_template(path):
    """ Load the informations stored in a template.

    Parameters
    ----------
        path : unicode
            Location of the template file.

    Returns
    -------
        data : ConfigObj
            The data needed to rebuild the tasks.

        doc : str
            The doc of the template.

    """
    config = ConfigObj(path)
    doc_list = [com[1:].strip() for com in config.initial_comment]
    doc = '\n'.join(doc_list)

    return config, doc


def save_template(path, data, doc):
    """ Save a template to a file

    Parameters
    ----------
        path : unicode
            Path of the file to which save the template
        data : dict(str : str)
            Dictionnary containing the tempate parameters
        doc : str
            The template doc

    """
    # Create an empty ConfigObj and set filename after so that the data are
    # not loaded. Otherwise merge might lead to corrupted data.
    config = ConfigObj(indent_type='    ')
    config.filename = path
    config.merge(data)
    config.initial_comment = wrap(doc, 80)

    config.write()
