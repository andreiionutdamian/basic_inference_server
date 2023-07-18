
import zlib
import sys
import base64

__VER__ = '0.4.0'

UNALLOWED_DICT = {
  'import '        : 'Imports are not allowed in plugin code',
  'globals'       : 'Global vars access is not allowed in plugin code',
  'locals'        : 'Local vars dict access is not allowed in plugin code',
  'memoryview'    : 'Pointer handling is unsafe in plugin code',
  'self.log.'     : 'Logger object cannot be used directly in plugin code - please use API',
  'vars('        : 'Usage of `vars(obj)` not allowed in plugin code',
  'dir('         : 'Usage of `dir(obj)` not allowed in plugin code',
  
}

class BaseCodeChecker:
  """
  This class should be used either as a associated object for code checking or
  as a mixin for running code
  """
  def __init__(self):
    super(BaseCodeChecker, self).__init__()
    return
  
  def __msg(self, m, color='w'):
    if hasattr(self, 'log'):
      self.log.P(m, color=color)
    else:
      print(m)
    return
  
  def _preprocess_code(self, code):
    res = ''
    in_string = False
    for c in code:
      if c == '"':
        if not in_string:
          in_string = True
        else:
          in_string = False

      if c == "'":
        if not in_string:
          in_string = True
        else:
          in_string = False
      
      if c == '\n' and in_string:
        res += '\\n'
      else:
        res += c
    return res

  def _check_unsafe_code(self, code):
    errors = {}
    lst_lines = code.splitlines()
    for line, _line in enumerate(lst_lines):
      # strip any lead and trail whitespace
      str_line = _line.strip()
      if len(str_line) == 0 or str_line[0] == '#':
        # if line is comment then skip it
        continue
      for fault in UNALLOWED_DICT:
        # lets check each possible fault for current line
        if (
            str_line.startswith(fault) or  # start with fault
            (' ' + fault) in str_line or   # contains a fault with a space before
            ('\t' + fault) in str_line or  # contains the fault with the tab before
            (',' + fault) in str_line or   # contains the fault with a leading comma
            (';' + fault) in str_line      # contains the fault with a leading ;
            ):
          msg = UNALLOWED_DICT[fault]
          if msg not in errors:
            errors[msg] = []
          errors[msg].append(line)
    if len(errors) == 0:
      return None
    else:
      return errors
    
  ###### PUB
  
  
  def check_code_text(self, code):
    return self._check_unsafe_code(code)
    
  




