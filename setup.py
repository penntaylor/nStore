from setuptools import setup

__version__ = '0.0.1'

setup(
  name = 'nStore',
  version = __version__,
  description = '',
  long_description = '',
  author = 'Penn Taylor',
  author_email = 'rpenn3@gmail.com',
  url = 'https://github.com/penntaylor/nStore.git',
  license='ALv2',
  packages = [ 'nstore' ],
  install_requires = [
    'boto3' ],
  include_package_data = True )
