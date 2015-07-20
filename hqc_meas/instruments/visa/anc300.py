# -*- coding: utf-8 -*-
"""
    lantz_drivers.attocube.anc300
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    Driver for the ANC300 open-loop positioner controller.

    :copyright: 2015 by The Lantz Authors
    :license: BSD, see LICENSE for more details.

"""
from time import sleep
from timeit import default_timer

from stringparser import Parser

from lantz_core.has_features import channel, set_feat
from lantz_core.channel import Channel
from lantz_core.features.feature import Feature
from lantz_core.features.mapping import Mapping
from lantz_core.features import Unicode, Float
from lantz_core.action import Action
from lantz_core.errors import InvalidCommand, LantzError
from lantz_core.backends.visa import VisaMessageDriver, errors
from lantz_core.unit import UNIT_SUPPORT, get_unit_registry

from ..visa_tools import VisaInstrument


def check_answer(res, msg):
    """Check the message returned by the ANC for errors.

    Parameters
    ----------
    res : bool


    msg : unicode
        Answer to the command sent to the ANC300.

    Raises
    ------
    InvalidCommand :
        Raised if an error was signaled by the instrument.

    """
    if not res:
        err = ' '.join(msg.split('\r\n')[::-1])
        raise InvalidCommand(err)


UNIT_REMOVER = Parser('{} {_}')

CAPA_EXTRACTER = Parser('capacitance = {}')

VOLTAGE_EXTRACTER = Parser('voltage = {}')

TRIGGER_MAP = {'off': 'off'}
TRIGGER_MAP.update({i: '{}'.format(i) for i in range(1, 8)})


class ANCModule(Channel):
    """Generic base class for ANC300 modules.

    """
    #: Serial number of the module.
    serial_number = Unicode('getser {id}')

    #: Current operating mode of the module.
    mode = Unicode('getm {id}', 'setm {id} {}', extract='mode = {}')

    #: Current value of the saved capacitance. Can be None if the value was
    # never measured.
    saved_capacitance = Feature('getc {id}')

    @Action()
    def stop_motion(self):
        """Stop any motion.

        """
        res, msg = self.parent.anc_query('stop {}'.format(self.id))
        check_answer(res, msg)

    @Action()
    def read_output_voltage(self):
        """Read the voltage currently applied on the module.

        """
        res, msg = self.parent.anc_query('geto {}'.format((self.id)))
        check_answer(res, msg)

        val = VOLTAGE_EXTRACTER(msg.split('\r\n')[0])
        if UNIT_SUPPORT:
            ureg = get_unit_registry()
            return ureg.parse_expression(val)
        else:
            float(UNIT_REMOVER(val))

    @Action()
    def measure_capacitance(self, block=False, timeout=10):
        """Ask the system to measure the capacitance.

        Parameters
        ----------
        block : bool, optional
            Whether or not to wait on the measure to finish before returning.
        timeout : float, optional
            Timeout to use when waiting for measure completion.

        Returns
        -------
        value : float, Quantity or None
            Return the new measured value if block is True, else return None.
            The value can be read at a later time using read_saved_capacitance
            but first wait_for_capacitance_measure should be called to ensure
            that the measure is over.

        """
        with self.lock:
            self.clear_cache(features=('saved_capacitance', 'mode'))
            self.parent.anc_query('setm {} cap'.format(self.id))
            if block:
                self.wait_for_capacitance_measure(timeout)
                return self.read_saved_capacitance()

    @Action()
    def wait_for_capacitance_measure(self, timeout=10):
        """Wait for the capacitance measurement to finish.

        """
        with self.lock:
            self.parent.write('capw {}'.format(self.id))
            self._wait_for(timeout)

    def _wait_for(self, timeout):
        """Wait for completion of an operation.

        """
        t = 0
        while t < timeout:
            try:
                tic = default_timer()
                err, msg = self.parent.anc_read()
                check_answer(err, msg)
            except errors.VisaIOError as e:
                if e.error_code != errors.VI_ERROR_TMO:
                    raise
                sleep(0.1)
                t += default_timer() - tic

    def _post_get_saved_capacitance(self, feat, value):
        """Transform the value returned by the instrument.

        """
        if '?' in value:
            return None

        val = CAPA_EXTRACTER(value)
        if UNIT_SUPPORT:
            ureg = get_unit_registry()
            return ureg.parse_expression(val).to('nF')
        else:
            return UNIT_REMOVER(val)


