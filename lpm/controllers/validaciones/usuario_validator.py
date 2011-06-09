from lpm.model import Usuario
from formencode.validators import String, Email, NotEmpty, FieldsMatch, NotEmpty
from formencode import FancyValidator, Schema, All, Invalid

__all__ = ["UsuarioAddFormValidator"]

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
            'Nombre de usuario incorrecto, maximo 32 caracteres'}), 
            UniqueUsername(), NotEmpty(messages={'empty':
                'Ingrese un nombre de usuario'}))
    nombre = All(String(min=2,max=50, messages={'tooShort':
            'Nombre incorrecto, minimo 4 caracteres','tooLong':
            'Nombre incorrecto, maximo 50 caracteres'}),
            NotEmpty(messages={'empty':'Ingrese un nombre'}))
    apellido = All(String(min=2,max=50, messages={'tooShort':
            'Apellido incorrecto, minimo 4 caracteres','tooLong':
            'Apellido incorrecto, maximo 50 caracteres'}),
            NotEmpty(messages={'empty':'Ingrese un apellido'}))
    password = All(String(min=6,messages={'tooShort':
            'Password incorrecto, minimo 6 caracteres'}), 
            NotEmpty(messages={'empty':'Ingrese password'}))
    repita_password = All(String(min=6,messages={'tooShort':
            'Password incorrecto, minimo 6 caracteres'}), 
            NotEmpty(messages={'empty':'Ingrese password'}))
    email = Email(not_empty=True,messages = {
        'empty': 'Ingrese una direccion de email',
        'noAt': 'Un email debe contener un @',
        'badUsername': 'Ingrese un usuario de email correcto',
        'badDomain': 'Ingrese un dominio de email correcto',
        })
    chained_validators=(FieldsMatch('password','repita_password',
                                               messages={'invalidNoMatch':
                                               'Passwords no coinciden'}),)
    nro_documento = All(String(min=5,max=50,messages = {
            'tooLong': "Nro de Documendo invalido, debe tener 5 digitos como minimo",
            'tooShort': "Nro de Documendo invalido",}),
             NotEmpty(messages={'empty':'Ingrese numero de documento'}))
    telefono = All(String(min=6,max=15,messages = {
            'tooLong': "Nro de Telefono invalido, debe tener 6 digitos como minimo",
            'tooShort': "Nro de Telefono invalido",}),
             NotEmpty(messages={'empty':'Ingrese numero de telefono'}))
