from lpm.model import Usuario
from formencode.validators import String, Email, NotEmpty, FieldsMatch
from formencode import FancyValidator, Schema, All, Invalid


class UniqueUsername(FancyValidator):
    def _to_python(self, value, state):
        usernames = Usuario.by_user_name(value)
        print usernames
        if usernames != None:
            raise Invalid('El usuario ya existe',
                                        value, state)
        return value

class UsuarioAddFormValidator(Schema):
    nombre_usuario = All(String(min=4, max=32,messages={'tooShort':
                                               'Nombre de usuario incorrecto, minimo 4 caracteres','tooLong':
                                               'Nombre de usuario incorrecto, maximo 32 caracteres'}), UniqueUsername())
    nombre = String(min=2,max=50)
    apellido = String(min=2,max=50)
    password = String(min=6)
    repita_password = String(min=6)
    email = Email(not_empty=True)
    chained_validators=(FieldsMatch('password','repita_password',
                                               messages={'invalidNoMatch':
                                               'Passwords no coinciden'}),)
    nro_documento = String(min=5,max=50)
    telefono = String(min=6,max=15)
