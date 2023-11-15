# System imports
import queue

from contextlib import contextmanager

###
class ObjectPool:

  def __init__( self, func, *args, **kwargs ):
    self.func = func
    self.max_size = kwargs.pop( "max_size", 1 )
    self.queue = queue.Queue()
    self.args = args
    self.kwargs = kwargs

  def get( self ):
    if self.queue.qsize() < self.max_size and self.queue.empty():
      self.queue.put( self.func( *self.args, **self.kwargs ) )
    return self.queue.get()

  def put( self, obj ):
    self.queue.put( obj )

###
@contextmanager
def get( pool ):
  obj = pool.get()
  try:
    yield obj
  finally:
    pool.put( obj )
