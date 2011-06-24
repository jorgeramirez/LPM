# -*- coding: utf-8 -*-
"""
Módulo que define el controlador de usuarios.

@authors:
    - U{Carlos Bellino<mailto:carlosbellino@gmail.com>}
    - U{Nahuel Hernández<mailto:nahuel.11990@gmail.com>}
    - U{Jorge Ramírez<mailto:jorgeramirez1990@gmail.com>}

@since: 1.0
"""
from tgext.crud import CrudRestController
from tg.controllers import RestController
from tg.decorators import (paginate, expose, with_trailing_slash, 
                           without_trailing_slash)
from tg import redirect, request, require, flash, url, validate 

from lpm.controllers.validaciones import UsuarioAddFormValidator, UsuarioEditFormValidator
from lpm.model import DBSession, Usuario, Rol, TipoItem, Proyecto, Fase
from lpm.lib.sproxcustom import CustomTableFiller
from lpm.lib.authorization import PoseePermiso, AlgunPermiso
from lpm.lib.util import UrlParser
from lpm.controllers.rol import (RolTable as RolRolTable,
                                     RolTableFiller as RolRolTableFiller)
from lpm.controllers.proyecto import (ProyectoTableFiller, ProyectoController)

from sprox.tablebase import TableBase
from sprox.fillerbase import TableFiller
#from sprox.dojo.tablebase import DojoTableBase as TableBase
#from sprox.dojo.fillerbase import DojoTableFiller as TableFiller
from sprox.fillerbase import EditFormFiller
#from sprox.formbase import AddRecordForm, EditableForm
from sprox.dojo.formbase import DojoAddRecordForm as AddRecordForm
from sprox.dojo.formbase import DojoEditableForm as EditableForm
from sprox.widgets import PropertySingleSelectField

from tw.forms.fields import PasswordField, TextField, InputField, SubmitButton

from repoze.what.predicates import not_anonymous

from formencode.validators import String, Email, NotEmpty

import transaction

from tg import tmpl_context, request

class UsuarioTable(TableBase):
    __model__ = Usuario
    __headers__ = {'nombre_usuario' : u'Nombre de Usuario', 'email' : u"E-mail",
                   'nombre' : u"Nombre", 'apellido' : u"Apellido", 'creado': u"Fecha Creación"
                  }
    __omit_fields__ = ['id_usuario', 'password', 'telefono', 'nro_documento', 
                       '_password', 'historial_lb', 'roles',
                       'historial_item']
    __default_column_width__ = '15em'
    __column_widths__ = {'email': "35em",
                         'creado': "35em",
                         '__actions__' : "50em"
                        }
#    __url__ = '/usuarios.json'
    
usuario_table = UsuarioTable(DBSession)


class UsuarioTableFiller(CustomTableFiller):
    __model__ = Usuario
    __omit_fields__ = ['password', 'telefono', 'nro_documento', 
                       '_password', 'historial_lb', 'roles',
                       'historial_item']

    def __actions__(self, obj):
        """Links de acciones para un registro dado"""

        clase = 'actions'
        value = "<div>"
        kw = request.params
        contexto=""
        if kw.has_key("id_proyecto"):
            contexto="id_proyecto"
        elif kw.has_key("id_fase"):
            contexto="id_fase"
        elif kw.has_key("id_tipo_item"):
            contexto="id_tipo_item"

        if contexto:
            id = kw[contexto]
            url = "/usuarios/roles/{id}?{ctx}={val}"
            url = url.format(id=obj.id_usuario, ctx=contexto, val=kw[contexto])
            value = '<div>' + \
                    '<a href="' + url + '" class="' + clase + '">Asignar</a>' + \
                    '</div>'
            return value
        
        if PoseePermiso('modificar usuario').is_met(request.environ):
            value += '<div>' + \
                        '<a href="/usuarios/'+ str(obj.id_usuario) +'/edit" ' + \
                        'class="' + clase + '">Modificar</a>' + \
                     '</div><br />'
        if PoseePermiso('eliminar usuario').is_met(request.environ):
            value += '<div><form method="POST" action="' + str(obj.id_usuario) + '" class="button-to">'+\
                     '<input type="hidden" name="_method" value="DELETE" />' +\
                     '<input onclick="return confirm(\'Está seguro?\');" value="Delete" type="submit" '+\
                     'style="background-color: transparent; float:left; border:0; color: #286571;'+\
                     'display: inline; margin: 0; padding: 0;" class="' + clase + '"/>'+\
                     '</form></div><br />'

        if PoseePermiso('asignar-desasignar rol').is_met(request.environ):
            value += '<div>' + \
                        '<a href="/usuarios/roles/' + str(obj.id_usuario) + '" ' +\
                        'class="' + clase + '">Roles</a>' + \
                     '</div><br />'
        value += '</div>'
        return value

    def _do_get_provider_count_and_objs(self, **kw):
        """
        Se muestra la lista de usuario si se tiene un permiso 
        necesario. Caso contrario se muestra solo su usuario
        """
        if AlgunPermiso(tipo="Usuario").is_met(request.environ):
            return super(UsuarioTableFiller,
                         self)._do_get_provider_count_and_objs(**kw)
        username = request.credentials['repoze.what.userid']
        user = Usuario.by_user_name(username)
        return 1, [user]


