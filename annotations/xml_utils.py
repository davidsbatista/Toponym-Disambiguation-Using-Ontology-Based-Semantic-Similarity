import xml.dom.minidom as minidom

_types = [(i, getattr(minidom.Node, i))
          for i in dir(minidom.Node) if i == i.upper()]
_type_from_num = dict((j, i) for i, j in _types)


def extract_nodes(f):
  result = []
  
  doc = minidom.parse(f)
  texts_tags = doc.getElementsByTagName('text')
  
  for text in texts_tags:
    
    children = text.childNodes
    count = 0
    len_children = len(children)
    first = True
    
    for child in children:
      count += 1
      
      if child.nodeType == minidom.Node.TEXT_NODE:
        sub_text = child.data
        if first and sub_text.startswith('\n'):
          sub_text = sub_text[1:]
        if count == len_children and sub_text.endswith('\n'):
          sub_text = sub_text[:-1]
        result.append((sub_text, 'text'))
      
      elif child.nodeType == minidom.Node.ELEMENT_NODE \
           and child.tagName == 'LOCAL_GeoNetPT02':
        sub_children = child.childNodes
        possibilities = []
        
        for sub_child in sub_children:
          if sub_child.nodeType == minidom.Node.TEXT_NODE:
            sub_text = sub_child.data
          elif sub_child.tagName.startswith('Geo-Net-PT02'):
            geonet_type = sub_child.tagName[13:16]
            f_id = int(sub_child.attributes['f_id'].value)
            t_id = sub_child.attributes['t_id'].value
            possibilities.append((geonet_type, f_id, t_id))
        
        result.append((sub_text, 'explicit', possibilities))
      
      elif child.nodeType == minidom.Node.ELEMENT_NODE \
           and child.tagName == 'LOCALIMPLICITO':
        sub_text = child.firstChild.data
        
        result.append((sub_text, 'implicit'))
  
  return result


def make_new_xml(f, choices, types):
  
  doc = minidom.parse(f)
  text = doc.getElementsByTagName('text')[0]
  children = text.childNodes
  
  count = 0
  
  for child in children:
    if child.nodeType == minidom.Node.ELEMENT_NODE:
    
      # No changes
      if choices[count] is None:
        pass
      
      elif choices[count] < 0:
        # Remove the child and replace it with a (possibly empty) Text Node
        
        # Find this child in the list of children and replace it with an empty
        # Text node
        index = children.index(child)
        children[index] = minidom.Text()
        
        if choices[count] == -1:
          # The choice was to keep the text
          place_name = child.childNodes[0].data
          
          # Now do a little processing to make sure the words are separated by
          # at least one space. If this place is not separated from the left and
          # right ones by spaces, add the spaces here
          if index > 0 and \
             children[index - 1].nodeType == minidom.Node.TEXT_NODE and \
             children[index - 1].data[-1] not in ' \t\n' and \
             place_name[0] not in ' \t\n':
            place_name = ' ' + place_name
          
          if index + 1 < len(children) and \
             children[index + 1].nodeType == minidom.Node.TEXT_NODE and \
             children[index + 1].data[0] not in ' \t\n' and \
             place_name[-1] not in ' \t\n':
            place_name += ' '
          
          children[index].data = place_name
      
      ## Select the choice made
      else:
        del child.childNodes[1:] # Keep the text only
        child.attributes['f_id'] = str(choices[count])
        child.attributes['t_id'] = str(types[count])
      
      count += 1
  
  return doc.toxml()
