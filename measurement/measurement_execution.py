# -*- coding: utf-8 -*-
"""
"""
import sys, os, logging, logging.config, warnings
from logging.handlers import RotatingFileHandler
from multiprocessing import Process, Pipe, Queue
from multiprocessing.synchronize import Event
from threading import Thread
from traits.api import (HasTraits, Instance, Button, Bool, Str, Any,
                        List, Dict, on_trait_change)
from traitsui.api import (View, UItem, HGroup, VGroup, Handler,
                        ListInstanceEditor, Item, Label, ListStrEditor,
                        TextEditor, TitleEditor)
from .task_management.tasks import RootTask
from .measurement_edition import MeasurementEditor
from .measurement_monitoring import MeasureSpy, MeasureMonitor
from .task_management.config import IniConfigTask
from .log.log_facility import (StreamToLogRedirector, QueueLoggerThread)

class TaskProcess(Process):
    """
    """

    def __init__(self, pipe, log_queue, monitor_queue, task_stop, process_stop):
        super(TaskProcess, self).__init__(name = 'MeasureProcess')
        self.task_stop = task_stop
        self.process_stop = process_stop
        self.pipe = pipe
        self.log_queue = log_queue
        self.monitor_queue = monitor_queue
        self.meas_log_handler = None

    def run(self):
        """
        """
        self._config_log()
        # Ugly patch to avoid pyvisa complaining about missing filters
        warnings.simplefilter("ignore")
        logger = logging.getLogger()
        redir_stdout = StreamToLogRedirector(logger)
        sys.stdout = redir_stdout
        logger.info('Logger parametrised')
        print 'Process running'
        while not self.process_stop.is_set():
            try:
                print 'Need task'
                self.pipe.send('Need task')
                self.pipe.poll(None)
                name, config, monitored_entries = self.pipe.recv()
                if config != 'STOP':
                    task = IniConfigTask().build_task_from_config(config)
                    print 'Task built'

                    if monitored_entries:
                        spy = MeasureSpy(self.monitor_queue, monitored_entries,
                                         task.task_database)

                    if self.meas_log_handler != None:
                        logger.removeHandler(self.meas_log_handler)
                    log_path = os.path.join(
                                        task.get_from_database('default_path'),
                                        name + '.log')
                    if os.path.isfile(log_path):
                        os.remove(log_path)
                    self.meas_log_handler = RotatingFileHandler(log_path,
                                                            mode = 'w',
                                                            maxBytes = 10**6,
                                                            backupCount = 10)
                    aux = '%(asctime)s | %(levelname)s | %(message)s'
                    formatter = logging.Formatter(aux)
                    self.meas_log_handler.setFormatter(formatter)
                    logger.addHandler(self.meas_log_handler)

                    self.task_stop.clear()
                    task.should_stop = self.task_stop
                    task.task_database.prepare_for_running()

                    check = task.check(test_instr = True)
                    if check[0]:
                        print 'Check successful'
                        task.process()
                        if self.task_stop.is_set():
                            print 'Task interrupted'
                        else:
                            print 'Task processed'
                    else:
                        message = '\n'.join('{} : {}'.format(path, mes)
                                    for path, mes in check[1].iteritems())
                        logger.critical(message)

                    if spy:
                        spy.close()
                        del spy

            except Exception as e:
                logger.critical(e.message, exc_info = True)

        self.pipe.send('Closing')
        print 'Process shuting down'
        self.meas_log_handler.close()
        self.log_queue.put_nowait(None)
        self.pipe.close()

    def _config_log(self):
        """
        """
        config_worker = {
            'version': 1,
            'disable_existing_loggers': True,
            'handlers': {
                'queue': {
                    'class': 'measurement.log.log_facility.QueueHandler',
                    'queue': self.log_queue,
                },
            },
            'root': {
                'level': 'DEBUG',
                'handlers': ['queue']
            },
        }
        logging.config.dictConfig(config_worker)
        if os.name == 'posix':
            # On POSIX, the setup logger will have been configured in the
            # parent process, but should have been disabled following the
            # dictConfig call.
            # On Windows, since fork isn't used, the setup logger won't
            # exist in the child, so it would be created and the message
            # would appear - hence the "if posix" clause.
            logger = logging.getLogger('setup')
            logger.critical('Should not appear, because of disabled logger ...')