#    def _do_get_provider_count_and_objs(self, **kw):
#        """
#        Se muestra la lista de usuario si se tiene un permiso 
#        necesario
#        """
#        count, filtrados = super(UsuarioTableFiller, self). \
#                                 _do_get_provider_count_and_objs(**kw)
#        if count == 0:
#            return count, filtrados
#        nombre_usuario = request.credentials['repoze.what.userid']
#        usuario = Usuario.by_user_name(nombre_usuario)
#        for r in usuario.roles:
#            for p in r.permisos:
#                if p.nombre_permiso.find("usuario") > 0:
#                    return count, filtrados
#
#        #si no tiene permisos necesarios lo unico que puede ver es su usuario
#        return 1, [usuario]

    
usuario_table_filler = UsuarioTableFiller(DBSession)


class UsuarioAddForm(AddRecordForm):
    __model__ = Usuario
    __omit_fields__ = ['id_usuario', 'creado', '_password', 'historial_lb', 'roles',
                       'historial_item']
    __require_fields__ = ['nombre_usuario', 'nombre', 'apellido', 'password',
                          'repita_password', 'email']
    __base_validator__ = UsuarioAddFormValidator
    __field_order__ = ['nombre_usuario', 'nombre', 'apellido', 'password',
                       'repita_password', 'email', 'nro_documento', 'telefono']
    __field_attrs__ = {}
    
    repita_password = PasswordField('repita_password')

#    from sprox.formbase import Field
#    roles_boton = Field(SubmitButton('roles'))
                             

usuario_add_form = UsuarioAddForm(DBSession)


class UsuarioEditForm(EditableForm):
    __model__ = Usuario
    __hide_fields__ = ['id_usuario']
    __omit_fields__ = ['nombre_usuario', 'creado', '_password', 'password',
                        'historial_lb', 'roles', 'historial_item']
    __require_fields__ = ['nombre', 'apellido', 'nuevo_password',
                          'repita_password', 'email']
    __base_validator__ = UsuarioEditFormValidator
    __field_order__ = ['nombre_usuario', 'nombre', 'apellido', 'nuevo_password',
                       'repita_password', 'email', 'nro_documento', 'telefono']
    __field_attrs__ = {
                       'nombre_usuario': { 'maxlength' : '32'},
                       'roles' : {'label_text' :'Roles'}
                       }

    nuevo_password = PasswordField('nuevo_password')
    repita_password = PasswordField('repita_nuevo_password')
    
usuario_edit_form = UsuarioEditForm(DBSession)        


class UsuarioEditFiller(EditFormFiller):
    __model__ = Usuario

usuario_edit_filler = UsuarioEditFiller(DBSession)


