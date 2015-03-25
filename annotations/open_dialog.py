import gtk
import consts
import re 

class OpenDialog:
  
  def __init__(self, main_window):
    builder = gtk.Builder()
    builder.add_from_file(consts.OPEN_FILE_GLADE)
    builder.connect_signals(self)
    
    self.open_window = builder.get_object('open_window')
    self.filename_list = builder.get_object('filename_list')
    self.filename_filter = builder.get_object('filename_filter')
    self.filename_view = builder.get_object('filename_view')
    self.ok_button = builder.get_object('ok_button')
    self.cancel_button = builder.get_object('cancel_button')
    
    self.open_window.set_transient_for(main_window)
    
    self.pattern = None
    self.filename_filter.set_visible_func(self.filter_function)
  
  
  def populate_list(self, filename_list):
    self.filename_list.clear()
    for filename in filename_list:
      self.filename_list.append((filename,))
  
  
  def filter_function(self, model, treeiter):
    if self.pattern is None:
      return True
    
    my_text = model.get(treeiter, 0)[0]
    match = self.pattern.search(my_text)
    return match is not None
  
  
  # GUI stuff
  
  def run(self, filename_list):
    self.populate_list(filename_list)
    self.response = False
    self.open_window.run()
    
    if not self.response:
      return None
    
    selection = self.filename_view.get_selection()
    treeiter = selection.get_selected()[1] # Extract only the TreeIter
    return self.filename_filter.get(treeiter, 0)[0]
  
  
  def on_open_window_delete_event(self, event, widget):
    self.open_window.hide()
    return True
  
  
  def on_ok_button_clicked(self, widget):
    self.response = True
    self.open_window.hide()
  
  
  def on_cancel_button_clicked(self, widget):
    self.open_window.hide()
  
  
  def on_search_entry_changed(self, widget):
    text = widget.get_text()
    self.pattern = re.compile(text)
    self.filename_filter.refilter()
    

