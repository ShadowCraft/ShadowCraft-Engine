from __future__ import absolute_import
from future import standard_library
standard_library.install_aliases()
import gettext
import os.path
import locale
import builtins
import sys

_ = gettext.gettext

# Domain: this needs to be the name of our .mo files
TRANSLATION_DOMAIN = 'SCE'
LOCALE_DIR = os.path.join(os.path.dirname(__file__), "locale")

def set_language(language):
    # This function will install gettext as the _() function and use the
    # language specified. It will fall back to code strings if given a not supported
    # language. Note that the 'local' value only makes sense when not running from
    # the hosted online version.
    install_args = { }
    if sys.api_version < 3:
        install_args['str'] = True
    if language == 'local':
        # Setting up a list of locales in your machine and asign them to the _() function
        languages_list = []

        default_local_language, encoding = locale.getdefaultlocale()
        if (default_local_language):
            languages_list = [default_local_language]

        gnu_lang = os.environ.get('LANGUAGE', None)
        if (gnu_lang):
            languages_list += gnu_lang.split(":")

        gettext.translation(TRANSLATION_DOMAIN, LOCALE_DIR, fallback=True, languages=languages_list).install(**install_args)

    else:
        gettext.translation(TRANSLATION_DOMAIN, LOCALE_DIR, fallback=True, languages=[language]).install(**install_args)
