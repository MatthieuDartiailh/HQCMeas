# -*- coding: utf-8 -*-

from atom.api import Str, Unicode, Enum, Atom, Member, Validate

def tagged_members(obj, meta = None, meta_value = None):
    """
    """
    members = obj.members()
    if meta is None and meta_value is None:
        return members
    elif meta_value is None:
        return {key : member for key, member in members.iteritems() 
                if member.metadata is not None and meta in member.metadata}
    else:
        return {key : member for key, member in members.iteritems() 
                if member.metadata is not None 
                and meta in member.metadata
                and member.metadata[meta] == meta_value}

def simple_member_from_str(member, str_value):
    """
    """
    # If the member type is 'Str' then we just take the raw value.
    if isinstance(member, Str):
        value = str_value

    # If the member type is 'Unicode' then we convert the raw value.
    elif isinstance(member, Unicode):
        value = unicode(str_value)

    elif isinstance(member, Enum) and isinstance(member.items[0], basestring):
        value = str_value
    # Otherwise, we eval it!
    else:
        value = eval(str_value)

    return value

def member_from_str(member, value):
    """
    """
    #if we get a container must check each member
    if isinstance(value, list):
        validation_mode = member.validate_mode
        if len(validation_mode) > 1:
            val_member = validation_mode[1]
            validated = [member_from_str(val_member, val)
                                                for val in value]
        else:
            validated = value
            
    if isinstance(value, dict):
        validation_mode = member.validate_mode
        if len(validation_mode) > 2:
            key_member = validation_mode[1]
            value_member = validation_mode[2]
            validated = {member_from_str(key_member, key) : 
                        member_from_str(value_member, val)
                        for key, val in value.iteritems}
        else:
            validated = value
    else:
        validated = simple_member_from_str(member, value)
        
    return validated
    
class PrefAtom(Atom):
    
    def update_members_from_preferences(self, **parameters):
        """
        """
        for name, member in tagged_members(self, 'pref').iteritems():

            if not parameters.has_key(name):
                continue

            value = parameters[name]
            converted = member_from_str(member, value)
            setattr(self, name, converted)
            
class Subclass(Member):
   
    __slots__ = 'subtype'

    def __init__(self, subtype):
        self.subtype = subtype
        self.set_validate_mode(Validate.MemberMethod_ObjectOldNew, 'validate')


    def validate(self, obj, old, new):
        assert isinstance(new, type)
        assert issubclass(new, self.subtype)
        return new