#tablas para la asignación/desasignación de roles
class RolTable(TableBase):
    __model__ = Rol
    __headers__ = {'nombre_rol' : u'Nombre de Rol',
                   'codigo' : u"Código", 'tipo' : u'Tipo',
                   'proyecto': u'Proyecto', 'fase': u"Fase", 
                   'tipo_item': u"Tipo de Ítem", 'check' : u'Check',
                  }
    __omit_fields__ = ['id_rol', 'permisos', 'usuarios',
                       'id_proyecto', 'id_fase', 'id_tipo_item',
                       'descripcion', 'creado']
    __default_column_width__ = '15em'
    
    __add_fields__ = {'proyecto':None, 'fase': None,
                      'tipo_item': None, 'check' : None}
    __xml_fields__ = ['Check']
    __column_widths__ = {'nombre_rol': "35em",
                         'codigo': "35em",
                         '__actions__' : "50em"
                        }
    __field_order__ = ["nombre_rol", "codigo", "tipo", "proyecto", "fase",
                       "tipo_item", "check"]

    
rol_user_table = RolTable(DBSession)

class RolTableFiller(TableFiller):
    __model__ = Rol
    __add_fields__ = {'proyecto':None, 'fase': None,
                      'tipo_item': None, 'check' : None}

    def check(self, obj, **kw):
        #id
        checkbox = '<input type="checkbox" class="checkbox_tabla" id="' + str(obj.id_rol) + '"/>'
        return checkbox
    
    def proyecto(self, obj, **kw):
        if obj.id_proyecto:
            proy = Proyecto.por_id(obj.id_proyecto)
            return proy.nombre
        else:
            return u"---------"

    def fase(self, obj, **kw):
        if obj.id_fase:
            fase = Fase.por_id(obj.id_fase)
            return fase.nombre
        else:
            return u"---------"
            
    def tipo_item(self, obj, **kw):
        if obj.id_tipo_item:
            tipo_item = TipoItem.por_id(obj.id_tipo_item)
            return tipo_item.codigo
        else:
            return u"---------"
    
    def _do_get_provider_count_and_objs(self, usuario=None, asignados=True, 
                                        id_proyecto=None, id_fase=None,
                                        id_tipo_item=None, **kw):

        if (not asignados):
            roles = Rol.roles_desasignados(usuario.id_usuario, id_proyecto,
                                           id_fase, id_tipo_item)
        elif (asignados):
            roles = usuario.roles
            if id_proyecto or id_fase or id_tipo_item:
                roles = []
                for r in usuario.roles:
                    if id_proyecto and r.id_proyecto != id_proyecto:
                        continue
                    elif id_fase and r.id_fase != id_fase:
                        continue
                    elif id_tipo_item and r.id_tipo_item != id_tipo_item:
                        continue
                    roles.append(r)

        return len(roles), roles

    def __actions__(self, obj):
        """Links de acciones para un registro dado"""

        value = '<div>'
        clase = 'actions'
        contexto = ""
        url_cont = ""
        
        #if (obj.tipo == "Sistema"):
        #    url_cont = "/roles/"
        #else:
        #    url_cont = "/rolesplantilla/"
        #    tipo = obj.tipo.lower()
        #    if (tipo.find(u"proyecto") >= 0):
        #        contexto = "proyecto"
        #    elif (tipo.find(u"fase") >= 0):
        #        contexto = "fase"
        #    else:
        #        contexto = "ti"

        perm_mod = None
        perm_del = None
        if (obj.tipo == "Sistema"):
            url_cont = "/roles/"
            perm_mod = PoseePermiso('modificar rol')
            perm_del = PoseePermiso('eliminar rol')
        else:
            url_cont = "/rolesplantilla/"
            tipo = obj.tipo.lower()
            if (tipo.find(u"proyecto") >= 0):
                contexto = "proyecto"
                if tipo == "proyecto":
                    perm_mod = PoseePermiso('modificar rol', 
                                            id_proyecto=obj.id_proyecto)
                    perm_del = PoseePermiso('eliminar rol',
                                            id_proyecto=obj.id_proyecto)
                else:
                    perm_mod = PoseePermiso('modificar rol')
                    perm_del = PoseePermiso('eliminar rol')
            elif (tipo.find(u"fase") >= 0):
                contexto = "fase"
                if tipo == "fase":
                    perm_mod = PoseePermiso('modificar rol', 
                                            id_fase=obj.id_fase)
                    perm_del = PoseePermiso('eliminar rol',
                                            id_fase=obj.id_fase)
                else:
                    perm_mod = PoseePermiso('modificar rol')
                    perm_del = PoseePermiso('eliminar rol')
            else:
                contexto = "ti"
                if tipo.find("plantilla") >= 0:
                    perm_mod = PoseePermiso('modificar rol')
                    perm_del = PoseePermiso('eliminar rol')
                else:
                    perm_mod = PoseePermiso('modificar rol', 
                                            id_tipo_item=obj.id_tipo_item)
                    perm_del = PoseePermiso('eliminar rol',
                                            id_tipo_item=obj.id_tipo_item)


        #if PoseePermiso('modificar rol').is_met(request.environ):
        if perm_mod.is_met(request.environ):
            value += '<div>' + \
                        '<a href="' +  url_cont + str(obj.id_rol) + "/edit?contexto="+  \
                        contexto + '" class="' + clase + '">Modificar</a>' + \
                     '</div><br />'
        #if PoseePermiso('eliminar rol').is_met(request.environ):
        if perm_del.is_met(request.environ):
            value += '<div><form method="POST" action="/roles/' + str(obj.id_rol) + '" class="button-to">'+\
                     '<input type="hidden" name="_method" value="DELETE" />' +\
                     '<input onclick="return confirm(\'Está seguro?\');" value="Delete" type="submit" '+\
                     'style="background-color: transparent; float:left; border:0; color: #286571;'+\
                     'display: inline; margin: 0; padding: 0;" class="' + clase + '"/>'+\
                     '</form></div><br />'
        value += '</div>'
        return value
        
