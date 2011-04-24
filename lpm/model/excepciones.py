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