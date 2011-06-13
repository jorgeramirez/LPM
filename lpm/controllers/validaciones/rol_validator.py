from formencode.validators import String, NotEmpty
from formencode import Schema, All

__all__ = ['RolFormValidator']

class RolFormValidator(Schema):
    nombre_rol = All(String(min=4, max=32,messages={'tooShort':
            'Nombre de rol incorrecto, minimo 4 caracteres','tooLong':
            'Nombre de rol incorrecto, maximo 70 caracteres'}), 
            NotEmpty(messages={'empty':
                'Ingrese un nombre de rol'}))
    descripcion = String(max=100,messages={'tooLong':
            'Descripcion no debe superar 100 caracteres'})
