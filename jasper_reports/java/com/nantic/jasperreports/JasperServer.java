package com.nantic.jasperreports;

import org.apache.xmlrpc.server.XmlRpcServer;
import org.apache.xmlrpc.webserver.WebServer;
//import org.apache.xmlrpc.webserver.*;
import org.apache.xmlrpc.*;
import org.apache.xmlrpc.server.PropertyHandlerMapping;
//import org.apache.xml.security.utils.Base64;

import net.sf.jasperreports.engine.JRRewindableDataSource;
import net.sf.jasperreports.engine.JRException;
import net.sf.jasperreports.engine.JRField;
import net.sf.jasperreports.engine.design.JRDesignField;
import net.sf.jasperreports.engine.util.JRLoader;
import net.sf.jasperreports.engine.JasperFillManager; 
import net.sf.jasperreports.engine.JasperExportManager;
import net.sf.jasperreports.engine.JasperCompileManager;
import net.sf.jasperreports.engine.JasperReport;
import net.sf.jasperreports.engine.JasperPrint;
import net.sf.jasperreports.engine.JRParameter;
import net.sf.jasperreports.engine.xml.JRXmlLoader;
import net.sf.jasperreports.engine.design.JasperDesign;
import net.sf.jasperreports.engine.data.JRXmlDataSource;
import net.sf.jasperreports.engine.data.JRCsvDataSource;
import net.sf.jasperreports.engine.JREmptyDataSource;

// Exporters
import net.sf.jasperreports.engine.JRAbstractExporter;
import net.sf.jasperreports.engine.JRExporterParameter;
import net.sf.jasperreports.engine.export.JRPdfExporter;
import net.sf.jasperreports.engine.export.JRRtfExporter;
import net.sf.jasperreports.engine.export.JRCsvExporter;
import net.sf.jasperreports.engine.export.JRXlsExporter;
import net.sf.jasperreports.engine.export.JRTextExporter;
import net.sf.jasperreports.engine.export.JRTextExporterParameter;
import net.sf.jasperreports.engine.export.JRHtmlExporter;
import net.sf.jasperreports.engine.export.JRHtmlExporterParameter;
import net.sf.jasperreports.engine.export.oasis.JROdtExporter;
import net.sf.jasperreports.engine.export.oasis.JROdsExporter;

import java.text.NumberFormat;
import java.lang.Object;
import java.util.Date;
import java.util.Iterator;
import java.util.List;
import java.util.Map;
import java.util.HashMap;
import java.util.Hashtable;
import java.util.ResourceBundle;
import java.text.SimpleDateFormat;
import java.util.Hashtable;
import java.io.ByteArrayInputStream;
import java.io.*;
import java.sql.*;
import java.lang.Class;
import java.math.BigDecimal;
import java.io.InputStream;
import java.util.Locale;



/*
This class overrides Hashtable's get() function to return 
the default language when the language (key) doesn't exist.
*/
class LanguageTable extends Hashtable {
	private String defaultLanguage;

	public LanguageTable(String defaultLanguage) {
		super();
		this.defaultLanguage = defaultLanguage;
	}
	public Object get(Object key) {
		if ( containsKey(key) )
			return super.get(key);
		else
			return super.get(defaultLanguage);
	}
}

/*
This class overrides getFieldValue() from JRCsvDataSource to parse
java.lang.Object fields that will come from Python coded with data
for each language.
*/
class CsvMultiLanguageDataSource implements JRRewindableDataSource {
	private JRCsvDataSource csvDataSource;
	private String fileName;
	private String charsetName;
	private java.text.DateFormat dateFormat;
	private char fieldDelimiter;
	private java.text.NumberFormat numberFormat;
	private String recordDelimiter;
	private String[] columnNames;
	private boolean useFirstRowAsHeader;

