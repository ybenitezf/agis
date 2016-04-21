# -*- coding: utf-8 -*-

import datetime
from gluon.storage import Storage
from agiscore.gui.mic import Accion, grid_simple
from agiscore.gui.evento import form_configurar_evento
from agiscore.gui.persona import form_crear_persona_ex
from agiscore.db.evento import esta_activo
from agiscore.db import pais as pais_model
from agiscore.db.matricula import SIN_MATRICULAR, SIN_MATRICULAR_CON_DEUDA
from agiscore.db.matricula import MATRICULADO, MATRICULADO_CON_DEUDAS
from agiscore.validators import IS_DATE_LT

# TODO: remove
response.menu = []

menu_lateral.append(Accion(T('Configurar evento'),
                           URL('configurar', args=[request.args(0)]),
                           auth.has_membership(role=myconf.take('roles.admin'))),
                    ['configurar'])
menu_lateral.append(Accion(T('Registro'),
                           URL('index', args=[request.args(0)]),
                           auth.user is not None),
                    ['index', 'pago', 'matricular', 'nuevo'])

@auth.requires(auth.has_membership(role=myconf.take('roles.admin')))
def configurar():
    """Configuración del evento"""
    C = Storage()
    C.evento = db.evento(request.args(0))
    C.ano = db.ano_academico(C.evento.ano_academico_id)
    C.unidad = db.unidad_organica(C.ano.unidad_organica_id)
    C.escuela = db.escuela(C.unidad.escuela_id)

    # breadcumbs
    u_link = Accion(C.unidad.abreviatura or C.unidad.nombre,
                    URL('unidad', 'index', args=[C.unidad.id]),
                    True)  # siempre dentro de esta funcion
    menu_migas.append(u_link)
    a_links = Accion(C.ano.nombre,
                     URL('unidad', 'index', args=[C.unidad.id]),
                     True)
    menu_migas.append(a_links)
    e_link = Accion(C.evento.nombre,
                    URL('index', args=[C.evento.id]),
                    True)
    menu_migas.append(e_link)
    menu_migas.append(T("Ajustes"))

    back_url = URL('index', args=[C.evento.id])

    C.form = form_configurar_evento(C.evento, back_url,
                                    db=db,
                                    request=request,
                                    T=T)
    if C.form.process().accepted:
        session.flash = T("Ajustes guardados")
        redirect(back_url)

    return dict(C=C)

@auth.requires_login()
def index():
    """UI evento de confirmación de matricua después del plazo"""
    C = Storage()
    C.evento = db.evento(request.args(0))
    C.ano = db.ano_academico(C.evento.ano_academico_id)
    C.unidad = db.unidad_organica(C.ano.unidad_organica_id)
    C.escuela = db.escuela(C.unidad.escuela_id)

    # breadcumbs
    u_link = Accion(C.unidad.abreviatura or C.unidad.nombre,
                    URL('unidad', 'index', args=[C.unidad.id]),
                    True)  # siempre dentro de esta funcion
    menu_migas.append(u_link)
    a_links = Accion(C.ano.nombre,
                     URL('unidad', 'index', args=[C.unidad.id]),
                     True)
    menu_migas.append(a_links)
    e_link = Accion(C.evento.nombre,
                    URL('index', args=[C.evento.id]),
                    True)
    menu_migas.append(e_link)
    menu_migas.append(T("Estudiantado"))

    con_pago = db.tipo_pago(nombre="CONFIRMAÇÃO DA MATRÍCULA APOS O PRAZO LEGAL")
    if con_pago is None:
        raise HTTP(404)

    C.titulo = T("Registro de estudiantes")

    # configuración del grid
    tbl = db.estudiante

    query = (tbl.persona_id == db.persona.id)
    query &= (tbl.unidad_organica_id == C.unidad.id)
    query &= (tbl.id == db.matricula.estudiante_id)
    query &= (db.matricula.ano_academico_id == C.ano.id)
    query &= (db.matricula.situacion != 1)
    query &= (~db.matricula.estado_uo.belongs(MATRICULADO,
                                              MATRICULADO_CON_DEUDAS))

    campos = [tbl.id,
              tbl.codigo,
              db.persona.id,
              db.persona.numero_identidad,
              db.persona.nombre_completo,
              db.matricula.regimen_id,
              db.matricula.estado_uo,
              db.matricula.id]
    for f in tbl:
        f.readable = False
    tbl.codigo.readable = True
    for f in db.persona:
        f.readable = False
    db.persona.numero_identidad.readable = True
    db.persona.nombre_completo.readable = True
    for f in db.matricula:
        f.readable = False
    db.matricula.estado_uo.readable = True
    db.matricula.regimen_id.readable = True
    tbl.codigo.label = T("#MEC")
    db.persona.numero_identidad.label = T("#IDENT")
    db.persona.nombre_completo.label = T("Nombre")
    db.matricula.estado_uo.label = T("ESTADO")
    text_lengths = {'persona.nombre_completo': 45,
                    'matricula.estado_uo': 45}
    es_admin = auth.has_membership(role=myconf.take('roles.admin'))
    admin_o_cobrador = es_admin or \
                       auth.has_membership(role=myconf.take('roles.cobrador_matricula'))
    adm_co_admdoc = es_admin
    adm_co_admdoc |= auth.has_membership(role=myconf.take('roles.confirmador_matricula'))
    adm_co_admdoc |= auth.has_membership(role=myconf.take('roles.admdocente'))
    ev_activo = esta_activo(C.evento)

    def _enlaces(row):
        co = CAT()
        # buscar un pago para la persona

        if row.matricula.estado_uo == SIN_MATRICULAR_CON_DEUDA:
            # si no ha pagado poner enlace para pagar
            pago_link = URL('pago', args=[C.evento.id, row.persona.id])
            puede_pagar = admin_o_cobrador

            puede_pagar &= ev_activo
            co.append(Accion(CAT(SPAN('', _class='glyphicon glyphicon-hand-up'),
                                 ' ',
                                 T("Falta de pago")),
                             pago_link,
                             puede_pagar,
                             _class="btn btn-default btn-xs",
                             _title=T("Pago confirmación de matricula")))
        if row.matricula.estado_uo == SIN_MATRICULAR:
            # poner enlace para confirmación de matricula
            c_link = URL('matricular', args=[C.evento.id, row.persona.id])
            puede_confirmar = adm_co_admdoc

            puede_confirmar &= ev_activo
            co.append(Accion(CAT(SPAN('', _class='glyphicon glyphicon-hand-up'),
                                 ' ',
                                 T("Confirmar")),
                             c_link,
                             puede_confirmar,
                             _class="btn btn-default btn-xs",
                             _title=T("Confirmación de matricula")))

        return co
    enlaces = [dict(header='', body=_enlaces)]

    C.nuevo = Accion(CAT(SPAN('', _class='glyphicon glyphicon-hand-up'),
                         ' ',
                         T("Crear nuevo")),
                     URL('nuevo', args=[C.evento.id]),
                     es_admin and ev_activo,
                     _class="btn btn-default")

    C.grid = grid_simple(query,
                         create=False,
                         field_id=db.persona.id,
                         searchable=True,
                         fields=campos,
                         links=enlaces,
                         paginate=20,
                         maxtextlengths=text_lengths,
                         args=request.args[:1])

    return dict(C=C)

@auth.requires(auth.has_membership(role=myconf.take('roles.admin')) or
               auth.has_membership(role=myconf.take('roles.cobrador_matricula')))
