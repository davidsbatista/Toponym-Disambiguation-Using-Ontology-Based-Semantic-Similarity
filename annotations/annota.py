#!/usr/bin/env python
#-*- coding:utf-8 -*-

# System imports
import os
import codecs
import pango      # text properties
import paramiko   # SSH connections
import pygtk, gtk # to handle User Interfaces 
import socket     # to create a socket for the SSH connection

# Local imports
import xml_utils

from consts import * #@UnusedWildImport
from annotator import Annotator
from preferences import Preferences
from open_dialog import OpenDialog
from utilities import *

# Make sure the pygtk package is the correct version
pygtk.require('2.0')


class GUI:
  
  def __init__(self):
    """Initializes the window and create pointers for all the important widgets.
    This function also runs some code to add functionality.
    """
    
    # Initialize the window and several other objects in the instance
    self.initialize_window()
    
    # Properties instance to handle the preferences window
    self.preferences = Preferences(self.main_window)
    
    # Now setup the variables needed for file access 
    try:
      self.setup_file_access()
    except Exception, e:
      # In case of error, the user must change the preferences
      log(e.__class__.__name__)
      log(e)
      self.preferences.run()
      self.setup_file_access()
    
    self.modified = set() # Store the names of the modified files
    
    # The next variable takes care of each file by holding the choices made for
    # it. The values of the dictionary are Annotator objects, where information
    # about the annotations made in the file
    self.results = {}
    
    # This flag determines whether signal handling should take place. It is True
    # when the interface is being adjusted programatically
    self.backend = False
  
  
  def initialize_window(self):
    """Creates the main window and all its widgets, storing in this GUI instance
    pointers for the widgets that will be needed throughout the program.
    """
    
    builder = gtk.Builder()
    builder.add_from_file(MAIN_GLADE)
    builder.connect_signals(self)
    
    # Important widgets
    self.main_window = builder.get_object('main_window')
    self.filename_label = builder.get_object('filename_label')
    self.previousfile_button = builder.get_object('previousfile_button')
    self.nextfile_button = builder.get_object('nextfile_button')
    self.progressbar = builder.get_object('progressbar')
    self.main_area_box = builder.get_object('main_area_box')
    self.main_area = builder.get_object('main_area')
    self.empty_buffer = builder.get_object('empty_buffer')
    self.debug_area = builder.get_object('debug_area')
    self.debug_buffer = builder.get_object('debug_buffer')
    self.selected_label = builder.get_object('selected_label')
    self.previous_button = builder.get_object('previous_button')
    self.next_button = builder.get_object('next_button')
    self.remove_check = builder.get_object('remove_check')
    self.remove_text_check = builder.get_object('remove_text_check')
    self.new_tag_button = builder.get_object('new_tag_button')
    self.possibilities_box = builder.get_object('possibilities_box')
    self.clear_button = builder.get_object('clear_button')
    self.possibilities = builder.get_object('possibilities')
    self.list_store = builder.get_object('list_store')
    self.other_name_button = builder.get_object('other_name_button')
    self.other_name_entry = builder.get_object('other_name_entry')
    self.properties_window = builder.get_object('properties_window')
    self.ssh_frame = builder.get_object('ssh_frame')
    self.modified_window = builder.get_object('modified_window')
    self.about_dialog = builder.get_object('about_dialog')
    
    # A little hack, because glade seems unable to see gtk.TreeSelection objects
    self.possibilities_selection = self.possibilities.get_selection()
    self.possibilities_selection.connect("changed",
      self.on_possibilities_selection_changed)
    
    # Sort the possibility list by id (default behavior)
    self.list_store.set_sort_column_id(2, gtk.SORT_ASCENDING)
  
  
  def create_text_tags(self, textbuffer):
    """Creates the tags that format the places in the text area."""
    
    textbuffer.create_tag("explicit", weight=pango.WEIGHT_BOLD, editable=False)
    textbuffer.create_tag("implicit", weight=pango.WEIGHT_BOLD,
                          foreground='grey', editable=False)
    textbuffer.create_tag("selected-place", underline=pango.UNDERLINE_SINGLE)
    textbuffer.create_tag("disambiguated", foreground='blue')
    textbuffer.create_tag("removed", foreground='red')
    textbuffer.create_tag("wiped", strikethrough=True)
  
  
  def setup_file_access(self):
    """This is used to create functions able to find files. It relies on 
    self.preferences to determine the directories and properties used for remote
    access.
    """
    
    pref = self.preferences
    remote = pref.remote
    
    if remote:
      # Try to connect to the server. When impossible, assume local directories
      # were meant
      try:
        log("Trying to connect to the server %s ..." % pref.server)
        transport = paramiko.Transport((pref.server, pref.port))
      
      except (socket.gaierror, socket.error):
        log("Connection failed. Reading local files instead.")
        remote = False
    
    if remote:
      log("Connection established. Opening SFTP channel ...")
      transport.connect(username=pref.username, password=pref.password)
      log("Done")
      
      sftp = paramiko.SFTPClient.from_transport(transport)
      
      # Establish the functions used to access files remotely
      _open = sftp.open
      _listdir = sftp.listdir
    
    else:
      _open = open
      _listdir = os.listdir
    
    # Define a function that returns a new function whose purpose is to return a
    # file for reading or writing in a utf8 encoding
    def func(directory, mode):
      get_filename = lambda x: os.path.join(directory, x)
      get_fh = lambda x: _open(get_filename(x), mode)
      return lambda x: codecs.EncodedFile(get_fh(x), 'utf8')
    
    self.get_input_file = func(pref.read_from, 'r')
    self.get_ann_file = func(pref.get_save_to(), 'r')
    self.get_file_to_save = func(pref.get_save_to(), 'w')
    
    # Get the list of files in the current directory
    try:
      self.list_of_filenames = sorted(
        i for i in _listdir(pref.read_from)
        if i.endswith('.xml') and not i.endswith('.final.xml'))
    except OSError:
      log("Impossible to read directory %s." % pref.read_from)
      self.list_of_filenames = []
    
    # No file is yet opened. Hold that thought.
    self.current_filename_index = -1
    
    # Also bring the database functions from the preferences into the scope of
    # this instance.
    self.find_municipality = pref.find_municipality
    self.find_by_name = pref.find_by_name
  
  
  def open_file(self, filename, revert=False):
    """This method reads a file contents and inserts the text read into the text
    buffer. Several things are done while the file is read: Tags are applied
    according to the type of place, the previous choices are also read and, if
    any are found, they are applied to the tags found, so that progress can be
    halted and resumed in further sessions. An Annotator object is created (or
    retrieved, in case of a file that is simply being revisited in this
    session), which will hold the annotations of the user.
    """
    
    # Store the name of the file currently opened
    self.current_filename = filename
    
    # Create or retrieve the Annotator and TextBuffer objects assigned to this
    # file. If we are asked to revert, then do not run this block
    if filename in self.results and not revert:
      # We have already seen this file, so a Annotator and a TextBuffer
      # objects were already constructed for it
      self.current_result = self.results[filename]
      self.current_buffer = self.current_result.buffer
      
      # When reusing these objects, we don't need to open the file again, but
      # simply to switch the text buffer associated to the text view. To do
      # this, we run the post_open_file() method, that also takes care of the
      # rest of the window. We don't need the pre_open_file() method because the
      # progress bar will never be needed.
      self.post_open_file()
      
      # No further processing needed
      return
    
    # Do not change the modified flag for this file
    self.backend = True
    
    # Create an empty TextBuffer to hold the text
    self.current_buffer = self.new_buffer()
    
    # If we are not reverting, then try to open the .ann file.
    if not revert:
      # Even if we are seeing this file for the first time, choices may already
      # have been made for it and saved in the disk. In that case, retrieve the
      # Annotator object from the file on disk.
      
      ann_filename = ANNOTATOR_TEMPLATE % clean_filename(filename)
      try:
        fh = self.get_ann_file(ann_filename)
      except IOError:
        # The file does not exist or is unreadable, so we will not use it
        pass
      else:
        # The file was successfully opened. Give the file descriptor to the method
        # that creates a new instance of the Annotator object with the information
        # read from the file.
        self.current_result = Annotator.from_saved(fh, self.current_buffer,
                                                   self.current_filename)
        self.results[filename] = self.current_result
        
        # As above, no further processing of the file is needed; just user
        # interface stuff
        self.post_open_file()
        
        # Further changes are user-made, so they must be processed
        self.backend = False
        
        return
    
    # Start the Annotator object as an empty instance
    self.results[filename] = self.current_result = \
      Annotator(self.current_buffer, self.current_filename)
    
    # Prepare for the opening process.
    self.pre_open_file()
    
    # Get the contents of the file as nodes
    f = self.get_input_file(filename)
    nodes = xml_utils.extract_nodes(f)
    
    # Record the number of places
    n_places = sum(1 for i in nodes if i[1] != "text")
    place_index = 0
    
    for node in nodes:
      # node comes from the xml_utils.extract_nodes() function, which returns
      # several tuples. Each tuple describes a string of data in the file:
      # text, explicit places (with GeoNetID, ...) or implicit places
      
      text, type = node[0], node[1]
      
      # Types are either "text", "explicit" or "implicit", with everything
      # except "text" signaling a place tag
      is_place = type != "text"
      
      if is_place:
        # Store the original name found on the file
        original_text = text
        
        # The position of the current cursor is the place this piece of text
        # will be inserted on. We create a mark (whose position remains fixed
        # relative to its surroundings) because the rest of the text may change.
        # The mark is created with left gravity because more text will be added
        # by the method, but it must change to right_gravity later on, so that
        # newly added text does not get inserted in the name of the place.
        start_iter = self.get_cursor_iter()
        start_mark = self.current_buffer.create_mark(None, start_iter, True)
        
        # We want to slightly change the visible text for implicit places
        if type == "implicit":
          text = "(" + text + ARROW + ")"
      
      # Insert the text in the current position of the cursor 
      self.current_buffer.insert_at_cursor(text)
      
      # When the node is a place, there are other things that must be done
      if is_place:
        # Put a mark on the end of the text, to signal the end of the place
        # name. This mark should have left gravity and remain so, because text
        # added after it must not modify the position of the mark in relative to
        # the place.
        end_iter = self.get_cursor_iter()
        end_mark = self.current_buffer.create_mark(None, end_iter, True)
        
        # As explained above, we need to recreate the start_mark with right
        # gravity
        start_iter = self.current_buffer.get_iter_at_mark(start_mark)
        start_mark = self.current_buffer.create_mark(None, start_iter, False)
        
        # Now we need to retrieve from the database more information about the
        # place.
        if type == "explicit":
          # node[2] contains triples with domain (physical or administrative),
          # GeoNet ID and type of location respectively
          possibilities = [(int(i[1]), i[2]) for i in node[2]]
        
        elif type == "implicit":
          # When dealing with implicit places, we only have the name. Retrieve
          # the possible GeoNet IDs from the database
          possibilities = self.find_by_name(node[0])
        
        # We also want the municipality name of the place to be present in the
        # possibilities list
        possibilities = [(i, j, self.find_municipality(i))
                         for i, j in possibilities]
        
        # We now add all the information to the self.current_result object
        self.current_result.add(original_text, start_mark, end_mark, type,
                                possibilities)
        
        # Increase the index of the places and update the progress bar showing
        # how much of the file has been gathered and processed
        place_index += 1
        self.update_progress_bar(place_index, n_places)
    
    # Format the text to give cues about each place's status
    self.current_result.format_buffer()
      
    # After opening the file, several operations must be performed
    self.post_open_file()
    
    # Further changes are user-made, so they must be processed
    self.backend = False
  
  
  def new_buffer(self):
    """Creates a new gtk.TextBuffer to handle the file contents. The buffer's
    mark-set and mar-deleted signals must be processed and tags must be created.
    """
    
    # Create the object
    buffer = gtk.TextBuffer()
    
    # Connect the signals
    buffer.connect("mark-set", self.on_text_buffer_mark_set)
    buffer.connect("changed", self.on_text_buffer_changed)
    
    # Add the tags
    self.create_text_tags(buffer)
    
    # Create an object that stores marks
    buffer.set_data("marks", [])
    
    # Return the object
    return buffer
  
  
  def pre_open_file(self):
    """This processes the operations that must be done before starting to open
    a file. Currently, the user interface is slightly changed to accommodate the
    feedback to the user.
    """
    
    # Show the progress bar and hide the text areas to prevent user distractions
    self.progressbar.show()
    self.main_area.set_buffer(self.empty_buffer)
    self.debug_area.set_buffer(self.empty_buffer)
  
  
  def post_open_file(self):
    """This processes the operations done after opening the file. It includes
    moving the cursor on the text view and updating the user interface.
    """
    
    # Initially, no place is selected
    self.current_place = None
    
    # Change sensitivity of the arrow widgets so that it is possible to find
    # places in the text
    self.next_button.set_sensitive(True)
    self.previous_button.set_sensitive(True)
    
    
    # Change sensitivity of the buttons that run through files
    self.previousfile_button.set_sensitive(self.current_filename_index > 0)
    self.nextfile_button.set_sensitive(\
      self.current_filename_index < len(self.list_of_filenames) - 1)
    
    # Set the filename to the label at the top of the window
    self.filename_label.set_label(self.current_filename)
    
    # Return the progress bar and the main area box to the default visibility
    # settings
    self.progressbar.hide()
    self.main_area.set_buffer(self.current_buffer)
    self.debug_area.set_buffer(self.debug_buffer)
    
    # Move the cursor on the text view to the beginning of the buffer
    start_iter = self.current_buffer.get_start_iter()
    self.current_buffer.place_cursor(start_iter)
    self.main_area.scroll_to_iter(start_iter, 0)
    
    # Now emulate the change of place. This is needed because self.backend is
    # True at this moment. We also need to force the method, because otherwise
    # if the text does not start with a tag, the method would not see a change
    # in the value of self.current_place
    self.cursor_moved(start_iter, True)
    
    # Update the content of the debug buffer with choice information
    self.update_debug()
  
  
  def get_cursor_iter(self):
    """Returns a gtk.TextIter representing the current position of the cursor on
    the text buffer.
    """
    
    return self.current_buffer.get_iter_at_mark(self.current_buffer.get_insert())
  
  
  def update_debug(self):
    """Updates the content of the debug buffer so that it reflects the choices
    made on the text.
    """
    
    if self.current_result is None:
      self.debug_buffer.set_text('')
      return
    
    s = '\n'.join('%i: %s, %s' % (i, j.choice, j.get_type())
                  for i, j in enumerate(self.current_result))
    self.debug_buffer.set_text(s)
  
  
  def update_progress_bar(self, done, length):
    """Updates the fraction of the progress bar that is shown. This reflects the
    amount of the text document that has been processed."""
    
    fraction = float(done) / length
    self.progressbar.set_fraction(fraction)
    self.progressbar.set_text("Progress: %i / %i" % (done, length))
    
    # The change in appearance is only passed as a change that must happen. The
    # GTK main loop takes care of it when it runs, but since we are processing
    # methods, code and all that, the loop will only get focus after the opening
    # of the file is complete, which means that the progress bar would be
    # changed only at the end, or, in other words, after being hidden again. To
    # force the update of the appearance, we need to run the iteration of the
    # GTK main loop until there is nothing more to do (ideally, we should run
    # only until the progress bar had been updated, but I don't think there is a
    # way to do it like that)
    while gtk.events_pending():
      gtk.main_iteration()
  
  
  def get_place_in_iter(self, textiter):
    """Determines the index of the place onto which the text iterator is. If
    the cursor is in regular text, return None."""
    
    # Get the current position of the cursor (as a gtk.TextIter)
    current_iter = self.get_cursor_iter()
    
    for index, info in enumerate(self.current_result):
      # Compare the gtk.TextIter objects that surround the place name with the
      # current position
      if current_iter.in_range(info.start_iter(), info.end_iter()):
        # If the current position is between start and end, then this is the
        # place we're asking for.
        return index
    
    # When not in a place, return None
    return None
  
  
  def get_path_from_geonet_id(self, geonet_id):
    """Finds the path of the row that contains the specified GeoNet ID. In case
    the GeoNet ID is not on the tree, returns None.
    """
    
    # We start by selecting the tree root iterator (which will be the first row
    # in the tree) and the go through them all by stepping one row down. If one
    # of the rows contains the specified GeoNet ID, return its path
    treeiter = self.list_store.get_iter_first()
    
    while treeiter is not None:
      # Get the GeoNet ID of the row identified by this tree iterator. The
      # GeoNet ID is in the first column of the list model that contains the
      # information
      this_geonet_id = self.list_store.get(treeiter, 0)[0]
      
      if this_geonet_id == geonet_id:
        return self.list_store.get_path(treeiter)
      
      # Go to the next row
      treeiter = self.list_store.iter_next(treeiter)
    
    # The GeoNet ID was not found
    return None
  
  
  def update_possibilities(self):
    """This method updates the information shown on the possibilities tree view
    based on the place currently selected. The sensitivity of the check boxes
    above the list are also changed according to the choice made to the place.
    """
    
    # A lot is going to change in the self.possibilities tree view. We don't
    # want to process the signals for the time being, so we signal it with this
    # flag.
    self.backend = True
    
    # Clear the list store
    self.list_store.clear()
    
    if self.current_place is None:
      # Nothing is selected, so remove sensitivity on the check boxes and the
      # list.
      self.remove_check.set_sensitive(False)
      self.remove_check.set_active(False)
      self.remove_text_check.set_sensitive(False)
      self.remove_text_check.set_active(False)
      self.possibilities_box.set_sensitive(False)
    
    else:
      # Something is selected, so we need to put the place's information on the
      # list and to determine whether one of them is selected. Also, the check
      # boxes sensitivity must be handled.
      
      for i in self.current_result[self.current_place].possibilities:
        # i is a tuple with three elements, GeoNet ID, type and municipality
        self.list_store.append(i)
      
      # Determine if a choice has been made for this place
      node = self.current_result[self.current_place]
      if node.choice is not None and node.choice > 0:
        # choice is the GeoNet ID of the place. We need to find the row that
        # refers to that ID
        path = self.get_path_from_geonet_id(node.choice)
        if path is not None:
          self.possibilities_selection.select_path(path)
        else:
          log("GeoNet ID %i is not a possibility for place %s. "
              "Removed this choice." % \
              (node.choice, node.name))
          node.choice = None
      
      self.remove_check.set_sensitive(True)
      self.remove_check.set_active(node.choice is not None and node.choice < 0)
      self.remove_check.toggled()
      
      self.remove_text_check.set_active(node.choice == -2)
      self.remove_text_check.toggled()
    
    # Restore the processing of signals
    self.backend = False
  
  
  def find_place_boundaries(self, direction, position, wrap):
    """This method takes a text iterator as a position and finds the first place
    that begins after that position (direction > 0) or the last place that ends
    before that position (direction < 0). The returned value is a tuple with two
    text iterators in order, or an empty tuple in case there are no such places.
    If wrap is True, the methods wraps around the text.
    """
    
    if len(self.current_result) == 0:
      # There are no places in the file. Return an empty tuple
      return ()
    
    if direction > 0:
      # Go through all the places until one is found that is
      for node in self.current_result:
        if position.compare(node.start_iter()) < 0:
          # This place starts after the position. It is also the first one
          # found, and since places are in physical order in Annotator objects,
          # it is guaranteed to be the next one. Break the for loop, so that
          # the variable node holds the next node
          break
      else:
        if wrap:
          # We want the first place to be chosen, since we have not found any
          # place after this position
          node = self.current_result[0]
        else:
          # No wrapping desired. Return the empty tuple
          return ()
    
    elif direction < 0:
      # Go through all places in reverse order:
      for node in reversed(self.current_result):
        # We do the same thing as above, with the corresponding comparisons
        # changed
        if position.compare(node.end_iter()) >= 0:
          break
      else:
        if wrap:
          node = self.current_result[-1]
        else:
          return ()
    
    else:
      # direction == 0. Don't do anything
      return ()
    
    return (node.start_iter(), node.end_iter())
  
  
  def select_neighbour_place(self, direction):
    """This method finds the next or previous place in the text, based on the
    current position of the cursor. If next is True, the method finds the
    next place; otherwise, it finds the previous. When no more places exist, the
    method wraps around the text.
    """
    
    # Get the text iterators that surround the place
    position = self.get_cursor_iter()
    boundaries = self.find_place_boundaries(direction, position, True)
    
    if not boundaries:
      # No place was found. Do nothing
      return
    
    # Select the place
    self.current_buffer.select_range(*boundaries)
    
    # Scroll to make the place visible and put focus on the main area. We use
    # the start iterator, but most of the times it would make no difference. The
    # amount 0.1 forces a small margin that will probably result in making the
    # next line visible too.
    self.main_area.scroll_to_iter(boundaries[0], 0.1)
    self.main_area.grab_focus()
  
  
  def commit(self):
    """Save the changes made on the files."""
    
    for filename, annotator in self.results.iteritems():
      # Only save the modified files
      if filename not in self.modified:
        continue
      
      # Get clean versions of the filenames
      cleaned = clean_filename(filename)
      ann_filename = ANNOTATOR_TEMPLATE % cleaned
      final_filename = FINAL_TEMPLATE % cleaned
      
      # Save the choices, one choice per line
      fh = self.get_file_to_save(ann_filename)
      annotator.save_ann(fh)
      fh.close()
      
      # Save the new XML file
      fh = self.get_file_to_save(final_filename)
      annotator.save_xml(fh)
      fh.close()
  
  
  def good_selection(self):
    """Determines whether there is a selected text and whether that text is all
    in the same line. In that case, returns True; otherwise, returns False.
    """
    
    if self.current_place is not None:
      # There is a place selected. This means that the selection is made over
      # another place, which is definitely a bad place to put a new tag
      return False
    
    bounds = self.current_buffer.get_selection_bounds()
    if not bounds:
      return False
    
    # Only allow new tags in selections that do not span across more than one
    # line.
    start_iter, end_iter = bounds
    if start_iter.get_line() != end_iter.get_line():
      return False
    
    # Get the first place after the beginning of the selection
    next_place = self.find_place_boundaries(1, start_iter, False)
    if next_place and next_place[0].compare(end_iter) < 0:
      # The next place exists and starts before the end of the selection, so
      # this is no good selection.
      return False
    
    # Get the last place before the end of the selection
    prev_place = self.find_place_boundaries(-1, end_iter, False)
    if prev_place and prev_place[1].compare(start_iter) > 0:
      # The previous place ends after the start of the selection, so the
      # selection is not good either
      return False
    
    return bounds
  
  
  def process_text_selection(self):
    # TODO:
    
    self.potential_name = self.current_buffer.get_text(*self.bounds)
    places = self.find_by_name(self.potential_name)
    
    # Find the municipality, also showing progress on the bar
    result = []
    for i, place in enumerate(places):
      result.append((place[0], place[1], self.find_municipality(place[0])))
      self.update_progress_bar(i + 1, len(places))
    
    return [(i[0], i[1], self.find_municipality(i[0])) for i in places]
  
  
  def cursor_moved(self, textiter, force=False):
    """This method handles the event raised by the change of position of the
    cursor in the current text buffer. When the cursor changes but the selected
    place does not, the method does not do anything useful, unless force is
    True.
    """
    
    bounds = self.good_selection()
    if bounds:
      self.new_tag_button.set_sensitive(True)
      self.bounds = bounds
    else:
      self.new_tag_button.set_sensitive(False)
      self.bounds = ()
    
    # Determine which place we are onto
    previous_place = self.current_place
    self.current_place = self.get_place_in_iter(textiter)
    
    if self.current_place is None:
      # Temporarily remove the text from the selected_label
      self.selected_label.set_label('')
    
    if previous_place == self.current_place and not force:
      # We have selected the same place. No need to do anything
      return
    
    # If there was a previous place selected, remove the 'selected' tag from it
    if previous_place is not None:
      span = self.current_result[previous_place].iter_span()
      start, end = span
      self.current_buffer.remove_tag_by_name('selected-place', start, end)
    
    # If selecting anything, we also need to add a tag to the selected place
    if self.current_place is not None:
      span = self.current_result[self.current_place].iter_span()
      start, end = span
      self.current_buffer.apply_tag_by_name('selected-place', start, end)
      
      # There is a label designed to show the text that is being considered
      node = self.current_result[self.current_place]
      if node.type == 'explicit':
        text = node.name
      elif node.type == 'implicit':
        text = node.name + ' (implicit)'
      self.selected_label.set_label(text)
    
    self.update_possibilities()
  
  
  # Signals
  
  def on_other_name_entry_changed(self, widget):
    """Update the sensitivity of other_name_button.
    """
    
    new_name = self.other_name_entry.get_text()
    self.other_name_button.set_sensitive(new_name != "")
  
  
  def on_other_name_button_clicked(self, widget):
    """We want the currently selected node to be renamed. Further, we want to
    change the list of possibilities both here and in the current Annotator
    object.
    """
    
    new_name = self.other_name_entry.get_text()
    
    # Prepare for the process of finding GeoNet IDs
    self.progressbar.show()
    
    # Find the new IDs and municipalities
    places = self.find_by_name(new_name)
    
    possibilities = []
    for i, place in enumerate(places):
      possibilities.append((place[0], place[1],
                            self.find_municipality(place[0])))
      self.update_progress_bar(i + 1, len(places))
    
    # Update the possibilities list of the place
    node = self.current_result[self.current_place]
    node.possibilities = possibilities
    node.name = new_name
    
    # And update the list view
    self.update_possibilities()
    
    self.progressbar.hide()
  
  
  def on_new_tag_button_clicked(self, widget):
    # Show the progress bar for feedback
    self.progressbar.show()
    
    possibilities = self.process_text_selection()
    start_iter, end_iter = self.bounds
    
    # Convert to marks
    start_mark = self.current_buffer.create_mark(None, start_iter, False)
    end_mark = self.current_buffer.create_mark(None, end_iter, True)
    
    self.current_result.add(self.potential_name, start_mark, end_mark,
                            "explicit", possibilities)
    self.current_result.format_buffer()
    
    # Move the cursor to the start of the new tag
    self.current_buffer.place_cursor(start_iter)
    
    # Return the progress bar and the main area box to the default visibility
    # settings
    self.progressbar.hide()
    
    # Signal that changes were made
    self.modified.add(self.current_filename)
    
    # Update the content of the debug buffer with choice information
    self.update_debug()
  
  
  def on_text_buffer_changed(self, textbuffer):
    if not self.backend:
      self.modified.add(self.current_filename)
  
  
  def on_text_buffer_mark_set(self, textbuffer, textiter, textmark):
    if not textbuffer.get_property("text"):
      return
    
    # We want to be able to track the position of the insertion cursor
    if textmark.get_name() in ['insert', 'selection_bound']:
      self.cursor_moved(textiter)
  
  
  def on_remove_check_toggled(self, widget):
    remove = self.remove_check.get_active()
    self.possibilities_box.set_sensitive(not remove)
    self.remove_text_check.set_sensitive(remove)
    
    if self.backend:
      # Just as happens when the selection of the possibilities TreeView, we
      # don't want to process this toggling when doing back-end operations
      return
    
    span = self.current_result[self.current_place].iter_span()
    start, end = span
    if remove:
      # Signal that the place tag is to be removed
      self.possibilities_selection.unselect_all()
      self.current_buffer.remove_tag_by_name('disambiguated', start, end)
      self.current_buffer.apply_tag_by_name('removed', start, end)
      self.current_result.change_choice(self.current_place, -1)
    else:
      self.current_result.change_choice(self.current_place, None)
      self.current_buffer.remove_tag_by_name('removed', start, end)
      self.current_buffer.remove_tag_by_name('wiped', start, end)
      self.remove_text_check.set_active(False)
    
    self.modified.add(self.current_filename)
    self.update_debug()
  
  
  def on_remove_text_check_toggled(self, remove_text_check):
    remove_text = remove_text_check.get_active()
    
    if self.backend:
      # Just as happens when the selection of the possibilities TreeView, we
      # don't want to process this toggling when doing back-end operations
      return
    
    span = self.current_result[self.current_place].iter_span()
    start, end = span
    if remove_text:
      # Signal that the text is to be removed
      self.current_buffer.apply_tag_by_name('wiped', start, end)
      self.current_result.change_choice(self.current_place, -2)
    else:
      self.current_result.change_choice(self.current_place, None)
      self.current_buffer.remove_tag_by_name('wiped', start, end)
    
    self.modified.add(self.current_filename)
  
  
  def on_possibilities_selection_changed(self, widget):
    if self.backend:
      # This happens because we are changing places, which will modify 
      # self.list_store. But we don't want to process this
      return
    
    # Get the rows that were selected
    # The method used returns (treemodel, treeiter)
    treeiter = self.possibilities_selection.get_selected()[1]
    
    if treeiter:
      # Get the GeoNet ID (column 0) from the list_store
      geonet_id = self.list_store.get(treeiter, 0)[0]
    else:
      geonet_id = None
    
    # We want to update several things
    self.current_result.change_choice(self.current_place, geonet_id)
    self.modified.add(self.current_filename)
    
    span = self.current_result[self.current_place].iter_span()
    start, end = span
    if geonet_id is not None:
      self.current_buffer.apply_tag_by_name('disambiguated', start, end)
    else:
      self.current_buffer.remove_tag_by_name('disambiguated', start, end)
    
    self.update_debug()
    
  
  def on_clear_button_clicked(self, widget):
    self.possibilities_selection.unselect_all()
    # By doing this, the on_possibilities_selection_changed signal will be
    # emitted and the update will be processed, so there is no need to for
    # further code
  
  
  def on_column_clicked(self, widget):
    # Determine the index of the column that was clicked. On the way, also
    # remove any sorting indicator from the other columns.
    
    clicked_column_index = None
    for index, column in enumerate(self.possibilities.get_columns()):
      if column == widget: # This is the clicked column
        column.set_sort_indicator(True)
        clicked_column_index = index
        clicked_column = column
      else:
        column.set_sort_indicator(False)
    
    # We now know what we want to sort. Get the current sorting properties
    current_index, order = self.list_store.get_sort_column_id()
    
    # Determine the sorting with this: If we are sorting on the same column
    # as previously, then toggle the sorting. Otherwise, use ascending sorting
    if current_index != clicked_column_index or order == gtk.SORT_DESCENDING:
      order = gtk.SORT_ASCENDING
    else:
      order = gtk.SORT_DESCENDING
    
    # Sort
    self.list_store.set_sort_column_id(clicked_column_index, order)
    clicked_column.set_sort_order(order)
  
  
  def on_next_button_clicked(self, widget):
    """Finds and selects the next place on the text."""
    self.select_neighbour_place(1)
  
  
  def on_previous_button_clicked(self, widget):
    """Finds and selects the previous place on the text."""
    self.select_neighbour_place(-1)
  
  
  def on_nextfile_button_clicked(self, widget):
    """Open the next file in the directory."""
    
    if self.current_filename_index < len(self.list_of_filenames) - 1:
      self.current_filename_index += 1
      
      filename = self.list_of_filenames[self.current_filename_index]
      try:
        self.open_file(filename)
      except IOError:
        # File is impossible to open (directory or other)
        pass
  
  
  def on_previousfile_button_clicked(self, widget):
    """Open the previous file in the directory."""
    
    if self.current_filename_index > 0:
      self.current_filename_index -= 1
      filename = self.list_of_filenames[self.current_filename_index]
      try:
        self.open_file(filename)
      except IOError:
        # File is impossible to open (directory or other)
        pass
      
      self.previousfile_button.set_sensitive(self.current_filename_index > 0)
      self.nextfile_button.set_sensitive(\
        self.current_filename_index < len(self.list_of_filenames) - 1)
  
  
  # Preferences
  
  # This function hides the widget that received the delete-event without
  # destroying it
  def on_about_dialog_delete_event(self, event, widget):
    widget.hide()
    return True
  
  
  # Menus
  
  def on_menu_open_specific_activate(self, widget):
    open_dialog = OpenDialog(self.main_window)
    filename = open_dialog.run(self.list_of_filenames)
    
    if filename is None:
      return
    
    else:
      # Find the correct index in the list of filenames
      self.current_filename_index = self.list_of_filenames.index(filename)
      try:
        self.open_file(filename)
      except IOError:
        # File is impossible to open (directory or other)
        pass
  
  
  def on_menu_revert_activate(self, widget):
    if self.current_filename_index == -1:
      return
    
    self.open_file(self.current_filename, True)
    self.modified.add(self.current_filename)
  
  
  def on_menu_clean_buffer_activate(self, widget):
    """Commit, delete all the transient objects and reopen the current file."""
    
    self.commit()
    self.results = {}
    
    filename = self.list_of_filenames[self.current_filename_index]
    self.open_file(filename)
  
  
  def on_menu_quit_activate(self, widget):
    return self.quit()
  
  
  def on_menu_commit_activate(self, widget):
    self.commit()
    self.modified = set()
  
  
  def on_menu_preferences_activate(self, widget):
    response = self.preferences.run()
    if response == gtk.RESPONSE_OK:
      self.setup_file_access()
  
  
  def on_menu_about_activate(self, widget):
    self.about_dialog.run()
    self.about_dialog.hide()
  
  
  # House keeping signals
  
  def on_main_window_delete_event(self, widget, event):
    return self.quit()
  
  
  def quit(self):
    if self.modified:
      
      # Setup the dialog
      builder = gtk.Builder()
      builder.add_from_file(MODIFIED_GLADE)
      dialog = builder.get_object('modified_window')
      
      result = dialog.run()
      dialog.destroy()
      
      if result == gtk.RESPONSE_YES:
        self.commit()
      elif result != gtk.RESPONSE_NO:
        return True
    
    gtk.main_quit()


if __name__ == '__main__':
  gui = GUI()
  gtk.main()
