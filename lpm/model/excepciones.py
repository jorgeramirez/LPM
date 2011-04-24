# -*- coding: utf-8 -*-

"""
Este módulo contiene las clases de las excepciones que se pueden lanzar por
el modelo

@authors:
    - U{Carlos Bellino<mailto:carlosbellino@gmail.com>}
    - U{Nahuel Hernández<mailto:nahuel.11990@gmail.com>}
    - U{Jorge Ramírez<mailto:jorgeramirez1990@gmail.com>}

@since: 1.0
"""

__all__ = ['ModelError', 'NombreDeAtributoError']


class ModelError(Exception):
    """ Excepcion Base para todas las del modulo """
    pass

    
class NombreDeAtributoError(ModelError):
    def __str__(self):
        return u"El nombre de atributo ya existe"


class CondicionAprobarError(ModelError):
    """
    Excepcion que indica que algunas de las condiciones
    de aprobación de un ítem no se cumplieron.
    """
    
    def __init__(self, msg=u"Algunas condiciones no se cumplen"):
        """
        Constructur para la clase
        
        @param msg: el mensaje a desplegar
        @type msg: C{unicode} o C{str}
        """
        if isinstance(msg, str):
            msg = unicode(msg)
        self.msg = msg
    
    def __str__(self):
        return "Error: %s" % msg