def pago():
    C = Storage()
    C.evento = db.evento(request.args(0))
    C.ano = db.ano_academico(C.evento.ano_academico_id)
    C.unidad = db.unidad_organica(C.ano.unidad_organica_id)
    C.escuela = db.escuela(C.unidad.escuela_id)
    C.persona = db.persona(request.args(1))
    C.estudiante = db.estudiante(persona_id=C.persona.id)
    matricula = db.matricula(estudiante_id=C.estudiante.id,
                       ano_academico_id=C.ano.id)
    if C.persona is None:
        raise HTTP(404)

    # buscar un tipo de pago que coincida en nombre con el tipo de evento
    concepto = db(
        db.tipo_pago.nombre == "CONFIRMAÇÃO DA MATRÍCULA APOS O PRAZO LEGAL"
    ).select().first()
    if not concepto:
        raise HTTP(404)
    C.concepto = concepto

    # breadcumbs
    u_link = Accion(C.unidad.abreviatura or C.unidad.nombre,
                    URL('unidad', 'index', args=[C.unidad.id]),
                    True)  # siempre dentro de esta funcion
    menu_migas.append(u_link)
    a_links = Accion(C.ano.nombre,
                     URL('unidad', 'index', args=[C.unidad.id]),
                     True)
    menu_migas.append(a_links)
    e_link = Accion(C.evento.nombre,
                    URL('index', args=[C.evento.id]),
                    True)
    menu_migas.append(e_link)
    menu_migas.append(T("Pago") + " de {}".format(concepto.nombre))

    campos = list()
    fld_cantidad = db.pago.get("cantidad")
    fld_cantidad.requires.append(
        IS_FLOAT_IN_RANGE(1.0,
                          9999999999.99,
                          error_message=T("Debe ser mayor que {0}".format(concepto.cantidad))))
    campos.append(db.pago.get("forma_pago"))
    campos.append(fld_cantidad)
    campos.append(db.pago.get("numero_transaccion"))
    campos.append(db.pago.get("transaccion"))
    campos.append(db.pago.get("codigo_recivo"))
    campos.append(db.pago.get("fecha_recivo"))
    back = URL('index', args=[C.evento.id])
    manejo = SQLFORM.factory(*campos, submit_button=T('Guardar'))
    manejo.add_button(T("Cancel"), back)
    C.form = manejo
    C.titulo = "{} {} - {}".format(T("Pago"),
                         concepto.nombre,
                         C.persona.nombre_completo)

    tbl = db.pago
    query =  (tbl.persona_id == C.persona.id)
    query &= (tbl.tipo_pago_id == C.concepto.id)
    query &= (tbl.evento_id == C.evento.id)

    C.pagos = db(query).select(tbl.forma_pago, tbl.numero_transaccion,
                               tbl.transaccion, tbl.codigo_recivo,
                               tbl.fecha_recivo,
                               tbl.cantidad)

    if manejo.process().accepted:
        valores = manejo.vars
        valores.tipo_pago_id = concepto.id
        valores.persona_id = C.persona.id
        valores.evento_id = C.evento.id
        db.pago.insert(**db.pago._filter_fields(valores))
        sum = db.pago.cantidad.sum()
        sum = db(query).select(sum).first()[sum]
        if sum >= concepto.cantidad:
            if matricula.estado_uo == SIN_MATRICULAR_CON_DEUDA:
                matricula.estado_uo = SIN_MATRICULAR
                matricula.update_record()
            redirect(back)
        else:
            redirect(URL("pago", args=request.args))
        session.flash = T('Pago registrado')

    return dict(C=C)

@auth.requires(auth.has_membership(role=myconf.take('roles.admin')) or
               auth.has_membership(role=myconf.take('roles.confirmador_matricula')) or
               auth.has_membership(role=myconf.take('roles.admdocente')))