	public CsvMultiLanguageDataSource(String fileName, String charsetName) throws java.io.FileNotFoundException, java.io.UnsupportedEncodingException {

		this.fileName = fileName;
		this.charsetName = charsetName;
		csvDataSource = new JRCsvDataSource( new File( fileName ), "utf-8");
		csvDataSource.setUseFirstRowAsHeader( true );
		csvDataSource.setDateFormat( new SimpleDateFormat( "yyyy-MM-dd HH:mm:ss" ) );
		csvDataSource.setNumberFormat( NumberFormat.getInstance( Locale.ENGLISH ) );
	}
	public void moveFirst() throws JRException {
		csvDataSource.close();
		try {
			csvDataSource = new JRCsvDataSource( new File( fileName ), "utf-8" );
			csvDataSource.setUseFirstRowAsHeader( true );
			csvDataSource.setDateFormat( new SimpleDateFormat( "yyyy-MM-dd HH:mm:ss" ) );
			csvDataSource.setNumberFormat( NumberFormat.getInstance( Locale.ENGLISH ) );
		} catch ( Exception exception ) {
			throw new JRException( exception );
		}
	}

	public Object getFieldValue(JRField jrField) throws JRException {
		Object value;
		if ( jrField.getValueClassName().equals( "java.lang.Object" ) ) {
			JRDesignField fakeField = new JRDesignField();
			fakeField.setName( jrField.getName() );
			fakeField.setDescription( jrField.getDescription() );
			fakeField.setValueClassName( "java.lang.String" );
			fakeField.setValueClass( String.class );
			value = csvDataSource.getFieldValue( fakeField );

			LanguageTable values = new LanguageTable("en_US");
			String v = (String) value;
			String[] p = v.split( "\\|" );
			for( int j=0; j < p.length ; j++ ) {
				System.out.println( p[j] );
				String[] map = p[j].split( "~" );
				if ( map.length == 2 ) 
					values.put( map[0], map[1] );
			}
			value = (Object)values;
		} else {
			value = csvDataSource.getFieldValue(jrField);
		}
		return value;
	}
	public void close() {
		csvDataSource.close();
	}
	public boolean next() throws JRException {
		return csvDataSource.next();
	}
	
}

/*
This class overrides getFieldValue() from JRXmlDataSource to parse
java.lang.Object fields that will come from Python coded with data
for each language.
*/
class XmlMultiLanguageDataSource extends JRXmlDataSource {
	public XmlMultiLanguageDataSource(String uri, String selectExpression) throws JRException {
		super(uri, selectExpression);
	}

	public Object getFieldValue(JRField jrField) throws JRException {
		Object value;
		if ( jrField.getValueClassName().equals( "java.lang.Object" ) ) {
			JRDesignField fakeField = new JRDesignField();
			fakeField.setName( jrField.getName() );
			fakeField.setDescription( jrField.getDescription() );
			fakeField.setValueClassName( "java.lang.String" );
			fakeField.setValueClass( String.class );
			value = super.getFieldValue( fakeField );

			LanguageTable values = new LanguageTable("en_US");
			String v = (String) value;
			String[] p = v.split( "\\|" );
			for( int j=0; j < p.length ; j++ ) {
				System.out.println( p[j] );
				String[] map = p[j].split( "~" );
				if ( map.length == 2 ) 
					values.put( map[0], map[1] );
			}
			value = (Object)values;
		} else {
			value = super.getFieldValue(jrField);
		}
		return value;
	}
}

public class JasperServer { 

	/* Compiles the given .jrxml (inputFile) */
	public Boolean compile( String jrxmlPath ) throws java.lang.Exception {
		File jrxmlFile;
		File jasperFile;

		System.setProperty("jasper.reports.compiler.class", "com.nantic.jasperreports.I18nGroovyCompiler");

		jrxmlFile = new File( jrxmlPath );
		jasperFile = new File( jasperPath( jrxmlPath ) );
		if ( (! jasperFile.exists()) || (jrxmlFile.lastModified() > jasperFile.lastModified()) ) {
			System.out.println( "Before compiling..") ;
			JasperCompileManager.compileReportToFile( jrxmlPath, jasperPath( jrxmlPath ) );
			System.out.println( "compiled...!");
		}
		return true;
	}

	/* Returns path where bundle files are expected to be */
	public String bundlePath( String jrxmlPath ) {
		int index;
		index = jrxmlPath.lastIndexOf('.');
		if ( index != -1 )
			return jrxmlPath.substring( 0, index );
		else
			return jrxmlPath;
	}

