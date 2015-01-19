# -*- coding: utf-8 -*-
#==============================================================================
# module : test_base_forms.py
# author : Matthieu Dartiailh
# license : MIT license
#==============================================================================
"""
"""
from nose.tools import assert_true, assert_false, assert_equal, raises

from hqc_meas.instruments.manager.forms.base_forms\
    import (AbstractConnectionForm, VisaForm, DummyForm)
     
@raises(NotImplementedError)                                              
def test_abstract_connection_form1():
    # Test check method.
    form = AbstractConnectionForm()
    form.check()


@raises(NotImplementedError) 
def test_abstract_connection_form2():
    # Test check required_fields.
    form = AbstractConnectionForm()
    form.required_fields()


@raises(NotImplementedError) 
def test_abstract_connection_form3():
    # Test check connection_form.
    form = AbstractConnectionForm()
    form.connection_dict()
    
    
def test_visa_form1():
    # Test check method.
    form = VisaForm()
    assert_false(form.check())
    
    form.connection_type = 'GPIB'
    form.address = '1'
    
    assert_true(form.check())


def test_visa_form2():
    # Test check required_fields.
    form = VisaForm()
    assert_equal(form.required_fields(), 'connection type and address')


def test_visa_form3():
    # Test check connection_form.
    form = VisaForm()
    form.connection_type = 'GPIB'
    form.address = '1'
    
    assert_equal(form.connection_dict(), 
                 {'connection_type': 'GPIB',
                  'address': '1',
                  'additionnal_mode': ''})
                  
   
def test_dummy_form1():
    # Test check method.
    form = DummyForm()
    assert_true(form.check())


def test_dummy_form2():
    # Test check required_fields.
    form = DummyForm()
    assert_equal(form.required_fields(), '')


def test_dummy_form3():
    # Test check connection_form.
    form = DummyForm()
    
    assert_equal(form.connection_dict(), {})
                  