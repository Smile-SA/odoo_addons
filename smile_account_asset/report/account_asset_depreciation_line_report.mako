<!DOCTYPE html SYSTEM "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">
<html xmlns="http://www.w3.org/1999/xhtml">
    <head>
	    <meta http-equiv="Content-Type" content="text/html; charset=UTF-8">
	    <style type="text/css">${css}</style>
		<title>${_('Account Asset Depreciation Lines')}</title>
    </head>
	<body>
	    <% setLang(lang) %>
	    <% depreciation_infos_by_asset_id = get_depreciation_infos_by_asset_id(objects, company) %>
        %if objects:
	    %for group, assets in group_by(objects):
			<h2>${group}</h2>
			<table>
				<tr>
					<th rowspan="2" class="header" width="10%">${_('Reference')}</th>
					<th rowspan="2" class="header" width="30%">${label_header}</th>
					<th rowspan="2" class="header" width="10%">${_('Gross Value')}</th>
					<th colspan="2">${_('Period Depreciation')}</th>
					<th rowspan="2" class="header" width="10%">${_('Year Depreciation')}</th>
					<th colspan="2">${_('Accumulated Depreciation')}</th>
				</tr>
				<tr>
					<th class="header" width="10%">${_('Accounting')}</th>
					<th class="header" width="10%">${_('Fiscal')}</th>
					<th class="header" width="10%">${_('Accounting')}</th>
					<th class="header" width="10%">${_('Fiscal')}</th>
				</tr>
			%for asset in assets:
				<%
					depr_info = depreciation_infos_by_asset_id[asset.id]
				%>
				<tr>
					<td style="text-align:left;">${asset.code}</td>
					<td style="text-align:left;">${get_label(asset)}</td>
					<td style="text-align:right;">${formatLang(asset.purchase_value)}</td>
					<td style="text-align:right;">${formatLang(depr_info['accounting_period'])}</td>
					<td style="text-align:right;">${formatLang(depr_info['fiscal_period'])}</td>
					<td style="text-align:right;">${formatLang(max(depr_info['accounting_year'], depr_info['fiscal_year']))}</td>
					<td style="text-align:right;">${formatLang(depr_info['accounting_total'])}</td>
					<td style="text-align:right;">${formatLang(depr_info['fiscal_total'])}</td>
				<tr/>
			%endfor
			</table>
	    %endfor
        %endif
	</body>
</html>
