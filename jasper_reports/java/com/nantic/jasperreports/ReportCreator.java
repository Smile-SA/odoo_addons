package com.nantic.jasperreports;

import net.sf.jasperreports.engine.JasperCompileManager;
import net.sf.jasperreports.engine.JasperFillManager;
import net.sf.jasperreports.engine.JasperExportManager;
import net.sf.jasperreports.engine.JasperReport;
import net.sf.jasperreports.engine.JasperPrint;
import net.sf.jasperreports.engine.util.JRLoader;
import net.sf.jasperreports.engine.data.JRXmlDataSource;
import net.sf.jasperreports.engine.JREmptyDataSource;
import net.sf.jasperreports.engine.util.JRXmlUtils;
import net.sf.jasperreports.engine.query.JRXPathQueryExecuterFactory;
import net.sf.jasperreports.engine.JRQuery;
import net.sf.jasperreports.view.JasperViewer;
import net.sf.jasperreports.engine.util.SimpleFileResolver;
import org.w3c.dom.Document;
import java.sql.*;
import java.util.*;
import java.io.FileInputStream;
import java.util.Locale;

public class ReportCreator {

	static String reportFile;
	static String xmlFile;
	static String outputFile;
	static String locale;
	static String dsn;
	static String user;
	static String password;
	static String params;
	static String standardDirectory;

	public static void createReport()
	{
		try {
			JasperReport report;
			JRQuery query;
			JasperPrint jasperPrint=null;
			String language;
			String[] locales;
			int index;
			
			report = (JasperReport) JRLoader.loadObject( reportFile );
			query = report.getQuery();
			
			Map parameters = parsedParameters();

			index = reportFile.lastIndexOf('/');
			if ( index != -1 )
				parameters.put( "SUBREPORT_DIR", reportFile.substring( 0, index+1 ) );
			parameters.put( "STANDARD_DIR", standardDirectory );
			locales = locale.split( "_" );
			if ( locales.length == 1 )
				parameters.put( "REPORT_LOCALE", new Locale( locales[0] ) );
			else
				parameters.put( "REPORT_LOCALE", new Locale( locales[0], locales[1] ) );

			if ( query == null )
				language = "";
			else
				language = query.getLanguage();

			if( language.equalsIgnoreCase( "XPATH")  ){
				JRXmlDataSource dataSource = new JRXmlDataSource( xmlFile, "/data/record" );
				dataSource.setDatePattern( "yyyy-MM-dd mm:hh:ss" );
				dataSource.setNumberPattern( "#######0.##" );
				dataSource.setLocale( Locale.ENGLISH );
				jasperPrint = JasperFillManager.fillReport( report, parameters, dataSource );
			} else if( language.equalsIgnoreCase( "SQL")  ) {
				Connection con=null;
				try {
					con = getConnection();
					jasperPrint = JasperFillManager.fillReport( report, parameters, con );
				} catch( Exception e ){
					e.printStackTrace();
				}
			} else {
				JREmptyDataSource dataSource = new JREmptyDataSource();
				jasperPrint = JasperFillManager.fillReport( report, parameters, dataSource );
			}
			JasperExportManager.exportReportToPdfFile( jasperPrint, outputFile );
		} catch (Exception e){
			e.printStackTrace();
			System.out.println( e.getMessage() );
		}
	}

	public static Connection getConnection() 
		throws java.lang.ClassNotFoundException, java.sql.SQLException
	{
		Connection connection;
		Class.forName("org.postgresql.Driver");

		connection = DriverManager.getConnection( dsn, user, password );
		connection.setAutoCommit(false);
		return connection;
	}

	public static HashMap parsedParameters(){
		HashMap parameters = new HashMap();
		System.out.println( "Params: " + params );
		String[] p = params.split(";");
		for( int j=0; j < p.length ; j++ ){
			System.out.println( p[j] );
			String[] map = p[j].split(":");
			if ( map.length == 2 ) 
				parameters.put( map[0] , map[1] );
		}
		System.out.println( parameters );
		return parameters;
	}

	public static void main( String[] args ) 
	{
		for( int i=0;i< args.length; i++ )
			System.out.println( "arguments:" + args[i]);

		if ( args.length < 8 ) {
			System.out.println( "Seven arguments needed." );
			return;
		}

		reportFile = args[0];
		xmlFile = args[1];
		outputFile = args[2];
		locale = args[3];
		dsn = args[4];
		user = args[5];
		password = args[6];
		params = args[7];
		standardDirectory = args[8];
		createReport();
	}
}

