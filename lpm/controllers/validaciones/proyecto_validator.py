from tg import request

from lpm.lib.util import UrlParser
from lpm.model import Proyecto

from formencode.validators import String, NotEmpty
from formencode import Schema, All, FancyValidator, Invalid

__all__ = ['ProyectoAddFormValidator', 'ProyectoEditFormValidator']

class UniqueNewNombre(FancyValidator):
    def _to_python(self, value, state):
        nombres = Proyecto.por_nombre(value)
        if nombres != None:
            raise Invalid('El nombre de proyecto ya existe en sistema',
                                        value, state)
        return value

class ProyectoAddFormValidator(Schema):
    nombre = All(String(min=4, max=32,messages={'tooShort':
            'Nombre de proyecto incorrecto, minimo 4 caracteres','tooLong':
            'Nombre de rol incorrecto, maximo 32 caracteres'}),UniqueNewNombre(), 
            NotEmpty(messages={'empty':
                'Ingrese un nombre de proyecto'}))
    descripcion = String(max=200,messages={'tooLong':
            'Descripcion no debe superar 200 caracteres'})
 
class UniqueEditNombre(FancyValidator):
    def _to_python(self, value, state):
        nombres = Proyecto.por_nombre(value)
        id_proyecto = UrlParser.parse_id(request.url, "proyectos")
        print id_proyecto
        if nombres != None and id_proyecto != nombres.id_proyecto:
            raise Invalid('El nombre de proyecto ya existe en sistema',
                                        value, state)
        return value

class ProyectoEditFormValidator(ProyectoAddFormValidator):
    nombre = All(String(min=4, max=32,messages={'tooShort':
            'Nombre de proyecto incorrecto, minimo 4 caracteres','tooLong':
            'Nombre de rol incorrecto, maximo 32 caracteres'}),UniqueEditNombre(), 
            NotEmpty(messages={'empty':
                'Ingrese un nombre de proyecto'}))
    
