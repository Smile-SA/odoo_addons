<!DOCTYPE html SYSTEM "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">
<html xmlns="http://www.w3.org/1999/xhtml">
    <head>
	    <meta http-equiv="Content-Type" content="text/html; charset=UTF-8">
	    <style type="text/css">${css}</style>
		<title>${_('Account Assets')}</title>
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
        <h1 class="center">Bilan et amortissements de l'exercice</h1>
        <br />
	    <% setLang(lang) %>
	    <% depreciation_infos_by_asset_id = get_depreciation_infos_by_asset_id(objects, company) %>
        <% purchase_company = salvage_company = start_company = current_company = end_company = book_company = 0.0 %>
        <% nb_element_company, group_establishment = group_by_establishment(objects) %>
        <% cpt_company = 0 %>
        %if objects:
        %for establishment, assets in group_establishment:
            <h2>${establishment}</h2>
            <%
              cpt_company += 1
              purchase_total = salvage_total = start_total = current_total = end_total = book_total = 0.0
              cpt_total = 0
              nb_element_total, group_asset = group_by(assets)
            %>
            %for group, assets in group_asset:
                <% cpt_total +=1 %>
                <h2>${group}</h2>
                <table class="table_asset" width="100%">
                    <tr>
                        <th rowspan="2" class="header" style="max-width: 10%;width: 10%;">${_('Reference')}</th>
                        <th rowspan="2" class="header" style="max-width: 15%;width: 15%;">${label_header}</th>
                        <th rowspan="2" class="header" style="max-width: 7%;width: 7%;text-align: center;">${_('Code Asset')}</th>
                        <th rowspan="2" class="header" style="max-width: 7%;width: 7%;text-align: center;">${_('Date start asset')}</th>
                        <th rowspan="2" class="header" style="max-width: 5%;width: 5%;text-align: center;">${_('Annuities')}</th>
                        <th rowspan="2" class="header" style="max-width: 10%;width: 10%;text-align: center;">${_('Gross Value')}</th>
                        <th rowspan="2" class="header" style="max-width: 10%;width: 10%;text-align: center;">${_('Salvage Value')}</th>
                        <th colspan="3" style="max-width: 26%;width: 26%;text-align: center;">${_('Depreciation')}</th>
                        <th rowspan="2" class="header" style="max-width: 10%;width: 10%;text-align: center;">${_('Book Value')}</th>
                    </tr>
                    <tr>
                        <th class="header" style="max-width: 10%;width: 10%;text-align: center;">${_('Start')}</th>
                        <th class="header" style="max-width: 10%;width: 10%;text-align: center;">${_('Fiscal Year')}</th>
                        <th class="header" style="max-width: 10%;width: 10%;text-align: center;">${_('End')}</th>
                    </tr>
                %for asset in assets:
                    <%
                        start_value, current_value, end_value, book_value, date_start = depreciation_infos_by_asset_id[asset.id]
                        purchase_soustotal = salvage_soustotal = start_soustotal = current_soustotal = end_soustotal = book_soustotal = 0.0
                        purchase_soustotal += asset.purchase_value
                        salvage_soustotal += asset.salvage_value
                        start_soustotal += depreciation_infos_by_asset_id[asset.id][0]
                        current_soustotal += depreciation_infos_by_asset_id[asset.id][1]
                        end_soustotal += depreciation_infos_by_asset_id[asset.id][2]
                        book_soustotal += depreciation_infos_by_asset_id[asset.id][3]
                    %>
                    <tr>
                        <td style="text-align:left;">${asset.code}</td>
                        <td style="text-align:left;">${get_label(asset)}</td>
                        <td style="text-align:center;">${_(get_value_selection('account.asset.asset', asset.accounting_method, 'accounting_method', context))}</td>
                        <td style="text-align:center;">${date_start}</td>
                        <td style="text-align:center;">${asset.accounting_annuities}</td>
                        <td style="text-align:right;">${('%.2f' % asset.purchase_value).replace('.', ',')}</td>
                        <td style="text-align:right;">${('%.2f' % asset.salvage_value).replace('.', ',')}</td>
                        <td style="text-align:right;">${('%.2f' % start_value).replace('.', ',')}</td>
                        <td style="text-align:right;">${('%.2f' % current_value).replace('.', ',')}</td>
                        <td style="text-align:right;">${('%.2f' % end_value).replace('.', ',')}</td>
                        <td style="text-align:right;">${('%.2f' % book_value).replace('.', ',')}</td>
                    <tr/>
                %endfor
                <%
                    purchase_total += purchase_soustotal
                    salvage_total += salvage_soustotal
                    start_total += start_soustotal
                    current_total += current_soustotal
                    end_total += end_soustotal
                    book_total += book_soustotal
                %>
                    <tr>
                        <td class="footer" style="text-align:left;font-weight:bold;" colspan="5">${_('Sous Total')}</td>
                        <td class="footer" style="text-align:right;font-weight:bold;">${formatLang(purchase_soustotal)}</td>
                        <td class="footer" style="text-align:right;font-weight:bold;">${formatLang(salvage_soustotal)}</td>
                        <td class="footer" style="text-align:right;font-weight:bold;">${formatLang(start_soustotal)}</td>
                        <td class="footer" style="text-align:right;font-weight:bold;">${formatLang(current_soustotal)}</td>
                        <td class="footer" style="text-align:right;font-weight:bold;">${formatLang(end_soustotal)}</td>
                        <td class="footer" style="text-align:right;font-weight:bold;">${formatLang(book_soustotal)}</td>
                    <tr/>
                    %if cpt_total == nb_element_total:
                        <tr>
                            <td colspan="11" height="30" style="border:none;">&nbsp;</td>
                        </tr>
                        <tr>
                            <td class="footer" style="text-align:left;font-weight:bold;border:none;" colspan="5">${_('Total')} ${establishment.split(':')[1]}</td>
                            <td class="footer" style="text-align:right;font-weight:bold;border:none;" >${formatLang(purchase_total)}</td>
                            <td class="footer" style="text-align:right;font-weight:bold;border:none;" width="75px">${formatLang(salvage_total)}</td>
                            <td class="footer" style="text-align:right;font-weight:bold;border:none;" width="69px">${formatLang(start_total)}</td>
                            <td class="footer" style="text-align:right;font-weight:bold;border:none;" width="56px">${formatLang(current_total)}</td>
                            <td class="footer" style="text-align:right;font-weight:bold;border:none;" width="2%">${formatLang(end_total)}</td>
                            <td class="footer" style="text-align:right;font-weight:bold;border:none;" width="5%" >${formatLang(book_total)}</td>
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
                                <td colspan="11" height="30" style="border:none;">&nbsp;</td>
                            </tr>
                            <tr>
                                <td class="footer" style="text-align:left;font-weight:bold;border:none;" colspan="5">${_('Total')} ${_('Company')}</td>
                                <td class="footer" style="text-align:right;font-weight:bold;border:none;" >${formatLang(purchase_company)}</td>
                                <td class="footer" style="text-align:right;font-weight:bold;border:none;" width="75px">${formatLang(salvage_company)}</td>
                                <td class="footer" style="text-align:right;font-weight:bold;border:none;" width="69px">${formatLang(start_company)}</td>
                                <td class="footer" style="text-align:right;font-weight:bold;border:none;" width="56px">${formatLang(current_company)}</td>
                                <td class="footer" style="text-align:right;font-weight:bold;border:none;" width="2%">${formatLang(end_company)}</td>
                                <td class="footer" style="text-align:right;font-weight:bold;border:none;" width="5%" >${formatLang(book_company)}</td>
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
