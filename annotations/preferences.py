import gtk
import consts
from utilities import log


class Preferences:
  
  slots = ['read_from', 'save_to', 'use_same', 'remote',
           'server', 'port', 'username', 'password',
           'database_access']
  
  
  def __init__(self, main_window):
    self.initialize_window(main_window)
    
    self.filename = 'annota.conf'
    self.read_from_file(self.filename)
    self.put_in_fields()
  
  
  def to_int(self, value):
    return int(value)
  
  
  def to_bool(self, value):
    if value.lower() in ['true', 'on', 'yes']:
      value = True
    elif value.lower() in ['false', 'off', 'no']:
      value = False
    else:
      raise ValueError("%r is not a valid boolean value" % value)
    return value
  
  
  def read_from_file(self, filename):
    slots_todo = set(Preferences.slots)
    slots_done = set()
    
    lines = [i.rstrip('\n') for i in open(filename) if not i.startswith('#')]
    
    for line in lines:
      key, value = (i.strip() for i in line.split('=', 1))
      
      key_lower = key.lower()
      if key_lower not in slots_todo:
        if key_lower in slots_done:
          log("Option %r is repeated." % key)
        else:
          log("I cannot understand option %r" % key)
        continue
      
      if key_lower in ['port']:
        try:
          value = self.to_int(value)
        except ValueError:
          log("Option %r: %r is not a valid integer" % (key, value))
          continue
      
      elif key_lower in ['remote', 'use_same']:
        try:
          value = self.to_bool(value)
        except ValueError:
          log("Option %r: %r is not a valid boolean" % (key, value))
          continue
      
      setattr(self, key_lower, value)
      slots_done.add(key_lower)
      slots_todo.remove(key_lower)
    
    for key in slots_todo:
      log("Option %r was not specified." % key)
    
    self.get_database_script()
  
  
  def put_in_fields(self):
    self.read_from_entry.set_text  (self.read_from)
    self.save_to_entry.set_text    (self.save_to)
    self.use_same_check.set_active (self.use_same)
    self.remote_check.set_active   (self.remote)
    self.server_entry.set_text     (self.server)
    self.port_entry.set_text       (str(self.port))
    self.username_entry.set_text   (self.username)
    self.password_entry.set_text   (self.password)
    self.database_entry.set_text   (self.database_access)
  
  
  def get_from_fields(self):
    self.read_from = self.read_from_entry.get_text()
    self.save_to = self.save_to_entry.get_text()
    self.use_same = self.use_same_check.get_active()
    self.remote = self.remote_check.get_active()
    self.server = self.server_entry.get_text()
    self.port = self.to_int(self.port_entry.get_text())
    self.username = self.username_entry.get_text()
    self.password = self.password_entry.get_text()
    self.database_access = self.database_entry.get_text()
    
    # Get the functions from the script (or default if empty filename)
    self.get_database_script()
  
  
  def get_save_to(self):
    """Returns the directory where saving should occur. This is the same as
    self.save_to, unless self.use_same is True, in which case it is the same as
    self.read_from.
    """
    
    if self.use_same:
      return self.read_from
    else:
      return self.save_to
  
  
  def save_to_file(self, filename):
    f = open(filename, 'w')
    for key in Preferences.slots:
      value = getattr(self, key)
      f.write('%s = %s\n' % (key, value))
    f.close()
  
  
  def get_database_script(self):
    connected = False
    
    if self.database_access:
      # Connect to the database and create convenience functions to access
      # information
      
      # Run the database file inside this dictionary to prevent pollution into
      # the local scope
      inner_locals = {} 
      
      try:
        log("Trying to access the database ...")
        f = open(self.database_access)
        exec f in inner_locals
        f.close()
        connected = True
      except IOError:
        log("%s does not exist or is not readable." % self.database_access)
      except Exception, e:
        log("Connection failed. Some information will be missing.")
        log(e.__class__.__name__)
        log(e)
    
    if connected:
      # Get the functions from the scope of the executed file.
      self.find_municipality = inner_locals['get_municipality_name']
      self.find_by_name = inner_locals['find_by_name']
    else:
      # Create dummy functions without any interesting functionality
      self.find_municipality = lambda x: ''
      self.find_by_name = lambda x: []
  
  
  # GUI stuff
  
  def initialize_window(self, main_window):
    builder = gtk.Builder()
    builder.add_from_file(consts.PROPERTIES_GLADE)
    builder.connect_signals(self)
    
    self.properties_window = builder.get_object('properties_window')
    self.read_from_entry = builder.get_object('read_from_entry')
    self.save_to_entry = builder.get_object('save_to_entry')
    self.use_same_check = builder.get_object('use_same_check')
    self.remote_check = builder.get_object('remote_check')
    self.server_entry = builder.get_object('server_entry')
    self.port_entry = builder.get_object('port_entry')
    self.username_entry = builder.get_object('username_entry')
    self.password_entry = builder.get_object('password_entry')
    self.database_entry = builder.get_object('database_entry')
    self.ssh_frame = builder.get_object('ssh_frame')
    
    self.properties_window.set_transient_for(main_window)
  
  
  def run(self):
    self.properties_window.run()
    return self.response
  
  
  def on_main_window_delete_event(self, event, widget):
    # Only hide the window, so that we don't need to recreate it again when the
    # preferences dialog is summoned again
    
    self.response = gtk.RESPONSE_CANCEL
    self.properties_window.hide()
    return True
  
  
  def on_cancel_button_clicked(self, widget):
    self.response = gtk.RESPONSE_CANCEL
    self.properties_window.hide()
    
    # Read the preferences from the file again and put them in the fields so
    # that when the user asks for the window again all properties are unchanged
    self.read_from_file(self.filename)
  
  
  def on_ok_button_clicked(self, widget):
    # Get the preferences from the entries and check buttons and save them to
    # the preferences file
    self.get_from_fields()
    self.save_to_file(self.filename)
    
    self.response = gtk.RESPONSE_OK
    self.properties_window.hide()
  
  
  def on_use_same_check_toggled(self, widget):
    self.save_to_entry.set_sensitive(not widget.get_active())
  
  
  def on_remote_check_toggled(self, widget):
    self.ssh_frame.set_sensitive(widget.get_active())


