from future import standard_library
standard_library.install_aliases()
import gettext
import builtins

builtins._ = gettext.gettext
