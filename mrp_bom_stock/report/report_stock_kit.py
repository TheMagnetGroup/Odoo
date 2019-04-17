# -*- coding: utf-8 -*-

from odoo import api, fields, models, tools


class ReportStockForecat(models.Model):
    _name = 'report.stock.kit'
    _auto = False

    product_tmpl_id = fields.Many2one('product.template', string='Product Template', readonly=True)
    qty_available = fields.Float(readonly=True, string="Quantity On Hand")

    @api.model_cr
    def init(self):
        tools.drop_view_if_exists(self._cr, 'report_stock_kit')
        self._cr.execute(
            """
                CREATE or REPLACE VIEW report_stock_kit AS (
                    SELECT
                        ROW_NUMBER() OVER () AS id,
                        FINAL.product_tmpl_id AS product_tmpl_id,
                        MIN(FINAL.qty_available)::integer AS qty_available
                    FROM stock_location l,(
                        SELECT
                            MAIN.product_tmpl_id AS product_tmpl_id,
                            MIN(MAIN.quantity) AS qty_available
                        FROM(
                            SELECT
                                sq.product_id,
                                bm.product_tmpl_id,
                                sum(sq.quantity/bml.product_qty)::integer AS quantity
                                FROM
                                    stock_quant sq
                                LEFT JOIN
                                    stock_location location_id ON sq.location_id = location_id.id
                                LEFT JOIN
                                    product_product ON product_product.id = sq.product_id
                                LEFT JOIN
                                    mrp_bom_line bml ON bml.product_id=sq.product_id
                                LEFT JOIN
                                    mrp_bom bm ON bm.id=bml.bom_id
                                LEFT JOIN
                                    product_template pt ON pt.id=bm.product_tmpl_id
                                WHERE
                                    location_id.usage = 'internal' AND
                                    pt.bom_id IS NOT NULL AND
                                    pt.bom_id=bm.id
                                GROUP BY
                                    sq.product_id,
                                    bm.product_tmpl_id
                            ) AS MAIN
                        GROUP BY
                            MAIN.product_tmpl_id

                        UNION ALL

                        SELECT
                            SUB.product_tmpl_id AS product_tmpl_id,
                            MIN(SUB.quantity) AS qty_available
                        FROM(
                            SELECT
                                sq.product_id,
                                pt.id AS product_tmpl_id,
                                sum(sq.quantity)::integer AS quantity
                                FROM
                                    stock_quant sq
                                LEFT JOIN
                                    stock_location location_id ON sq.location_id = location_id.id
                                LEFT JOIN
                                    product_product ON product_product.id = sq.product_id
                                LEFT JOIN
                                    product_template pt ON pt.id=product_product.product_tmpl_id
                                WHERE
                                    location_id.usage = 'internal' AND
                                    pt.bom_id IS NULL
                                GROUP BY
                                    sq.product_id,
                                    pt.id
                            ) AS SUB
                        GROUP BY
                            SUB.product_tmpl_id
                    ) AS FINAL
                GROUP BY
                    FINAL.product_tmpl_id
            )""")


