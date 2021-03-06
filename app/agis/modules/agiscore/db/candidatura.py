#!/usr/bin/env python
# -*- coding: utf-8 -*-
from gluon import *
from agiscore.db import estudiante
from agiscore.db import tipos_ensennanza
from agiscore.db import escuela_media
# from agiscore.tools import requerido
from agiscore.db import unidad_organica
from agiscore.db import discapacidad
from agiscore.db import regimen
from agiscore.db import regimen_uo
from agiscore.db import ano_academico
# from agiscore.db import escuela
from agiscore.db import evento
# from agiscore.db import provincia
from agiscore import tools
from datetime import datetime

class ResultadosHistoricosXLS(tools.ExporterXLS):
    
    file_name = "Resultados Históricos"

    def __init__(self, *args, **kwargs):
        super(ResultadosHistoricosXLS, self).__init__(*args, **kwargs)

    def export(self):
        db = self.rows.db
        T = current.T
        request = current.request
        response = current.response
        wb = self.workbook
        hoja = self.workbook.add_worksheet()
        
        records = self.represented()
        _can = db.candidatura(records[0][0])
        _aa = db.ano_academico(_can.ano_academico_id)
        _uo = db.unidad_organica(_can.unidad_organica_id)
        _esc = db.escuela(_uo.escuela_id)
        _car = db.carrera_uo(int(request.vars.carrera_id))
        _des = db.descripcion_carrera(_car.descripcion_id)
        hoja.merge_range('A1:D1', _esc.nombre.decode('utf-8'),
                         wb.add_format({'bold': True}))
        hoja.merge_range('A2:D2', _uo.nombre.decode('utf-8'),
                         wb.add_format({'bold': True}))
        hoja.merge_range('A4:D4',
                         T("Resultados hitóricos inscripción").decode('utf-8'),
                         wb.add_format({'align': 'center'}))
        hoja.merge_range('A5:D5', _des.nombre.decode('utf-8'),
                         wb.add_format({'align': 'center'}))
        texto = "Año Académico: {}".format(_aa.nombre)
        hoja.merge_range('A6:D6', T(texto).decode('utf-8'),
                         wb.add_format({'align': 'center'}))
        hoja.write('A8', '#', wb.add_format({'bold': True, 'align': 'right'}))
        hoja.set_column('B:B', 30)
        hoja.write('B8', T("Nombre").decode("utf-8"),
                   wb.add_format({'bold': True, 'align': 'left'}))
        hoja.set_column('C:C', 15)
        hoja.write('C8', T("Media").decode('utf-8'),
                   wb.add_format({'bold': True, 'align': 'right'}))
        format1 = wb.add_format()
        format1.set_num_format("0.00")
        for fila, r in enumerate(records):
            hoja.write(fila + 8, 0, r[1], wb.add_format({'align': 'right'}))
            hoja.write(fila + 8, 1, r[2], wb.add_format({'align': 'left'}))
            hoja.write(fila + 8, 2, r[3], format1)
        self.workbook.close()
        return self.output.getvalue()
    

class EAEXLS(tools.ExporterXLS):
    """Export a exel el listado generado por estudiantes_examinar"""
    file_name = 'estudiantes_examinar_por_aula'

    def __init__(self, rows):
        super(EAEXLS, self).__init__(rows)

    def export(self):
        T = current.T
        request = current.request
        response = current.response
        escuela = response.context['escuela']
        unidad_organica = response.context['unidad_organica']
        ano_academico = response.context['ano_academico']
        ex = response.context['examen']
        db = current.db
        hoja = self.workbook.add_worksheet()
        neg = self.workbook.add_format({'bold': True})
        cod_format = self.workbook.add_format({'num_format': '#####'})
        hoja.set_column(0, 0, 15)  # cambiar el ancho
        hoja.set_column(1, 1, 30)
        hoja.set_column(2, 2, 8)
        if escuela.logo:
            (filename, stream) = db.escuela.logo.retrieve(escuela.logo)
            hoja.insert_image('A1', stream.name)
        hoja.merge_range('B1:E1', '')  # para la escuela
        hoja.merge_range('B2:E2', '')  # la la UO
        # año académico
        hoja.merge_range('B4:D4',
            T("Año académico").decode('utf-8') + ': ' + 
            ano_academico.nombre.decode('utf-8')
            )
        hoja.merge_range('B5:D5',
            # nombre de la asignatura
            T('Asignatura').decode('utf-8') + ': ' + 
            db.asignatura(ex.asignatura_id).nombre.decode('utf-8'),
        )
        hoja.merge_range('B6:D6',
           T("Fecha").decode('utf-8') + ': ' + 
           str(ex.fecha)
        )
        from agiscore.db import examen
        hoja.merge_range('B7:D7',
            T('Periódo').decode('utf-8') + ': ' + 
            ("{0}-{1}".format(ex.inicio.strftime("%H:%M"), ex.fin.strftime("%H:%M"))).decode('utf8')
        )
        hoja.write('B1',
                   response.context['escuela'].nombre.decode('utf-8'),
                   neg)
        hoja.write('B2',
                   response.context['unidad_organica'].nombre.decode('utf-8'),
                   neg)
        h1 = T(u'# Inscripción').decode('utf-8')
        h2 = T(u'Nombre').decode('utf-8')
        h3 = T(u'Aula').decode('utf-8')
        hoja.write(9, 0, h1, neg)
        hoja.write(9, 1, h2, neg)
        hoja.write(9, 2, h3, neg)
        records = self.represented()
        for num, item in enumerate(records):
            hoja.write(num + 10, 0, item[0].decode('utf8'), cod_format)
            hoja.write(num + 10, 1, item[1].decode('utf8'))
            hoja.write(num + 10, 2, item[2].decode('utf8'))
        self.workbook.close()
        return self.output.getvalue()

