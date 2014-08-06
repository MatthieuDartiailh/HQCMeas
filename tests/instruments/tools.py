# -*- coding: utf-8 -*-
from enaml.workbench.api import Workbench
import enaml
import os
from configobj import ConfigObj

with enaml.imports():
    from enaml.workbench.core.core_manifest import CoreManifest
    from hqc_meas.utils.state_manifest import StateManifest
    from hqc_meas.utils.pref_manifest import PreferencesManifest

from ..util import complete_line, clean_directory, create_test_dir
from . import TEMP_FOLDER


class BaseClass(object):

    test_dir = ''
    mod = __name__
    dir_id = 0

    @classmethod
    def setup_class(cls):
        print complete_line(__name__ +
                            ':{}.setup_class()'.format(cls.__name__), '-', 77)
        # Creating dummy directory for prefs (avoid prefs interferences).
        directory = os.path.dirname(__file__)
        cls.test_dir = os.path.join(directory, TEMP_FOLDER)
        clean_directory(cls.test_dir)

        # Creating dummy default.ini file in utils.
        util_path = os.path.join(directory, '..', '..', 'hqc_meas', 'utils')
        def_path = os.path.join(util_path, 'default.ini')

        # Making the preference manager look for info in test dir.
        default = ConfigObj(def_path)
        default['folder'] = cls.test_dir
        default['file'] = 'default_test.ini'
        default.write()

        # Creating driver preferences.
        driv_path = os.path.join(directory, '..', '..', 'hqc_meas',
                                 'instruments', 'drivers')
        driv_api = set(('driver_tools.py', 'dummy.py'))
        driv_loading = [('drivers.' + mod[:-3])
                        for mod in os.listdir(driv_path)
                        if mod.endswith('.py') and mod not in driv_api]

        # Creating false profile.
        aux = 'temp_profiles{}'.format(cls.dir_id)
        profile_path = os.path.join(cls.test_dir, aux)
        create_test_dir(profile_path)
        prof = ConfigObj(os.path.join(profile_path, 'dummy.ini'))
        prof['driver_type'] = 'Dummy'
        prof['driver'] = 'PanelTestDummy'
        prof.write()

        # Saving plugin preferences.
        man_conf = {'drivers_loading': repr(driv_loading),
                    'profiles_folders': repr([profile_path])}

        conf = ConfigObj(os.path.join(cls.test_dir, 'default_test.ini'))
        conf['hqc_meas.instr_manager'] = {}
        conf['hqc_meas.instr_manager'].update(man_conf)
        conf.write()

    @classmethod
    def teardown_class(cls):
        print complete_line(__name__ +
                            ':{}.teardown_class()'.format(cls.__name__), '-',
                            77)

        # Restoring default.ini file in utils
        directory = os.path.dirname(__file__)
        util_path = os.path.join(directory, '..', '..', 'hqc_meas', 'utils')
        def_path = os.path.join(util_path, 'default.ini')
        os.remove(def_path)

    def setup(self):

        self.workbench = Workbench()
        self.workbench.register(CoreManifest())
        self.workbench.register(StateManifest())
        self.workbench.register(PreferencesManifest())

    def teardown(self):
        self.workbench.unregister(u'hqc_meas.instr_manager')
        self.workbench.unregister(u'hqc_meas.preferences')
        self.workbench.unregister(u'hqc_meas.state')
        self.workbench.unregister(u'enaml.workbench.core')
