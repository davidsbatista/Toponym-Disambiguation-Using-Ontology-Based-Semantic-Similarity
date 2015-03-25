import xml.dom.minidom as minidom


def _iter_to_tuple(textiter):
  return (textiter.get_line(), textiter.get_line_offset())


# This class helps define properties of each place
class PlaceNode:
  
  def __init__(self, name=None, start=None, end=None,
               type=None, possibilities=None, choice=None):
    """Initializes the place node with information on where to find it, its 
    name, type, possible choices and choice made. Possibilities is a list of
    triples, where each triple contains a GeoNet ID, a GeoNet type and the name
    of the municipality that contains this place.
    """ 
    
    self.name = name
    self.start = start
    self.end = end
    self.type = type
    self.possibilities = possibilities
    self.choice = choice
  
  
  def remove_choice(self):
    # Return the node to the default setting
    self.choice = None
  
  
  def get_type(self):
    """Get the type of the chosen place for this node."""
    
    if self.choice is None or self.choice < 0:
      return None
    
    # Find the triple of the chosen place
    triple = [i for i in self.possibilities if i[0] == self.choice][0]
    
    # Return the type of the chosen place
    return triple[1]
  
  
  # The next functions return iterators based on the positions where the name
  # is located
    
  def start_iter(self):
    return self.start.get_buffer().get_iter_at_mark(self.start)
  
  def end_iter(self):
    return self.end.get_buffer().get_iter_at_mark(self.end)
  
  def iter_span(self):
    return (self.start_iter(), self.end_iter())


