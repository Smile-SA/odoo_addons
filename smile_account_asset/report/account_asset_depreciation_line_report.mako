<!DOCTYPE html SYSTEM "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">
<html xmlns="http://www.w3.org/1999/xhtml">
    <head>
	    <meta http-equiv="Content-Type" content="text/html; charset=UTF-8">
	    <style type="text/css">${css}</style>
		<title>${_('Account Asset Depreciation Lines')}</title>
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
        <h1 class="center">Situation des dotations</h1>
        <br />
	    <% setLang(lang) %>
        <%
          purchase_company = accounting_period_company = fiscal_period_company = accounting_yearcompany = accounting_company = fiscal_company = 0.0
          depreciation_infos_by_asset_id = get_depreciation_infos_by_asset_id(objects, company)
          nb_element_company, group_establishment = group_by_establishment(objects)
          cpt_company = 0
        %>

        %if objects:
        %for establishment, assets in group_establishment:
            <h2>${establishment}</h2>

            <%
                purchase_total = accounting_period_total = fiscal_period_total = accounting_yeartotal = accounting_total = fiscal_total = 0.0
                cpt_company += 1
                nb_element_total, group_asset = group_by(assets)
                cpt_total = 0
            %>
            %for group, assets in group_asset:
                <%
                    cpt_total +=1
                %>
                <h2>${group}</h2>
                <table class="table_asset" width="100%">
                    <tr>
                        <th rowspan="2" class="header" style="max-width: 10%;width: 10%;">${_('Reference')}</th>
                        <th rowspan="2" class="header" style="max-width: 20%;width: 20%;">${label_header}</th>
                        <th rowspan="2" class="header" style="max-width: 10%;width: 10%;text-align: center;">${_('Gross Value')}</th>
                        <th colspan="2" style="max-width: 40%;width: 40%;text-align: center;">${_('Period Depreciation')}</th>
                        <th rowspan="2" class="header" style="max-width: 10%;width: 10%;text-align: center;">${_('Year Depreciation')}</th>
                        <th colspan="2" style="max-width: 40%;width: 40%;text-align: center;">${_('Accumulated Depreciation')}</th>
                    </tr>
                    <tr>
                        <th class="header" style="max-width: 10%;width: 10%;text-align: center;">${_('Accounting')}</th>
                        <th class="header" style="max-width: 10%;width: 10%;text-align: center;">${_('Fiscal')}</th>
                        <th class="header" style="max-width: 10%;width: 10%;text-align: center;">${_('Accounting')}</th>
                        <th class="header" style="max-width: 10%;width: 10%;text-align: center;">${_('Fiscal')}</th>
                    </tr>
                <%
                    purchase_soustotal = accounting_period_soustotal = fiscal_period_soustotal = accounting_yearsoustotal = accounting_soustotal = fiscal_soustotal = 0.0
                %>
                %for asset in assets:
                    <%
                        depr_info = depreciation_infos_by_asset_id[asset.id]
                        purchase_soustotal += asset.purchase_value
                        accounting_period_soustotal += depr_info['accounting_period']
                        fiscal_period_soustotal += depr_info['fiscal_period']
                        accounting_yearsoustotal += max(depr_info['accounting_year'], depr_info['fiscal_year'])
                        accounting_soustotal += depr_info['accounting_total']
                        fiscal_soustotal += depr_info['fiscal_total']

                    %>
                    <tr>
                        <td style="text-align:left;">${asset.code}</td>
                        <td style="text-align:left;">${get_label(asset)}</td>
                        <td style="text-align:right;">${('%.2f' % asset.purchase_value).replace('.', ',')}</td>
                        <td style="text-align:right;">${('%.2f' % depr_info['accounting_period']).replace('.', ',')}</td>
                        <td style="text-align:right;">${('%.2f' % depr_info['fiscal_period']).replace('.', ',')}</td>
                        <td style="text-align:right;">${('%.2f' % max(depr_info['accounting_year'], depr_info['fiscal_year'])).replace('.', ',')}</td>
                        <td style="text-align:right;">${('%.2f' % depr_info['accounting_total']).replace('.', ',')}</td>
                        <td style="text-align:right;">${('%.2f' % depr_info['fiscal_total']).replace('.', ',')}</td>
                    <tr/>

                %endfor
                <tr>
                    <td style="text-align:left;font-weight:bold;">${_('Sous Total')}</td>
                    <td style="text-align:left;font-weight:bold;"></td>
                    <td style="text-align:right;font-weight:bold;">${purchase_soustotal}</td>
                    <td style="text-align:right;font-weight:bold;">${accounting_period_soustotal}</td>
                    <td style="text-align:right;font-weight:bold;">${fiscal_period_soustotal}</td>
                    <td style="text-align:right;font-weight:bold;">${accounting_yearsoustotal}</td>
                    <td style="text-align:right;font-weight:bold;">${accounting_soustotal}</td>
                    <td style="text-align:right;font-weight:bold;">${fiscal_soustotal}</td>
                <tr/>
                <%
                    purchase_total += purchase_soustotal
                    accounting_period_total += accounting_period_soustotal
                    fiscal_period_total += fiscal_soustotal
                    accounting_yeartotal += accounting_yearsoustotal
                    accounting_total += accounting_soustotal
                    fiscal_total += fiscal_soustotal
                %>
                %if cpt_total == nb_element_total:
                    <br />
                    <tr>
                        <td colspan="8" height="30" style="border:none;">&nbsp;</td>
                    </tr>
                    <tr>
                        <td colspan="2" style="text-align:left;font-weight:bold;border:none;">${_('Total')} ${establishment.split(':')[1]}</td>
                        <td style="text-align:right;font-weight:bold;border:none;">${purchase_total}</td>
                        <td style="text-align:right;font-weight:bold;border:none;">${accounting_period_total}</td>
                        <td style="text-align:right;font-weight:bold;border:none;">${fiscal_period_total}</td>
                        <td style="text-align:right;font-weight:bold;border:none;">${accounting_yeartotal}</td>
                        <td style="text-align:right;font-weight:bold;border:none;">${accounting_total}</td>
                        <td style="text-align:right;font-weight:bold;border:none;">${fiscal_total}</td>
                    <tr/>
                    <%
                        purchase_company += purchase_total
                        accounting_period_company += accounting_period_total
                        fiscal_period_company += fiscal_total
                        accounting_yearcompany += accounting_yeartotal
                        accounting_company += accounting_total
                        fiscal_company += fiscal_total
                    %>

                    %if cpt_company == nb_element_company:
                        <br />
                        <tr>
                            <td colspan="8" height="30" style="border:none;">&nbsp;</td>
                        </tr>
                        <tr>
                            <td colspan="2" style="text-align:left;font-weight:bold;border:none;">${_('Total')} ${_('Company')}</td>
                            <td style="text-align:right;font-weight:bold;border:none;">${purchase_company}</td>
                            <td style="text-align:right;font-weight:bold;border:none;">${accounting_period_company}</td>
                            <td style="text-align:right;font-weight:bold;border:none;">${fiscal_period_company}</td>
                            <td style="text-align:right;font-weight:bold;border:none;">${accounting_yearcompany}</td>
                            <td style="text-align:right;font-weight:bold;border:none;">${accounting_company}</td>
                            <td style="text-align:right;font-weight:bold;border:none;">${fiscal_company}</td>
                        <tr/>
                    %endif
                %endif
                </table>
            %endfor

        %endfor
        %endif
	</body>
</html>