class ResultadosPorCarreraXLS(tools.ExporterXLS):
    """Exporta a XLS el reporte de resultados por carrera"""
    file_name = 'resultados_por_carrera'

    def __init__(self, rows):
        super(ResultadosPorCarreraXLS, self).__init__(rows)

    def export(self):
        db = current.db
        T = current.T
        request = current.request
        response = current.response
        c = response.context
        unidad_organica = c.unidad
        escuela = c.escuela
        ano_academico = c.ano
        carrera = c.carrera
        hoja = self.workbook.add_worksheet()
        neg = self.workbook.add_format({'bold': True})
        cod_format = self.workbook.add_format({'num_format': '00000'})
        md_format = self.workbook.add_format({'num_format': '00.00'})
        n_format = self.workbook.add_format({'num_format': '00'})
        hoja.set_column(0, 0, 15)  # cambiar el ancho
        hoja.set_column(1, 1, 30)
        hoja.set_column(2, 2, 8)
        hoja.merge_range('A1:E1', '')  # para la escuela
        hoja.merge_range('A2:E2', '')  # la la UO
        # año académico
        hoja.merge_range('A4:D4',
            T("Año académico").decode('utf-8') + ': ' + 
            ano_academico.nombre.decode('utf-8')
            )
        from agiscore.db.carrera_uo import carrera_uo_format
        n_carrera = T("Resultados para %s", carrera_uo_format(carrera)).decode('utf-8')
        hoja.merge_range('A5:J5',
            # # nombre de la carrera
            n_carrera,
        )
        hoja.write('A1',
                   escuela.nombre.decode('utf-8'),
                   neg)
        hoja.write('A2',
                   unidad_organica.nombre.decode('utf-8'),
                   neg)
        h1 = T(u'# Ins.').decode('utf-8')
        h2 = T(u'Nombre').decode('utf-8')
        h25 = T(u'R').decode('utf-8')
        h3 = T(u'N.F').decode('utf8')
        h4 = T(u'Estado').decode('utf8')
        hoja.write(9, 0, h1, neg)
        hoja.write(9, 1, h2, neg)
        hoja.write(9, 2, h25, neg)
        asig_set = c.asignaturas
        for col, a_id in enumerate(asig_set):
            hoja.write(9, col + 3,
                       db.asignatura(a_id.asignatura_id).abreviatura.decode('utf8'),
                       neg)
        hoja.write(9, len(asig_set) + 3, h3, neg)
        hoja.write(9, len(asig_set) + 4, h4, neg)
        hoja.set_column(9, len(asig_set) + 5, 15)
        from agiscore.db.nota import nota_format
        for num, item in enumerate(self.rows):
            hoja.write(num + 10, 0, item.ninscripcion, cod_format)
            hoja.write(num + 10, 1, item.nombre.decode('utf8'))
            hoja.write(num + 10, 2, item.regimen.decode('utf8'))
            for col, n in enumerate(item.notas):
                hoja.write(num + 10, col + 3, n, n_format)
            hoja.write(num + 10, len(item.notas) + 3, item.media, md_format)
            hoja.write(num + 10, len(item.notas) + 4, item.estado.decode('utf8'))
        self.workbook.close()
        return self.output.getvalue()

