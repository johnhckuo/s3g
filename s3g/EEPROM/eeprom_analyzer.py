"""
Analyzes the eeprom map in the Mightyboards Source code's
Eeprom.hh file.  Expects blocks of information in the form of:
//$BEGIN_ENTRY
//$S:<some size>
const static uint16_t <some name> = <some address>

Takes the above information and turns it into a python
dict in the form of:
{
  <some name> : {
      size  : <some size>,
      address : <some address>,
      }
}
"""

class EndOfNamespaceError(IOError):
  def __init__(self):
    pass

class EndOfEepromError(IOError):
  def __init__(self):
    pass

import json

class eeprom_analyzer(object):

  def __init__(self):
    self.filename = 'eeprom_map.json'
    self.eeprom_map = {}
    self.necessary_eeproms = {
        'toolhead_eeprom_offsets' : False,
        'eeprom_offsets' : False,
        }

  def parse_file(self):
    try:
      while True:
        namespace_name = self.find_next_namespace().lower()
        if namespace_name in self.necessary_eeproms:
          self.necessary_eeproms[namespace_name] = True
        namespace = {}
        try:
          while True:
            self.find_next_entry()
            pack_type = self.parse_out_type(self.file.readline())
            (name, location) = self.parse_out_name_and_location(self.file.readline())
            namespace[name] = {
                'location'  : location,
                'type'      : pack_type,
                }
        except EndOfNamespaceError:
          eeprom_map = {
              namespace_name  : namespace,
              }
          self.dump_json(namespace_name, eeprom_map)
    except EndOfEepromError:
      pass
      
  def find_next_entry(self):
    namespace_end = '}'
    entry_line = '//$BEGIN_ENTRY'
    line = self.file.readline()
    while entry_line not in line:
      if namespace_end in line:
        raise EndOfNamespaceError
      line = self.file.readline()
    return line

  def find_next_namespace(self):
    """
    Reads lines from the file until a line that 
    starts with namespace is encountered.  The name 
    of that namespace is then parsed out and returned.

    @return str name: The name of the current namespace
    """
    namespace = 'namespace'
    end_of_eeprom = '#endif'
    line = self.file.readline()
    while not line.startswith(namespace):
      if end_of_eeprom in line:
        raise EndOfEepromError
      line = self.file.readline()
    return self.parse_out_namespace_name(line)

  def parse_out_namespace_name(self, line):
    """
    Given a line in the form of 
      "namespace <name> {"
    parses out the name
  
    @param str line: The line with the namespace
    @return str name: The name of the namespace 
    """
    line = line.strip()
    for s in ['\n', '\r', '\t', '{']:
      line = line.rstrip(s)
    line = line.lstrip('namespace')
    line = line.replace(' ', '')
    return line

  def parse_out_name_and_location(self, line):
    """
    Given a line in the form of:
      const static uint16_t <name> = <location>;
    parses out the name and location.
    If we get a line not of this form, we will fail.

    @param str line: the line we want information from
    @return tuple: Information in the form of (name, location)
    """
    for w in ['const', 'static', 'uint16_t']:
      line = line.replace(w, '')
    for s in ["\r", "\n", ";"]:
      line = line.rstrip(s)
    line = line.replace('\t', '')
    line = line.replace(" ", "")
    (name, location) = line.split("=")
    return name, location

  def parse_out_type(self, line):
    line = line.strip()
    for s in ['\n', '\r','\t', ]:
      line = line.rstrip(s)
    line = line.lstrip('//')
    parts = line.split(':')
    if parts[0] == '$S':
      return parts[1]
    else:
      return line

  def dump_json(self, name, eeprom_map):
    output = json.dumps(eeprom_map)
    with(open(name, 'w')) as f:
      f.write(output)
