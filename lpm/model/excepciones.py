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
    'NombreTipoItemError', 'TipoAtributoError', 'CondicionAprobarError',
    'BloquearItemError', 'DesBloquearItemError', 'DesAprobarItemError',
    'ModificarItemError', 'EliminarItemError', 'AdjuntarArchivoError',
    'EliminarArchivoAdjuntoError'
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

class RelacionError(ModelError):
    def __init__(self, msg):
        """
        Constructor para la clase
        
        @param msg: el mensaje a desplegar
        @type msg: C{unicode} o C{str}
        """
        if isinstance(msg, str):
            msg = unicode(msg)
        self.msg = msg
    
    def __str__(self):
        return u"Error: %s" % self.msg

class NombreTipoItemError(ModelError):
    def __str__(self):
        return u"El nombre para el tipo de item es repetido"


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
        return u"Error: %s" % self.msg


class BloquearItemError(ModelError):
    """
    Excepcion lanzada cuando se intenta bloquear un L{Item}
    con estado distinto al de "Aprobado"
    """
    def __str__(self):
        return u"Error: Para bloquear un ítem, el mismo de estar Aprobado"

class DesBloquearItemError(ModelError):
    """
    Excepcion lanzada cuando se intenta desbloquear un L{Item}
    con estado distinto al de "Bloqueado"
    """
    def __str__(self):
        return u"Error: Para desbloquear un ítem, el mismo de estar Bloqueado o Revision-Bloq"

class DesAprobarItemError(ModelError):
    """
    Excepcion lanzada cuando se intenta desaprobar un L{Item}
    con estado distinto al de "Aprobado" o “Revisión-Desbloq”
    """
    def __str__(self):
        return u"Error: Para desaprobar un ítem, el mismo de estar Aprobabo o Revision-Desbloq"


class ModificarItemError(ModelError):
    """
    Excepcion lanzada cuando se intenta modificar un L{Item}
    con estado igual a "Bloqueado", "Revision-Bloq" o "Eliminado"
    """
    def __str__(self):
        return u"Error: No puede modificar un ítem en estado " + \
               u"Bloqueado, Revision-Bloq o Eliminado"

class RevivirItemError(ModelError):
    """
    Excepcion lanzada cuando se intenta revivir un L{Item}
    con estado distinto al de "Eliminado"
    """
    def __str__(self):
        return u"Error: Para revivir un ítem, el mismo debio haber sido eliminado"


class EliminarItemError(ModelError):
    """
    Excepcion lanzada cuando se intenta eliminar un L{Item}
    con estado igual a "Bloqueado", "Revision-Bloq" o "Eliminado"
    """
    def __str__(self):
        return u"Error: No puede eliminar un ítem en estado Bloqueado, Revision-Bloq o Eliminado"


class AdjuntarArchivoError(ModelError):
    """
    Excepcion lanzada cuando se intenta adjuntar un archivo a un L{Item}
    con estado igual a "Bloqueado", "Revision-Bloq" o "Eliminado"
    """
    def __str__(self):
        return u"Error: No puede adjuntar un archivo a un ítem en estado Bloqueado, Revision-Bloq o Eliminado"


class EliminarArchivoAdjuntoError(ModelError):
    """
    Excepcion lanzada cuando se intenta eliminar un archivo de un L{Item}
    con estado igual a "Bloqueado", "Revision-Bloq" o "Eliminado"
    """
    def __str__(self):
        return u"Error: No puede eliminar un archivo de un ítem en estado Bloqueado, Revision-Bloq o Eliminado"