class PNXLS(tools.ExporterXLS):
    """Export a exel el listado generado por estudiantes_examinar"""
    file_name = 'publicacion_notas'

    def __init__(self, rows):
        super(PNXLS, self).__init__(rows)

    def export(self):
        T = current.T
        request = current.request
        response = current.response
        escuela = response.context['escuela']
        unidad_organica = response.context['unidad_organica']
        ano_academico = response.context['ano_academico']
        ex = response.context['examen']
        db = current.db
        hoja = self.workbook.add_worksheet()
        neg = self.workbook.add_format({'bold': True})
        cod_format = self.workbook.add_format({'num_format': '#####'})
        hoja.set_column(0, 0, 15)  # cambiar el ancho
        hoja.set_column(1, 1, 30)
        hoja.set_column(2, 2, 8)
        if escuela.logo:
            (filename, stream) = db.escuela.logo.retrieve(escuela.logo)
            hoja.insert_image('A1', stream.name)
        hoja.merge_range('B1:E1', '')  # para la escuela
        hoja.merge_range('B2:E2', '')  # la la UO
        # año académico
        hoja.merge_range('B4:D4',
            T("Año académico").decode('utf-8') + ': ' + 
            ano_academico.nombre.decode('utf-8')
            )
        hoja.merge_range('B5:D5',
            # nombre de la asignatura
            T('Asignatura').decode('utf-8') + ': ' + 
            db.asignatura(ex.asignatura_id).nombre.decode('utf-8'),
        )
        hoja.merge_range('B6:D6',
           T("Fecha").decode('utf-8') + ': ' + 
           str(ex.fecha)
        )
        from agiscore.db import examen
#         hoja.merge_range('B7:D7',
#             T('Periódo').decode('utf-8') + ': ' +
#             (examen.examen_periodo_represent(
#                 ex.periodo, None
#             )).decode('utf8')
#         )
        hoja.write('B1',
                   response.context['escuela'].nombre.decode('utf-8'),
                   neg)
        hoja.write('B2',
                   response.context['unidad_organica'].nombre.decode('utf-8'),
                   neg)
        h1 = T(u'# Inscripción').decode('utf-8')
        h2 = T(u'Nombre').decode('utf-8')
        h3 = T(u'Nota').decode('utf-8')
        hoja.write(9, 0, h1, neg)
        hoja.write(9, 1, h2, neg)
        hoja.write(9, 2, h3, neg)
        records = self.represented()
        for num, item in enumerate(records):
            hoja.write(num + 10, 0, item[0].decode('utf8'), cod_format)
            hoja.write(num + 10, 1, item[1].decode('utf8'))
            hoja.write(num + 10, 2, item[2])
        self.workbook.close()
        return self.output.getvalue()

CANDIDATURA_ESTADO = {
    '1':'INSCRITO COM DÍVIDAS',
    '2':'INSCRITO',
    '3':'NÃO ADMITIDO',
    '4':'ADMITIDO',
}
INSCRITO_CON_DEUDAS = '1'
INSCRITO = '2'
NO_ADMITIDO = '3'
ADMITIDO = '4'
def candidatura_estado_represent(valor, fila):
    T = current.T
    if valor:
        return T(CANDIDATURA_ESTADO[ valor ])
    else:
        return ''

def contar_candidatos(ano_academico_id=None, condicion=None):
    db = current.db
    definir_tabla()
    query = (db.candidatura.id > 0)
    if condicion:
        query &= condicion
    if ano_academico_id is None:
        # usar año académico actual
        hoy = datetime.today()
        hoy = str(hoy.year)
        a_a = db.ano_academico(nombre=hoy)
        ano_academico_id = a_a.id
    query &= (db.candidatura.ano_academico_id == ano_academico_id)
    return db(query).count()

def obtener_persona(candidatura_id):
    """Dado el ID de una candidatura retorna la persona asociadad a esta"""
    db = current.db
    definir_tabla()
    cand = db.candidatura[candidatura_id]
    return estudiante.obtener_persona(cand.estudiante_id)

def obtener_candidatura_por_persona(persona_id):
    """Retorna"""
    db = current.db
    definir_tabla()
    est = estudiante.obtener_por_persona(persona_id)
    if not est:
        return None
    return est.candidatura.select().first()

def inscribir(persona_id, evento_id):
    """Cambia el estado de la candidatua para la persona con ID persona_id"""
    db = current.db
    ev = db.evento(evento_id)
    # buscar todos los candidatos inscritos para este año academico y ordenarlos de forma desendente.
    aa = db.ano_academico(ev.ano_academico_id)
    query = ((db.candidatura.ano_academico_id == aa.id) &
             (db.candidatura.estado_candidatura != INSCRITO_CON_DEUDAS))
    ultimo = db(query).select(orderby=db.candidatura.numero_inscripcion).last()
    if ultimo:
        numero = int(ultimo.numero_inscripcion)
    else:
        numero = 0
    numero += 1
    est = db(db.estudiante.persona_id == persona_id).select().first()
    can = db(db.candidatura.estudiante_id == est.id).select().first()
    db(db.candidatura.id == can.id).update(numero_inscripcion=str(numero).zfill(4))
    cambiar_estado(INSCRITO, can.id)