	/* Returns the path to the .jasper file for the given .jrxml */
	public String jasperPath( String jrxmlPath ) {
		return bundlePath( jrxmlPath ) + ".jasper";
	}

	public Boolean execute( Hashtable connectionParameters, String jrxmlPath, String outputPath, Hashtable parameters) throws java.lang.Exception {
		try {
			return privateExecute( connectionParameters, jrxmlPath, outputPath, parameters );
		} catch (Exception exception) {
			exception.printStackTrace();
			throw exception;
		}
	}

	public Boolean privateExecute( Hashtable connectionParameters, String jrxmlPath, String outputPath, Hashtable parameters) throws java.lang.Exception {

		JasperReport report = null;
		byte[] result = null;
		JasperPrint jasperPrint = null;
		InputStream in = null;
		int index;

		// Ensure report is compiled
		compile( jrxmlPath );

		System.out.println( parameters );

		report = (JasperReport) JRLoader.loadObject( jasperPath( jrxmlPath ) );

		// Add SUBREPORT_DIR parameter
		index = jrxmlPath.lastIndexOf('/');
		if ( index != -1 )
			parameters.put( "SUBREPORT_DIR", jrxmlPath.substring( 0, index+1 ) );

		// Fill in report parameters
		JRParameter[] reportParameters = report.getParameters();
		System.out.println( "Parameters.length:"+ reportParameters.length );
		for( int j=0; j < reportParameters.length; j++ ){
			JRParameter jparam = reportParameters[j];	
			if ( jparam.getValueClassName().equals( "java.util.Locale" ) ) {
				// REPORT_LOCALE
				if ( ! parameters.containsKey( jparam.getName() ) )
					continue;
				String[] locales = ((String)parameters.get( jparam.getName() )).split( "_" );
				Locale locale;
				
				if ( locales.length == 1 )
					locale = new Locale( locales[0] );
				else
					locale = new Locale( locales[0], locales[1] );
				parameters.put( jparam.getName(), locale );

				// Initialize translation system
				i18n.init( bundlePath(jrxmlPath), locale );

			} else if( jparam.getValueClassName().equals( "java.lang.BigDecimal" )){
				Object param = parameters.get( jparam.getName());
				System.out.println( "1" + jparam.getValueClassName() ) ;
				parameters.put( jparam.getName(), new BigDecimal( (Double) parameters.get(jparam.getName() ) ) );
				System.out.println( "2" + jparam.getValueClassName() ) ;
			}
		}

		if ( connectionParameters.containsKey("subreports") ) {
			Object[] subreports = (Object[]) connectionParameters.get("subreports");
			for (int i = 0; i < subreports.length; i++ ) {
				Map m = (Map)subreports[i];

				// Ensure subreport is compiled
				compile( (String)m.get("jrxmlFile") );

				// Create DataSource for subreport
				CsvMultiLanguageDataSource dataSource = new CsvMultiLanguageDataSource( (String)m.get("dataFile"), "utf-8" );
				System.out.println( "ADDING PARAMETER: " + ( (String)m.get("parameter") ) + " WITH DATASOURCE: " + ( (String)m.get("dataFile") ) );

				parameters.put( m.get("parameter"), dataSource );
			}
		}

		System.out.println( "Before Filling report " );

		// Fill in report
		String language;
		if ( report.getQuery() == null )
			language = "";
		else
			language = report.getQuery().getLanguage();

		if( language.equalsIgnoreCase( "XPATH")  ){
			// If available, use a CSV file because it's faster to process.
			// Otherwise we'll use an XML file.
			if ( connectionParameters.containsKey("csv") ) {
				CsvMultiLanguageDataSource dataSource = new CsvMultiLanguageDataSource( (String)connectionParameters.get("csv"), "utf-8" );
				jasperPrint = JasperFillManager.fillReport( report, parameters, dataSource );
			} else {
				JRXmlDataSource dataSource = new JRXmlDataSource( (String)connectionParameters.get("xml"), "/data/record" );
				dataSource.setDatePattern( "yyyy-MM-dd HH:mm:ss" );
				dataSource.setNumberPattern( "#######0.##" );
				dataSource.setLocale( Locale.ENGLISH );
				jasperPrint = JasperFillManager.fillReport( report, parameters, dataSource );
			}
		} else if( language.equalsIgnoreCase( "SQL")  ) {
			Connection connection = getConnection( connectionParameters );
			jasperPrint = JasperFillManager.fillReport( report, parameters, connection );
		} else {
			JREmptyDataSource dataSource = new JREmptyDataSource();
			jasperPrint = JasperFillManager.fillReport( report, parameters, dataSource );
		}

		// Create output file
		File outputFile = new File( outputPath );
		JRAbstractExporter exporter;

		String output;
		if ( connectionParameters.containsKey( "output" ) )
			output = (String)connectionParameters.get("output");
		else
			output = "pdf";

		System.out.println( "EXPORTING..." );
		if ( output.equalsIgnoreCase( "html" ) ) {
			exporter = new JRHtmlExporter();
			exporter.setParameter(JRHtmlExporterParameter.IS_USING_IMAGES_TO_ALIGN, Boolean.FALSE);
			exporter.setParameter(JRHtmlExporterParameter.HTML_HEADER, "");
			exporter.setParameter(JRHtmlExporterParameter.BETWEEN_PAGES_HTML, "");
			exporter.setParameter(JRHtmlExporterParameter.IS_REMOVE_EMPTY_SPACE_BETWEEN_ROWS, Boolean.TRUE);
			exporter.setParameter(JRHtmlExporterParameter.HTML_FOOTER, "");
		} else if ( output.equalsIgnoreCase( "csv" ) ) {
			exporter = new JRCsvExporter();
		} else if ( output.equalsIgnoreCase( "xls" ) ) {
			exporter = new JRXlsExporter();
		} else if ( output.equalsIgnoreCase( "rtf" ) ) {
			exporter = new JRRtfExporter();
		} else if ( output.equalsIgnoreCase( "odt" ) ) {
			exporter = new JROdtExporter();
		} else if ( output.equalsIgnoreCase( "ods" ) ) {
			exporter = new JROdsExporter();
		} else if ( output.equalsIgnoreCase( "txt" ) ) {
			exporter = new JRTextExporter();
			exporter.setParameter(JRTextExporterParameter.PAGE_WIDTH, new Integer(80));
			exporter.setParameter(JRTextExporterParameter.PAGE_HEIGHT, new Integer(150));
		} else {
			exporter = new JRPdfExporter();
		}
		exporter.setParameter(JRExporterParameter.JASPER_PRINT, jasperPrint);
		exporter.setParameter(JRExporterParameter.OUTPUT_FILE, outputFile);
		exporter.exportReport();
		System.out.println( "EXPORTED." );
		return true; 
	}

