<!DOCTYPE html SYSTEM "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">
<html xmlns="http://www.w3.org/1999/xhtml">
    <head>
	    <meta http-equiv="Content-Type" content="text/html; charset=UTF-8">
	    <style type="text/css">${css}</style>
		<title>${_('Account Asset Sales')}</title>
    </head>
    <style>
        .center {
            text-align: center;
        }
        .table_asset td, .table_asset th {
            border: 1px solid black;
        }
        .table_asset {
            border-collapse:collapse;
        }
    </style>
	<body>
        <h1 class="center">Plus ou moins values fiscales</h1>
        <br />
	    <% setLang(lang) %>
        %if objects:
            %for group, assets in group_by(objects):
                <h2>${group}</h2>
                <table class="table_asset" width="100%">
                    <tr>
                        <th rowspan="2" class="header" style="max-width: 10%;width: 10%;">${_('Reference')}</th>
                        <th rowspan="2" class="header" style="max-width: 16%;width: 16%;">${label_header}</th>
                        <th rowspan="2" class="header" style="max-width: 8%;width: 8%;text-align: center;">${_('Purchase Date')}</th>
                        <th colspan="2">${_('Sale')}</th>
                        <th rowspan="2" class="header" style="max-width: 10%;width: 10%;text-align: center;">${_('Gross Value')}</th>
                        <th rowspan="2" class="header" style="max-width: 10%;width: 10%;text-align: center;">${_('Accumulated Depreciation')}</th>
                        <th rowspan="2" class="header" style="max-width: 10%;width: 10%;text-align: center;">${_('Fiscal Book Value')}</th>
                        <th colspan="2">${_('Sale Results')}</th>
                    </tr>
                    <tr>
                        <th class="header" style="max-width: 8%;width: 8%;text-align: center;">${_('Date')}</th>
                        <th class="header" style="max-width: 8%;width: 8%;text-align: center;">${_('Type')}</th>
                        <th class="header" style="max-width: 10%;width: 10%;text-align: center;">${_('Short Term')}</th>
                        <th class="header" style="max-width: 10%;width: 10%;text-align: center;">${_('Long Term')}</th>
                    </tr>
                %for asset in assets:
                    <tr>
                        <td style="text-align:left;">${asset.code}</td>
                        <td style="text-align:left;">${get_label(asset)}</td>
                        <td style="text-align:center;">${asset.purchase_date}</td>
                        <td style="text-align:center;">${asset.sale_date}</td>
                        <td style="text-align:center;">${asset.sale_type or '-'}</td>
                        <td style="text-align:right;">${('%.2f' % asset.purchase_value).replace('.', ',')}</td>
                        <td style="text-align:right;">${('%.2f' % asset.accumulated_amortization_value).replace('.', ',')}</td>
                        <td style="text-align:right;">${('%.2f' % asset.fiscal_book_value).replace('.', ',')}</td>
                        <td style="text-align:right;">${('%.2f' % asset.sale_result_short_term).replace('.', ',')}</td>
                        <td style="text-align:right;">${('%.2f' % asset.sale_result_long_term).replace('.', ',')}</td>
                    <tr/>
                %endfor
                    <%
                        purchase_total = accumulated_total = fiscal_book_total = short_term_total = long_term_total = 0.0
                        for asset in assets:
                            purchase_total += asset.purchase_value
                            accumulated_total += asset.accumulated_amortization_value
                            fiscal_book_total += asset.fiscal_book_value
                            short_term_total += asset.sale_result_short_term
                            long_term_total += asset.sale_result_long_term
                    %>
                    <br/>
                    <tr>
                        <td colspan="6" height="30" style="border:none;">&nbsp;</td>
                    </tr>
                    <tr>
                        <td class="footer" style="text-align:left;font-weight:bold;border:none;" colspan="5">${_('Total')}</td>
                        <td class="footer" style="text-align:right;font-weight:bold;border:none;">${formatLang(purchase_total)}</td>
                        <td class="footer" style="text-align:right;font-weight:bold;border:none;">${formatLang(accumulated_total)}</td>
                        <td class="footer" style="text-align:right;font-weight:bold;border:none;">${formatLang(fiscal_book_total)}</td>
                        <td class="footer" style="text-align:right;font-weight:bold;border:none;">${formatLang(short_term_total)}</td>
                        <td class="footer" style="text-align:right;font-weight:bold;border:none;">${formatLang(long_term_total)}</td>
                    <tr/>
                    <tr>
                        <td colspan="6" height="30" style="border:none;">&nbsp;</td>
                    </tr>
                </table>
            %endfor
            <%
                global_short_term = global_long_term = global_tax_origin = global_tax_add = global_tax_to_pay = 0.0
                for asset in assets:
                    global_short_term += asset.sale_result_short_term
                    global_long_term += asset.sale_result_long_term
                    global_tax_origin += asset.purchase_tax_amount
                    if asset.regularization_tax_amount < 0.0:
                        global_tax_add += abs(asset.regularization_tax_amount)
                    else:
                        global_tax_to_pay += asset.regularization_tax_amount
            %>
            <h2 style="page-break-before: always;">${_('Summary')}</h2>
            <table class="table_asset" width="100%">
                <tr>
                    <th colspan="2">${_('Sale Results')}</th>
                    <th colspan="2">${_('Deductible Taxes')}</th>
                    <th class="header" style="max-width: 20%;width: 20%;text-align: center;" rowspan="2">${_('Taxes to pay')}</th>
                </tr>
                <tr>
                    <th class="header" style="max-width: 20%;width: 20%;text-align: center;">${_('Short Term')}</th>
                    <th class="header" style="max-width: 20%;width: 20%;text-align: center;">${_('Long Term')}</th>
                    <th class="header" style="max-width: 20%;width: 20%;text-align: center;">${_('Origin')}</th>
                    <th class="header" style="max-width: 20%;width: 20%;text-align: center;">${_('Additionnal')}</th>
                </tr>
                <tr>
                    <td style="text-align:right;">${global_short_term}</td>
                    <td style="text-align:right;">${global_long_term}</td>
                    <td style="text-align:right;">${global_tax_origin}</td>
                    <td style="text-align:right;">${global_tax_add}</td>
                    <td style="text-align:right;">${global_tax_to_pay}</td>
                </tr>
            </table>
            <br />
        %endif
	</body>
</html>
