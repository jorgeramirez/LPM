# -*- coding: utf-8 -*-

"""
Este módulo contiene clases de ayuda 
utilizadas en el sistema

@authors:
    - U{Carlos Bellino<mailto:carlosbellino@gmail.com>}
    - U{Nahuel Hernández<mailto:nahuel.11990@gmail.com>}
    - U{Jorge Ramírez<mailto:jorgeramirez1990@gmail.com>}

@since: 1.0
"""

__all__ = ['UrlParser']

class UrlParser(object):
    """
    Parseador basico de urls.
    """
    
    @classmethod
    def parse_id(cls, url=None, name=None):
        """
        Obtiene el identificador para un componente de la url.
        
        @url: la url a parsear
        @type url: C{str}
        @name: el nombre del elemento a buscar en la url
        @type name: C{str}
        @return: el identificador para el elemento.
        @rtype: C{int}
        """
        if not url: return
        partes = url.split("/")
        for i, v in enumerate(partes):
            if v == name:
                return int(partes[i + 1])
        return None
