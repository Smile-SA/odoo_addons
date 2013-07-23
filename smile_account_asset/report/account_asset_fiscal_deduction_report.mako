<!DOCTYPE html SYSTEM "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">
<html xmlns="http://www.w3.org/1999/xhtml">
    <head>
	    <meta http-equiv="Content-Type" content="text/html; charset=UTF-8">
	    <style type="text/css">
	    	${css}
	    	td {vertical-align: top;}
	    </style>
		<title>${_('Account Asset Fiscal Deductions')}</title>
    </head>
	<body>
	    <% setLang(lang) %>
	    <% depreciation_infos_by_asset_id = get_depreciation_infos_by_asset_id(objects, company) %>
	    %for group, assets in group_by(objects):
			<h2>${group}</h2>
			<table>
				<tr>
					<th class="header" width="10%">${_('Reference')}</th>
					<th class="header" width="30%">${label_header}</th>
					<th class="header" width="10%">${_('Gross Value')}</th>
					<th class="header" width="10%">${_('Yearly Depreciation')}<br/><i>${_('Non Ded. Part')}</i></th>
					<th class="header" width="10%">${_('Accumulated Depreciation')}<br/><i>${_('Non Ded. Part')}</i></th>
					<th class="header" width="10%">${_('Book Value')}</th>
				</tr>
			%for asset in assets:
				<%
					year_value, accumulated_value, non_ded_year_value, non_ded_accumulated_value, book_value = depreciation_infos_by_asset_id[asset.id]
				%>
				<tr>
					<td style="text-align:left;">${asset.code}</td>
					<td style="text-align:left;">${get_label(asset)}</td>
					<td style="text-align:right;">${formatLang(asset.purchase_value)}</td>
					<td style="text-align:right;">${formatLang(year_value)}<br/><i>${formatLang(non_ded_year_value)}</i></td>
					<td style="text-align:right;">${formatLang(accumulated_value)}<br/><i>${formatLang(non_ded_accumulated_value)}</i></td>
					<td style="text-align:right;">${formatLang(book_value)}</td>
				<tr/>
			%endfor
				<%
					purchase_total = year_total = accumulated_total = non_ded_year_total = non_ded_accumulated_total = book_total = 0.0
					for asset in assets:
						purchase_total += asset.purchase_value
						year_total += depreciation_infos_by_asset_id[asset.id][0]
						accumulated_total += depreciation_infos_by_asset_id[asset.id][1]
						non_ded_year_total += depreciation_infos_by_asset_id[asset.id][2]
						non_ded_accumulated_total += depreciation_infos_by_asset_id[asset.id][3]
						book_total += depreciation_infos_by_asset_id[asset.id][4]
				%>
				<tr>
					<td class="footer" style="text-align:left;" colspan="2">${_('Total')}</td>
					<td class="footer" style="text-align:right;">${formatLang(purchase_total)}</td>
					<td class="footer" style="text-align:right;">${formatLang(year_total)}<br/><i>${formatLang(non_ded_year_total)}</i></td>
					<td class="footer" style="text-align:right;">${formatLang(accumulated_total)}<br/><i>${formatLang(non_ded_accumulated_total)}</i></td>
					<td class="footer" style="text-align:right;">${formatLang(book_total)}</td>
				<tr/>
			</table>
	    %endfor
	</body>
</html>