def cambiar_estado(valor, can_id):
    db = current.db
    if valor in CANDIDATURA_ESTADO.keys():
        db(db.candidatura.id == can_id).update(estado_candidatura=valor)

def obtener_selector_estado(estado='1', link_generator=[]):
    """ Retornar un grid donde se puede seleccionar un candidato
    """
    db = current.db
    db.persona.id.readable = False
    return obtener_manejo(
        estado=estado,
        campos=[db.persona.numero_identidad,
                db.persona.nombre,
                db.persona.apellido1,
                db.persona.apellido2,
                db.persona.id, ],
        buscar=True,
        enlaces=link_generator
        )

def obtener_por(filtro):
    """retorna todas las candidaturas que cumplan con el filtro dado"""
    db = current.db
    definir_tabla()
    return db(filtro).select(db.candidatura.ALL)

def obtener_manejo(estado=None,
        campos=None,
        buscar=False,
        editar=False,
        crear=False,
        borrar=False,
        exportar=False,
        exportadores={},
        enlaces=[],
        cabeceras={},
        ):
    db = current.db
    if not campos:
        campos = [db.persona.nombre_completo,
                db.candidatura.estado_candidatura,
                db.candidatura.id,
                db.persona.id]
    query = ((db.persona.id == db.estudiante.persona_id) & 
             (db.candidatura.estudiante_id == db.estudiante.id))
    if estado:
        query &= (db.candidatura.estado_candidatura == estado)
    db.candidatura.id.readable = False
    db.persona.id.readable = False
    manejo = SQLFORM.grid(query=query,
        fields=campos,
        orderby=[db.persona.nombre_completo],
        details=False,
        csv=exportar,
        searchable=buscar,
        deletable=borrar,
        editable=editar,
        headers=cabeceras,
        create=crear,
        showbuttontext=False,
        maxtextlength=100,
        exportclasses=exportadores,
        # formstyle='bootstrap',
        links=enlaces,
    )
    return manejo

def numero_inscripcion_represent(valor, fila):
    T = current.T
    if not valor:
        return T('N/A')

    return valor

def candidatura_format(registro):
    db = current.db
    definir_tabla()
    est = db.estudiante[registro.estudiante_id]
    return estudiante.estudiante_format(est)

def obtener_evento(cand):
    """Dada una candidatura retorna el evento de tipo inscripción que corresponde"""
    db = current.db
    definir_tabla()
    evento.definir_tabla()
    # asumiendo que por año académico solo exista un evento de tipo inscripción
    e = db((db.evento.tipo == '1') & 
           (db.evento.ano_academico_id == cand.ano_academico_id) & 
           (db.evento.estado == True)
          ).select(db.evento.id).first()
    return e

def copia_uuid_callback(valores):
    """Se llama antes de insertar un valor en la tabla

    En este caso lo estamos usando para copiar el UUID de la persona
    """
    db = current.db
    e = db.estudiante(valores['estudiante_id'])
    valores['uuid'] = e.uuid

def definir_tabla():
    db = current.db
    T = current.T
    estudiante.definir_tabla()
    tipos_ensennanza.definir_tabla()
    escuela_media.definir_tabla()
    unidad_organica.definir_tabla()
    discapacidad.definir_tabla()
    regimen.definir_tabla()
    regimen_uo.definir_tabla()
    ano_academico.definir_tabla()
    if not hasattr(db, 'candidatura'):
        tbl = db.define_table('candidatura',
            Field('estudiante_id', 'reference estudiante'),
            Field('regimen_id', 'reference regimen_unidad_organica'),
            Field('ano_academico_id', 'reference ano_academico'),
            Field('estado_candidatura', 'string', length=1, default='1'),
            Field('numero_inscripcion', 'string', length=4, default=None),
            db.my_signature,
            format=candidatura_format,
            )
        tbl._before_insert.append(copia_uuid_callback)
        tbl.numero_inscripcion.label = T('Número de inscripción')
        tbl.numero_inscripcion.writable = False
        tbl.numero_inscripcion.represent = numero_inscripcion_represent
        tbl.estado_candidatura.writable = False
        tbl.estado_candidatura.label = T('Estado')
        tbl.estado_candidatura.represent = candidatura_estado_represent
        tbl.estado_candidatura.requires = IS_IN_SET(CANDIDATURA_ESTADO, zero=None)
        tbl.estudiante_id.label = T('Estudiante')
        tbl.regimen_id.label = T('Régimen')
        tbl.ano_academico_id.label = T('Año académico')
