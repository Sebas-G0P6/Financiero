import logging
import random
from datetime import datetime

import pytz

from odoo import api, fields, models
from odoo.exceptions import ValidationError
from odoo.tools.misc import file_path

_logger = logging.getLogger(__name__)


class FenalcoReportesInterfazUnoe(models.Model):
    _name = 'fenalco.reportes.interfaz.unoe'
    _description = 'fenalco.reportes.interfaz.unoe'

    def _default_fecha(self, option):
        _hora = '23:59:59'
        if option == 'HORA_INICIO':
            _hora = '00:00:00'

        _tz_user = pytz.timezone(self.env.user.tz or pytz.utc)
        _datetime_user = datetime.now(_tz_user)
        _fecha_hora_inicio = datetime.strptime(_datetime_user.strftime("%Y-%m-%d " + _hora), "%Y-%m-%d %H:%M:%S")
        _fecha_hora_inicio_zone_user = _tz_user.localize(_fecha_hora_inicio)
        _fecha_hora_inicio_zone_utc = _fecha_hora_inicio_zone_user.astimezone(pytz.UTC)

        return _fecha_hora_inicio_zone_utc.strftime("%Y-%m-%d %H:%M:%S")

    company_id = fields.Many2one('res.company', 'Company', default=lambda self: self.env.user.company_id.id, index=1)
    currency_id = fields.Many2one('res.currency', 'Currency', default=lambda self: self.env.user.company_id.currency_id.id, required=True)
    active = fields.Boolean(default=True)

    _fv_fecha_inicio = fields.Datetime('Fecha de inicio', default=lambda self: self._default_fecha('HORA_INICIO'))
    _fv_fecha_fin = fields.Datetime('Fecha de fin', default=lambda self: self._default_fecha('HORA_FIN'))

    _total_recaudo = fields.Float(tracking=True, digits=(25, 0), required=False, string='Total Pagos', help='')
    _total_recaudo_caja = fields.Float(tracking=True, digits=(25, 0), required=False, string='Pagos de Caja', help='')
    _total_recaudo_cobranzas = fields.Float(tracking=True, digits=(25, 0), required=False, string='Pagos de Cobranzas', help='')
    _total_recaudo_manuales_open = fields.Float(tracking=True, digits=(25, 0), required=False, string='Pagos Manuales de Open', help='')
    _number_related_info = fields.Float(tracking=True, digits=(25, 0), required=False, string='Numero Relacion', help='')

    _fv_fecha_ultimo_pago_aplicado = fields.Datetime(string='Ultimo Pago', tracking=True, required=False, help='')

    def ver_reporte_caja(self):
        _tz_user = pytz.timezone(self.env.user.tz or pytz.utc)
        _fecha_inicio = self._fv_fecha_inicio.astimezone(_tz_user).strftime('%d/%m/%Y %H:%M:%S')
        _fecha_fin = self._fv_fecha_fin.astimezone(_tz_user).strftime('%d/%m/%Y %H:%M:%S')

        return {
            'name': ('Reporte - ' + _fecha_inicio + " - " + _fecha_fin),
            'res_model': 'fenalco.reportes.interfaz.consolidado',
            'view_mode': 'list,form',
            'context': {'order': '_no_recibo desc', 'search_default_group_by_origen': True, 'search_default_group_by_fv_account_journal': True, 'search_default_filter_aprobados': True},
            'domain': [('_fecha_pago_aplicado', '>=', self._fv_fecha_inicio), ('_fecha_pago_aplicado', '<=', self._fv_fecha_fin)],
            'target': 'self',
            'type': 'ir.actions.act_window',
        }

    def fv_generar_consolidado_caja(self):
        """Trae el recaudo consolidado desde la Oracle de producción (Fenalco) y lo
        materializa como registros de fenalco.reportes.interfaz.consolidado.

        Puerto de fv_generar_consolidado_caja() del módulo Odoo15 fenalco_recaudo_pagos.
        El SQL y la lógica de lectura de Oracle se mantienen sin cambios; se removió
        únicamente la sección que mezclaba pagos registrados internamente en Odoo vía
        fenalco.caja.fuentes.pago (funcionalidad "Registrar Pagos en Caja"), que no
        forma parte de este reporte migrado.
        """
        userId = self.env.user
        _tz_user = pytz.timezone(self.env.user.tz or pytz.utc)

        _fecha_inicio = self._fv_fecha_inicio.astimezone(_tz_user).strftime('%d/%m/%Y %H:%M:%S')
        _fecha_fin = self._fv_fecha_fin.astimezone(_tz_user).strftime('%d/%m/%Y %H:%M:%S')
        random.seed(datetime.now().timestamp())
        _number_related_info = random.randint(1000000, 99000000)

        try:
            _nombre_dbsource = 'fena-produccion-' + self.env.cr.dbname
            text_file_path = file_path('fenalco_cuadre_cajas/reports/consolidado_caja_financiero.sql')

            with open(text_file_path, 'r') as fileIMPPN:
                queryFenaCaja = fileIMPPN.read()

            queryFenaCaja = queryFenaCaja.replace('$FECHA_INICIO$', _fecha_inicio)
            queryFenaCaja = queryFenaCaja.replace('$FECHA_FIN$', _fecha_fin)

            dbsource = self.env['base.external.dbsource'].search([('name', '=', _nombre_dbsource), ('connector', '=', 'cx_Oracle')], limit=1)
            if not dbsource:
                raise ValidationError("No existe niguna relacion de base de datos modulo (base.external.dbsource), para nombre (" + _nombre_dbsource + ") y connector Oracle")

            cursor = dbsource.execute(queryFenaCaja, {}, True)
            columnaInfo = cursor['cols']

            if cursor['rows']:
                for row in cursor['rows'] or []:

                    cajeroId = row[columnaInfo.index('CAJERO')]
                    cajeroNombre = row[columnaInfo.index('NOMBRE_CAJERO')]

                    userId = self.env['res.users'].search([("login", "=", cajeroId)], limit=1)
                    if not userId.id:
                        _grupo_cuadre_cajas = self.env.ref('fenalco_cuadre_cajas.group_cuadre_cajas_user')
                        userId = self.env['res.users'].create({
                            'login': cajeroId,
                            'name': cajeroNombre,
                            'groups_id': [(4, _grupo_cuadre_cajas.id)],
                        })

                    id_forma_pago = row[columnaInfo.index('ID_FORMA_PAGO')]
                    descripcion_forma_pago = row[columnaInfo.index('DES_PAGO')]
                    id_transaccion = row[columnaInfo.index('ID_PAGO')]
                    id_recibo = row[columnaInfo.index('RECIBO')]
                    id_liqui = row[columnaInfo.index('ID_LIQUIDACION')]
                    _comprobante = row[columnaInfo.index('COMPROBANTE')]
                    _valor = row[columnaInfo.index('VALOR')]
                    _codigo_barras_open = row[columnaInfo.index('CODIGO_BARRAS_OPEN')]
                    _cajero = row[columnaInfo.index('CAJERO')]
                    _origen = row[columnaInfo.index('CAJA')]
                    _paz_salvo_open = row[columnaInfo.index('PAZ_ZALVO_OPEN')]
                    _hora = row[columnaInfo.index('HORA')]
                    _cedula_deudor = row[columnaInfo.index('CEDULA_DEUDOR')]
                    _grupo_producto = row[columnaInfo.index('GRUPO_PRODUCTO')]

                    _no_secuencia_tucompra = row[columnaInfo.index('OPERADOR')]
                    _fecha_pago = row[columnaInfo.index('FECHA_PAGO')]

                    _fv_estado_externo = row[columnaInfo.index('ESTADO')]

                    _id = str(id_transaccion) + "-" + str(id_recibo) + "-" + str(id_forma_pago) + "-" + str(_cedula_deudor) + "-" + str(_valor) + "-" + str(_comprobante)

                    _forma_pago = self.env["account.journal"].sudo().search(['|', ("code", "=", id_forma_pago), ("_fv_forma_pago_id", "=", id_forma_pago)], limit=1)
                    if not _forma_pago:
                        raise ValidationError("No se ha encotrada una forma de pago :: " + id_forma_pago + " = " + descripcion_forma_pago + " relacionada con la caja actual")

                    _registro_informe = self.env["fenalco.reportes.interfaz.consolidado"].sudo().search([("_id", "=", _id)])
                    if len(_registro_informe) > 1:
                        for dataIN in _registro_informe:
                            dataIN.unlink()

                    _registro_informe = self.env["fenalco.reportes.interfaz.consolidado"].sudo().search([("_id", "=", _id)], limit=1)

                    id_forma_pago_odoo = False if id_forma_pago == 'BANCO' else _forma_pago.id
                    _validado = False if id_forma_pago == 'BANCO' else True
                    _fecha_pago_aplicado = datetime.strptime(_fecha_pago + " -0500", '%d/%m/%Y %H:%M:%S %z')

                    if not _registro_informe:
                        self.with_user(userId).env["fenalco.reportes.interfaz.consolidado"].create({
                            "_id": _id,
                            "_no_recibo": str(id_recibo),
                            "_fv_account_journal": id_forma_pago_odoo,
                            "_no_liquidacion": id_liqui,
                            "_no_secuencia_tucompra": _no_secuencia_tucompra,
                            "_fecha_pago": _fecha_pago,
                            "_fecha_pago_aplicado": _fecha_pago_aplicado.astimezone(pytz.UTC).strftime('%Y-%m-%d %H:%M:%S'),
                            "_fv_estado": "recaudado_externo",
                            "_fv_estado_externo": _fv_estado_externo.lower(),
                            "_comprobante": _comprobante,
                            "_valor": _valor,
                            "_codigo_barras_open": _codigo_barras_open,
                            "_paz_salvo_open": _paz_salvo_open,
                            "_cajero": _cajero,
                            "_hora": _hora,
                            "_origen": _origen.lower(),
                            "_cedula_deudor": str(_cedula_deudor),
                            "_number_related_info": _number_related_info,
                            "_grupo_producto": _grupo_producto.lower(),
                            "_validado": _validado,
                            "_relacion_informe": self.id,
                        })
                        self.env.cr.commit()
                    else:
                        _registro_informe.write({
                            "_number_related_info": _number_related_info,
                            "_no_secuencia_tucompra": _no_secuencia_tucompra,
                            "_fv_estado_externo": _fv_estado_externo.lower(),
                        })
                        self.env.cr.commit()

            self._number_related_info = _number_related_info

            _list_pagos_racaudados = self.env['fenalco.reportes.interfaz.consolidado'].sudo().search(
                [('_fecha_pago_aplicado', '>=', self._fv_fecha_inicio), ('_fecha_pago_aplicado', '<=', self._fv_fecha_fin)],
                order='_fecha_pago_aplicado desc',
            )
            self._total_recaudo = sum(c._valor for c in _list_pagos_racaudados if c['_fv_estado_externo'] == 'aprobado')
            self._total_recaudo_caja = sum(c._valor for c in _list_pagos_racaudados if c['_origen'] == 'caja' and c['_fv_estado_externo'] == 'aprobado')
            self._total_recaudo_cobranzas = sum(c._valor for c in _list_pagos_racaudados if c['_origen'] == 'cobranzas' and c['_fv_estado_externo'] == 'aprobado')
            self._total_recaudo_manuales_open = sum(c._valor for c in _list_pagos_racaudados if c['_origen'] == 'pago_manual_open' and c['_fv_estado_externo'] == 'aprobado')
            if _list_pagos_racaudados:
                self._fv_fecha_ultimo_pago_aplicado = _list_pagos_racaudados[0]._fecha_pago_aplicado

            _list_reporte = self.env['fenalco.reportes.interfaz.unoe'].search(
                [('_fv_fecha_inicio', '>=', self._fv_fecha_inicio), ('_fv_fecha_fin', '<=', self._fv_fecha_fin), ('active', '=', True)]
            )
            for _reporte in _list_reporte:
                if _reporte.id != self.id:
                    _reporte.active = False

        except Exception as ex:
            _logger.exception('Error generando el reporte consolidado de recaudos.')
            raise ValidationError("Por favor validar : " + repr(ex))

        return {
            'name': ('Reporte - ' + _fecha_inicio + " - " + _fecha_fin),
            'res_model': 'fenalco.reportes.interfaz.consolidado',
            'view_mode': 'list,form',
            'context': {'order': '_no_recibo desc', 'search_default_group_by_origen': True, 'search_default_group_by_fv_account_journal': True, 'search_default_filter_aprobados': True},
            'domain': [('_fecha_pago_aplicado', '>=', self._fv_fecha_inicio), ('_fecha_pago_aplicado', '<=', self._fv_fecha_fin)],
            'target': 'self',
            'type': 'ir.actions.act_window',
        }
