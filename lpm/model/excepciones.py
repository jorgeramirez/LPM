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

__all__ = [
    'ModelError', 'NombreDeAtributoError', 'NombreFaseError',
    'CodigoTipoItemError', 'TipoAtributoError', 'CondicionAprobarError',
    'BloquearItemError'
]


class ModelError(Exception):
    """ Excepcion Base para todas las del modulo """
    pass


class NombreFaseError(ModelError):
    def __str__(self):
        return u"El nombre de fase ya existe"

    
class NombreDeAtributoError(ModelError):
    def __str__(self):
        return u"El nombre de atributo ya existe"


class CodigoTipoItemError(ModelError):
    def __str__(self):
        return u"El código para el tipo de item es repetido"


class TipoAtributoError(ModelError):
    def __str__(self):
        return u"No se puede cambiar el tipo de un atributo de tipo instanciado"

    
class CondicionAprobarError(ModelError):
    """
    Excepcion que indica que algunas de las condiciones
    de aprobación de un ítem no se cumplieron.
    """
    
    def __init__(self, msg=u"Algunas condiciones no se cumplen"):
        """
        Constructor para la clase
        
        @param msg: el mensaje a desplegar
        @type msg: C{unicode} o C{str}
        """
        if isinstance(msg, str):
            msg = unicode(msg)
        self.msg = msg
    
    def __str__(self):
        return "Error: %s" % self.msg


class BloquearItemError(ModelError):
    """
    Excepcion lanzada cuando se intenta bloquear un L{Item}
    con estado distinto al de "Aprobado"
    """
    def __str__(self):
        return u"Error: Para bloquear un ítem, el mismo de estar Aprobado"