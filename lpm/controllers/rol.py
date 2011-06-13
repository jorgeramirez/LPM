# -*- coding: utf-8 -*-
"""
Módulo que define el controlador de roles.

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

from lpm.model import (DBSession, Usuario, Rol, Permiso, Proyecto, 
                       Fase, TipoItem)
from lpm.lib.sproxcustom import CustomTableFiller
from lpm.lib.sproxcustom import WidgetSelectorDojo, MultipleSelectDojo
from lpm.lib.authorization import PoseePermiso, AlgunPermiso

from sprox.tablebase import TableBase
from sprox.fillerbase import TableFiller
#from sprox.dojo.tablebase import DojoTableBase as TableBase
#from sprox.dojo.fillerbase import DojoTableFiller as TableFiller
from sprox.fillerbase import EditFormFiller
#from sprox.formbase import AddRecordForm, EditableForm
from sprox.dojo.formbase import DojoAddRecordForm as AddRecordForm
from sprox.dojo.formbase import DojoEditableForm as EditableForm
from sprox.widgets import PropertySingleSelectField

from tw.forms.fields import PasswordField, TextField, TextArea, Button

from repoze.what.predicates import not_anonymous

from tg import tmpl_context, request

import transaction


class RolTable(TableBase):
    __model__ = Rol
    __headers__ = {'nombre_rol' : u'Nombre de Rol',
                   'codigo' : u"Código", 'creado': u"Fecha Creación",
                   'tipo' : u'Tipo'
                  }
    __omit_fields__ = ['id_rol', 'permisos', 'usuarios',
                       'id_proyecto', 'id_fase', 'id_tipo_item',
                       'descripcion']
    __default_column_width__ = '15em'
    __column_widths__ = {'nombre_rol': "35em",
                         'codigo': "35em",
                         '__actions__' : "50em"
                        }
    
rol_table = RolTable(DBSession)


class RolTableFiller(CustomTableFiller):
    __model__ = Rol
    __omit_fields__ = ['permisos', 'usuarios',
                       'id_proyecto', 'id_fase', 'id_tipo_item',
                       'descripcion']
   
    def __actions__(self, obj):
        """Links de acciones para un registro dado"""
        value = '<div>'
        clase = 'actions'
        url_cont = ""
        if obj.tipo == "Sistema":
            url_cont = "/roles/"
        elif obj.tipo == "Plantilla":
            url_cont = "/rolesplantilla/"
        else:
            url_cont = "/rolescontexto/"
        if PoseePermiso('modificar rol').is_met(request.environ):
            value += '<div>' + \
                        '<a href="' + url_cont + str(obj.id_rol) +'/edit" ' + \
                        'class="' + clase + '">Modificar</a>' + \
                     '</div><br />'
        if PoseePermiso('eliminar rol').is_met(request.environ):
            value += '<div><form method="POST" action="' + url_cont + str(obj.id_rol) + '" class="button-to">'+\
                     '<input type="hidden" name="_method" value="DELETE" />' +\
                     '<input onclick="return confirm(\'Está seguro?\');" value="Delete" type="submit" '+\
                     'style="background-color: transparent; float:left; border:0; color: #286571;'+\
                     'display: inline; margin: 0; padding: 0;" class="' + clase + '"/>'+\
                     '</form></div><br />'
        value += '</div>'
        return value
    
    def _do_get_provider_count_and_objs(self, **kw):
        """
        Se muestra la lista de rol si se tiene un permiso 
        necesario. Caso contrario le muestra sus roles.
        """
        if AlgunPermiso(patron="rol").is_met(request.environ):
            return super(RolTableFiller,
                         self)._do_get_provider_count_and_objs(**kw)
        username = request.credentials['repoze.what.userid']
        user = Usuario.by_user_name(username)
        return len(user.roles), user.roles 

rol_table_filler = RolTableFiller(DBSession)


class RolPlantillaTableFiller(RolTableFiller):
    def _do_get_provider_count_and_objs(self, **kw):
        """
        Se muestra la lista de rol si se tiene un permiso 
        necesario.
        """
        if AlgunPermiso(patron="rol").is_met(request.environ):
            query = DBSession.query(Rol).filter(Rol.tipo.like(u"Plantilla"))
            return query.count(), query.all()
        return 0, []

rol_plantilla_table_filler = RolPlantillaTableFiller(DBSession)


class RolContextoTableFiller(RolTableFiller):
    def _do_get_provider_count_and_objs(self, **kw):
        """
        Se muestra la lista de rol si se tiene un permiso 
        necesario.
        """
        if AlgunPermiso(patron="rol").is_met(request.environ):
            query = DBSession.query(Rol).filter(Rol.tipo.in_([u"Proyecto",
                                                u"Fase", u"Tipo de Ítem"]))
            return query.count(), query.all()
        return 0, []

rol_contexto_table_filler = RolContextoTableFiller(DBSession)


class CodProyectoField(PropertySingleSelectField):
    """Dropdown list para codigo de proyecto"""
    def _my_update_params(self, d, nullable=False):
        options = []
        options.append((0, "----------"))
        proyectos = DBSession.query(Proyecto).all()
        for p in proyectos:
            options.append((p.id_proyecto, '%s (%s)' % (p.codigo, 
                    p.nombre)))
        d['options'] = options
        return d
  

class CodFaseField(PropertySingleSelectField):
    """Dropdown list para codigo de fase"""
    def _my_update_params(self, d, nullable=False):
        options = []
        options.append((0, "----------"))
        fases = DBSession.query(Fase).all()
        for f in fases:
            options.append((f.id_fase, '%s (%s)' % (f.codigo, 
                    f.nombre)))
        d['options'] = options
        return d


class CodTipoItemField(PropertySingleSelectField):
    """Dropdown list para codigo de tipo de item"""
    def _my_update_params(self, d, nullable=False):
        options = []
        options.append((0, "----------"))
        tipos = DBSession.query(TipoItem).all()
        for t in tipos:
            options.append((t.id_tipo_item, '%s' % t.codigo))
        d['options'] = options
        return d

#para mejorar el multiple selector hecho en dojo
class PermisosMultipleSelect(MultipleSelectDojo):
    def _my_update_params(self, d, nullable=False):
        options, selected = [], []
        permisos = self.get_permisos()
        for p in permisos:
            if d['value'] and p.id_permiso in d['value']: #seleccionados
                selected.append((p.id_permiso, '%s' % p.nombre_permiso))
            else:
                options.append((p.id_permiso, '%s' % p.nombre_permiso))
        d['options'] = options
        d['selected_options'] = selected
        return d
    
    def get_permisos(self):
        pass


#para mejorar el multiple selector hecho en dojo
class PermisosSistemaMultipleSelect(PermisosMultipleSelect):
    def get_permisos(self):
        return Permiso.permisos_de_sistema()


class PermisosPlantillaMultipleSelect(PermisosMultipleSelect):
    def get_permisos(self):
        return DBSession.query(Permiso).all()


class PermisosContextoMultipleSelect(PermisosMultipleSelect):
    def get_permisos(self):
        return Permiso.permisos_con_contexto()


class SelectorPermisosSistema(WidgetSelectorDojo):
    default_multiple_select_field_widget_type = PermisosSistemaMultipleSelect


class SelectorPermisosPlantilla(WidgetSelectorDojo):
    default_multiple_select_field_widget_type = PermisosPlantillaMultipleSelect


class SelectorPermisosContexto(WidgetSelectorDojo):
    default_multiple_select_field_widget_type = PermisosContextoMultipleSelect


class RolAddForm(AddRecordForm):
    __model__ = Rol
    __omit_fields__ = ['id_rol', 'usuarios',
                       'codigo', 'creado', 'tipo', 'id_proyecto', 'id_fase',
                       'id_tipo_item']
    __require_fields__ = ['nombre_rol', 'permisos']
    __check_if_unique__ = True
    __field_order__ = ['nombre_rol', 'descripcion', 'permisos']
    __field_attrs__ = {'descripcion' : {'row': '1'},
                       'nombre_rol': { 'maxlength' : '32'}
                       
                       }
    __widget_selector_type__ = SelectorPermisosSistema
    descripcion = TextArea                         
    
rol_add_form = RolAddForm(DBSession)


class RolPlantillaAddForm(RolAddForm):
    __widget_selector_type__ = SelectorPermisosPlantilla

rol_plantilla_add_form = RolPlantillaAddForm(DBSession)


class RolContextoAddForm(RolAddForm):
    __omit_fields__ = ['id_rol', 'usuarios','codigo', 'creado', 'tipo']
    __field_order__ = ['nombre_rol', 'descripcion',
                        'id_proyecto', 'id_fase', 'id_tipo_item',
                        'permisos']
    __widget_selector_type__ = SelectorPermisosContexto
    id_proyecto = CodProyectoField("id_proyecto", label_text="Proyecto")
    id_fase = CodFaseField("id_fase", label_text="Fase")
    id_tipo_item = CodTipoItemField("id_tipo_item", label_text="Tipo de Item")
    descripcion = TextArea
    
rol_contexto_add_form = RolContextoAddForm(DBSession)
    


class RolEditForm(EditableForm):
    __model__ = Rol
    __hide_fields__ = ['id_rol']
    __omit_fields__ = [ 'usuarios',
                       'codigo', 'creado', 'tipo', 'id_proyecto',
                       'id_fase', 'id_tipo_item']
    __require_fields__ = ['nombre_rol', 'permisos']
    __check_if_unique__ = True
    __field_order__ = ['nombre_rol', 'descripcion', 'permisos']
    __field_attrs__ = {'descripcion' : {'row': '1'},
                       'nombre_rol': { 'maxlength' : '32'}
                       
                      }
    __widget_selector_type__ = SelectorPermisosSistema
    descripcion = TextArea

rol_edit_form = RolEditForm(DBSession)


class RolPlantillaEditForm(RolEditForm):
    __widget_selector_type__ = SelectorPermisosPlantilla
    
rol_plantilla_edit_form = RolPlantillaEditForm(DBSession)


class RolContextoEditForm(RolEditForm):
    __omit_fields__ = ['id_rol', 'usuarios','codigo', 'creado', 'tipo']
    __field_order__ = ['nombre_rol', 'descripcion',
                        'id_proyecto', 'id_fase', 'id_tipo_item',
                        'permisos']
    __widget_selector_type__ = SelectorPermisosContexto
    id_proyecto = CodProyectoField("id_proyecto", label_text="Proyecto")
    id_fase = CodFaseField("id_fase", label_text="Fase")
    id_tipo_item = CodTipoItemField("id_tipo_item", label_text="Tipo de Item")
    descripcion = TextArea

rol_contexto_edit_form = RolContextoEditForm(DBSession)        


class RolEditFiller(EditFormFiller):
    __model__ = Rol

rol_edit_filler = RolEditFiller(DBSession)


class RolController(CrudRestController):
    """Controlador de roles"""
    #{ Variables
    title = u"Administrar Roles"
    action = "/roles/"
    rol_tipo = u"Sistema" #indica que el tipo no hay que averiguar.
    #{ Plantillas

    # No permitir rols anonimos (?)
    allow_only = not_anonymous(u"El rol debe haber iniciado sesión")
    
    #{ Modificadores
    model = Rol
    table = rol_table
    table_filler = rol_table_filler
    new_form = rol_add_form
    edit_form = rol_edit_form
    edit_filler = rol_edit_filler

    #para el form de busqueda
    columnas = dict(codigo="texto", nombre_rol="texto", tipo="combobox")
    tipo_opciones = [u'Plantilla', u'Sistema', u'Proyecto',
                        u'Fase', u'Tipo de Ítem']
 
    #{ Métodos
    @with_trailing_slash
    @paginate('lista_elementos', items_per_page=5)
    @expose('lpm.templates.rol.get_all')
    @expose('json')
    def get_all(self, *args, **kw):
        """ 
        Retorna todos los registros
        Retorna una página HTML si no se especifica JSON
        """
        puede_crear = PoseePermiso("crear rol").is_met(request.environ)
        if request.response_type == 'application/json':
            return self.table_filler.get_value(**kw)
        if not getattr(self.table.__class__, '__retrieves_own_value__', False):
            roles = self.table_filler.get_value(**kw)
        else:
            roles = []
        tmpl_context.widget = self.table
        return dict(lista_elementos=roles, page=self.title, titulo=self.title, 
                    modelo=self.model.__name__, columnas=self.columnas,
                    tipo_opciones=self.tipo_opciones, url_action=self.action,
                    puede_crear=puede_crear)

    @expose('lpm.templates.rol.edit')
    def edit(self, *args, **kw):
        """Despliega una pagina para modificar rol"""
        pp = PoseePermiso('modificar rol')
        if not pp.is_met(request.environ):
            flash(pp.message % pp.nombre_permiso, 'warning')
            redirect(self.action)
        tmpl_context.widget = self.edit_form
        value = self.edit_filler.get_value(values={'id_rol': int(args[0])})
        value['_method'] = 'PUT'
        page = "Rol {nombre}".format(nombre=value["nombre_rol"])
        nav = dict(atras=self.action, adelante=self.action)
        return dict(value=value, page=page, nav=nav)

    @without_trailing_slash
    @expose('lpm.templates.rol.new')
    def new(self, *args, **kw):
        """Despliega una pagina para crear un rol"""
        pp = PoseePermiso('crear rol')
        if not pp.is_met(request.environ):
            flash(pp.message % pp.nombre_permiso, 'warning')
            redirect(self.action)
        tmpl_context.widget = self.new_form
        nav = dict(atras=self.action, adelante=self.action)
        return dict(value=kw, page="Nuevo Rol", action=self.action, nav=nav)
    
    @validate(rol_add_form, error_handler=new)
    @expose()
    def post(self, *args, **kw):
        """create a new record"""
        pp = PoseePermiso('crear rol')
        if not pp.is_met(request.environ):
            flash(pp.message % pp.nombre_permiso, 'warning')
            redirect(self.action)
        transaction.begin()
        kw["tipo"] = self.rol_tipo
        Rol.crear_rol(**kw)
        transaction.commit()
        redirect(self.action)
        
    @validate(rol_edit_form, error_handler=edit)
    @expose()
    def put(self, *args, **kw):
        """update a record"""
        print kw
        pp = PoseePermiso('modificar rol')
        if not pp.is_met(request.environ):
            flash(pp.message % pp.nombre_permiso, 'warning')
            redirect(self.action)
        id_rol = int(args[0][0])
        if kw.has_key("id_rol"):
            del kw["id_rol"]
        transaction.begin()
        Rol.actualizar_rol(id_rol, **kw)
        transaction.commit()
        redirect(self.action)

    @with_trailing_slash
    @paginate('lista_elementos', items_per_page=5)
    @expose('lpm.templates.rol.get_all')
    @expose('json')
    def post_buscar(self, *args, **kw):
        puede_crear = PoseePermiso("crear rol").is_met(request.environ)
        tmpl_context.widget = self.table
        buscar_table_filler = self.table_filler.__class__(DBSession)
        buscar_table_filler.filtros = kw
        roles = buscar_table_filler.get_value()
        return  dict(lista_elementos=roles, page=self.title, titulo=self.title, 
                    modelo=self.model.__name__, columnas=self.columnas,
                    tipo_opciones=self.tipo_opciones, url_action=self.action,
                    puede_crear=puede_crear)
    #}
    

class RolPlantillaController(RolController):
    """Controlador de roles de tipo plantilla"""
    #{ Variables
    title = u"Administrar Roles de Plantilla"
    action = "/rolesplantilla/"
    rol_tipo = u"Plantilla" #indica que el tipo no hay que averiguar.

    #{ Modificadores
    model = Rol
    table = rol_table
    table_filler = rol_plantilla_table_filler
    new_form = rol_plantilla_add_form
    edit_form = rol_plantilla_edit_form
    edit_filler = rol_edit_filler

    #para el form de busqueda
    columnas = dict(codigo="texto", nombre_rol="texto")
    tipo_opciones = []
    
    #{ Métodos
    @expose('lpm.templates.rol.edit')
    def edit(self, *args, **kw):
        """Despliega una pagina para modificar rol"""
        return super(RolPlantillaController, self).edit(*args, **kw)

    @without_trailing_slash
    @expose('lpm.templates.rol.new')
    def new(self, *args, **kw):
        return super(RolPlantillaController, self).new(*args, **kw)

    @validate(rol_plantilla_add_form, error_handler=new)
    @expose()
    def post(self, *args, **kw):
        super(RolPlantillaController, self).post(*args, **kw)

    @validate(rol_plantilla_edit_form, error_handler=edit)
    @expose()
    def put(self, *args, **kw):
        super(RolPlantillaController, self).put(*args, **kw)

    @with_trailing_slash
    @paginate('lista_elementos', items_per_page=5)
    @expose('lpm.templates.rol.get_all')
    @expose('json')
    def post_buscar(self, *args, **kw):
        return super(RolPlantillaController, self).post_buscar(*args, **kw)
    #}


class RolContextoController(RolController):
    """Controlador de roles con contexto"""
    #{ Variables
    title = u"Administrar Roles con Contexto"
    action = "/rolescontexto/"
    rol_tipo = u"deducir" #indica que el tipo hay que deducir.
    
    #{ Modificadores
    model = Rol
    table = rol_table
    table_filler = rol_contexto_table_filler
    new_form = rol_contexto_add_form
    edit_form = rol_contexto_edit_form
    edit_filler = rol_edit_filler

    #para el form de busqueda
    columnas = dict(codigo="texto", nombre_rol="texto")
    tipo_opciones = [u'Proyecto', u'Fase', u'Tipo de Ítem']
    
    #{ Métodos
    @expose('lpm.templates.rol.edit')
    def edit(self, *args, **kw):
        """Despliega una pagina para modificar rol"""
        return super(RolContextoController, self).edit(*args, **kw)

    @without_trailing_slash
    @expose('lpm.templates.rol.new')
    def new(self, *args, **kw):
        return super(RolContextoController, self).new(*args, **kw)
        
    @validate(rol_contexto_add_form, error_handler=new)
    @expose()
    def post(self, *args, **kw):
        super(RolContextoController, self).post(*args, **kw)

    @validate(rol_contexto_edit_form, error_handler=edit)
    @expose()
    def put(self, *args, **kw):
        super(RolContextoController, self).put(*args, **kw)

    @with_trailing_slash
    @paginate('lista_elementos', items_per_page=5)
    @expose('lpm.templates.rol.get_all')
    @expose('json')
    def post_buscar(self, *args, **kw):
        return super(RolContextoController, self).post_buscar(*args, **kw)
    #}
