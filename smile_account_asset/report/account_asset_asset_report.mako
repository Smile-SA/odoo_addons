<!DOCTYPE html SYSTEM "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">
<html xmlns="http://www.w3.org/1999/xhtml">
    <head>
	    <meta http-equiv="Content-Type" content="text/html; charset=UTF-8">
	    <style type="text/css">${css}</style>
		<title>${_('Account Assets')}</title>
    </head>
	<body>
	    <% setLang(lang) %>
	    <% depreciation_infos_by_asset_id = get_depreciation_infos_by_asset_id(objects, company) %>
	    %for group, assets in group_by(objects):
			<h2>${group}</h2>
			<table>
				<tr>
					<th rowspan="2" class="header" width="10%">${_('Reference')}</th>
					<th rowspan="2" class="header" width="30%">${label_header}</th>
					<th rowspan="2" class="header" width="10%">${_('Gross Value')}</th>
					<th rowspan="2" class="header" width="10%">${_('Salvage Value')}</th>
					<th colspan="3">${_('Depreciation')}</th>
					<th rowspan="2" class="header" width="10%">${_('Book Value')}</th>
				</tr>
				<tr>
					<th class="header" width="10%">${_('Start')}</th>
					<th class="header" width="10%">${_('Fiscal Year')}</th>
					<th class="header" width="10%">${_('End')}</th>
				</tr>
			%for asset in assets:
				<%
					start_value, current_value, end_value, book_value = depreciation_infos_by_asset_id[asset.id]
				%>
				<tr>
					<td style="text-align:left;">${asset.code}</td>
					<td style="text-align:left;">${get_label(asset)}</td>
					<td style="text-align:right;">${formatLang(asset.purchase_value)}</td>
					<td style="text-align:right;">${formatLang(asset.salvage_value)}</td>
					<td style="text-align:right;">${formatLang(start_value)}</td>
					<td style="text-align:right;">${formatLang(current_value)}</td>
					<td style="text-align:right;">${formatLang(end_value)}</td>
					<td style="text-align:right;">${formatLang(book_value)}</td>
				<tr/>
			%endfor
				<%
					purchase_total = salvage_total = start_total = current_total = end_total = book_total = 0.0
					for asset in assets:
						purchase_total += asset.purchase_value
						salvage_total += asset.salvage_value
						start_total += depreciation_infos_by_asset_id[asset.id][0]
						current_total += depreciation_infos_by_asset_id[asset.id][1]
						end_total += depreciation_infos_by_asset_id[asset.id][2]
						book_total += depreciation_infos_by_asset_id[asset.id][3]
				%>
				<tr>
					<td class="footer" style="text-align:left;" colspan="2">${_('Total')}</td>
					<td class="footer" style="text-align:right;">${formatLang(purchase_total)}</td>
					<td class="footer" style="text-align:right;">${formatLang(salvage_total)}</td>
					<td class="footer" style="text-align:right;">${formatLang(start_total)}</td>
					<td class="footer" style="text-align:right;">${formatLang(current_total)}</td>
					<td class="footer" style="text-align:right;">${formatLang(end_total)}</td>
					<td class="footer" style="text-align:right;">${formatLang(book_total)}</td>
				<tr/>
			</table>
	    %endfor
	</body>
</html>
