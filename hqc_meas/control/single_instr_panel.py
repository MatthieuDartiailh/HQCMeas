# -*- coding: utf-8 -*-

from threading import Thread, Timer
from Queue import Queue
from atom.api import (Atom, Typed, Bool, Str, Instance, Float, Callable, Tuple,
                      Dict, List, Event, Int, Value)
from inspect import getmembers, ismethod, cleandoc
from configobj import ConfigObj
from ..instruments.drivers import BaseInstrument, InstrError
from ..atom_util import PrefAtom, tagged_members
from ..instruments.drivers import DRIVERS

class RepeatedTimer(Atom):
    """
    """
    interval = Float()
    function = Callable()
    args = Tuple()
    kwargs = Dict()
    is_running = Bool()
    _timer = Typed(Thread) # the Timer class is not supposed to be accessed to
    
    def __init__(self, interval, function, *args, **kwargs):
        super(RepeatedTimer, self).__init__()
        self.interval   = interval
        self.function   = function
        self.args       = args
        self.kwargs     = kwargs
        self.start()
        
    #---- Public API -----------------------------------------------------------

    def start(self):
        if not self.is_running:
            self._timer = Timer(self.interval, self._run)
            self._timer.start()
            self.is_running = True

    def cancel(self):
        self._timer.cancel()
        self.is_running = False
        
    #---- Private API ----------------------------------------------------------        
        
    def _run(self):
        self.is_running = False
        self.start()
        self.function(*self.args, **self.kwargs)

def dsetter(method):
    
    def wrapper(self, name, new_val):
        try:
            method(self, new_val)
        except InstrError as e:
            self.dsetter_report = (name, e)
            return
            
        setattr(self, name, new_val)
        self.dsetter_report = (name, new_val)
            
    wrapper.__name__ = method.__name__
    wrapper.__doc__ = method.__doc__
    return wrapper

