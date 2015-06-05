# -*- coding: utf-8 -*-
# =============================================================================
# module : hqc_meas/pulses/manager/filters/base_filters.py
# author : Matthieu Dartiailh
# license : MIT license
# =============================================================================
""" Module defining the basic filters.

"""


class AbstractFilter(object):
    """ Base class for all item filters.

    Filters should simply override the filter_items classmethod.

    """

    @classmethod
    def filter_items(cls, py_items, template_items):
        """ Class method used to filter tasks.

        Parameters
        ----------
            py_items : dict
                Dictionary of known python items as name : class

            template_items : dict
                Dictionary of known templates as name : path

        Returns
        -------
            task_names : list(str)
                List of the name of the task matching the filters criteria.

        """
        err_str = 'This method should be implemented by subclasses of\
        AbstractFilter. This method is called when the program requires\
        the task filter to filter the list of available tasks'
        raise NotImplementedError(err_str)


class AllSequenceFilter(AbstractFilter):
    """ Filter returning all tasks.

    """

    @classmethod
    def filter_items(cls, py_sequences, template_sequences):

        items = list(py_sequences.keys()) + list(template_sequences.keys())
        items.remove('Pulse')
        items.remove('RootSequence')
        return items


class PySequenceFilter(AbstractFilter):
    """ Filter keeping only the python tasks.

    """

    @classmethod
    def filter_items(cls, py_sequences, template_sequences):

        sequences = py_sequences.keys()
        sequences.remove('RootSequence')


class TemplateSequenceFilter(AbstractFilter):
    """ Filter keeping only the templates.

    """

    @classmethod
    def filter_items(cls, py_sequences, template_sequences):

        return template_sequences.keys()


class SubclassFilter(AbstractFilter):
    """ Filter keeping only the python tasks which are subclass of task_class.

    """

    # Class attribute to which task will be compared.
    task_class = type

    @classmethod
    def filter_items(cls, py_sequences, template_sequences):
        """
        """
        sequences = []
        for name, t_class in py_sequences.iteritems():
            if issubclass(t_class, cls.task_class):
                sequences.append(name)

        try:
            sequences.remove('Pulse')
            sequences.remove('RootSequence')
        except ValueError:
            pass

        return sequences


class ClassAttrTaskFilter(AbstractFilter):
    """ Filter keeping only the tasks with the right class attribute.

    """

    class_attr = {'name': '', 'value': None}

    @classmethod
    def filter_items(cls, py_sequences, template_sequences):
        """
        """
        sequences = []
        attr_name = cls.class_attr['name']
        attr_val = cls.class_attr['value']
        for name, t_class in py_sequences.iteritems():
            if (hasattr(t_class, attr_name)
                    and getattr(t_class, attr_name) == attr_val):
                sequences.append(name)

        try:
            sequences.remove('Pulse')
            sequences.remove('RootSequence')
        except ValueError:
            pass

        return sequences


SEQUENCES_FILTERS = {'All': AllSequenceFilter,
                     'Python': PySequenceFilter,
                     'Template': TemplateSequenceFilter}
