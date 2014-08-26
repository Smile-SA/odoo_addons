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
        <h1 class="center">Amortissement des voitures particulières</h1>
        <br />
	    <% setLang(lang) %>
        %if objects:
        <% assets = filter(lambda asset: not asset.parent_id or asset.parent_id not in objects, objects) %>
	    <% depreciation_infos_by_asset_id = get_depreciation_infos_by_asset_id(assets, company) %>
        <% purchase_company = year_company = accumulated_company = non_ded_year_company = non_ded_accumulated_company = book_company = 0.0 %>
        <% nb_element_company, group_establishment = group_by_establishment(assets) %>
        <% cpt_company = 0 %>
        %for establishment, assets in group_establishment:
            <h2>${establishment}</h2>
            <%
              cpt_company += 1
              purchase_total = year_total = accumulated_total = non_ded_year_total = non_ded_accumulated_total = book_total = 0.0
              nb_element_total, group_asset = group_by(assets)
              cpt_total = 0
            %>
            %for group, assets_category in group_asset:
                <h2>${group}</h2>
                <%
                    cpt_total += 1
                    purchase_service = year_service = accumulated_service = non_ded_year_service = non_ded_accumulated_service = book_service = 0.0
                    nb_element_service, group_service = group_by_service(assets_category)
                    cpt_service = 0
                %>
                %for service, assets in group_service:
                    <% cpt_service +=1 %>
                    <h3>${service}</h3>
                    <table class="table_asset" width="100%">
                        <tr>
                            <th class="header" style="max-width: 10%;width: 10%;">${_('Reference')}</th>
                            <th class="header" style="max-width: 30%;width: 30%;">${label_header}</th>
                            <th class="header" style="max-width: 10%;width: 10%;text-align: center;">${_('CO2 Rate')}</th>
                            <th class="header" style="max-width: 10%;width: 10%;text-align: center;">${_('Value results')}</th>
                            <th class="header" style="max-width: 10%;width: 10%;text-align: center;">${_('Gross Value')}</th>
                            <th class="header" style="max-width: 10%;width: 10%;text-align: center;">${_('Yearly Depreciation')}<br/><i>${_('Non Ded. Part')}</i></th>
                            <th class="header" style="max-width: 10%;width: 10%;text-align: center;">${_('Accumulated Depreciation')}<br/><i>${_('Non Ded. Part')}</i></th>
                            <th class="header" style="max-width: 10%;width: 10%;text-align: center;">${_('Book Value')}</th>
                        </tr>
                    %for asset in assets:
                        <%
                            year_value, accumulated_value, non_ded_year_value, non_ded_accumulated_value, book_value, purchase_value = depreciation_infos_by_asset_id[asset.id]
                        %>
                        <tr>
                            <td style="text-align:left;">${asset.code}</td>
                            <td style="text-align:left;">${get_label(asset)}</td>
                            <td style="text-align:center;">${('%.2f' % asset.co2_rate).replace('.', ',')}</td>
                            <td style="text-align:right;">${('%.2f' % float(book_value  - year_value)).replace('.', ',')}</td>
                            <td style="text-align:right;">${('%.2f' % purchase_value).replace('.', ',')}</td>
                            <td style="text-align:right;">${('%.2f' % year_value).replace('.', ',')}<br/><i>${('%.2f' % non_ded_year_value).replace('.', ',')}</i></td>
                            <td style="text-align:right;">${('%.2f' % accumulated_value).replace('.', ',')}<br/><i>${('%.2f' % non_ded_accumulated_value).replace('.', ',')}</i></td>
                            <td style="text-align:right;">${('%.2f' % book_value).replace('.', ',')}</td>
                        <tr/>
                    %endfor
                        <%
                            purchase_soustotal = year_soustotal = accumulated_soustotal = non_ded_year_soustotal = non_ded_accumulated_soustotal = book_soustotal = 0.0
                            for asset in assets:
                                purchase_soustotal += depreciation_infos_by_asset_id[asset.id][-1]
                                year_soustotal += depreciation_infos_by_asset_id[asset.id][0]
                                accumulated_soustotal += depreciation_infos_by_asset_id[asset.id][1]
                                non_ded_year_soustotal += depreciation_infos_by_asset_id[asset.id][2]
                                non_ded_accumulated_soustotal += depreciation_infos_by_asset_id[asset.id][3]
                                book_soustotal += depreciation_infos_by_asset_id[asset.id][4]
                            purchase_service += purchase_soustotal
                            year_service += year_soustotal
                            accumulated_service += accumulated_soustotal
                            non_ded_year_service += non_ded_year_soustotal
                            non_ded_accumulated_service += non_ded_accumulated_soustotal
                            book_service += book_soustotal
                        %>
                        <tr>
                            <td class="footer" style="text-align:left;font-weight:bold;" colspan="4">${_('Sous Total')}</td>
                            <td class="footer" style="text-align:right;font-weight:bold;">${formatLang(purchase_soustotal)}</td>
                            <td class="footer" style="text-align:right;font-weight:bold;">${formatLang(year_soustotal)}<br/><i>${formatLang(non_ded_year_soustotal)}</i></td>
                            <td class="footer" style="text-align:right;font-weight:bold;">${formatLang(accumulated_soustotal)}<br/><i>${formatLang(non_ded_accumulated_soustotal)}</i></td>
                            <td class="footer" style="text-align:right;font-weight:bold;">${formatLang(book_soustotal)}</td>
                        <tr/>
                        %if cpt_service == nb_element_service:
                            <tr>
                                <td colspan="11" height="30" style="border:none;">&nbsp;</td>
                            </tr>
                            <tr>
                                <td class="footer" style="text-align:left;font-weight:bold;border:none;" colspan="4">${_('Total')} </td>
                                <td class="footer" style="text-align:right;font-weight:bold;border:none;">${formatLang(purchase_service)}</td>
                                <td class="footer" style="text-align:right;font-weight:bold;border:none;">${formatLang(year_service)}<br/><i>${formatLang(non_ded_year_service)}</i></td>
                                <td class="footer" style="text-align:right;font-weight:bold;border:none;">${formatLang(accumulated_service)}<br/><i>${formatLang(non_ded_accumulated_service)}</i></td>
                                <td class="footer" style="text-align:right;font-weight:bold;border:none;">${formatLang(book_service)}</td>
                            <tr/>
                            <%
                                purchase_total += purchase_service
                                year_total += year_service
                                accumulated_total += accumulated_service
                                non_ded_year_total += non_ded_year_service
                                non_ded_accumulated_total += non_ded_accumulated_service
                                book_total += book_service
                            %>
                            %if cpt_total == nb_element_total:
                                <tr>
                                    <td colspan="11" height="30" style="border:none;">&nbsp;</td>
                                </tr>
                                <tr>
                                    <td class="footer" style="text-align:left;font-weight:bold;border:none;" colspan="4">${_('Total')} ${establishment.split(':')[1]}</td>
                                    <td class="footer" style="text-align:right;font-weight:bold;border:none;">${formatLang(purchase_total)}</td>
                                    <td class="footer" style="text-align:right;font-weight:bold;border:none;">${formatLang(year_total)}<br/><i>${formatLang(non_ded_year_total)}</i></td>
                                    <td class="footer" style="text-align:right;font-weight:bold;border:none;">${formatLang(accumulated_total)}<br/><i>${formatLang(non_ded_accumulated_total)}</i></td>
                                    <td class="footer" style="text-align:right;font-weight:bold;border:none;">${formatLang(book_total)}</td>
                                <tr/>
                                <%
                                    purchase_company += purchase_total
                                    year_company += year_total
                                    accumulated_company += accumulated_total
                                    non_ded_year_company += non_ded_year_total
                                    non_ded_accumulated_company += non_ded_accumulated_total
                                    book_company += book_total
                                %>
                                %if cpt_company == nb_element_company:
                                    <tr>
                                        <td colspan="11" height="30" style="border:none;">&nbsp;</td>
                                    </tr>
                                    <tr>
                                        <td class="footer" style="text-align:left;font-weight:bold;border:none;" colspan="4">${_('Total')} ${_('Company')}</td>
                                        <td class="footer" style="text-align:right;font-weight:bold;border:none;">${formatLang(purchase_company)}</td>
                                        <td class="footer" style="text-align:right;font-weight:bold;border:none;">${formatLang(year_company)}<br/><i>${formatLang(non_ded_year_company)}</i></td>
                                        <td class="footer" style="text-align:right;font-weight:bold;border:none;">${formatLang(accumulated_company)}<br/><i>${formatLang(non_ded_accumulated_company)}</i></td>
                                        <td class="footer" style="text-align:right;font-weight:bold;border:none;">${formatLang(book_company)}</td>
                                    <tr/>
                                %endif
                            %endif
                        %endif
                    </table>
                %endfor
            %endfor
        %endfor
        %endif
	</body>
</html>