class TaskCheckDisplay(HasTraits):
    """
    """
    check_dict_result = Dict(Str, Str)

    name_to_path_dict = Dict(Str, Str)
    failed_check_list = List(Str)

    seleted_check = Str
    full_path = Str
    message = Str

    view = View(
            HGroup(
                UItem('failed_check_list',
                      editor = ListStrEditor(selected = 'selected_check'),
                    width = 300),
                VGroup(
                    UItem('full_path', editor = TitleEditor(), width = 500),
                    UItem('message', editor = TextEditor(multi_line = True,
                                          read_only = True)),
                    ),
                ),
            kind = 'live',
            title = 'Errors in the check'
            )

    def __init__(self, check_dict_result):
        super(TaskCheckDisplay, self).__init__()
        self.check_dict_result = check_dict_result
        self.name_to_path_dict = {key.rpartition('/')[-1] : key
                                    for key in self.check_dict_result.keys()}
        self.failed_check_list = self.name_to_path_dict.keys()
        self.seleted_check = self.failed_check_list[0]
        self.full_path = self.name_to_path_dict[self.seleted_check]
        self.message = self.check_dict_result[self.full_path]
        self.edit_traits()

    @on_trait_change('selected_check')
    def _update(self, new):
        """
        """
        self.full_path = self.name_to_path_dict[new]
        self.message = self.check_dict_result[self.full_path]



class TaskHolderHandler(Handler):
    """
    """
    def object_edit_button_changed(self, info):
        """
        """
        model = info.object
        meas_editor = MeasurementEditor(root_task = model.root_task,
                                        is_new_meas = False)
        model.status = 'EDITING'
        task =  model.root_task
        default_path = task.default_path
        meas_editor.edit_traits(parent = info.ui.control,
                                kind = 'livemodal',
                                )
        path = os.path.join(default_path,
                                model.name + '.ini')
        if task.default_path == default_path:
            with open(path, 'w') as f:
                task.task_preferences.write(f)
        else:
            os.remove(path)
            path = os.path.join(task.default_path,
                                model.name + '.ini')
            with open(path, 'w') as f:
                task.task_preferences.write(f)

        model.status = ''

    def object_edit_monitor_changed(self, info):
        """
        """
        model = info.object
        model.monitor.define_monitored_entries(model.root_task.task_database,
                                               parent = info.ui.control)


class TaskHolder(HasTraits):
    """
    """
    name = Str
    status = Str('READY')
    edit_button = Button('Edit')
    is_running = Bool(False)
    root_task = Instance(RootTask)

    monitor = Instance(MeasureMonitor)
    use_monitor = Bool(True)
    edit_monitor = Button('Edit monitor')

    traits_view = View(
                    VGroup(
                        UItem('name', style = 'readonly'),
                        VGroup(
                            UItem('status', style = 'readonly',
                                  resizable = True),
                            show_border = True,
                            label = 'Status',
                            ),
                        HGroup(
                            UItem('edit_button',
                                  enabled_when = 'not is_running'),
                            Item('use_monitor',
                                  enabled_when = 'not is_running'),
                            UItem('edit_monitor',
                                  enabled_when = 'not is_running',
                                  visible_when = 'use_monitor'),
                            ),
                        show_border = True,
                        label = 'Measure',
                        ),
                    handler = TaskHolderHandler(),
                    resizable = False,
                    height = -50,
                    )
    def __init__(self, *args, **kwargs):
        super(TaskHolder, self).__init__(*args, **kwargs)
        self.monitor = MeasureMonitor(measure_name = kwargs.get('name',''))

class TaskHolderDialog(HasTraits):
    """
    """
    name = Str
    use_monitor = Bool(True)

    traits_view = View(
                    VGroup(
                        UItem('name'),
                        HGroup(
                            Label('Use monitor'),
                            UItem('use_monitor'),
                            ),
                       ),
                   buttons = ['OK', 'Cancel'],
                   title = 'Enter a name for your measurement',
                   width = 200, kind = 'modal')

class TaskExecutionControlHandler(Handler):
    """
    """
    def closed(self, info, is_ok):
        if info.object.current_monitor:
            if hasattr(info.object.current_monitor, 'ui'):
                info.object.current_monitor.ui.dispose()