def matricular():
    C = Storage()
    C.evento = db.evento(request.args(0))
    C.ano = db.ano_academico(C.evento.ano_academico_id)
    C.unidad = db.unidad_organica(C.ano.unidad_organica_id)
    C.escuela = db.escuela(C.unidad.escuela_id)
    C.persona = db.persona(request.args(1))
    C.estudiante = db.estudiante(persona_id=C.persona.id)
    matricula = db.matricula(estudiante_id=C.estudiante.id,
                       ano_academico_id=C.ano.id)

    if C.persona is None:
        raise HTTP(404)

    # breadcumbs
    u_link = Accion(C.unidad.abreviatura or C.unidad.nombre,
                    URL('unidad', 'index', args=[C.unidad.id]),
                    True)  # siempre dentro de esta funcion
    menu_migas.append(u_link)
    a_links = Accion(C.ano.nombre,
                     URL('unidad', 'index', args=[C.unidad.id]),
                     True)
    menu_migas.append(a_links)
    e_link = Accion(C.evento.nombre,
                    URL('index', args=[C.evento.id]),
                    True)
    menu_migas.append(e_link)
    menu_migas.append(T("CONFIRMAÇÃO DA MATRÍCULA APOS O PRAZO LEGAL"))

    # inicializar el proceso
    # -- cancelar
    mi_vars = Storage(request.vars)  # make a copy
    mi_vars._formulario_inscribir = 1
    cancelar = URL(c=request.controller, f=request.function,
                   args=request.args, vars=mi_vars)
    back = URL('index', args=[C.evento.id])
    proximo = URL(c=request.controller,
               f=request.function,
               args=request.args,
               vars=request.vars)

    if request.vars._formulario_inscribir:
        session.wh2db = None
        redirect(back)

    if session.wh2db is None:
        session.wh2db = Storage(dict(step=0))
        session.wh2db.persona = Storage()
        session.wh2db.estudiante = Storage()
        session.wh2db.matricula = Storage()
    data = session.wh2db
    step = data.step

    # ------------------------------------------------- PERSONA

    if step == 0:
        # datos personales
        fld_nombre = db.persona.get("nombre")
        fld_apellido1 = db.persona.get("apellido1")
        fld_apellido2 = db.persona.get("apellido2")
        fld_fecha_nacimiento = db.persona.get("fecha_nacimiento")
        fld_genero = db.persona.get("genero")
        fld_padre = db.persona.get("nombre_padre")
        fld_madre = db.persona.get("nombre_madre")
        fld_estado_civil = db.persona.get("estado_civil")
        fld_estado_politico = db.persona.get("estado_politico")
        fld_situacion_militar = db.persona.get("situacion_militar")
        fld_pais_origen = db.persona.get("pais_origen")

        fld_nombre.requires = [IS_NOT_EMPTY(), IS_UPPER()]
        fld_apellido1.requires = IS_UPPER()
        fld_apellido2.requires = [IS_NOT_EMPTY(), IS_UPPER()]
        hoy = datetime.date.today()
        _15anos = datetime.timedelta(days=(15 * 365))
        fld_fecha_nacimiento.requires = [IS_DATE_LT(maximo=hoy - _15anos),
                                         IS_NOT_EMPTY()]
        fld_padre.requires = [IS_NOT_EMPTY(), IS_UPPER()]
        fld_madre.requires = [IS_NOT_EMPTY(), IS_UPPER()]
        fld_pais_origen.requires = IS_IN_DB(db, "pais.id",
                                            "%(nombre)s",
                                            zero=T("(ESCOGER UNO)"))

        form = SQLFORM.factory(fld_nombre,
            fld_apellido1,
            fld_apellido2,
            fld_fecha_nacimiento,
            fld_genero,
            fld_padre, fld_madre,
            fld_estado_civil,
            fld_estado_politico,
            fld_situacion_militar,
            fld_pais_origen,
            record=C.persona,
            showid=False,
            table_name="persona",
            submit_button=T("Next"),
            )
        form.add_button("Cancel", cancelar)
        C.grid = form
        C.titulo = T("Datos personales")
        if form.process().accepted:
            session.wh2db.step = 1
            # en form_crear_persona.valores tenemos los datos validados
            session.wh2db.persona.update(db.persona._filter_fields(form.vars))
            C.persona.update_record(**session.wh2db.persona)
            redirect(proximo)
        return dict(C=C)

    if step == 1:
        # ORIGEN
        # Si el país de origen es ANGOLA, se puede preguntar por el lugar
        # de nacimiento.
        origen = db.pais(C.persona.pais_origen)
        campos = list()
        if origen.codigo == pais_model.ANGOLA:
            s = db(db.comuna.id > 0 and db.municipio.id == db.comuna.municipio_id)
            comunas = [(r.comuna.id, "{0} / {1}".format(r.comuna.nombre, r.municipio.nombre)) \
                for r in s.select(orderby=db.comuna.nombre)]
            fld_lugar_nacimiento = db.persona.get("lugar_nacimiento")
            fld_lugar_nacimiento.requires = IS_IN_SET(comunas, zero=T("(ESCOGER UNO)"))
            # -- arreglo para la representasión de las comunas.
            campos.append(fld_lugar_nacimiento)
        else:
            data.persona.lugar_nacimiento = None
            # no debe tener lugar de nacimiento
            C.persona.update_record(lugar_nacimiento=None)
            fld_tiene_nacionalidad = Field('tiene_nacionalidad',
                                           'boolean',
                                           default=True)
            fld_tiene_nacionalidad.label = T("¿Posee nacionalidad angolana?")
            campos.append(fld_tiene_nacionalidad)
        form = SQLFORM.factory(*campos,
                               table_name="persona",
                               submit_button=T("Next"))
        form.vars.update(C.persona)
        form.add_button("Cancel", cancelar)
        C.grid = form
        C.titulo = T("Origen")
        if form.process().accepted:
            session.wh2db.persona.update(db.persona._filter_fields(form.vars))
            C.persona.update_record(**session.wh2db.persona)
            session.wh2db.step = 2
            redirect(proximo)
        return dict(C=C)

    if data.persona.lugar_nacimiento or data.persona.tiene_nacionalidad:
        # BILHETE DE IDENTIDADE
        session.wh2db.persona.tipo_documento_identidad_id = 1
    else:
        # PASAPORTE
        session.wh2db.persona.tipo_documento_identidad_id = 2

    if step == 2:
        # residencia 1
        campos = []
        fld_numero_identidad = db.persona.get("numero_identidad")
        fld_pais_residencia = db.persona.get("pais_residencia")
        fld_pais_residencia.requires = IS_IN_DB(db, "pais.id",
                                                "%(nombre)s",
                                                zero=None)
        if data.persona.tipo_documento_identidad_id == 1:
            fld_pais_residencia.default = 3
            fld_numero_identidad.label = T("Carnet de identidad")
        else:
            fld_pais_residencia.default = C.persona.pais_origen
            fld_numero_identidad.label = T("Número de pasaporte")
        fld_numero_identidad.requires = [IS_NOT_EMPTY(), IS_UPPER(),
            IS_NOT_IN_DB(db, "persona.numero_identidad")]
        campos.append(fld_numero_identidad)
        campos.append(fld_pais_residencia)
        form = SQLFORM.factory(*campos,
                               record=C.persona,
                               showid=False,
                               table_name="persona",
                               submit_button=T("Next"))
        form.add_button("Cancel", cancelar)
        C.grid = form
        C.titulo = T("Residencia 1/2")
        if form.process().accepted:
            session.wh2db.persona.update(db.persona._filter_fields(form.vars))
            C.persona.update_record(**session.wh2db.persona)
            session.wh2db.step = 3
            redirect(proximo)
        return dict(C=C)

    if step == 3:
        # residencia 2
        campos = []
        fld_direccion = db.persona.get("direccion")
        pais_residencia = db.pais(C.persona.pais_residencia)
        if pais_residencia.codigo == pais_model.ANGOLA:
            fld_comuna = db.persona.get("dir_comuna_id")
            fld_comuna.label = T("Localidad")
            s = db((db.comuna.id > 0) & (db.municipio.id == db.comuna.municipio_id))
            comunas = [(r.comuna.id, "{0} / {1}".format(r.comuna.nombre, r.municipio.nombre)) \
                for r in s.select(orderby=db.comuna.nombre)]
            fld_comuna.requires = IS_IN_SET(comunas, zero=T("(ESCOGER UNO)"))
            campos.append(fld_comuna)
        campos.append(fld_direccion)
        form = SQLFORM.factory(*campos,
                               record=C.persona,
                               showid=False,
                               table_name="persona",
                               submit_button=T("Next"))
        form.add_button("Cancel", cancelar)
        C.grid = form
        C.titulo = T("Residencia 2/2")
        if form.process().accepted:
            session.wh2db.persona.update(db.persona._filter_fields(form.vars))
            C.persona.update_record(**session.wh2db.persona)
            session.wh2db.step = 4
            redirect(proximo)
        return dict(C=C)

    if step == 4:
        # datos de contacto
        campos = []
        fld_telefono = db.persona.get("telefono")
        fld_telefono2 = db.persona.get("telefono_alternativo")
        fld_email = db.persona.get("email")
        fld_email.requires = IS_EMPTY_OR(IS_EMAIL())
        campos.append(fld_telefono)
        campos.append(fld_telefono2)
        campos.append(fld_email)
        form = SQLFORM.factory(*campos,
                               record=C.persona,
                               showid=False,
                               table_name="persona",
                               submit_button=T("Next"))
        form.add_button("Cancel", cancelar)
        C.grid = form
        C.titulo = T("Contacto")
        if form.process().accepted:
            session.wh2db.persona.update(db.persona._filter_fields(form.vars))
            C.persona.update_record(**session.wh2db.persona)
            session.wh2db.step = 5
            redirect(proximo)
        return dict(C=C)

    # ------------------------------------------------- FIN PERSONA

    # ------------------------------------------------- ESTUDIANTE
    if step == 5:
        # -- recoger los datos del estudiante
        fld_habilitacion = db.estudiante.get('pro_habilitacion')
        fld_tipo_escuela = db.estudiante.get('pro_tipo_escuela')
        fld_pro_carrera = db.estudiante.get('pro_carrera')
        fld_pro_carrera.comment = T('''
            Nombre de la carrera que concluyó en la enseñanza previa
        ''')
        fld_pro_ano = db.estudiante.get('pro_ano')
        fld_pro_ano.comment = T('''
            Año en que se gradúo en la enseñanza media
        ''')
        fld_pro_ano.requires = IS_IN_SET(range(1950,
                                               datetime.date.today().year + 1),
                                         zero=None)
        fld_pro_ano.default = datetime.date.today().year - 1
        fld_tipo_escuela.requires = IS_IN_DB(db,
                                             'tipo_escuela_media.id',
                                             "%(nombre)s",
                                             zero=T("(ESCOGER UNO)"))

        form = SQLFORM.factory(fld_habilitacion,
                                 fld_tipo_escuela,
                                 fld_pro_carrera,
                                 fld_pro_ano,
                                 record=C.estudiante,
                                 showid=False,
                                 table_name="estudiante",
                                 submit_button=T("Next"))
        form.add_button("Cancel", cancelar)
        C.grid = form
        C.titulo = T("Procedencia 1/2")
        if form.process().accepted:
            session.wh2db.step = 6
            session.wh2db.estudiante.update(db.estudiante._filter_fields(form.vars))
            C.estudiante.update_record(**session.wh2db.estudiante)
            redirect(proximo)

        return dict(C=C)

    if step == 6:
        # --segunda parte de los datos de procedencia
        C.titulo = T("Procedencia 2/2")

        # -- configurar campos
        campos = []
        tipo_escuela_id = C.estudiante.pro_tipo_escuela
        tipo_escuela = db.tipo_escuela_media(tipo_escuela_id)
        if tipo_escuela.uuid != "a57d6b2b-8f0e-4962-a2a6-95f5c82e015d":
            fld_pro_escuela = db.estudiante.get("pro_escuela_id")
            esc_set = (db.escuela_media.id > 0)
            esc_set &= (db.escuela_media.tipo_escuela_media_id == tipo_escuela_id)
            fld_pro_escuela.requires = IS_IN_DB(db(esc_set),
                                                db.escuela_media.id,
                                                '%(nombre)s',
                                                zero=None)
            campos.append(fld_pro_escuela)
        fld_pro_media = db.estudiante.get("pro_media")
        campos.append(fld_pro_media)
        fld_es_trab = Field('es_trab', 'string', length=1, default='Não')
        fld_es_trab.label = T('¿Es trabajador?')
        fld_es_trab.requires = IS_IN_SET(['Sim', 'Não'], zero=None)
        campos.append(fld_es_trab)

        form = SQLFORM.factory(*campos,
                                 table_name="estudiante",
                                 submit_button=T("Next"))
        form.add_button("Cancel", cancelar)
        form.vars.update(C.estudiante)
        form.vars.es_trab = 'Sim' if C.estudiante.es_trabajador else 'Não'
        C.grid = form

        if form.process().accepted:
            vals = form.vars
            vals.es_trabajador = False if vals.es_trab == 'Não' else True
            session.wh2db.step = 7
            session.wh2db.estudiante.update(db.estudiante._filter_fields(form.vars))
            C.estudiante.update_record(**session.wh2db.estudiante)
            redirect(proximo)
        return dict(C=C)

    if step == 7:
        if C.estudiante.es_trabajador:
            # --pedir los datos del centro de trabajo
            C.titulo = T("Información laboral 1/2")
            fld_trab_profesion = db.estudiante.get('trab_profesion')
            fld_trab_profesion.requires = [IS_NOT_EMPTY(), IS_UPPER()]
            fld_trab_nombre = db.estudiante.get("trab_nombre")
            fld_trab_nombre.requires = [IS_NOT_EMPTY(), IS_UPPER()]
            fld_trab_provincia = db.estudiante.get("trab_provincia")
            fld_trab_provincia.label = T("Provincia")
            fld_trab_provincia.comment = T('''
                Seleccione la provincia donde se desempeña el trabajo
            ''')
            fld_trab_provincia.requires = IS_IN_DB(db, db.provincia.id,
                                                   "%(nombre)s",
                                                   zero=T("(ESCOGER UNO)"))
            fld_trab_tipo_instituto = db.estudiante.get('trab_tipo_instituto')
            from agiscore.db.estudiante import TRAB_TIPO_INSTITUTO
            fld_trab_tipo_instituto.requires = IS_IN_SET(TRAB_TIPO_INSTITUTO,
                                                         zero=None)
            fld_trab_con_titulo = Field('con_titulo', 'string', length=3,
                                        default='Não')
            fld_trab_con_titulo.label = T("¿Tiene salida con título?")
            fld_trab_con_titulo.requires = IS_IN_SET(['Sim', 'Não'], zero=None)

            form = SQLFORM.factory(fld_trab_profesion,
                                     fld_trab_nombre,
                                     fld_trab_tipo_instituto,
                                     fld_trab_con_titulo,
                                     fld_trab_provincia,
                                     table_name="estudiante",
                                     submit_button=T("Next"))
            form.add_button("Cancel", cancelar)
            form.vars.update(C.estudiante)
            form.vars.con_titulo = 'Sim' if C.estudiante.trab_titulo else 'Não'
            C.grid = form

            if form.process().accepted:
                session.wh2db.estudiante.update(db.estudiante._filter_fields(form.vars))
                C.estudiante.update_record(**session.wh2db.estudiante)
                if form.vars.con_titulo == 'Sim':
                    session.wh2db.step = 8
                else:
                    session.wh2db.step = 9
                redirect(proximo)

            return dict(C=C)
        else:
            # -- sino es trabajador seguir al proximo paso
            session.wh2db.step = 9
            redirect(proximo)

    if step == 8:
        # -- tipo de titulo que da el trabajo
        C.titulo = T("Información laboral 2/2")

        fld_trab_titulo = db.estudiante.get('trab_titulo')
        from agiscore.db.estudiante import TRAB_TITULO_VALUES
        fld_trab_titulo.requires = IS_IN_SET(TRAB_TITULO_VALUES, zero=None)

        form = SQLFORM.factory(fld_trab_titulo,
                               record=C.estudiante,
                               showid=False,
                               table_name="estudiante",
                               submit_button=T("Next"))
        form.add_button("Cancel", cancelar)
        C.grid = form

        if form.process().accepted:
            session.wh2db.step = 9
            session.wh2db.estudiante.update(db.estudiante._filter_fields(form.vars))
            C.estudiante.update_record(**session.wh2db.estudiante)
            redirect(proximo)

        return dict(C=C)

    if step == 9:
        # -- institucionales
        C.titulo = T("Institucionales")

        fld_modalidad = db.estudiante.get("modalidad")
        fld_forma_acceso = db.estudiante.get("forma_acceso")
        fld_ano_ies = db.estudiante.get("ano_ies")
        fld_ano_es = db.estudiante.get("ano_es")
        fld_es_internado = db.estudiante.get("es_internado")
        fld_documentos = db.estudiante.get("documentos")
        fld_discapacidades = db.estudiante.get("discapacidades")
        fld_bolsa_estudio = db.estudiante.get("bolsa_estudio")

        fld_ano_ies.requires = IS_IN_SET(range(1950,
                                               datetime.date.today().year),
                                         zero=None)
        fld_ano_es.requires = IS_IN_SET(range(1950,
                                               datetime.date.today().year),
                                         zero=None)

        form = SQLFORM.factory(fld_modalidad,
                                 fld_forma_acceso,
                                 fld_ano_ies,
                                 fld_ano_es,
                                 fld_es_internado,
                                 fld_documentos,
                                 fld_discapacidades,
                                 fld_bolsa_estudio,
                                 record=C.estudiante,
                                 showid=False,
                                 table_name="estudiante",
                                 submit_button=T("Next"))
        form.add_button("Cancel", cancelar)
        C.grid = form

        if form.process().accepted:
            session.wh2db.step = 10
            session.wh2db.estudiante.update(db.estudiante._filter_fields(form.vars))
            C.estudiante.update_record(**session.wh2db.estudiante)
            redirect(proximo)

        return dict(C=C)
    # ------------------------------------------------- FIN ESTUDIANTE

    # ------------------------------------------------- MATRICULA
    if step == 10:
        C.titulo = T("Matricula 1/5")

        campos = []
        fld_carrera_id = db.matricula.get("carrera_id")
        campos.append(fld_carrera_id)
        fld_regimen = db.matricula.get("regimen_id")
        campos.append(fld_regimen)
        fld_nivel = db.matricula.get("nivel")
        q_nivel = (db.nivel_academico.id > 1)
        q_nivel &= (db.nivel_academico.unidad_organica_id == C.unidad.id)
        from agiscore.db.nivel_academico import nivel_represent
        n_set = [(r.id, nivel_represent(r.nivel, r)) for r in db(q_nivel).select()]
        fld_nivel.requires = IS_IN_SET(n_set, zero=None)
        campos.append(fld_nivel)
        fld_situacion = db.matricula.get("situacion")
        campos.append(fld_situacion)

        form = SQLFORM.factory(*campos,
                               showid=False,
                               record=matricula,
                               table_name="matricula",
                               submit_button=T("Next"))

        form.add_button("Cancel", cancelar)
        C.grid = form

        if form.process().accepted:
            session.wh2db.step = 11
            session.wh2db.matricula.update(db.matricula._filter_fields(form.vars))
            matricula.update_record(**session.wh2db.matricula)
            redirect(proximo)

        return dict(C=C)

    if step == 11:
        C.titulo = T("Matricula 2/5")

        campos = []
        fld_turma = db.matricula.get("turma_id")
        q_turmas  = (db.turma.carrera_id == matricula.carrera_id)
        q_turmas &= (db.turma.regimen_id == matricula.regimen_id)
        q_turmas &= (db.turma.nivel_id == matricula.nivel)
        q_turmas &= (db.turma.unidad_organica_id == C.unidad.id)
        fld_turma.requires = IS_IN_DB(db(q_turmas),
                                      db.turma.id,
                                      "%(nombre)s",
                                      zero=T('(ESCOGER UNO)'))
        campos.append(fld_turma)

        fld_plan_id = db.matricula.get("plan_id")
        q_planes = (db.plan_curricular.carrera_id == matricula.carrera_id)
        fld_plan_id.requires = IS_IN_DB(db(q_planes),
                                        db.plan_curricular.id,
                                        "%(nombre)s",
                                        zero=T('(ESCOGER UNO)'))
        campos.append(fld_plan_id)

        niv = db.nivel_academico(matricula.nivel)
        if niv.nivel >= 3:
            fld_especialidad = db.matricula.get("espacialidad_id")
            q_esp = (db.especialidad.carrera_id == matricula.carrera_id)
            esp_set = [(r.id, r.nombre) for r in db(q_esp).select(db.especialidad.ALL)]
            fld_especialidad.requires = IS_IN_SET(esp_set, zero=T('(ESCOGER UNO)'))
            if esp_set:
                campos.append(fld_especialidad)

        form = SQLFORM.factory(*campos,
                               showid=False,
                               record=matricula,
                               table_name="matricula",
                               submit_button=T("Next"))

        form.add_button("Cancel", cancelar)
        C.grid = form

        if form.process().accepted:
            session.wh2db.step = 12
            session.wh2db.matricula.update(db.matricula._filter_fields(form.vars))
            matricula.update_record(**session.wh2db.matricula)
            redirect(proximo)

        return dict(C=C)

    TERM = ['1', '2', '5', '11', '12']
    if matricula.situacion in TERM:
        step = 20

    if step == 12 and matricula.situacion == '3':
        # seleccionar asignaturas de arrastre
        C.titulo = T("Matricula 3/5 - Arrastre")
        tbl = db.arrastre
        arr = db.arrastre(matricula_id=matricula.id)
        tbl.matricula_id.default = matricula.id
        tbl.matricula_id.writable = False
        tbl.matricula_id.readable = False
        as_query  = (db.asignatura.id == db.asignatura_plan.asignatura_id)
        as_query &= (db.asignatura_plan.plan_curricular_id == db.plan_curricular.id)
        as_query &= (db.asignatura_plan.nivel_academico_id > 1)
        as_query &= (db.asignatura_plan.nivel_academico_id < matricula.nivel)
        as_query &= (db.plan_curricular.id == matricula.plan_id)
        as_query &= (db.plan_curricular.carrera_id == matricula.carrera_id)
        tbl.asignaturas.requires = IS_IN_DB(db(as_query),
                                            db.asignatura.id,
                                            "%(nombre)s",
                                            multiple=(1, 4),
                                            zero=None,
                                            distinct=True)

        if arr is None:
            form = SQLFORM(tbl, submit_button=T("Next"))
        else:
            form = SQLFORM(tbl,
                           record=arr,
                           showid=False,
                           submit_button=T("Next"))
        form.add_button("Cancel", cancelar)
        C.grid = form

        if form.process().accepted:
            session.wh2db.step = 20
            redirect(proximo)

        return dict(C=C)

    if step == 12 and matricula.situacion == '4':
        C.titulo = T("Matricula 3/5 - Repitente")
        tbl = db.repitensia
        arr = db.repitensia(matricula_id=matricula.id)
        tbl.matricula_id.default = matricula.id
        tbl.matricula_id.writable = False
        tbl.matricula_id.readable = False
        r_nivel = matricula.nivel
        as_query  = (db.asignatura.id == db.asignatura_plan.asignatura_id)
        as_query &= (db.asignatura_plan.plan_curricular_id == db.plan_curricular.id)
        as_query &= (db.asignatura_plan.nivel_academico_id == r_nivel)
        as_query &= (db.plan_curricular.id == matricula.plan_id)
        as_query &= (db.plan_curricular.carrera_id == matricula.carrera_id)
        tbl.asignaturas.requires = IS_IN_DB(db(as_query),
                                            db.asignatura.id,
                                            "%(nombre)s",
                                            multiple=(1,
                                                      db(as_query).count() + 1),
                                            zero=None,
                                            distinct=True)

        if arr is None:
            form = SQLFORM(tbl, submit_button=T("Next"))
        else:
            form = SQLFORM(tbl,
                           record=arr,
                           showid=False,
                           submit_button=T("Next"))
        form.add_button("Cancel", cancelar)
        C.grid = form

        if form.process().accepted:
            session.wh2db.step = 13
            redirect(proximo)

        return dict(C=C)

    if step == 13 and matricula.situacion == '4':
        C.titulo = T("Matricula 3/5 - Repitente con arrastre")

        fld_con_arrastre = Field('con_arrastre', 'string', length=3, default='NÃO')
        fld_con_arrastre.label = T("¿Tiene arrastres de cursos anteriores?")
        fld_con_arrastre.requires = IS_IN_SET(['SIM', 'NÃO'], zero=None)

        form = SQLFORM.factory(fld_con_arrastre,
                               table_name="matricula_arr",
                               submit_button=T("Next"))

        form.add_button("Cancel", cancelar)
        C.grid = form

        if form.process().accepted:
            if form.vars.con_arrastre == 'SIM':
                session.wh2db.step = 14
            else:
                session.wh2db.step = 20
            redirect(proximo)

        return dict(C=C)

    if step == 14:
        # seleccionar asignaturas de arrastre
        C.titulo = T("Matricula 3/5 - Repitente con arrastre")
        tbl = db.arrastre
        arr = db.arrastre(matricula_id=matricula.id)
        tbl.matricula_id.default = matricula.id
        tbl.matricula_id.writable = False
        tbl.matricula_id.readable = False
        as_query  = (db.asignatura.id == db.asignatura_plan.asignatura_id)
        as_query &= (db.asignatura_plan.plan_curricular_id == db.plan_curricular.id)
        as_query &= (db.asignatura_plan.nivel_academico_id > 1)
        as_query &= (db.asignatura_plan.nivel_academico_id < matricula.nivel)
        as_query &= (db.plan_curricular.id == matricula.plan_id)
        as_query &= (db.plan_curricular.carrera_id == matricula.carrera_id)
        tbl.asignaturas.requires = IS_IN_DB(db(as_query),
                                            db.asignatura.id,
                                            "%(nombre)s",
                                            multiple=(1, 4),
                                            zero=None,
                                            distinct=True)

        if arr is None:
            form = SQLFORM(tbl, submit_button=T("Next"))
        else:
            form = SQLFORM(tbl,
                           record=arr,
                           showid=False,
                           submit_button=T("Next"))
        form.add_button("Cancel", cancelar)
        C.grid = form

        if form.process().accepted:
            session.wh2db.step = 20
            redirect(proximo)

        return dict(C=C)

    if step == 20:
        # terminar la matricula
        matricula.update_record(estado_uo=MATRICULADO)
        session.wh2db = None
        redirect(back)
    # ------------------------------------------------- FIN MATRICULA
    return dict(C=C)