class ANCStepper(ANCModule):
    """Base class for ANC300 stepper modules.

    """
    #: Stepping frequency.
    frequency = Float('getf {id}', 'setf {id} {}', unit='Hz',
                      limits=(0, 10000, 1), extract='frequency = {} Hz')

    #: Stepping amplitude.
    amplitude = Float('getv {id}', 'setv {id} {}', unit='V',
                      limits=(0.0, 150.0, 1e-3),
                      discard={'limits': ['frequency']},
                      extract='voltage = {} V')

    #: Trigger triggering an up step
    up_trigger = Mapping('gettu {id}', 'settu {id} {}', mapping=TRIGGER_MAP,
                         extract='trigger = {}')

    #: Trigger triggering a down step
    down_trigger = Mapping('gettd {id}', 'settd {id} {}', mapping=TRIGGER_MAP,
                           extract='trigger = {}')

    mode = set_feat(mapping={'Ground': 'gnd', 'Step': 'stp'})

    @Action(checks='self.mode == "Step";direction in ("Up", "Down")')
    def step(self, direction, steps=1):
        """Execute steps in the positive direction.

        Parameters
        ----------
        direction : {'Up', 'Down'}
            Direction in which to execute the steps.

        steps : int
            Number of steps to execute, a negative value (<1) can be used to
            indicate a continuous sweep.

        """
        steps = 'c' if steps < 1 else steps
        cmd = 'stepu' if direction == 'Up' else 'stepd'
        cmd += ' {} {}'
        res, msg = self.parent.anc_query(cmd.format(self.id, steps))

        msg += ('\r\n You may be above the power limit: check the '
                'amplitude and frequency settings.')
        check_answer(res, msg)

    @Action()
    def wait_for_stepping_end(self, timeout=10):
        """Wait for the current stepping operation to end.

        For unknow reasons this takes far more time than it should.

        """
        with self.lock:
            self.parent.write('stepw {}'.format(self.id))
            self._wait_for(timeout)

# TODO implement
class ANCScanner(ANCModule):
    """Base class for ANC scanning modules.

    """
    pass


# TODO add ANM200 and ANM300 modules.
class ANC300(VisaMessageDriver, VisaInstrument):
    """Driver for the ANC300 piezo controller.

    Notes
    -----
    If you set a password different from the default one on your system
    you should pass it under the key password in the connection_infos

    """
    PROTOCOLES = {'TCPIP': '7230::SOCKET'}

    DEFAULTS = {'COMMON': {'write_termination': '\r\n',
                           'read_termination': '\r\n'}}

    #: Drivers of the ANM150 modules.
    anm150 = channel('_list_anm150', ANCStepper)

    def __init__(self, connection_infos, caching_allowed=True):
        """Extract the password from the connection info.

        """
        super(ANC300, self).__init__(connection_infos, caching_allowed)
        self.password = connection_infos.get('password', '123456')

    def initialize(self):
        """Handle autentification after connection opening.


        """
        super(ANC300, self).initialize()
        self.write(self.password)
        # First line contains non-ascii characters
        try:
            self.read()
        except UnicodeDecodeError:
            pass

        self.read()  # Get stupid infos.
        self.read()  # Empty line
        self.read()  # Get authentification request with given password.
        msg = self.read()  # Get authentification status
        if msg != 'Authorization success':
            raise LantzError('Failed to authentify :' + msg)

        res, msg = self.anc_query('echo off')  # Desactivate command echo
        check_answer(res, msg)

    close_connection = VisaMessageDriver.finalize

    @property
    def connected(self):
        """Query the serial number to check connection.

        """
        try:
            self.anc_query('ver')
        except Exception:
            return False

        return True

    def default_get_feature(self, iprop, cmd, *args, **kwargs):
        """Query the value using the provided command.

        The command is formatted using the provided args and kwargs before
        being passed on to the instrument.

        """
        err, msg = self.anc_query(cmd.format(*args, **kwargs))
        check_answer(err, msg)
        return msg

    def default_set_feature(self, iprop, cmd, *args, **kwargs):
        """Set the iproperty value of the instrument.

        The command is formatted using the provided args and kwargs before
        being passed on to the instrument.

        """
        err, msg = self.anc_query(cmd.format(*args, **kwargs))
        return (err, msg)

    def default_check_operation(self, feat, value, i_value, state=None):
        """Same implementation as in HasFeature.

        """
        return state

    def anc_query(self, msg):
        """Special query taking into account that answer can be multiple lines
        and are termintaed either with OK or ERROR.


        """
        with self.lock:
            self.write(msg)
            return self.anc_read()

    def anc_read(self):
        """Special read taking into account that answer can be multiple lines
        and are terminated either with OK or ERROR.

        """
        with self.lock:
            answer = ''
            while True:
                # XXXX some commands terminate with \n only to avoid warnings
                # we use strip
                ans = self.read_raw().rstrip()
                if ans in ('OK', 'ERROR'):
                    break
                else:
                    answer += ans + '\n'

        return True if ans == 'OK' else False, answer.rstrip()

    # =========================================================================
    # --- Private API ---------------------------------------------------------
    # =========================================================================

    def _list_anm150(self):
        """List the ANM150 modules installed on that rack.

        """
        anm150 = []
        for i in self._list_modules():
            res, msg = self.anc_query('getser {}'.format(i))
            if msg.startswith('ANM150'):
                anm150.append(i)

        return anm150

    def _list_modules(self):
        """List the modules installed on the rack.

        """
        if not hasattr(self, '_modules'):
            modules = []
            for i in range(1, 8):
                res, msg = self.anc_query('getser {}'.format(i))
                if res:
                    modules.append(i)

            self._modules = modules

        return self._modules


DRIVERS = {'ANC300': ANC300}
