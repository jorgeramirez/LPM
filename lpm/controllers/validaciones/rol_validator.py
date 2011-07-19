from formencode.validators import String, NotEmpty
from formencode import Schema, All, FancyValidator

__all__ = ['RolFormValidator']

class RolFormValidator(Schema):
    nombre_rol = All(String(min=4, max=32,messages={'tooShort':
            'Nombre de rol incorrecto, minimo 4 caracteres','tooLong':
            'Nombre de rol incorrecto, maximo 32 caracteres'}), 
            NotEmpty(messages={'empty':
                'Ingrese un nombre de rol'}))
    descripcion = String(max=100,messages={'tooLong':
            'Descripcion no debe superar 100 caracteres'})

    permisos = NotEmpty(messages={"empty": 
                                    u"Debe seleccionar al menos un permiso"})
    permisos_src = NotEmpty(messages={"empty": 
                                    u"Debe seleccionar al menos un permiso"})
    #para que no salga el error ese de permisos_src.

