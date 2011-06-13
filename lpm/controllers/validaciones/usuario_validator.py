from tg import request

from lpm.lib.util import UrlParser
from lpm.model import Usuario

from formencode.validators import String, Email, NotEmpty, FieldsMatch, NotEmpty, Int
from formencode import FancyValidator, Schema, All, Invalid

__all__ = ['UsuarioAddFormValidator','UsuarioEditFormValidator']

class UniqueUsername(FancyValidator):
    def _to_python(self, value, state):
        usernames = Usuario.by_user_name(value)
        if usernames != None:
            raise Invalid('El usuario ya existe en sistema',
                                        value, state)
        return value

class UniqueNewEmail(FancyValidator):
    def _to_python(self, value, state):
        emails = Usuario.by_email_address(value)
        if emails != None:
            raise Invalid('Email ya existe en sistema',
                                        value, state)
        return value

class UniqueNewNroDocumento(FancyValidator):
    def _to_python(self, value, state):
        nro_doc = Usuario.by_nro_documento(value)
        if nro_doc != None:
            raise Invalid('Nro de Documento ya existe en sistema',
                                        value, state)
        return value

class isInt(Int):
    def _to_python(self, value, state):
        try:
            int(value)
            return value
        except (ValueError, TypeError):
            raise Invalid(self.message('integer', state),
                          value, state)    

class UsuarioAddFormValidator(Schema):
    nombre_usuario = All(String(min=4, max=32,messages={'tooShort':
            'Nombre de usuario incorrecto, minimo 4 caracteres','tooLong':
            'Nombre de usuario incorrecto, maximo 32 caracteres'}), 
            UniqueUsername(), NotEmpty(messages={'empty':
                'Ingrese un nombre de usuario'}))
    nombre = All(String(min=2,max=50, messages={'tooShort':
            'Nombre incorrecto, minimo 2 caracteres','tooLong':
            'Nombre incorrecto, maximo 50 caracteres'}),
            NotEmpty(messages={'empty':'Ingrese un nombre'}))
    apellido = All(String(min=2,max=50, messages={'tooShort':
            'Apellido incorrecto, minimo 2 caracteres','tooLong':
            'Apellido incorrecto, maximo 50 caracteres'}),
            NotEmpty(messages={'empty':'Ingrese un apellido'}))
    password = All(String(min=6,messages={'tooShort':
            'Password incorrecto, minimo 6 caracteres'}), 
            NotEmpty(messages={'empty':'Ingrese password'}))
    repita_password = All(String(min=6,messages={'tooShort':
            'Password incorrecto, minimo 6 caracteres'}), 
            NotEmpty(messages={'empty':'Ingrese password'}))
    email = All(UniqueNewEmail(),Email(not_empty=True,messages = {
        'empty': 'Ingrese una direccion de email',
        'noAt': 'Un email debe contener un @',
        'badUsername': 'Ingrese un usuario de email correcto',
        'badDomain': 'Ingrese un dominio de email correcto',
        }))
    chained_validators=(FieldsMatch('password','repita_password',
                                               messages={'invalidNoMatch':
                                               'Passwords no coinciden'}),)
    nro_documento = All(UniqueNewNroDocumento(),String(min=5,max=50,messages = {
            'tooLong': "Nro de Documendo invalido, debe tener 5 digitos como minimo",
            'tooShort': "Nro de Documendo invalido",}),
             NotEmpty(messages={'empty':'Ingrese numero de documento'}),
             isInt(messages={'integer':'Ingrese un numero'}))
    telefono = All(String(min=6,max=15,messages = {
            'tooShort': "Nro de Telefono invalido, debe tener 6 digitos como minimo",
            'tooLong': "Nro de Telefono invalido",}),
             NotEmpty(messages={'empty':'Ingrese numero de telefono'}),
             isInt(messages={'integer':'Ingrese un numero'}))
             

class UniqueEditEmail(FancyValidator):
    def _to_python(self, value, state):
        emails = Usuario.by_email_address(value)
        id_usuario = UrlParser.parse_id(request.url, "usuarios")
        if emails != None and id_usuario != emails.id_usuario:
            raise Invalid('Email ya existe en sistema',
                                        value, state)
        return value

class UniqueEditNroDocumento(FancyValidator):
    def _to_python(self, value, state):
        nro_doc = Usuario.by_nro_documento(value)
        id_usuario = UrlParser.parse_id(request.url, "usuarios")
        if nro_doc != None and id_usuario != nro_doc.id_usuario:
            raise Invalid('Nro de Documento ya existe en sistema',
                                        value, state)
        return value

class UsuarioEditFormValidator(UsuarioAddFormValidator):
    nombre_usuario = None
    password = None
    repita_password = None
    nuevo_password = All(String(min=6,messages={'tooShort':
            'Password incorrecto, minimo 6 caracteres'}), 
            NotEmpty(messages={'empty':'Ingrese password'}))
    repita_nuevo_password = All(String(min=6,messages={'tooShort':
            'Password incorrecto, minimo 6 caracteres'}), 
            NotEmpty(messages={'empty':'Ingrese password'}))
    email = All(UniqueEditEmail(),Email(not_empty=True,messages = {
        'empty': 'Ingrese una direccion de email',
        'noAt': 'Un email debe contener un @',
        'badUsername': 'Ingrese un usuario de email correcto',
        'badDomain': 'Ingrese un dominio de email correcto',
        }))
    chained_validators=(FieldsMatch('nuevo_password','repita_nuevo_password',
                                               messages={'invalidNoMatch':
                                               'Passwords no coinciden'}),)
    nro_documento = All(UniqueEditNroDocumento(),String(min=5,max=50,messages = {
            'tooShort': "Nro de Documendo invalido, debe tener 5 digitos como minimo",
            'tooLong': "Nro de Documendo invalido",}),
             NotEmpty(messages={'empty':'Ingrese numero de documento'}),
             isInt(messages={'integer':'Ingrese un numero'}))
