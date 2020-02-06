# -*- coding: utf-8 -*-

from odoo import api, fields, models, tools


class ReportStockKitForcasted(models.Model):
    _name = 'report.stock.kit.forcasted'
    _auto = False
    """
    Report that shows the forcasted manufacturable quantity of the products based on the on forecasted quantity of bom componants.
    Group by warehouse.
    """

    product_tmpl_id = fields.Many2one('product.template', string='Product Template', readonly=True)
    product_id = fields.Many2one('product.product', string="Product", readonly=True)
    virtual_available = fields.Float(readonly=True, string="Quantity On Hand")
    warehouse_id = fields.Many2one('stock.warehouse', string="Warehouse", readonly=True)

    @api.model_cr
    def init(self):
        tools.drop_view_if_exists(self._cr, 'report_stock_kit_forcasted')
        self._cr.execute(
            """
                CREATE or REPLACE VIEW report_stock_kit_forcasted AS (
                    SELECT
                        ROW_NUMBER() OVER () AS id,
                        FINAL.product_id AS product_id,
                        FINAL.product_tmpl_id AS product_tmpl_id,
                        FINAL.warehouse_id,
                        SUM(FINAL.virtual_available) as virtual_available
                    FROM (
                        -- CALCULATE INCOMING QUANTITIES
                        SELECT
                            MAIN.prod_id AS product_id,
                            MAIN.tmpl_id AS product_tmpl_id,
                            MAIN.warehouse_id,
                            MIN(MAIN.quantity) as virtual_available
                        FROM (
                            SELECT
                                pp.id as prod_id,
                                mbl.product_id as bom_product_id,
                                pt.id as tmpl_id,
                                sm.warehouse_id AS warehouse_id,
                                SUM(sm.product_qty/mbl.product_qty)::integer as quantity
                            FROM
                                product_product pp
                            LEFT JOIN
                                product_template pt ON pt.id = pp.product_tmpl_id
                            LEFT JOIN
                                mrp_bom mb ON mb.id = pt.bom_id
                            LEFT JOIN
                                mrp_bom_line mbl ON mbl.bom_id = mb.id AND mbl.to_exclude = False
                            LEFT JOIN
                                mrp_bom_line_product_attribute_value_rel bml_att_rel ON bml_att_rel.mrp_bom_line_id = mbl.id
                            LEFT JOIN
                                product_attribute_value_product_product_rel pa_rel on pa_rel.product_attribute_value_id = bml_att_rel.product_attribute_value_id
                            LEFT JOIN
                                stock_move sm ON sm.product_id = mbl.product_id OR sm.product_id = pp.id
                            LEFT JOIN
                                stock_location source_location ON source_location.id = sm.location_id
                            LEFT JOIN
                                stock_location dest_location ON dest_location.id = sm.location_dest_id
                            WHERE
                                sm.state IN ('confirmed','partially_available','assigned','waiting') AND
                                source_location.usage != 'internal' AND dest_location.usage = 'internal' AND
                                pt.bom_id IS NOT NULL AND
                                pa_rel.product_product_id = pp.id
                            GROUP BY
                                pp.id,
                                pt.id,
                                sm.warehouse_id,
                                mbl.product_id
                            UNION ALL
                            SELECT
                                pp.id as prod_id,
                                mbl.product_id as bom_product_id,
                                pt.id as tmpl_id,
                                sm.warehouse_id AS warehouse_id,
                                SUM(sm.product_qty/mbl.product_qty)::integer as quantity
                            FROM
                                product_product pp
                            LEFT JOIN
                                product_template pt ON pt.id = pp.product_tmpl_id
                            LEFT JOIN
                                mrp_bom mb ON mb.id = pt.bom_id
                            LEFT JOIN
                                mrp_bom_line mbl ON mbl.bom_id = mb.id AND mbl.to_exclude = False
                            LEFT JOIN
                                stock_move sm ON sm.product_id = mbl.product_id OR sm.product_id = pp.id
                            LEFT JOIN
                                stock_location source_location ON source_location.id = sm.location_id
                            LEFT JOIN
                                stock_location dest_location ON dest_location.id = sm.location_dest_id
                            WHERE
                                sm.state IN ('confirmed','partially_available','assigned','waiting') AND
                                source_location.usage != 'internal' AND dest_location.usage = 'internal' AND
                                pt.bom_id IS NOT NULL AND
                                mbl.id NOT IN (select rel.mrp_bom_line_id from mrp_bom_line_product_attribute_value_rel rel)
                            GROUP BY
                                pp.id,
                                pt.id,
                                sm.warehouse_id,
                                mbl.product_id) AS MAIN
                        GROUP BY
                            MAIN.prod_id,
                            MAIN.tmpl_id,
                            MAIN.warehouse_id
                        UNION ALL
                        -- CALCULATE OUTGOING QUANTITIES
                        SELECT
                            MAIN1.prod_id AS product_id,
                            MAIN1.tmpl_id AS product_tmpl_id,
                            MAIN1.warehouse_id,
                            MIN(-MAIN1.quantity) as virtual_available
                        FROM (
                            SELECT
                                pp.id as prod_id,
                                mbl.product_id as bom_product_id,
                                pt.id as tmpl_id,
                                dest_location.warehouse_id AS warehouse_id,
                                SUM(sm.product_qty/mbl.product_qty)::integer as quantity
                            FROM
                                product_product pp
                            LEFT JOIN
                                product_template pt ON pt.id = pp.product_tmpl_id
                            LEFT JOIN
                                mrp_bom mb ON mb.id = pt.bom_id
                            LEFT JOIN
                                mrp_bom_line mbl ON mbl.bom_id = mb.id AND mbl.to_exclude = False
                            LEFT JOIN
                                mrp_bom_line_product_attribute_value_rel bml_att_rel ON bml_att_rel.mrp_bom_line_id = mbl.id
                            LEFT JOIN
                                product_attribute_value_product_product_rel pa_rel on pa_rel.product_attribute_value_id = bml_att_rel.product_attribute_value_id
                            LEFT JOIN
                                stock_move sm ON sm.product_id = mbl.product_id OR sm.product_id = pp.id
                            LEFT JOIN
                                stock_location source_location ON source_location.id = sm.location_id
                            LEFT JOIN
                                stock_location dest_location ON dest_location.id = sm.location_dest_id
                            WHERE
                                sm.state IN ('confirmed','partially_available','assigned','waiting') AND
                                source_location.usage in ('internal', 'destination') AND dest_location.usage != 'internal' AND
                                pt.bom_id IS NOT NULL AND
                                pa_rel.product_product_id = pp.id
                            GROUP BY
                                pp.id,
                                pt.id,
                                dest_location.warehouse_id,
                                mbl.product_id
                            UNION ALL
                            SELECT
                                pp.id as prod_id,
                                mbl.product_id as bom_product_id,
                                pt.id as tmpl_id,
                                sm.warehouse_id AS warehouse_id,
                                SUM(sm.product_qty/mbl.product_qty)::integer as quantity
                            FROM
                                product_product pp
                            LEFT JOIN
                                product_template pt ON pt.id = pp.product_tmpl_id
                            LEFT JOIN
                                mrp_bom mb ON mb.id = pt.bom_id
                            LEFT JOIN
                                mrp_bom_line mbl ON mbl.bom_id = mb.id AND mbl.to_exclude = False
                            LEFT JOIN
                                stock_move sm ON sm.product_id = mbl.product_id OR sm.product_id = pp.id
                            LEFT JOIN
                                stock_location source_location ON source_location.id = sm.location_id
                            LEFT JOIN
                                stock_location dest_location ON dest_location.id = sm.location_dest_id
                            WHERE
                                sm.state IN ('confirmed','partially_available','assigned','waiting') AND
                                source_location.usage in ('internal', 'destination') AND dest_location.usage != 'internal' AND
                                pt.bom_id IS NOT NULL AND
                                mbl.id NOT IN (select rel.mrp_bom_line_id from mrp_bom_line_product_attribute_value_rel rel)
                            GROUP BY
                                pp.id,
                                pt.id,
                                sm.warehouse_id,
                                mbl.product_id) AS MAIN1
                        GROUP BY
                            MAIN1.prod_id,
                            MAIN1.tmpl_id,
                            MAIN1.warehouse_id
                        UNION ALL
                        -- CALCULATE ON HAND QUANTITIES
                        SELECT
                            MAIN2.prod_id AS product_id,
                            MAIN2.tmpl_id AS product_tmpl_id,
                            MAIN2.warehouse_id,
                            MIN(MAIN2.quantity) as virtual_available
                        FROM (
                            SELECT
                                pp.id as prod_id,
                                mbl.product_id as bom_product_id,
                                pt.id as tmpl_id,
                                sl.warehouse_id AS warehouse_id,
                                SUM(sq.quantity/mbl.product_qty)::integer as quantity
                            FROM
                                product_product pp
                            LEFT JOIN
                                product_template pt ON pt.id = pp.product_tmpl_id
                            LEFT JOIN
                                mrp_bom mb ON mb.id = pt.bom_id
                            LEFT JOIN
                                mrp_bom_line mbl ON mbl.bom_id = mb.id AND mbl.to_exclude = False
                            LEFT JOIN
                                mrp_bom_line_product_attribute_value_rel bml_att_rel ON bml_att_rel.mrp_bom_line_id = mbl.id
                            LEFT JOIN
                                product_attribute_value_product_product_rel pa_rel on pa_rel.product_attribute_value_id = bml_att_rel.product_attribute_value_id
                            LEFT JOIN
                                stock_quant sq ON sq.product_id = mbl.product_id OR sq.product_id = pp.id
                            LEFT JOIN
                                stock_location sl ON sl.id = sq.location_id
                            WHERE
                                sl.usage = 'internal' AND
                                pt.bom_id IS NOT NULL AND
                                pa_rel.product_product_id = pp.id
                            GROUP BY
                                pp.id,
                                pt.id,
                                sl.warehouse_id,
                                mbl.product_id
                            UNION ALL
                            SELECT
                                pp.id as prod_id,
                                mbl.product_id as bom_product_id,
                                pt.id as tmpl_id,
                                sl.warehouse_id AS warehouse_id,
                                SUM(sq.quantity/mbl.product_qty)::integer as quantity
                            FROM
                                product_product pp
                            LEFT JOIN
                                product_template pt ON pt.id = pp.product_tmpl_id
                            LEFT JOIN
                                mrp_bom mb ON mb.id = pt.bom_id
                            LEFT JOIN
                                mrp_bom_line mbl ON mbl.bom_id = mb.id AND mbl.to_exclude = False
                            LEFT JOIN
                                stock_quant sq ON sq.product_id = mbl.product_id OR sq.product_id = pp.id
                            LEFT JOIN
                                stock_location sl ON sl.id = sq.location_id
                            WHERE
                                sl.usage = 'internal' AND
                                pt.bom_id IS NOT NULL AND
                                mbl.id NOT IN (select rel.mrp_bom_line_id from mrp_bom_line_product_attribute_value_rel rel)
                            GROUP BY
                                pp.id,
                                pt.id,
                                sl.warehouse_id,
                                mbl.product_id) AS MAIN2
                        GROUP BY
                            MAIN2.prod_id,
                            MAIN2.tmpl_id,
                            MAIN2.warehouse_id
                        ) AS FINAL
                    GROUP BY
                        FINAL.product_id,
                        FINAL.product_tmpl_id,
                        FINAL.warehouse_id
            )""")
