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
        <% purchase_company = salvage_company = start_company = current_company = end_company = book_company = 0.0 %>
        <% cpt_company, nb_element_company = (0, len(list(group_by_establishment(objects)))) %>
        %if objects:
        %for establishment, assets in group_by_establishment(objects):
            <h2>${establishment}</h2>
            <%
              cpt_company += 1
              purchase_total = salvage_total = start_total = current_total = end_total = book_total = 0.0
              cpt_total, nb_element_total = (0, len(list(group_by(assets))))
            %>
            %for group, assets in group_by(assets):
                <% cpt_total +=1 %>
                <h2>${group}</h2>
                <table>
                    <tr>
                        <th rowspan="2" class="header" width="10%">${_('Reference')}</th>
                        <th rowspan="2" class="header" width="30%">${label_header}</th>
                        <th rowspan="2" class="header" width="10%">${_('Code Asset')}</th>
                        <th rowspan="2" class="header" width="10%">${_('Date start asset')}</th>
                        <th rowspan="2" class="header" width="10%">${_('Annuities')}</th>
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
                        start_value, current_value, end_value, book_value, date_start = depreciation_infos_by_asset_id[asset.id]
                    %>
                    <tr>
                        <td style="text-align:left;">${asset.code}</td>
                        <td style="text-align:left;">${get_label(asset)}</td>
                        <td style="text-align:right;">${_(get_value_selection('account.asset.asset', asset.accounting_method, 'accounting_method', context))}</td>
                        <td style="text-align:right;">${date_start}</td>
                        <td style="text-align:right;">${asset.accounting_annuities}</td>
                        <td style="text-align:right;">${formatLang(asset.purchase_value)}</td>
                        <td style="text-align:right;">${formatLang(asset.salvage_value)}</td>
                        <td style="text-align:right;">${formatLang(start_value)}</td>
                        <td style="text-align:right;">${formatLang(current_value)}</td>
                        <td style="text-align:right;">${formatLang(end_value)}</td>
                        <td style="text-align:right;">${formatLang(book_value)}</td>
                    <tr/>
                %endfor
                    <%
                        purchase_soustotal = salvage_soustotal = start_soustotal = current_soustotal = end_soustotal = book_soustotal = 0.0
                        for asset in assets:
                            purchase_soustotal += asset.purchase_value
                            salvage_soustotal += asset.salvage_value
                            start_soustotal += depreciation_infos_by_asset_id[asset.id][0]
                            current_soustotal += depreciation_infos_by_asset_id[asset.id][1]
                            end_soustotal += depreciation_infos_by_asset_id[asset.id][2]
                            book_soustotal += depreciation_infos_by_asset_id[asset.id][3]
                        purchase_total += purchase_soustotal
                        salvage_total += salvage_soustotal
                        start_total += start_soustotal
                        current_total += current_soustotal
                        end_total += end_soustotal
                        book_total += book_soustotal
                    %>
                    <tr>
                        <td class="footer" style="text-align:left;" colspan="5">${_('Sous Total')}</td>
                        <td class="footer" style="text-align:right;">${formatLang(purchase_soustotal)}</td>
                        <td class="footer" style="text-align:right;">${formatLang(salvage_soustotal)}</td>
                        <td class="footer" style="text-align:right;">${formatLang(start_soustotal)}</td>
                        <td class="footer" style="text-align:right;">${formatLang(current_soustotal)}</td>
                        <td class="footer" style="text-align:right;">${formatLang(end_soustotal)}</td>
                        <td class="footer" style="text-align:right;">${formatLang(book_soustotal)}</td>
                    <tr/>
                    %if cpt_total == nb_element_total:
                        <tr>
                            <td colspan="11" height="30">&nbsp;</td>
                        </tr>
                        <tr>
                            <td class="footer" style="text-align:left;" colspan="5">${_('Total')} ${establishment.split(':')[1]}</td>
                            <td class="footer" style="text-align:right;" >${formatLang(purchase_total)}</td>
                            <td class="footer" style="text-align:right;" width="75px">${formatLang(salvage_total)}</td>
                            <td class="footer" style="text-align:right;" width="69px">${formatLang(start_total)}</td>
                            <td class="footer" style="text-align:right;" width="56px">${formatLang(current_total)}</td>
                            <td class="footer" style="text-align:right;" width="2%">${formatLang(end_total)}</td>
                            <td class="footer" style="text-align:right;" width="5%" >${formatLang(book_total)}</td>
                        <tr/>
                        <%
                            purchase_company += purchase_total
                            salvage_company += salvage_total
                            start_company += start_total
                            current_company += current_total
                            end_company += end_total
                            book_company += book_total
                        %>
                        %if cpt_company == nb_element_company:
                            <tr>
                                <td colspan="11" height="30">&nbsp;</td>
                            </tr>
                            <tr>
                                <td class="footer" style="text-align:left;" colspan="5">${_('Total')} ${_('Company')}</td>
                                <td class="footer" style="text-align:right;" >${formatLang(purchase_company)}</td>
                                <td class="footer" style="text-align:right;" width="75px">${formatLang(salvage_company)}</td>
                                <td class="footer" style="text-align:right;" width="69px">${formatLang(start_company)}</td>
                                <td class="footer" style="text-align:right;" width="56px">${formatLang(current_company)}</td>
                                <td class="footer" style="text-align:right;" width="2%">${formatLang(end_company)}</td>
                                <td class="footer" style="text-align:right;" width="5%" >${formatLang(book_company)}</td>
                            <tr/>
                        %endif
                    %endif
                </table>
            %endfor
            <br />
        %endfor
        %endif
	</body>
</html>
