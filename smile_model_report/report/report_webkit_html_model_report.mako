<!DOCTYPE html SYSTEM "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">
<html xmlns="http://www.w3.org/1999/xhtml">
    <head>
	    <meta http-equiv="Content-Type" content="text/html; charset=UTF-8">
	    <style type="text/css">
			body {
			    font-family: helvetica;
			    font-size: 12;
			}
			
			table {
				font-family:Arial, Helvetica, sans-serif;
				color:#666;
				font-size:12px;
				text-shadow: 1px 1px 0px #fff;
				background:#eaebec;
				margin:2px;
				border:#ccc 1px solid;
				border-radius:3px;
			   	box-shadow: 0 1px 2px #d1d1d1;
			        -fs-table-paginate: paginate;
			}
			table th {
				padding:2px 25px 2px 25px;
				border-top:1px solid #fafafa;
				border-bottom:1px solid #e0e0e0;
			
				background: #ededed;
			}
			table th:first-child {
				text-align: left;
				padding-left:20px;
			}
			table tr:first-child th:first-child {
				border-top-left-radius:3px;
			}
			table tr:first-child th:last-child {
				border-top-right-radius:3px;
			}
			table tr {
				text-align: center;
				padding-left:20px;
			}
			table td:first-child {
				text-align: left;
				padding-left:20px;
				border-left: 0;
			}
			table td {
				padding:2px 18px 2px 18px;
				border-top: 1px solid #ffffff;
				border-bottom:1px solid #e0e0e0;
				border-left: 1px solid #e0e0e0;
				text-align: left;
				background: #fafafa;
			}
			table tr.even td {
				background: #f6f6f6;
			}
			table tr:last-child td {
				border-bottom:0;
			}
			table tr:last-child td:first-child {
				border-bottom-left-radius:3px;
			}
			table tr:last-child td:last-child {
				border-bottom-right-radius:3px;
			}
			thead{
				display: table-header-group;
			}
            h1 {
                text-align: center;
                color: #F37021;
            }
            h2 {
                color: #F37021;
            }
		</style>
		<style type="text/css" media="screen,print">
            .break{
                display: block;
                clear: both;
                page-break-after: always;
            }
            thead {
                display: table-header-group;
            }
		</style>
		<title>${_('Objects documentation')}</title>
    </head>
	<body>
	    <% setLang(lang) %>
		<h1>${_("Objects documentation")}</h1>
	    <p>${_("This document provides a detailed description of object attributes.")}</p>
		<h2>${_('Summary')}</h2>
	    %for model in objects:
	    <ul>
	      <li><a href="${model.name}">${model.name}</a></li>
        </ul>
        %endfor
	    %for model in objects:
	    %if not model.osv_memory:
        <div class="break"></div>
	    <h2><a id="${model.name}">${_('Object name :') + ' %s' % model.name}</a></h2>
	    <p>${_('File :') +  ' %s.csv' % model.model}</p>
	    <p>${model.info or ''}</p>
	    <table>
	      <thead>
	      	<tr>
	      		<th>${_("Name")}</th>
	      		<th>${_("Description")}</th>
	      		<th>${_("Type")}</th>
	      		<th>${_("Required")}</th>
	      		<th>${_("Additional information")}</th>
	      	</tr>
	      </thead>
	      <tbody>
	        <tr>
		        <td>id</td>
	            <td>${_("External ID")}</td>
	            <td>char</td>
	            <td><center>${_("True")}</center></td>
		        <td>${'%s 128' % _("Size:")}</td>
		    </tr>
	        %for field in model.field_id:
	        %if field.display_in_report and pool.get(model.model)._columns.get(field.name):
	        <%
	           model_obj = pool.get(model.model)
	           data = model_obj._columns[field.name]
	           other_info = ''
	           if field.ttype == 'char':
	             other_info = u'%s %s' % (_('Size:'), data.size)
	           elif field.ttype == 'selection' and data.selection:
	             selection = data.selection
	             if hasattr(data.selection, '__call__'):
	               selection = data.selection(model, cr, uid, None)
	             selection = ", ".join(["%s (%s)" % (k, translate(cr, uid, model_obj, field.name, 'selection', lang, v)) for k, v in selection])
	             selection = selection or ""
	             other_info = u'%s %s' % (_('Selection:'), selection)
	           elif '2one' in field.ttype:
	             relation_label = translate(cr, uid, model, 'name', 'model', lang, pool.get(field.relation)._description)
	             other_info = u'%s %s' % (_('Relation:'), '%s (%s)' % (relation_label, field.relation))
	           elif '2many' in field.ttype:
	             relation_label = translate(cr, uid, model, 'name', 'model', lang, pool.get(field.relation)._description)
	             other_info = u'%s %s' % (_('Relations list (comma-separated):'), '%s (%s)' % (relation_label, field.relation))
	           elif field.ttype == 'boolean':
	             other_info = _('Available values: 0 or 1')
		    %>
	        <tr>
		        <td>${'2' in field.ttype and '%s:id' % field.name or field.name}</td>
	            <td>${translate(cr, uid, model_obj, field.name, 'field', lang) or field.field_description}</td>
	            <td>${field.ttype}</td>
	            <td><center>${_(str(field.required))}</center></td>
		        <td>${field.info or ''}${other_info or ''}</td>
		    </tr>
	        %endif
	        %endfor
	      </tbody>
	    </table>
	    %endif
	    %endfor
	</body>
</html>