roles_usuario_filler = RolTableFiller(DBSession)


class UsuarioController(CrudRestController):
    """Controlador de usuarios"""
    #{ Variables
    title = u"Administrar usuarios"
    action = '/usuarios/'
    #{ Plantillas

    # No permitir usuarios anonimos (?)
    allow_only = not_anonymous(u"El usuario debe haber iniciado sesión")
    
    #{ Modificadores
    model = Usuario
    table = usuario_table
    table_filler = usuario_table_filler
    new_form = usuario_add_form
    edit_form = usuario_edit_form
    edit_filler = usuario_edit_filler

    #para el form de busqueda
    #columnas = dict(nombre_usuario="texto", nombre="texto", apellido="texto",
    #                email="texto", nro_documento="texto")
    opciones = dict(nombre_usuario="Nombre de Usuario", 
                    nombre="Nombre", 
                    apellido="Apellido",
                    email="Email", 
                    nro_documento="Nro. de Documento")
    columnas = dict(nombre_usuario="texto", 
                    nombre="texto", 
                    apellido="texto",
                    email="texto", 
                    nro_documento="entero")
    #comboboxes = dict()
 
    #{ Métodos
    @with_trailing_slash
    @paginate('lista_elementos', items_per_page=5)
    @expose('lpm.templates.usuario.get_all')
    @expose('json')
    def get_all(self, *args, **kw):
        """ 
        Retorna todos los registros
        Retorna una página HTML si no se especifica JSON
        """
        puede_crear = PoseePermiso("crear usuario").is_met(request.environ)
        titulo = self.title

        if request.response_type == 'application/json':
            return self.table_filler.get_value(**kw)
        if not getattr(self.table.__class__, '__retrieves_own_value__', False):
            usuarios = self.table_filler.get_value(**kw)
        else:
            usuarios = []
            
        tmpl_context.widget = usuario_table
        
        de_proyectos = ""
        try:
            de_proyectos = "http://" + request.environ.get('HTTP_HOST',) + "/proyectos/" + kw["id_proyecto"] + "/edit"
        except Exception: 
            pass
        if request.environ.get('HTTP_REFERER') == de_proyectos:
            atras = request.environ.get('HTTP_REFERER')
        else:
            atras = '/'

        
        retorno = dict(lista_elementos=usuarios, 
                    page=titulo, titulo=titulo, 
                    modelo=self.model.__name__, 
                    columnas=self.columnas,
                    opciones=self.opciones,
                    url_action=self.action,
                    puede_crear=puede_crear, 
                    atras=atras)

        params_buscar = u""
        if kw.has_key("id_proyecto"):
            params_buscar = "id_proyecto=%s" % kw["id_proyecto"]
        elif kw.has_key("id_fase"):
            params_buscar = "id_proyecto=%s" % kw["id_fase"]
        elif kw.has_key("id_tipo_item"):
            params_buscar = "id_proyecto=%s" % kw["id_tipo_item"]
        
        if params_buscar:
            retorno["titulo"] = u"Seleccionar Usuario"
            retorno["params_buscar"] = params_buscar
            retorno["puede_crear"] = False
        
        return retorno

    @expose('lpm.templates.usuario.edit')
    def edit(self, *args, **kw):
        """Despliega una pagina para modificar usuario"""
        '''
        pp = PoseePermiso('modificar usuario', id_usuario=args[0])
        if not pp.is_met(request.environ):
            flash(pp.message % pp.nombre_permiso, 'warning')
            redirect("/usuarios")
        '''
        
        puede_asignar_rol = PoseePermiso("asignar-desasignar rol").is_met(request.environ)
        class mis_roles_tf(RolRolTableFiller):
            def __actions__(self, obj):
                """Links de acciones para un registro dado"""
                clase = 'actions'
                contexto = ""
                url_cont = ""
                value = "<div></div>"
                if (obj.tipo == "Sistema"):
                    url_cont = "/roles/"
                else:
                    url_cont = "/rolesplantilla/"
                    tipo = obj.tipo.lower()
                    if (tipo.find(u"proyecto") >= 0):
                        contexto = "proyecto"
                    elif (tipo.find(u"fase") >= 0):
                        contexto = "fase"
                    else:
                        contexto = "ti"
                
                if PoseePermiso('modificar rol').is_met(request.environ):
                    value = '<div>' + \
                                '<a href="' +  url_cont + str(obj.id_rol) + "/edit?contexto="+  \
                                contexto + '" class="' + clase + '">Ver</a>' + \
                             '</div>'
                return value

            def _do_get_provider_count_and_objs(self, **kw):
                user = Usuario.por_id(int(kw["id_usuario"]))
                return len(user.roles), user.roles

        tmpl_context.widget = self.edit_form
        usuarios = self.table_filler.get_value(**kw)
        roles = mis_roles_tf(DBSession).get_value(id_usuario=args[0])
        tmpl_context.tabla_roles = RolRolTable(DBSession)
        user = Usuario.por_id(args[0])
        
        if request.environ.get('HTTP_REFERER') == "http://" + request.environ.get('HTTP_HOST',) + "/":
            atras = "/"
        else:
            atras = '/usuarios'
        
        if (False): # si viene de /usuarios/perfil
            page = "Mi perfil"
        else:
            page = "Usuario {nombre}".format(nombre=user.nombre_usuario)
        
        return dict(super(UsuarioController, self).edit(*args, **kw), 
                    page=page,
                    roles=roles,
                    id=args[0], 
                    puede_asignar_rol=puede_asignar_rol,
                    atras=atras
                    )
        
    @expose()
    def perfil(self, *args, **kw):
        """ Despliega una pagina para modificar el perfil del usuario que 
        inició sesión """
        user = request.identity['repoze.who.userid']
        id = Usuario.by_user_name(user)

        url = '/usuarios/' + str(id.id_usuario) + '/edit'
        redirect(url)

    @expose('lpm.templates.usuario.new')
    def new(self, *args, **kw):
        """Despliega una pagina para crear un usuario"""
