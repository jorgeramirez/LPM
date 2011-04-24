# -*- coding: utf-8 -*-
"""
Módulo de prueba para lpm.model.gestconf

@authors:
    - U{Carlos Bellino<mailto:carlosbellino@gmail.com>}
    - U{Nahuel Hernández<mailto:nahuel.11990@gmail.com>}
    - U{Jorge Ramírez<mailto:jorgeramirez1990@gmail.com>}

@since: 1.0 
"""
from nose.tools import eq_

from lpm.model import DBSession
from lpm.model.desarrollo import *
from lpm.model.administracion import *
from lpm.model.gestconf import *
from lpm.model.excepciones import *

from lpm.tests.models import ModelTest
