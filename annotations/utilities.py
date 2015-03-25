import sys


__all__ = ['clean_filename', 'log']


def clean_filename(filename):
  """This function removes every extension from a filename."""
  
  index = filename.find('.')
  if index == -1:
    return filename
  else:
    return filename[:index]


def log(text):
  """This function writes its argument into standard error """
  print >> sys.stderr, text


