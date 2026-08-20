import logging
import os

import oracledb

from odoo import fields, models

_logger = logging.getLogger(__name__)

# El Oracle de producción de Fenalco es una versión que el modo "thin" de
# python-oracledb no soporta (DPY-3010), igual que ya le pasaba al cx_Oracle
# original. Se activa modo "thick" apuntando al Instant Client local.
_INSTANT_CLIENT_DIR = r"C:\odoo\oracle\instantclient_19_31"
try:
    oracledb.init_oracle_client(lib_dir=_INSTANT_CLIENT_DIR)
except Exception:
    _logger.exception("No se pudo inicializar el Oracle Instant Client en modo thick (%s)", _INSTANT_CLIENT_DIR)


class BaseExternalDbsource(models.Model):
    """Adaptador Oracle para base.external.dbsource usando python-oracledb
    en modo "thick" (requiere el Oracle Instant Client instalado en
    _INSTANT_CLIENT_DIR, inicializado arriba).

    Se mantiene el mismo valor técnico de conector ('cx_Oracle') y los
    mismos nombres de método (connection_open_cx_Oracle, execute_cx_Oracle,
    connection_close_cx_Oracle) que usaba el módulo original en Odoo15, para
    que el código portado de fenalco_reportes_unoe.py (que busca
    ('connector', '=', 'cx_Oracle')) funcione sin cambios.
    """

    _inherit = "base.external.dbsource"

    connector = fields.Selection(
        selection_add=[("cx_Oracle", "Oracle")],
        ondelete={"cx_Oracle": "cascade"},
    )

    PWD_STRING_CX_ORACLE = "Password=%s;"

    def connection_open_cx_Oracle(self):
        os.environ["NLS_LANG"] = "AMERICAN_AMERICA.UTF8"
        return oracledb.connect(self.conn_string_full)

    def connection_close_cx_Oracle(self, connection):
        return connection.close()

    def execute_cx_Oracle(self, sqlquery, sqlparams, metadata):
        return self._execute_generic(sqlquery, sqlparams, metadata)

    def execute_pk(self, sqlquery, sqlparams):
        return self._execute_pk(sqlquery, sqlparams)