#        pp = PoseePermiso('modificar usuario', id_usuario=args[0])
#        if not pp.is_met(request.environ):
#            flash(pp.message % pp.nombre_permiso, 'warning')
#            redirect("/usuarios")
        if request.environ.get('HTTP_REFERER') == "http://" + request.environ.get('HTTP_HOST',) + "/":
            atras = "../"
        else:
            atras = self.action
        return dict(super(UsuarioController, self).new(*args, **kw),
                     page='Nuevo Usuario', atras=atras)
 
    @validate(usuario_edit_form, error_handler=edit)
    @expose()
    def put(self, *args, **kw):
        if "sprox_id" in kw:
            del kw["sprox_id"]
        if "repita_nuevo_password" in kw:
            del kw["repita_nuevo_password"]
        if kw["nro_documento"]:
            kw["nro_documento"] = int(kw["nro_documento"])
        pp = PoseePermiso('modificar usuario')
        if not pp.is_met(request.environ):
            flash(pp.message % pp.nombre_permiso, 'warning')
            redirect(self.action)

        usuario = Usuario.por_id(args[0])
        usuario.nombre = kw["nombre"]
        usuario.apellido = kw["apellido"]
        usuario.email = kw["email"]
        usuario.telefono = kw["telefono"]
        usuario.nro_documento = kw["nro_documento"]
        usuario.password = kw["nuevo_password"]
    
        redirect("../") 
    
    @validate(usuario_add_form, error_handler=new)
    @expose()
    def post(self, *args, **kw):
        if "sprox_id" in kw:
            del kw["sprox_id"]
        if "repita_password" in kw:
            del kw["repita_password"]
        if kw["nro_documento"]:
            kw["nro_documento"] = int(kw["nro_documento"])
            
        usuario = Usuario(**kw)
        DBSession.add(usuario)
        redirect("./")

    @expose('lpm.templates.usuario.roles')
    def roles(self, *args, **kw):
        """ Asignar y desasignar Roles """
        tmpl_context.tabla_asignados = rol_user_table
        tmpl_context.tabla_desasignados = rol_user_table
        user = Usuario.por_id(args[0])
        page = "Roles de Usuario {nombre}".format(nombre=user.nombre_usuario)

        contexto=""
        valor = None
        for k in ["id_fase", "id_proyecto", "id_tipo_item"]:
            if kw.has_key(k):
                kw[k] = int(kw[k])
                contexto = k
                valor = kw[k]
                break
                
        asignados = roles_usuario_filler.get_value(usuario=user,
                                                          asignados=True, **kw)
        desasignados = roles_usuario_filler.get_value(usuario=user,
                                                       asignados=False, **kw)
        
        if request.environ.get('HTTP_REFERER') == "http://" + request.environ.get('HTTP_HOST',) + "/usuarios/":
            atras = self.action
        if kw.has_key("id_proyecto"):
            atras = "/proyectos/%s/edit" % kw["id_proyecto"]
        else:
            atras = self.action + str(user.id_usuario) + '/edit'
        return dict(asignados=asignados, 
                    desasignados=desasignados,
                    page=page, 
                    id=args[0], 
                    atras=atras,
                    contexto=contexto,
                    valor_contexto=valor)

    @with_trailing_slash
    @paginate('lista_elementos', items_per_page=5)
    @expose('lpm.templates.usuario.get_all')
    @expose('json')
    def post_buscar(self, *args, **kw):

        params_buscar = u""
        ctx = ""
        val_ctx = ""
        if kw.has_key("id_proyecto"):
            params_buscar = "id_proyecto=%s" % kw["id_proyecto"]
            ctx = "id_proyecto"
        elif kw.has_key("id_fase"):
            params_buscar = "id_proyecto=%s" % kw["id_fase"]
            ctx = "id_fase"
        elif kw.has_key("id_tipo_item"):
            params_buscar = "id_proyecto=%s" % kw["id_tipo_item"]
            ctx = "id_tipo_item"
        
        if ctx:
            val_ctx = kw[ctx]
            del kw[ctx]

        puede_crear = PoseePermiso("crear usuario").is_met(request.environ)
        tmpl_context.widget = self.table
        buscar_table_filler = UsuarioTableFiller(DBSession)
        buscar_table_filler.filtros = kw
        
        if ctx:
            kw[ctx] = int(val_ctx)
            
        usuarios = buscar_table_filler.get_value(**kw)
        
        if request.environ.get('HTTP_REFERER') != "http://" + request.environ.get('HTTP_HOST',) + "/usuarios/":
            atras = request.environ.get('HTTP_REFERER')
        else:
            atras = '/usuarios'  

        
        retorno = dict(lista_elementos=usuarios, 
                    page=self.title, titulo=self.title, 
                    modelo=self.model.__name__, 
                    columnas=self.columnas,
                    opciones=self.opciones,
                    url_action=self.action, 
                    puede_crear=puede_crear, 
                    atras=atras)

        if params_buscar:
            retorno["titulo"] = u"Seleccionar Usuario"
            retorno["params_buscar"] = params_buscar
            retorno["puede_crear"] = False
        
        return retorno
            
    
    @expose('lpm.templates.usuario.roles')
    def desasignar_roles(self, *args, **kw):
        """ Desasigna los roles seleccionados a un usuario """
        if kw:
            pks = []
            for k, pk in kw.items():
                if not k.isalnum():
                    continue
                pks.append(int(pk))
            transaction.begin()
            user = Usuario.por_id(int(args[0]))
            c = 0
            while c < len(user.roles):
                if user.roles[c].id_rol in pks:
                    del user.roles[c]
                else:
                    c += 1
            transaction.commit()
        return self.roles(*args, **kw)

    @expose('lpm.templates.usuario.roles')
    def asignar_roles(self, *args, **kw):
        """ Asigna los roles seleccionados a un usuario """
        if kw:
            pks = []
            for k, pk in kw.items():
                if not k.isalnum():
                    continue
                pks.append(int(pk))
            transaction.begin()
            user = Usuario.por_id(int(args[0]))
            roles = DBSession.query(Rol).filter(Rol.id_rol.in_(pks)).all()
            for r in roles:
                if r.tipo.find("Plantilla") >= 0: #crear rol a partir de plantilla
                    id = None
                    for k in ["id_proyecto", "id_fase", "id_tipo_item"]:
                        if kw.has_key(k):
                            id = kw[k]
                            break
                    rol_new = Rol.nuevo_rol_desde_plantilla(plantilla=r, id=id)
                    rol_new.usuarios.append(user)
                else:
                    r.usuarios.append(user)
            transaction.commit()
        return self.roles(*args, **kw)
    
    @without_trailing_slash
    @paginate('lista_elementos', items_per_page=5)
    @expose('lpm.templates.proyecto.get_all')
    @expose('json')
    def proyectos(self, *args, **kw):
        id_usuario = args[0]


        class user_proy_filler(ProyectoTableFiller):
            """
            TableFiller temporal utilizado para recuperar los proyectos del
            usuario
            """
            def _do_get_provider_count_and_objs(self, id_usuario=None, **kw):
                count, proys = super(user_proy_filler, 
                                     self)._do_get_provider_count_and_objs(**kw)
                filtrados = []
                for p in proys:
                    if p.obtener_lider().id_usuario == int(id_usuario):
                        filtrados.append(p)
                return len(filtrados), filtrados

            def __actions__(self, obj):
                """Links de acciones para un registro dado"""
                value = '<div>'
                clase = 'actions'
                if PoseePermiso('modificar proyecto',
                                id_proyecto=obj.id_proyecto).is_met(request.environ):
                    value += '<div>' + \
                                '<a href="/proyectos/'+ str(obj.id_proyecto) + '/edit" ' + \
                                'class="' + clase + '">Examinar</a>' + \
                             '</div><br />'
                value += '</div>'
                return value

        
        upf = user_proy_filler(DBSession)
        if kw.keys():
            upf.filtros = kw
        proyectos = upf.get_value(id_usuario=id_usuario)
        tmpl_context.widget = ProyectoController.table
        atras = '../%s/edit' % id_usuario
        titulo = u"Proyectos del Usuario"
        url_action = "./%s/" % id_usuario
        if UrlParser.parse_nombre(request.url, "post_buscar"):
            url_action = "../"
            atras = "../"
            
        return dict(lista_elementos=proyectos, 
                    page=titulo,
                    titulo=titulo, 
                    modelo="Proyecto", 
                    columnas=ProyectoController.columnas,
                    opciones=ProyectoController.opciones,
                    url_action=url_action,
                    puede_crear=False,
                    comboboxes=ProyectoController.comboboxes,
                    atras=atras
                    )
    #}
