# -*- coding: utf-8 -*-
"""
Global configuration file for TG2-specific settings in LPM.

This file complements development/deployment.ini.

Please note that **all the argument values are strings**. If you want to
convert them into boolean, for example, you should use the
:func:`paste.deploy.converters.asbool` function, as in::
    
    from paste.deploy.converters import asbool
    setting = asbool(global_conf.get('the_setting'))
 
"""

from tg.configuration import AppConfig

import lpm
from lpm import model
from lpm.lib import app_globals, helpers 

base_config = AppConfig()
base_config.renderers = []

base_config.package = lpm

#Enable json in expose
base_config.renderers.append('json')
#Set the default renderer
base_config.default_renderer = 'genshi'
base_config.renderers.append('genshi')
# if you want raw speed and have installed chameleon.genshi
# you should try to use this renderer instead.
# warning: for the moment chameleon does not handle i18n translations
#base_config.renderers.append('chameleon_genshi')

#Configure the base SQLALchemy Setup
base_config.use_sqlalchemy = True
base_config.model = lpm.model
base_config.DBSession = lpm.model.DBSession

# Configure the authentication backend

# YOU MUST CHANGE THIS VALUE IN PRODUCTION TO SECURE YOUR APP 
base_config.sa_auth.cookie_secret = "hola"#"ChangeME" 

base_config.auth_backend = 'sqlalchemy'
base_config.sa_auth.dbsession = model.DBSession
# what is the class you want to use to search for users in the database
base_config.sa_auth.user_class = model.Usuario
# what is the class you want to use to search for groups in the database
base_config.sa_auth.group_class = model.Rol
# what is the class you want to use to search for permissions in the database
base_config.sa_auth.permission_class = model.Permiso

#translatios, para llamar de otra manera lo que usa repoze.what
base_config.sa_auth.translations.users = 'usuarios'
base_config.sa_auth.translations.groups = 'roles'
base_config.sa_auth.translations.user_name = 'nombre_usuario'
base_config.sa_auth.translations.group_name = 'nombre_rol'
base_config.sa_auth.translations.permission_name = 'nombre_permiso'
base_config.sa_auth.translations.permissions = 'permisos'

# override this if you would like to provide a different who plugin for
# managing login and logout of your application
base_config.sa_auth.form_plugin = None

# override this if you are using a different charset for the login form
base_config.sa_auth.charset = 'utf-8'

# You may optionally define a page where you want users to be redirected to
# on login:
base_config.sa_auth.post_login_url = '/post_login'

# You may optionally define a page where you want users to be redirected to
# on logout:
base_config.sa_auth.post_logout_url = '/post_logout'

#toscawidget ON
base_config.use_toscawidgets = True
