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
		<h1>${_("Unit Tests")}</h1>
	    <p>${_("This document provides a detailed description of tests.")}</p>
        <%
           module_obj = pool.get('ir.module.module')
           module_ids = [module.id for module in objects]
           tests = sum(module_obj.get_tests(cr, uid, module_ids, context).values(), [])
		%>
	    %for file, path, comments in tests:
	    <h2>${_('Test: %s') % file}</h2>
	    <p>${_('File: %s') % path}</p>
	    <ol>
	        %for comment in comments:
	    	<li>${comment}</li>
	    	%endfor
	    </ol>
	    %endfor
	</body>
</html>
