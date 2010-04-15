import ast
from generic import *
from grfstrings import grf_strings, get_translation
from action6 import *
from actionD import *

class ActionB:
    def __init__(self, severity, lang, msg, data, param1, param2):
        self.severity = severity
        self.lang = lang
        self.msg = msg
        self.data = data
        self.param1 = param1
        self.param2 = param2
    
    def write(self, file):
        file.write("-1 * 0 0B ")
        self.severity.write(file, 1)
        print_bytex(file, self.lang)
        if isinstance(self.msg, int):
            print_bytex(file, self.msg)
        else:
            print_bytex(file, 0xFF)
            print_string(file, self.msg)
        if self.data != None:
            print_string(file, self.data)
            if self.param1 != None:
                self.param1.write(file, 1)
                if self.param2 != None:
                    self.param2.write(file, 1)
        file.write("\n\n")
    
    def skip_action7(self):
        return False
    
    def skip_action9(self):
        return True
    
    def skip_needed(self):
        return True

default_error_msg = {
    'REQUIRES_TTDPATCH' : 0,
    'REQUIRES_DOS_WINDOWS' : 1,
    'USED_WITH' : 2,
    'INVALID_PARAMETER' : 3,
    'MUST_LOAD_BEFORE' : 4,
    'MUST_LOAD_AFTER' : 5,
    'REQUIRES_OPENTTD' : 6,
}

error_severity = {
    'NOTICE'  : 0,
    'WARNING' : 1,
    'ERROR'   : 2,
    'FATAL'   : 3,
}

def parse_error_block(error):
    global free_parameters, default_error_msg, grf_strings
    free_parameters_backup = free_parameters[:]
    action_list = []
    action6 = Action6()
    
    if isinstance(error.severity, ast.ConstantNumeric):
        severity = error.severity
    elif isinstance(error.severity, ast.Parameter) and isinstance(error.severity.num, ast.ConstantNumeric):
        action6.modify_bytes(error.severity.num.value, 1, 1)
        severity = ast.ConstantNumeric(0)
    else:
        tmp_param, tmp_param_actions = get_tmp_parameter(error.severity)
        action_list.extend(tmp_param_actions)
        action6.modify_bytes(tmp_param, 1, 1)
        severity = ast.ConstantNumeric(0)
    
    if not isinstance(error.msg, str):
        raise ScriptError("Error parameter 2 'message' should be the identifier of a built-in or custom sting")
    
    langs = [0x7F]
    if error.msg in default_error_msg:
        custom_msg = False
        msg = default_error_msg[error.msg]
    else:
        custom_msg = True
        for translation in grf_strings[error.msg]:
            langs.append(translation['lang'])
    
    if error.data != None:
        if not isinstance(error.data, str):
            raise ScriptError("Error parameter 3 'data' should be the identifier of a custom sting")
        for translation in grf_strings[error.data]:
            langs.append(translation['lang'])
    
    params = []
    for expr in error.params:
        if expr is None:
            params.append(None)
        elif isinstance(expr, ast.Parameter) and isinstance(expr.num, ast.ConstantNumeric):
            params.append(expr.num)
        else:
            tmp_param, tmp_param_actions = get_tmp_parameter(expr)
            action_list.extend(tmp_param_actions)
            params.append(ast.ConstantNumeric(tmp_param))
    
    assert len(params) == 2
    
    langs = set(langs)
    for lang in langs:
        if custom_msg:
            msg = get_translation(error.msg, lang)
        data = None if error.data == None else get_translation(error.data, lang)
        if len(action6.modifications) > 0: action_list.append(action6)
        action_list.append(ActionB(severity, lang, msg, data, params[0], params[1]))
    
    free_parameters = free_parameters_backup
    return action_list
