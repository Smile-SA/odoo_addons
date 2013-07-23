<!DOCTYPE html SYSTEM "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">
<html xmlns="http://www.w3.org/1999/xhtml">
    <head>
	    <meta http-equiv="Content-Type" content="text/html; charset=UTF-8">
	    <style type="text/css">${css}</style>
		<title>${_('Account Asset Sales')}</title>
    </head>
	<body>
	    <% setLang(lang) %>
	    %for group, assets in group_by(objects):
			<h2>${group}</h2>
			<table>
				<tr>
					<th rowspan="2" class="header" width="10%">${_('Reference')}</th>
					<th rowspan="2" class="header" width="16%">${label_header}</th>
					<th rowspan="2" class="header" width="8%">${_('Purchase Date')}</th>
					<th colspan="2">${_('Sale')}</th>
					<th rowspan="2" class="header" width="10%">${_('Gross Value')}</th>
					<th rowspan="2" class="header" width="10%">${_('Accumulated Depreciation')}</th>
					<th rowspan="2" class="header" width="10%">${_('Fiscal Book Value')}</th>
					<th colspan="2">${_('Sale Results')}</th>
				</tr>
				<tr>
					<th class="header" width="8%">${_('Date')}</th>
					<th class="header" width="8%">${_('Type')}</th>
					<th class="header" width="10%">${_('Short Term')}</th>
					<th class="header" width="10%">${_('Long Term')}</th>
				</tr>
			%for asset in assets:
				<tr>
					<td style="text-align:left;">${asset.code}</td>
					<td style="text-align:left;">${get_label(asset)}</td>
					<td style="text-align:left;">${asset.purchase_date}</td>
					<td style="text-align:left;">${asset.sale_date}</td>
					<td style="text-align:left;">${asset.sale_type or '-'}</td>
					<td style="text-align:right;">${formatLang(asset.purchase_value)}</td>
					<td style="text-align:right;">${formatLang(asset.accumulated_amortization_value)}</td>
					<td style="text-align:right;">${formatLang(asset.fiscal_book_value)}</td>
					<td style="text-align:right;">${formatLang(asset.sale_result_short_term)}</td>
					<td style="text-align:right;">${formatLang(asset.sale_result_long_term)}</td>
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
				<tr>
					<td class="footer" style="text-align:left;" colspan="5">${_('Total')}</td>
					<td class="footer" style="text-align:right;">${formatLang(purchase_total)}</td>
					<td class="footer" style="text-align:right;">${formatLang(accumulated_total)}</td>
					<td class="footer" style="text-align:right;">${formatLang(fiscal_book_total)}</td>
					<td class="footer" style="text-align:right;">${formatLang(short_term_total)}</td>
					<td class="footer" style="text-align:right;">${formatLang(long_term_total)}</td>
				<tr/>
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
	    <table>
	    	<tr>
				<th colspan="2">${_('Sale Results')}</th>
				<th colspan="2">${_('Deductible Taxes')}</th>
				<th class="header" width="20%" rowspan="2">${_('Taxes to pay')}</th>
			</tr>
			<tr>
				<th class="header" width="20%">${_('Short Term')}</th>
				<th class="header" width="20%">${_('Long Term')}</th>
				<th class="header" width="20%">${_('Origin')}</th>
				<th class="header" width="20%">${_('Additionnal')}</th>
			</tr>
	    	<tr>
				<td style="text-align:right;">${global_short_term}</td>
				<td style="text-align:right;">${global_long_term}</td>
				<td style="text-align:right;">${global_tax_origin}</td>
				<td style="text-align:right;">${global_tax_add}</td>
				<td style="text-align:right;">${global_tax_to_pay}</td>
	    	</tr>
	    </table>
	</body>
</html>