class SingleInstrPanel(PrefAtom):
    """
    """
    # Class attribute
    driver_type = None
    
    # Members
    title = Str().tag(pref = True)
    error = Str()
    driver = Instance(BaseInstrument)
    profile = Str().tag(pref = True)
    profile_available = Bool()
    profile_in_use = Bool()
    validate_all = Event()
    cancel_all = Event()
    propose_val = Event()
    dsetter_report = Event()
    display_additional = Bool()
    
    check_corrupt = Bool().tag(pref = True)
    corrupt_time = Float(5).tag(pref = True)
    fast_refresh = Bool().tag(pref = True)
    fast_refresh_members = List(Str()).tag(pref = True)
    fast_refresh_time = Float(1).tag(pref = True)
    refresh_time = Float(60).tag(pref = True)
    
    use_for_header = Bool().tag(pref = True)
    accesible_members = List(Str())
    header = Str().tag(pref = True)
    
    _op_queue = Value(factory = Queue)
    _process_thread = Typed(Thread)
    _corrup_timer = Typed(RepeatedTimer)
    _fast_refresh_timer = Typed(RepeatedTimer)
    _refresh_timer = Typed(RepeatedTimer)
    _dgetters = Dict(Str(), Callable())
    _dsetters = Dict(Str(), Callable())
    _proposed_val_counter = Int()
    
    def __init__(self, state):
        super(SingleInstrPanel, self).__init__()

        # Collect dgetter and dsetters here
        methods = getmembers(self, ismethod)
        self._dgetters = {meth_name[5:] : meth for meth_name, meth in methods
                            if meth_name.startswith('dget_')}
        self._dsetters = {meth_name[5:] : meth for meth_name, meth in methods
                            if meth_name.startswith('dset_')}

        self.update_members_from_preferences(**state['pref'])
        if state['profile_available']:
            self.profile_available = True
        config = ConfigObj(self.profile)

        driver_class = DRIVERS[config['driver']]
        try:
            self.driver = driver_class(config,
                                   caching_allowed = False,
                                   auto_open = self.profile_available)
            self.profile_in_use = True
        except InstrError:
            self.driver = driver_class(config,
                                   caching_allowed = False,
                                   auto_open = False)
            self.error = cleandoc('''Connection to the instrument failed, please
                    check that the instrument is connected and try again''')            
            
        if 'dstate' in state:
            self.propose_val = state['dstate']
            
        if self.profile_in_use:
            # Start worker thread and timers
            self._process_thread = Thread(target = self._process_pending_op)
            self._process_thread.start()
            self.refresh_driver_info(force_notification = True)
            if self.check_corrupt:
                self._corrupt_timer = RepeatedTimer(self.corrupt_time,
                                                    self.check_driver_state)
            if self.fast_refresh:
                self._fast_refresh_timer = RepeatedTimer(self.fast_refresh_time,
                                                    self.refresh_driver_info,
                                                    self.fast_refresh_members)
                                                    
            self._refresh_timer = RepeatedTimer(self.refresh_time,
                                                self.refresh_driver_info)
              
    #---- Public API -----------------------------------------------------------
                              
    def check_driver_state(self):
        """
        """
        self._op_queue.put((self._check_driver_state, (), {}))
        
    def refresh_driver_info(self, *args, **kwargs):
        """
        """
        self._op_queue.put((self._refresh_driver_info, args,
                            kwargs))
                            
    def restart_driver(self):
        """
        """
        self.profile_available = True
        try:
            self.driver.open_connection()
        except InstrError:
            self.profile_in_use = False
            self.error = cleandoc('''Connection to the instrument failed, please
                    check that the instrument is connected and try again.''')
            return
            
        self.profile_in_use = True
        self.error = ''
        self._process_thread = Thread(target = self._process_pending_op)
        self._process_thread.start()
        self.refresh_driver_info(force_notification = True)
        if self.check_corrupt:
            self._corrupt_timer = RepeatedTimer(self.corrupt_time,
                                                self.check_driver_state)
        if self.fast_refresh:
            self._fast_refresh_timer = RepeatedTimer(self.fast_refresh_times,
                                                self.refresh_driver_info,
                                                self.fast_refresh_members)
        self._refresh_timer = RepeatedTimer(self.refresh_time,
                                            self.refresh_driver_info)        
                                            
    def release_driver(self):
        """
        """
        if self._corrup_timer:
            self._corrupt_timer.cancel()
        if self._refresh_timer:
            self._refresh_timer.cancel()
        self._op_queue.put(None)
        self._process_thread.join()
        self._process_thread = None
        self.driver.close_connection()
        self.profile_in_use = False
        self.profile_available = False
        
    def update_driver(self, name, new_val):
        """
        """
        self._op_queue.put((self._dsetters[name],
                                (name, new_val), {}))
        
    def format_header(self):
        # TODO
        pass
        
    def get_panel_state(self):
        """
        """
        pref = {name : str(getattr(self, name)) 
                    for name in tagged_members(self, 'pref')}
        driver_state = {d : getattr(self, d) for d in self._dsetters}
        return {'pref' : pref, 'dstate' : driver_state}
            
    def _check_driver_state(self, *args, **kwargs):
        """
        """
        raise NotImplementedError('''''')
        
    def _refresh_driver_info(self, *args, **kwargs):
        """
        """

        notify = False
        if 'force_notification' in kwargs:
            notify = kwargs['force_notification']
        if args:
            for member in args:
                val = self._dgetters[member]()
                setattr(self, member, val)
                if notify:
                    self.notify(member, {'name' : member,'value' : val})
        else:
            for member in self._dgetters:
                val = self._dgetters[member]()
                print member, val
                setattr(self, member, val)
                if notify:
                    self.notify(member, {'name' : member,'value' : val})
                                            
    def _process_pending_op(self):
        """
        """
        while True:
            op = self._op_queue.get()
            if op is None:
                break
            func = op[0]
            func(*op[1], **op[2])
            
    #---- Observers-------------------------------------------------------------
            
    def _observe_proposed_val_counter(self, change):
        """
        """
        if change['value'] == 0:
            self.propose_val = True
            self.display_additional = False
    
    def _observe_check_corrupt(self, change):
        """
        """
        if change['value']:
            if self._process_thread:
                self._corrupt_timer = RepeatedTimer(self.corrupt_time,
                                                self.check_driver_state)
        else:
            if self._corrup_timer:
                self._corrup_timer.cancel()
                
    def _observe_check_corrupt_time(self, change):
        """
        """
        if self._process_thread and self._corrup_timer:
            self._corrup_timer.cancel()
            self._corrupt_timer = RepeatedTimer(change['value'],
                                            self.check_driver_state)
                                            
    def _observe_fast_refresh(self, change):
        """
        """
        if change['value']:
            if self._process_thread:
                self._fast_refresh_timer = RepeatedTimer(self.fast_refresh_time,
                                                self.refresh_driver_info,
                                                self.fast_refresh_members)
        else:
            if self._fast_refresh_timer:
                self._fast_refresh_timer.cancel()
                
    def _observe_fast_refresh_time(self, change):
        """
        """
        if self._process_thread and self._fast_refresh_timer:
            self._fast_refresh_timer.cancel()
            self._fast_refresh_timer = RepeatedTimer(change['value'],
                                                self.refresh_driver_info,
                                                self.fast_refresh_members)
                                                
    def _observe_refresh_time(self, change):
        """
        """
        if self._process_thread and self._refresh_timer:
            self._refresh_timer.cancel()
            self._refresh_timer = RepeatedTimer(change['value'],
                                                self.refresh_driver_info)
                                                
    #---- Default values -------------------------------------------------------
            
    def _default_accessible_members(self):
        # TODO use header tag and all getters
        pass