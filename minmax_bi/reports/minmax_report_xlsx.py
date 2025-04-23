# minmax_bi/reports/minmax_report_xlsx.py
from odoo import models
import datetime

class MinMaxReportXlsx(models.AbstractModel):
    _name = 'report.minmax_bi.report_minmax_xlsx'
    _inherit = 'report.report_xlsx.abstract'
    _description = 'Reporte de Mínimos y Máximos en Excel'

    def generate_xlsx_report(self, workbook, data, calculations):
        # Este método se llamará para generar el reporte
        for calculation in calculations:
            # Crear hoja para las líneas de cálculo
            sheet = workbook.add_worksheet('Líneas de cálculo')
            
            # Estilos
            header_format = workbook.add_format({
                'bold': True,
                'align': 'center',
                'valign': 'vcenter',
                'bg_color': '#D3D3D3',
                'border': 1
            })
            
            cell_format = workbook.add_format({
                'align': 'center',
                'valign': 'vcenter',
                'border': 1
            })
            
            number_format = workbook.add_format({
                'align': 'right',
                'valign': 'vcenter',
                'border': 1,
                'num_format': '0.00'
            })
            
            # Encabezados
            headers = [
                'Producto', 'Almacén', 'Mínimo actual', 'Máximo actual',
                'Plazo de entrega (días)', 'Vendidos', 'Demanda diaria estimada',
                'Mínimo sugerido', 'Máximo sugerido'
            ]
            
            for col, header in enumerate(headers):
                sheet.write(0, col, header, header_format)
                sheet.set_column(col, col, 15)  # Ancho de columna
            
            # Datos
            row = 1
            for line in calculation.line_ids:
                sheet.write(row, 0, line.product_id.display_name, cell_format)
                sheet.write(row, 1, line.warehouse_id.name, cell_format)
                sheet.write(row, 2, line.current_min, number_format)
                sheet.write(row, 3, line.current_max, number_format)
                sheet.write(row, 4, line.lead_time_days, cell_format)
                sheet.write(row, 5, line.total_sold, number_format)
                sheet.write(row, 6, line.avg_daily_demand, number_format)
                sheet.write(row, 7, line.suggested_min, number_format)
                sheet.write(row, 8, line.suggested_max, number_format)
                row += 1
            
            # Agregar info del cálculo en una hoja separada
            info_sheet = workbook.add_worksheet('Info del cálculo')
            
            info_data = [
                ['Fecha de cálculo', calculation.calculation_date.strftime('%Y-%m-%d %H:%M:%S')],
                ['Usuario', calculation.user_id.name],
                ['Cobertura mínima (días)', calculation.min_coverage_days],
                ['Cobertura máxima (días)', calculation.max_coverage_days],
                ['Factor de ajuste (%)', calculation.adjustment_factor],
                ['Fecha inicial de análisis', calculation.date_start.strftime('%Y-%m-%d')],
                ['Fecha final de análisis', calculation.date_end.strftime('%Y-%m-%d')],
            ]
            
            for i, (label, value) in enumerate(info_data):
                info_sheet.write(i, 0, label, header_format)
                info_sheet.write(i, 1, value, cell_format)
            
            info_sheet.set_column(0, 0, 25)
            info_sheet.set_column(1, 1, 30)
