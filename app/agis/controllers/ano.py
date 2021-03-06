# -*- coding: utf-8 -*-
from agiscore.gui.mic import Accion

def index():
    return dict()

@auth.requires_login()
def show():
    """Muestra eventos del año académico"""
    ano = db.ano_academico(request.args(0))
    query = (db.evento.id > 0)
    query &= (db.evento.ano_academico_id == ano.id)
    eventos = db(query).select(orderby=db.evento.fecha_fin)
    edit_link = Accion(SPAN(_class="glyphicon glyphicon-cog"),
        URL('edit', args=request.args),
        auth.has_membership(role=myconf.take('roles.admin')),
        cid="ano{}".format(ano.id),
        _class="btn btn-default btn-xs",
        _title=T("Configuración"))
    return dict(ano=ano, eventos=eventos, edit_link=edit_link)

@auth.requires(auth.has_membership(role=myconf.take('roles.admin')))
def edit():
    ano = db.ano_academico(request.args(0))
    assert ano is not None
    for f in db.ano_academico:
        f.writable = False
    fld_meses = db.ano_academico.meses
    fld_meses.requires = IS_IN_SET(
        [1,2,3,4,5,6,7,8,9,10,11,12], multiple=True
        )
    fld_meses.writable = True
    fld_dia_limite = db.ano_academico.dia_limite
    fld_dia_limite.writable = True
    fld_multa = db.ano_academico.multa
    fld_multa.writable = True

    form = SQLFORM.factory(
        fld_meses,
        fld_multa,
        fld_dia_limite,
        submit_button=T('Guardar'),
        table_name="ano_academico"
        )
    meses = list() if ano.meses is None else ano.meses
    # if meses is None:
    #     meses = list()

    if form.process().accepted:
        ano.update_record(meses=form.vars.meses,
            dia_limite=form.vars.dia_limite,
            multa=form.vars.multa)
        cid = "ano{}".format(ano.id)
        response.js =  "jQuery('#{0}').get(0).reload();".format(cid)
        response.flash = T("Configuración guardada")
    return dict(form=form, meses=meses, ano=ano)
