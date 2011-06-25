from formencode.validators import String, NotEmpty
from formencode import Schema, All, FancyValidator

__all__ = ['FaseFormValidator']

class FaseFormValidator(Schema):
    nombre = All(String(min=4, max=32,messages={'tooShort':
            'Nombre de fase incorrecto, minimo 4 caracteres','tooLong':
            'Nombre de fase incorrecto, maximo 32 caracteres'}), 
            NotEmpty(messages={'empty':
                'Ingrese un nombre de fase'}))
    descripcion = String(max=100,messages={'tooLong':
            'Descripcion no debe superar 100 caracteres'})

 