class Annotator:
  """This class holds the annotations done on the text. It knows of the choices
  made on each file and of the new tags created
  """
  
  def __init__(self, buffer, filename):
    first_dot = filename.find('.')
    if first_dot > -1:
      filename = filename[:first_dot]
    self.title = filename
    self.buffer = buffer
    self.place_nodes = []
  
  
  def add(self, name, start, end, type, possibilities):
    """Adds a new place node to this Annotator instance."""
    
    # Create the new node
    p = PlaceNode(name, start, end, type, possibilities)
    
    # We want place nodes to be in order. As such, we must compare the new node
    # with the existing ones. For that, determine the position of the new node
    start_iter = p.start_iter()
    
    for i, node in enumerate(self.place_nodes):
      if start_iter.compare(node.start_iter()) < 0:
        # This node is after the new one
        self.place_nodes.insert(i, p)
        break
    else:
      self.place_nodes.append(p)
  
  
  def change_choice(self, index, geonet_id):
    """If choice is -1, it means that the place is to be discarded. None means
    that the choice has been undone. Otherwise, it is the GeoNet ID that
    disambiguates the place.
    """
    
    if index < 0:
      raise IndexError("You must specify positive indexes.")
    self.place_nodes[index].choice = geonet_id
  
  
  def get_done(self):
    """Get the number of places where a choice has been made (either a GeoNET ID
    has been chosen, or the place was selected for removal).
    """
    
    return sum(1 for i in self if i.choice is not None)
  
  
  def get_choices(self):
    return [i.choice for i in self.place_nodes]
  
  
  def get_types(self):
    return [i.get_type() for i in self.place_nodes]
  
  
  def save_ann(self, fh):
    """This saves the Annotator instance in a format that can be used to
    recreate this instance
    """
    
    start_iter = self.buffer.get_start_iter()
    end_iter = self.buffer.get_end_iter()
    text = self.buffer.get_text(start_iter, end_iter).decode('utf8')
    text_lines = text.splitlines()
    
    # This holds the tuples to save in the .ann file
    tuples = []
    
    # These variable holds the number of characters removed from the current
    # line. There is no need to take lines removed into consideration because
    # tags never span more than one line.
    chars_removed = 0
    last_line = -1
    
    for node in self.place_nodes:
      choice = node.choice
      
      if choice == -1:
        # This node is irrelevant to the annotation, so don't consider it
        continue
      
      # We convert the tuples to lists, lest we need make a change in one of the
      # coordinates (in which case, tuples would be unsuitable) 
      start_tuple = list(_iter_to_tuple(node.start_iter()))
      end_tuple = list(_iter_to_tuple(node.end_iter()))
      
      # If this line is after the line done previously, we must reset the
      # chars_removed variable to 0
      if start_tuple[0] > last_line:
        chars_removed = 0
      last_line = start_tuple[0]
      
      # Go on by removing chars_removed from the coordinates, if it is needed
      if chars_removed > 0: 
        start_tuple[1] -= chars_removed
        end_tuple[1] -= chars_removed
      
      if choice == -2:
        # The tag is irrelevant and the text should be deleted.
        tmp_line = text_lines[start_tuple[0]]
        tmp_line = tmp_line[:start_tuple[1]] + tmp_line[end_tuple[1]:]
        text_lines[start_tuple[0]] = tmp_line
        chars_removed += end_tuple[1] - start_tuple[1]
        
        # Don't save anything about this deletion
        continue
      
      name = node.name
      type = node.type
      possibilities = node.possibilities
      
      t = (name, start_tuple, end_tuple, type, possibilities, choice)
      tuples.append(t)
    
    # Finally, write the file. First the remaining text
    fh.write("%r\n" % '\n'.join(text_lines))
    
    # Then the tuples found (in reversed order)
    for t in tuples:
      fh.write("%r\n" % (t,))
  
  
  def new_place_element(self, doc, node):
    if node.choice == -1:
      element = doc.createTextNode(node.name)
      return element
    
    elif node.choice == -2:
      return None
    
    if node.type == "explicit":
      tag_name = "LOCAL_GeoNetPT02"
    else:
      tag_name = "LOCALIMPLICITO"
    
    element = doc.createElement(tag_name)
    text = doc.createTextNode(node.name)
    element.appendChild(text)
    
    if node.choice is None:
      for i in node.possibilities:
        tmp = doc.createElement("Geo-Net-PT02_Feature")
        tmp.setAttribute("f_id", str(i[0]))
        tmp.setAttribute("t_id", i[1])
        element.appendChild(tmp)
    
    else:
      element.setAttribute("f_id", str(node.choice))
      element.setAttribute("t_id", node.get_type())
    
    return element
  
  
  def get_text_between(self, node1, node2):
    if node1 is None:
      start_iter = self.buffer.get_start_iter()
    else:
      start_iter = node1.end_iter()
    
    if node2 is None:
      end_iter = self.buffer.get_end_iter()
    else:
      end_iter = node2.start_iter()
    
    return self.buffer.get_text(start_iter, end_iter)
  
  
  def save_xml(self, fh):
    doc = minidom.Document()
    
    root = doc.createElement("root")
    doc.appendChild(root)
    
    title = doc.createElement("title")
    root.appendChild(title)
    
    title_text = doc.createTextNode(self.title)
    title.appendChild(title_text)
    
    text_element = doc.createElement("text")
    root.appendChild(text_element)
    
    # Now we go through each node, stopping for text in the meantime
    previous_node = None
    previous_had_space = True
    
    for node in self.place_nodes:
      # First the text
      text = self.get_text_between(previous_node, node)
      
      if not previous_had_space:
        text = ' ' + text
      
      text_node = doc.createTextNode(text)
      text_element.appendChild(text_node)
      
      if text and text[-1] in ' \t\n':
        previous_had_space = True
      else:
        previous_had_space = False
      
      # Then the place
      element = self.new_place_element(doc, node)
      
      if element is not None:
        text_element.appendChild(element)
        if element.nodeType == minidom.Node.TEXT_NODE:
          if not previous_had_space:
            element.data = ' ' + element.data
          previous_had_space = False
          if element.data[-1] in ' \t\n':
            previous_had_space = True
      
      previous_node = node
    
    # Now we need to add the remaining text
    text = self.get_text_between(previous_node, None)
    
    if not previous_had_space:
      text = ' ' + text
      
    text_node = doc.createTextNode(text)
    text_element.appendChild(text_node)
    
    content = doc.toxml('utf8')
    if type(content) == unicode:
      fh.write(content.encode('utf8'))
    else:
      fh.write(str(content))
  
  
  def __getitem__(self, index):
    try:
      return self.place_nodes[index]
    except:
      print index
      return self.place_nodes[0]
  
  
  def __len__(self):
    return len(self.place_nodes)
  
  
  # Iterator protocol
  def __iter__(self):
    return iter(self.place_nodes)
  
  
  @classmethod
  def from_saved(cls, fh, buffer, filename):
    """This class method creates an Annotator instance based on the information
    stored in a file descriptor.
    """
    
    # Create the text by reading the first line
    text = eval(fh.readline())
    text_lines = text.splitlines() # Needed to extract from (line, offset)
    
    # Insert the text in the buffer
    buffer.set_text(text)
    
    # The rest of the lines are place nodes in raw format
    nodes = []
    for line in fh:
      t = eval(line)
      
      if len(t) == 5:
        start_tuple, end_tuple, type, possibilities, choice = t
      elif len(t) == 6:
        new_name, start_tuple, end_tuple, type, possibilities, choice = t
      
      # Get the name from the text
      if start_tuple[0] == end_tuple[0]:
        name = text_lines[start_tuple[0]][start_tuple[1]:end_tuple[1]]
      
      # Notice the gravity for the marks: start mark has right gravity, end mark
      # has left gravity.
      start_iter = buffer.get_iter_at_line_offset(*start_tuple)
      start_mark = buffer.create_mark(None, start_iter, False)
      end_iter = buffer.get_iter_at_line_offset(*end_tuple)
      end_mark = buffer.create_mark(None, end_iter, True)
      
      # Create a PlaceNode with the information and in case it is needed rename
      # the name of the node.
      if len(t) == 6:
        name = new_name
      node = PlaceNode(name, start_mark, end_mark, type, possibilities, choice)
      
      # Append the node to the list
      nodes.append(node)
    
    # Create the Annotator instance with the constructed list of place nodes
    result = cls(buffer, filename)
    result.place_nodes = nodes
    
    # Format the text according to the choices read from the file
    result.format_buffer()
    
    # Return the resulting Annotator object
    return result
  
  
  def format_buffer(self):
    for node in self.place_nodes:
      start_iter = node.start_iter()
      end_iter = node.end_iter()
      
      # Store the first tag to apply to the text. The tag name is the same as
      # the node type ("explicit" or "implicit")
      tags = [node.type]
      
      # Now we must decide whether tags other than the basic "implicit" or
      # "explicit" apply to the text (based on the choice)
      choice = node.choice
      if choice is not None:
        if choice < 0:
          # The tag is removed
          tags.append("removed")
          
          if choice == -2:
            # And the text inside too
            tags.append("wiped")
        
        else:
          # The place has been disambiguated with some GeoNet ID
          tags.append("disambiguated")
      
      # Now we know all the tags that must be applied to the place name
      for tag in tags:
        self.buffer.apply_tag_by_name(tag, start_iter, end_iter)
  
  
  def to_final_xml(self, fh):
    pass