class TaskExecutionControl(HasTraits):
    """
    """

    start_button = Button('Start')
    stop_button = Button('Stop all')
    stop_task_button = Button('Stop task')
    show_monitor = Button('Show monitor')
    running = Bool(False)
    task_stop = Instance(Event, ())
    process_stop = Instance(Event, ())

    task_holders = List(Instance(TaskHolder), [])

    process = Instance(Process)
    log_thread = Instance(Thread)
    log_queue = Instance(Queue, ())
    monitor_queue = Instance(Queue, ())
    current_monitor = Instance(MeasureMonitor)
    pipe = Any #Instance of Connection but ambiguous when the OS is not known

    traits_view = View(
                    VGroup(
                        VGroup(
                            UItem('task_holders',
                                  editor = ListInstanceEditor(style = 'custom',
                                                      addable = False),
                                  ),
                            show_border = True,
                            label = 'Enqueued tasks',
                            ),
                        HGroup(
                            UItem('start_button',
                              enabled_when = 'not running and task_holders'),
                            UItem('stop_task_button', enabled_when = 'running'),
                            UItem('stop_button', enabled_when = 'running'),
                            ),
                        UItem('show_monitor', enabled_when = 'running'),
                        ),
                    resizable = False,
                    width = 300,
                    handler = TaskExecutionControlHandler(),
                    )

    def append_task(self, new_task):
        """
        """
        check = new_task.check(
                    test_instr = not self.running)
        if check[0]:
            dialog = TaskHolderDialog()
            ui = dialog.edit_traits()
            if ui.result:
                if dialog.name == '':
                    dialog.name = 'Meas' + str(len(self.task_holders))
                task_holder = TaskHolder(root_task = new_task,
                                         name = dialog.name)
                if dialog.use_monitor:
                    res = task_holder.monitor.define_monitored_entries(
                                        task_holder.root_task.task_database)
                    task_holder.use_monitor = res
                self.task_holders.append(task_holder)

                path = os.path.join(new_task.default_path, dialog.name + '.ini')
                with open(path, 'w') as f:
                    new_task.update_preferences_from_traits()
                    new_task.task_preferences.write(f)

                return True
            else:
                return False
        else:
           TaskCheckDisplay(check[1])
           return False

    def _start_button_changed(self):
        """
        """
        print 'Starting process'
        self.task_stop.clear()
        self.process_stop.clear()
        self.pipe, process_pipe = Pipe()
        self.process = TaskProcess(process_pipe,
                                   self.log_queue,
                                   self.monitor_queue,
                                   self.task_stop,
                                   self.process_stop)
        self.log_thread = QueueLoggerThread(self.log_queue)
        self.log_thread.daemon = True
        self.log_thread.start()

        self.process.start()
        self.running = True
        Thread(group = None, target = self._process_listerner).start()

    def _stop_button_changed(self):
        """
        """
        print 'Stopping process'
        self.process_stop.set()
        self.pipe.send('STOP')
        self.task_stop.set()
        self.process.join()
        self.log_thread.join()
        self.running = False

    def _stop_task_button_changed(self):
        """
        """
        print 'Stopping task'
        self.task_stop.set()

    def _show_monitor_changed(self):
        """
        """
        self.current_monitor.open_window()

    def _process_listerner(self):
        """
        """
        print 'Starting listener'
        while not self.process_stop.is_set():
            self.pipe.poll(None)
            mess = self.pipe.recv()
            print 'Message received'
            if mess == 'Need task':
                if self.task_holders:
                    i = 0
                    while i < len(self.task_holders):
                        if self.task_holders[i].status == 'EDITING':
                            i += 1
                            continue
                        else:
                            task_holder = self.task_holders.pop(i)
                            task = task_holder.root_task
                            name = task_holder.name
                            break
                    if task is not None:
                        task.update_preferences_from_traits()

                        if self.current_monitor:
                            self.current_monitor.stop_monitor()
                            self.current_monitor = None

                        if task_holder.use_monitor:
                            self.current_monitor = task_holder.monitor
                            self.current_monitor.status = 'Running'
                            self.current_monitor.start_monitor(
                                                        self.monitor_queue)
                            self.current_monitor.open_window()
                            self.pipe.send((name, task.task_preferences,
                                    self.current_monitor.monitored_map.keys()))
                        else:
                            self.pipe.send((name, task.task_preferences,
                                        None))
                        print 'Measurement sent'
                    else:
                        self.process_stop.set()
                        print 'The only task is the queue is being edited'
                        self.pipe.send(('', 'STOP',''))
                        self.pipe.poll(None)
                        self.pipe.close()
                        self.process.join()
                        self.log_thread.join()
                        self.running = False
                        break
                else:
                    if self.current_monitor:
                        self.current_monitor.status = 'Stopped'
                    self.process_stop.set()
                    print 'All measurements have been sent'
                    self.pipe.send(('','STOP',''))
                    self.pipe.poll(None)
                    self.pipe.close()
                    self.process.join()
                    self.log_thread.join()
                    self.running = False
                    break
            else:
                self.pipe.close()
                self.process.join()
                self.log_thread.join()
                self.running = False
                break
        if self.current_monitor:
            self.current_monitor.status = 'Stopped'