class ReportStockForcasted(models.Model):
    _name = 'report.stock.kit.forcasted'
    _auto = False

    date = fields.Date()
    product_tmpl_id = fields.Many2one('product.template', string='Product Template', readonly=True)
    qty_available = fields.Float(readonly=True, string="Quantity On Hand")
    virtual_available = fields.Float(readonly=True, string="Forecast Quantity")

    @api.model_cr
    def init(self):
        tools.drop_view_if_exists(self._cr, 'report_stock_kit_forcasted')
        self._cr.execute(
            """
                CREATE or REPLACE VIEW report_stock_kit_forcasted AS (
                    SELECT
                        ROW_NUMBER() OVER () AS id,
                        FINAL.product_tmpl_id AS product_tmpl_id,
                        SUB.date as date,
                        CASE WHEN FINAL.date = SUB.date THEN MIN(FINAL.qty_available)::integer ELSE 0 END as qty_available,
                        CASE WHEN FINAL.date = SUB.date THEN MIN(FINAL.virtual_available)::integer ELSE 0 END as virtual_available
                    FROM stock_warehouse wh,(
                        SELECT
                            MAIN.product_tmpl_id AS product_tmpl_id,
                            SUM(MAIN.quantity) AS qty_available,
                            SUM(MAIN.quantity) AS virtual_available,
                            MAIN.date AS date
                        FROM(
                            SELECT
                                sq.product_id,
                                bm.product_tmpl_id,
                                sum(sq.quantity/bml.product_qty)::integer AS quantity,
                                date_trunc('week', to_date(to_char(CURRENT_DATE, 'YYYY/MM/DD'), 'YYYY/MM/DD')) as date
                                FROM
                                    stock_quant sq
                                LEFT JOIN
                                    stock_location location_id ON sq.location_id = location_id.id
                                LEFT JOIN
                                    product_product ON product_product.id = sq.product_id
                                LEFT JOIN
                                    mrp_bom_line bml ON bml.product_id=sq.product_id
                                LEFT JOIN
                                    mrp_bom bm ON bm.id=bml.bom_id
                                LEFT JOIN
                                    product_template pt ON pt.id=bm.product_tmpl_id
                                WHERE
                                    location_id.usage = 'internal' AND
                                    pt.bom_id IS NOT NULL AND
                                    pt.bom_id=bm.id
                                GROUP BY
                                    sq.product_id,
                                    bm.product_tmpl_id,
                                    date
                            ) AS MAIN
                        GROUP BY
                            MAIN.product_tmpl_id,
                            MAIN.date

                        UNION ALL
                        -- Find out incoming shipment moves
                        SELECT
                            MAIN1.product_tmpl_id AS product_tmpl_id,
                            0 AS qty_available, -- we do not need to calculate here
                            SUM(MAIN1.quantity) AS virtual_quantity,
                            MAIN1.date AS date
                        FROM
                            (SELECT
                                sm.product_id,
                                bm.product_tmpl_id,
                                sum(sm.product_qty/bml.product_qty)::integer as quantity,
                                CASE WHEN sm.date_expected > CURRENT_DATE
                                    THEN date_trunc('week', to_date(to_char(sm.date_expected, 'YYYY/MM/DD'), 'YYYY/MM/DD'))
                                    ELSE date_trunc('week', to_date(to_char(CURRENT_DATE, 'YYYY/MM/DD'), 'YYYY/MM/DD')) END
                                    AS date
                                FROM
                                   stock_move as sm
                                LEFT JOIN
                                   product_product ON product_product.id = sm.product_id
                                LEFT JOIN
                                stock_location dest_location ON sm.location_dest_id = dest_location.id
                                LEFT JOIN
                                stock_location source_location ON sm.location_id = source_location.id
                                LEFT JOIN
                                    mrp_bom_line bml ON bml.product_id=sm.product_id
                                LEFT JOIN
                                    mrp_bom bm ON bm.id=bml.bom_id
                                LEFT JOIN
                                    product_template pt ON pt.id=bm.product_tmpl_id
                                WHERE
                                    sm.state IN ('confirmed','partially_available','assigned','waiting') AND
                                    source_location.usage != 'internal' AND dest_location.usage = 'internal' AND
                                    pt.bom_id IS NOT NULL AND
                                    pt.bom_id=bm.id
                                GROUP BY
                                    sm.product_id,
                                    bm.product_tmpl_id,
                                    sm.date_expected
                            ) AS MAIN1
                        GROUP BY
                            MAIN1.product_tmpl_id,
                            MAIN1.date

                        UNION ALL

                        -- Find out outgoing shipment moves

                        SELECT
                            MAIN2.product_tmpl_id AS product_tmpl_id,
                            0 AS qty_available,
                            SUM(-MAIN2.quantity) AS virtual_quantity,
                            MAIN2.date AS date
                        FROM
                            (SELECT
                                sm.product_id,
                                bm.product_tmpl_id,
                                sum(sm.product_qty/bml.product_qty)::integer AS quantity,
                                CASE WHEN sm.date_expected > CURRENT_DATE
                                    THEN date_trunc('week', to_date(to_char(sm.date_expected, 'YYYY/MM/DD'), 'YYYY/MM/DD'))
                                    ELSE date_trunc('week', to_date(to_char(CURRENT_DATE, 'YYYY/MM/DD'), 'YYYY/MM/DD')) END
                                AS date
                                FROM
                                   stock_move AS sm
                                LEFT JOIN
                                   product_product ON product_product.id = sm.product_id
                                LEFT JOIN
                                   stock_location source_location ON sm.location_id = source_location.id
                                LEFT JOIN
                                   stock_location dest_location ON sm.location_dest_id = dest_location.id
                                LEFT JOIN
                                    mrp_bom_line bml ON bml.product_id=sm.product_id
                                LEFT JOIN
                                    mrp_bom bm ON bm.id=bml.bom_id
                                LEFT JOIN
                                    product_template pt ON pt.id=bm.product_tmpl_id
                                WHERE
                                    sm.state IN ('confirmed','partially_available','assigned','waiting') AND
                                    source_location.usage = 'internal' AND dest_location.usage != 'internal' AND
                                    pt.bom_id IS NOT NULL AND
                                    pt.bom_id=bm.id
                                GROUP BY
                                    sm.product_id,
                                    bm.product_tmpl_id,
                                    sm.date_expected
                            ) AS MAIN2
                        GROUP BY
                            MAIN2.product_tmpl_id,
                            MAIN2.date
                    ) AS FINAL

                    LEFT JOIN
                     (SELECT DISTINCT date
                        FROM
                        (SELECT date_trunc('week', CURRENT_DATE) AS DATE
                            UNION ALL
                            SELECT date_trunc('week', to_date(to_char(sm.date_expected, 'YYYY/MM/DD'), 'YYYY/MM/DD')) AS date
                            FROM stock_move sm
                            LEFT JOIN
                                stock_location source_location ON sm.location_id = source_location.id
                              LEFT JOIN
                                stock_location dest_location     ON sm.location_dest_id = dest_location.id
                            WHERE
                                sm.state IN ('confirmed','assigned','waiting') AND sm.date_expected > CURRENT_DATE AND
                             ((dest_location.usage = 'internal' AND source_location.usage != 'internal')
                              or (source_location.usage = 'internal' AND dest_location.usage != 'internal'))) AS DATE_SEARCH)
                             SUB ON (SUB.date IS NOT NULL)
                GROUP BY
                    FINAL.product_tmpl_id,
                    SUB.date,
                    FINAL.date
            )""")