@auth.requires(auth.has_membership(role=myconf.take('roles.admin')))
def nuevo():
    """Premite registrar un estudiante desde 0, para los casos de traslados
    y que no existian en el sistema antiguo"""
    C = Storage()
    C.evento = db.evento(request.args(0))
    C.ano = db.ano_academico(C.evento.ano_academico_id)
    C.unidad = db.unidad_organica(C.ano.unidad_organica_id)
    C.escuela = db.escuela(C.unidad.escuela_id)

    # breadcumbs
    u_link = Accion(C.unidad.abreviatura or C.unidad.nombre,
                    URL('unidad', 'index', args=[C.unidad.id]),
                    True)  # siempre dentro de esta funcion
    menu_migas.append(u_link)
    a_links = Accion(C.ano.nombre,
                     URL('unidad', 'index', args=[C.unidad.id]),
                     True)
    menu_migas.append(a_links)
    e_link = Accion(C.evento.nombre,
                    URL('index', args=[C.evento.id]),
                    True)
    menu_migas.append(e_link)
    menu_migas.append(T("REGISTRAR ESTUDIANTE"))

    # -- cancelar
    mi_vars = Storage(request.vars)  # make a copy
    mi_vars._nuevo_estudiante = 1
    cancelar = URL(c=request.controller, f=request.function,
                   args=request.args, vars=mi_vars)
    if request.vars._nuevo_estudiante:
        session.sd2hm = None
        redirect(URL('index', args=[C.evento.id]))
    # inicialización del formulario
    if session.sd2hm is None:
        session.sd2hm = Storage(dict(step=0))
        session.sd2hm.estudiante = Storage()
        session.sd2hm.matricula = Storage()
    data = session.sd2hm
    step = session.sd2hm.step

    back = URL('index', args=[C.evento.id])
    proximo = URL(c=request.controller,
               f=request.function,
               args=request.args,
               vars=request.vars)

    # -- recoger los datos personales
    if session.sd2hm.persona is None:
        (C.form_persona, pdata) = form_crear_persona_ex(cancel_url=back,
                                               db=db,
                                               T=T,
                                               session=session,
                                               request=request)
        if pdata is None:
            return dict(C=C)
        session.sd2hm.persona = pdata
        C.form_persona = None

    # ------------------------------------------------- ESTUDIANTE
    if step == 0:
        # -- recoger los datos del estudiante
        fld_habilitacion = db.estudiante.get('pro_habilitacion')
        fld_tipo_escuela = db.estudiante.get('pro_tipo_escuela')
        fld_pro_carrera = db.estudiante.get('pro_carrera')
        fld_pro_carrera.comment = T('''
            Nombre de la carrera que concluyó en la enseñanza previa
        ''')
        fld_pro_ano = db.estudiante.get('pro_ano')
        fld_pro_ano.comment = T('''
            Año en que se gradúo en la enseñanza media
        ''')
        fld_pro_ano.requires = IS_IN_SET(range(1950,
                                               datetime.date.today().year + 1),
                                         zero=None)
        fld_pro_ano.default = datetime.date.today().year - 1
        fld_tipo_escuela.requires = IS_IN_DB(db,
                                             'tipo_escuela_media.id',
                                             "%(nombre)s",
                                             zero=T("(ESCOGER UNO)"))

        form = SQLFORM.factory(fld_habilitacion,
                                 fld_tipo_escuela,
                                 fld_pro_carrera,
                                 fld_pro_ano,
                                 table_name="estudiante",
                                 submit_button=T("Next"))
        form.add_button("Cancel", cancelar)
        C.grid = form
        C.titulo = T("Procedencia 1/2")
        if form.process().accepted:
            session.sd2hm.step = 1
            session.sd2hm.estudiante.update(db.estudiante._filter_fields(form.vars))
            redirect(proximo)

        return dict(C=C)

    if step == 1:
        # --segunda parte de los datos de procedencia
        C.titulo = T("Procedencia 2/2")

        # -- configurar campos
        campos = []
        tipo_escuela_id = data.estudiante.pro_tipo_escuela
        tipo_escuela = db.tipo_escuela_media(tipo_escuela_id)
        if tipo_escuela.uuid != "a57d6b2b-8f0e-4962-a2a6-95f5c82e015d":
            fld_pro_escuela = db.estudiante.get("pro_escuela_id")
            esc_set = (db.escuela_media.id > 0)
            esc_set &= (db.escuela_media.tipo_escuela_media_id == tipo_escuela_id)
            fld_pro_escuela.requires = IS_IN_DB(db(esc_set),
                                                db.escuela_media.id,
                                                '%(nombre)s',
                                                zero=None)
            campos.append(fld_pro_escuela)
        fld_pro_media = db.estudiante.get("pro_media")
        campos.append(fld_pro_media)
        fld_es_trab = Field('es_trab', 'string', length=1, default='Não')
        fld_es_trab.label = T('¿Es trabajador?')
        fld_es_trab.requires = IS_IN_SET(['Sim', 'Não'], zero=None)
        campos.append(fld_es_trab)

        form = SQLFORM.factory(*campos,
                                 table_name="estudiante",
                                 submit_button=T("Next"))
        form.add_button("Cancel", cancelar)
        #form.vars.update(C.estudiante)
        form.vars.es_trab = 'Sim' if data.estudiante.es_trabajador else 'Não'
        C.grid = form

        if form.process().accepted:
            vals = form.vars
            vals.es_trabajador = False if vals.es_trab == 'Não' else True
            session.sd2hm.step = 7
            session.sd2hm.estudiante.update(db.estudiante._filter_fields(form.vars))
            redirect(proximo)
        return dict(C=C)

    if step == 7:
        if data.estudiante.es_trabajador:
            # --pedir los datos del centro de trabajo
            C.titulo = T("Información laboral 1/2")
            fld_trab_profesion = db.estudiante.get('trab_profesion')
            fld_trab_profesion.requires = [IS_NOT_EMPTY(), IS_UPPER()]
            fld_trab_nombre = db.estudiante.get("trab_nombre")
            fld_trab_nombre.requires = [IS_NOT_EMPTY(), IS_UPPER()]
            fld_trab_provincia = db.estudiante.get("trab_provincia")
            fld_trab_provincia.label = T("Provincia")
            fld_trab_provincia.comment = T('''
                Seleccione la provincia donde se desempeña el trabajo
            ''')
            fld_trab_provincia.requires = IS_IN_DB(db, db.provincia.id,
                                                   "%(nombre)s",
                                                   zero=T("(ESCOGER UNO)"))
            fld_trab_tipo_instituto = db.estudiante.get('trab_tipo_instituto')
            from agiscore.db.estudiante import TRAB_TIPO_INSTITUTO
            fld_trab_tipo_instituto.requires = IS_IN_SET(TRAB_TIPO_INSTITUTO,
                                                         zero=None)
            fld_trab_con_titulo = Field('con_titulo', 'string', length=3,
                                        default='Não')
            fld_trab_con_titulo.label = T("¿Tiene salida con título?")
            fld_trab_con_titulo.requires = IS_IN_SET(['Sim', 'Não'], zero=None)

            form = SQLFORM.factory(fld_trab_profesion,
                                     fld_trab_nombre,
                                     fld_trab_tipo_instituto,
                                     fld_trab_con_titulo,
                                     fld_trab_provincia,
                                     table_name="estudiante",
                                     submit_button=T("Next"))
            form.add_button("Cancel", cancelar)
            # form.vars.update(C.estudiante)
            form.vars.con_titulo = 'Sim' if data.estudiante.trab_titulo else 'Não'
            C.grid = form

            if form.process().accepted:
                session.sd2hm.estudiante.update(db.estudiante._filter_fields(form.vars))
                if form.vars.con_titulo == 'Sim':
                    session.sd2hm.step = 8
                else:
                    session.sd2hm.step = 9
                redirect(proximo)

            return dict(C=C)
        else:
            # -- sino es trabajador seguir al proximo paso
            session.sd2hm.step = 9
            redirect(proximo)

    if step == 8:
        # -- tipo de titulo que da el trabajo
        C.titulo = T("Información laboral 2/2")

        fld_trab_titulo = db.estudiante.get('trab_titulo')
        from agiscore.db.estudiante import TRAB_TITULO_VALUES
        fld_trab_titulo.requires = IS_IN_SET(TRAB_TITULO_VALUES, zero=None)

        form = SQLFORM.factory(fld_trab_titulo,
                               table_name="estudiante",
                               submit_button=T("Next"))
        form.add_button("Cancel", cancelar)
        C.grid = form

        if form.process().accepted:
            session.sd2hm.step = 9
            session.sd2hm.estudiante.update(db.estudiante._filter_fields(form.vars))
            redirect(proximo)

        return dict(C=C)

    if step == 9:
        # -- institucionales
        C.titulo = T("Institucionales")

        fld_modalidad = db.estudiante.get("modalidad")
        fld_forma_acceso = db.estudiante.get("forma_acceso")
        fld_ano_ies = db.estudiante.get("ano_ies")
        fld_ano_es = db.estudiante.get("ano_es")
        fld_es_internado = db.estudiante.get("es_internado")
        fld_documentos = db.estudiante.get("documentos")
        fld_discapacidades = db.estudiante.get("discapacidades")
        fld_bolsa_estudio = db.estudiante.get("bolsa_estudio")

        fld_ano_ies.requires = IS_IN_SET(range(1950,
                                               datetime.date.today().year),
                                         zero=None)
        fld_ano_es.requires = IS_IN_SET(range(1950,
                                               datetime.date.today().year),
                                         zero=None)

        form = SQLFORM.factory(fld_modalidad,
                                 fld_forma_acceso,
                                 fld_ano_ies,
                                 fld_ano_es,
                                 fld_es_internado,
                                 fld_documentos,
                                 fld_discapacidades,
                                 fld_bolsa_estudio,
                                 table_name="estudiante",
                                 submit_button=T("Next"))
        form.add_button("Cancel", cancelar)
        C.grid = form

        if form.process().accepted:
            session.sd2hm.step = 10
            session.sd2hm.estudiante.update(db.estudiante._filter_fields(form.vars))
            redirect(proximo)

        return dict(C=C)

    # ------------------------------------------------- FIN ESTUDIANTE

    # ------------------------------------------------- MATRICULA
    if step == 10:
        C.titulo = T("Matricula 1/5")

        campos = []
        fld_carrera_id = db.matricula.get("carrera_id")
        campos.append(fld_carrera_id)
        fld_regimen = db.matricula.get("regimen_id")
        campos.append(fld_regimen)
        fld_nivel = db.matricula.get("nivel")
        q_nivel = (db.nivel_academico.id > 1)
        q_nivel &= (db.nivel_academico.unidad_organica_id == C.unidad.id)
        from agiscore.db.nivel_academico import nivel_represent
        n_set = [(r.id, nivel_represent(r.nivel, r)) for r in db(q_nivel).select()]
        fld_nivel.requires = IS_IN_SET(n_set, zero=None)
        campos.append(fld_nivel)
        fld_situacion = db.matricula.get("situacion")
        campos.append(fld_situacion)

        form = SQLFORM.factory(*campos,
                               table_name="matricula",
                               submit_button=T("Next"))

        form.add_button("Cancel", cancelar)
        C.grid = form

        if form.process().accepted:
            session.sd2hm.step = 11
            session.sd2hm.matricula.update(db.matricula._filter_fields(form.vars))
            redirect(proximo)

        return dict(C=C)

    if step == 11:
        C.titulo = T("Matricula 2/5")

        campos = []
        fld_turma = db.matricula.get("turma_id")
        q_turmas  = (db.turma.carrera_id == data.matricula.carrera_id)
        q_turmas &= (db.turma.regimen_id == data.matricula.regimen_id)
        q_turmas &= (db.turma.nivel_id == data.matricula.nivel)
        q_turmas &= (db.turma.unidad_organica_id == C.unidad.id)
        fld_turma.requires = IS_IN_DB(db(q_turmas),
                                      db.turma.id,
                                      "%(nombre)s",
                                      zero=T('(ESCOGER UNO)'))
        campos.append(fld_turma)

        fld_plan_id = db.matricula.get("plan_id")
        q_planes = (db.plan_curricular.carrera_id == data.matricula.carrera_id)
        fld_plan_id.requires = IS_IN_DB(db(q_planes),
                                        db.plan_curricular.id,
                                        "%(nombre)s",
                                        zero=T('(ESCOGER UNO)'))
        campos.append(fld_plan_id)

        niv = db.nivel_academico(data.matricula.nivel)
        if niv.nivel >= 3:
            fld_especialidad = db.matricula.get("espacialidad_id")
            q_esp = (db.especialidad.carrera_id == data.matricula.carrera_id)
            esp_set = [(r.id, r.nombre) for r in db(q_esp).select(db.especialidad.ALL)]
            fld_especialidad.requires = IS_IN_SET(esp_set, zero=T('(ESCOGER UNO)'))
            if esp_set:
                campos.append(fld_especialidad)

        form = SQLFORM.factory(*campos,
                               table_name="matricula",
                               submit_button=T("Next"))

        form.add_button("Cancel", cancelar)
        C.grid = form

        if form.process().accepted:
            session.sd2hm.step = 12
            session.sd2hm.matricula.update(db.matricula._filter_fields(form.vars))
            redirect(proximo)

        return dict(C=C)

    TERM = ['1', '2', '5', '11', '12']
    if data.matricula.situacion in TERM:
        step = 20

    if step == 12 and data.matricula.situacion == '3':
        # seleccionar asignaturas de arrastre
        C.titulo = T("Matricula 3/5 - Arrastre")
        session.sd2hm.arrastre = Storage()
        fld_asignaturas = db.arrastre.get("asignaturas")
        as_query  = (db.asignatura.id == db.asignatura_plan.asignatura_id)
        as_query &= (db.asignatura_plan.plan_curricular_id == db.plan_curricular.id)
        as_query &= (db.asignatura_plan.nivel_academico_id > 1)
        as_query &= (db.asignatura_plan.nivel_academico_id < data.matricula.nivel)
        as_query &= (db.plan_curricular.id == data.matricula.plan_id)
        as_query &= (db.plan_curricular.carrera_id == data.matricula.carrera_id)
        fld_asignaturas.requires = IS_IN_DB(db(as_query),
                                            db.asignatura.id,
                                            "%(nombre)s",
                                            multiple=(1, 4),
                                            zero=None,
                                            distinct=True)

        form = SQLFORM.factory(fld_asignaturas,
                               table_name="arrastre",
                               submit_button=T("Next"))

        form.add_button("Cancel", cancelar)
        C.grid = form

        if form.process().accepted:
            session.sd2hm.arrastre.update(db.arrastre._filter_fields(form.vars))
            session.sd2hm.step = 20
            redirect(proximo)

        return dict(C=C)

    if step == 12 and data.matricula.situacion == '4':
        C.titulo = T("Matricula 3/5 - Repitente")
        session.sd2hm.repitensia = Storage()

        fld_asignaturas = db.repitensia.get("asignaturas")
        r_nivel = data.matricula.nivel
        as_query  = (db.asignatura.id == db.asignatura_plan.asignatura_id)
        as_query &= (db.asignatura_plan.plan_curricular_id == db.plan_curricular.id)
        as_query &= (db.asignatura_plan.nivel_academico_id == r_nivel)
        as_query &= (db.plan_curricular.id == data.matricula.plan_id)
        as_query &= (db.plan_curricular.carrera_id == data.matricula.carrera_id)
        fld_asignaturas.requires = IS_IN_DB(db(as_query),
                                            db.asignatura.id,
                                            "%(nombre)s",
                                            multiple=(1,
                                                      db(as_query).count() + 1),
                                            zero=None,
                                            distinct=True)

        form = SQLFORM.factory(fld_asignaturas,
                               table_name="repitensia",
                               submit_button=T("Next"))
        form.add_button("Cancel", cancelar)
        C.grid = form

        if form.process().accepted:
            session.sd2hm.repitensia.update(db.repitensia._filter_fields(form.vars))
            session.sd2hm.step = 13
            redirect(proximo)

        return dict(C=C)

    if step == 13 and data.matricula.situacion == '4':
        C.titulo = T("Matricula 3/5 - Repitente con arrastre")

        fld_con_arrastre = Field('con_arrastre', 'string', length=3, default='NÃO')
        fld_con_arrastre.label = T("¿Tiene arrastres de cursos anteriores?")
        fld_con_arrastre.requires = IS_IN_SET(['SIM', 'NÃO'], zero=None)

        form = SQLFORM.factory(fld_con_arrastre,
                               table_name="matricula_arr",
                               submit_button=T("Next"))

        form.add_button("Cancel", cancelar)
        C.grid = form

        if form.process().accepted:
            if form.vars.con_arrastre == 'SIM':
                session.sd2hm.step = 14
            else:
                session.sd2hm.step = 20
            redirect(proximo)

        return dict(C=C)

    if step == 14:
        # seleccionar asignaturas de arrastre
        C.titulo = T("Matricula 3/5 - Repitente con arrastre")
        session.sd2hm.arrastre = Storage()
        fld_asignaturas = db.arrastre.get("asignaturas")
        as_query  = (db.asignatura.id == db.asignatura_plan.asignatura_id)
        as_query &= (db.asignatura_plan.plan_curricular_id == db.plan_curricular.id)
        as_query &= (db.asignatura_plan.nivel_academico_id > 1)
        as_query &= (db.asignatura_plan.nivel_academico_id < data.matricula.nivel)
        as_query &= (db.plan_curricular.id == data.matricula.plan_id)
        as_query &= (db.plan_curricular.carrera_id == data.matricula.carrera_id)
        fld_asignaturas.requires = IS_IN_DB(db(as_query),
                                            db.asignatura.id,
                                            "%(nombre)s",
                                            multiple=(1, 4),
                                            zero=None,
                                            distinct=True)

        form = SQLFORM.factory(fld_asignaturas,
                               table_name="arrastre",
                               submit_button=T("Next"))

        form.add_button("Cancel", cancelar)
        C.grid = form

        if form.process().accepted:
            session.sd2hm.arrastre.update(db.arrastre._filter_fields(form.vars))
            session.sd2hm.step = 20
            redirect(proximo)

        return dict(C=C)

    if step == 20:
        # terminar el registro de nuevo estudiante
        #matricula.update_record(estado_uo=MATRICULADO)
        persona_id = db.persona.insert(**db.persona._filter_fields(data.persona))
        data.estudiante.update(persona_id=persona_id)
        data.estudiante.update(unidad_organica_id=C.unidad.id)
        # para el número mecanografico
        no_meca = ""
        no_meca += C.unidad.codigo_escuela
        c_e = db.carrera_escuela(db.carrera_uo(data.matricula.carrera_id).carrera_escuela_id)
        no_meca += c_e.codigo
        no_meca += C.ano.nombre[2:]
        no_meca += "1" if data.persona.genero == "M" else "2"
        query = (db.estudiante.id == db.matricula.estudiante_id)
        query &= (db.matricula.carrera_id == data.matricula.carrera_id)
        query &= (db.estudiante.unidad_organica_id == C.unidad.id)
        query &= (db.matricula.ano_academico_id == C.ano.id)
        query &= (db.matricula.estado_uo == MATRICULADO)
        ultimo = db(query).select(db.estudiante.codigo, orderby=~db.estudiante.codigo).first()
        if ultimo is None:
            no_meca += "00001"
        else:
            ultimo = ultimo.codigo[-5:]
            ultimo = int(ultimo) + 1
            no_meca += str(ultimo).zfill(5)
        data.estudiante.update(codigo=no_meca)
        estudiante_id = db.estudiante.insert(**db.estudiante._filter_fields(data.estudiante))
        data.matricula.update(estado_uo=SIN_MATRICULAR_CON_DEUDA,
                              estudiante_id=estudiante_id,
                              ano_academico_id=C.ano.id)
        matricula_id = db.matricula.insert(**db.matricula._filter_fields(data.matricula))
        if data.arrastre is not None:
            data.arrastre.update(matricula_id=matricula_id)
            db.arrastre.insert(**db.arrastre._filter_fields(data.arrastre))
        if data.repitensia is not None:
            data.repitensia.update(matricula_id=matricula_id)
            db.repitensia.insert(**db.repitensia._filter_fields(data.repitensia))
        session.sd2hm = None
        redirect(back)
    # ------------------------------------------------- FIN MATRICULA

    return dict(C=C)