	public static Connection getConnection( Hashtable datasource ) throws java.lang.ClassNotFoundException, java.sql.SQLException { 
		Connection connection; 
		Class.forName("org.postgresql.Driver"); 
		connection = DriverManager.getConnection( (String)datasource.get("dsn"), (String)datasource.get("user"), 
		(String)datasource.get("password") ); 
		connection.setAutoCommit(true); 
		return connection; 
	}

	public static void main (String [] args) {
		try {
			int port = 8090;
			if ( args.length > 0 ) {
				port = java.lang.Integer.parseInt( args[0] );
			}
			java.net.InetAddress localhost = java.net.Inet4Address.getByName("localhost");
			System.out.println("Attempting to start XML-RPC Server at " + localhost.toString() + ":" + port + "...");
			WebServer server = new WebServer( port, localhost );
			XmlRpcServer xmlRpcServer = server.getXmlRpcServer();

			PropertyHandlerMapping phm = new PropertyHandlerMapping();
			phm.addHandler("Report", JasperServer.class);
			xmlRpcServer.setHandlerMapping(phm);

			server.start();
			System.out.println("Started successfully.");
			System.out.println("Accepting requests. (Halt program to stop.)");
		} catch (Exception exception) {
			System.err.println("Jasper Server: " + exception);
		}
	}
}
