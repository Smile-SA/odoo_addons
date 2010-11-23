package com.nantic.jasperreports;

import net.sf.jasperreports.engine.JasperCompileManager;
import java.util.*;

public class ReportCompiler {

	public static void compile( String src, String dst )
	{
		try {
			JasperCompileManager.compileReportToFile( src, dst );
		} catch (Exception e){
		  e.printStackTrace();
			System.out.println( e.getMessage() );
		}
	}

	public static void main( String[] args ) 
	{
		if ( args.length == 2 )
			compile( args[0], args[1] );
		else
			System.out.println( "Two arguments needed. Example: java ReportCompiler src.jrxml dst.jasper" );
	}
}

