package com.nantic.jasperreports;

import java.io.FileInputStream;
import java.util.PropertyResourceBundle;
import java.util.Hashtable;
import java.util.Map;
import java.util.Locale;
import java.util.ResourceBundle;
import java.util.Enumeration;

import org.xnap.commons.i18n.I18n;

public class i18n {
	static Hashtable<Locale, I18n> resources = new Hashtable<Locale, I18n>();
	static String baseName = null;
	static Locale defaultLocale = null;
	static Hashtable<Locale, Boolean> unavailableResources = new Hashtable<Locale, Boolean>();

	public static void init(String baseName, Locale defaultLocale) {
		i18n.baseName = baseName;
		i18n.defaultLocale = defaultLocale;
	}
	/* Ensures the given locale is loaded */
	protected static boolean loadLocale( Locale locale ) {
		// If the resource wasn't available don't try to load it each time.
		if ( baseName == null || locale == null )
			return false;
		if ( unavailableResources.containsKey( locale ) )
			return false;
		if ( ! resources.containsKey( locale ) ) {
			String fileName = baseName + "_" + locale.toString() + ".properties";
			ResourceBundle bundle; 
			try {
				FileInputStream fis = new FileInputStream( fileName );
				bundle = new PropertyResourceBundle(fis);
				resources.put( locale, new I18n( bundle ) );
			} catch (Exception e) {
				e.printStackTrace();
				unavailableResources.put( locale, true );
				System.out.println( "No bundle file named: " + fileName );
				return false;
			}
		}
		return true;
	}
	public static Locale stringToLocale(String localeCode) {
		Locale locale;
		String[] locales = localeCode.split( "_" );
		if ( locales.length == 1 )
			locale = new Locale( locales[0] );
		else if ( locales.length == 2 )
			locale = new Locale( locales[0], locales[1] );
		else
			locale = new Locale( locales[0], locales[1], locales[2] );
		return locale;
	}
	/* tr(Locale..) and tr(Locale..Object) functions */
	public static String tr(Locale locale, String text) {
		if ( ! loadLocale( locale ) )
			return text;
		return resources.get( locale ).tr( text );
	}
	public static String tr(Locale locale, String text, Object o) {
		if ( ! loadLocale( locale ) )
			return text;
		return resources.get( locale ).tr( text, o );
	}
	public static String tr(Locale locale, String text, Object o1, Object o2) {
		if ( ! loadLocale( locale ) )
			return text;
		return resources.get( locale ).tr( text, o1, o2 );
	}
	public static String tr(Locale locale, String text, Object o1, Object o2, Object o3) {
		if ( ! loadLocale( locale ) )
			return text;
		return resources.get( locale ).tr( text, o1, o2, o3 );
	}
	public static String tr(Locale locale, String text, Object o1, Object o2, Object o3, Object o4) {
		if ( ! loadLocale( locale ) )
			return text;
		return resources.get( locale ).tr( text, o1, o2, o3, o4 );
	}
	public static String tr(Locale locale, String text, Object[] objects) {
		if ( ! loadLocale( locale ) )
			return text;
		return resources.get( locale ).tr( text, objects );
	}
	/* trl() and trl(..Object) functions */
	public static String trl(String localeCode, String text) {
		return tr(stringToLocale(localeCode), text);
	}
	public static String trl(String localeCode, String text, Object o) {
		return tr(stringToLocale(localeCode), text, o);
	}
	public static String trl(String localeCode, String text, Object o1, Object o2) {
		return tr(stringToLocale(localeCode), text, o1, o2);
	}
	public static String trl(String localeCode, String text, Object o1, Object o2, Object o3) {
		return tr(stringToLocale(localeCode), text, o1, o2, o3);
	}
	public static String trl(String localeCode, String text, Object o1, Object o2, Object o3, Object o4) {
		return tr(stringToLocale(localeCode), text, o1, o2, o3, o4);
	}
	public static String trl(String localeCode, String text, Object[] objects) {
		return tr(stringToLocale(localeCode), text, objects);
	}
	/* tr(..) and tr(..Object) functions */
	public static String tr(String text) {
		return tr(defaultLocale, text);
	}
	public static String tr(String text, Object o) {
		return tr(defaultLocale, text, o);
	}
	public static String tr(String text, Object o1, Object o2) {
		return tr(defaultLocale, text, o1, o2);
	}
	public static String tr(String text, Object o1, Object o2, Object o3) {
		return tr(defaultLocale, text, o1, o2, o3);
	}
	public static String tr(String text, Object o1, Object o2, Object o3, Object o4) {
		return tr(defaultLocale, text, o1, o2, o3, o4);
	}
	public static String tr(String text, Object[] objects) {
		return tr(defaultLocale, text, objects);
	}
	/* trn(Locale..) and trn(Locale..Object) functions */
	public static String trn(Locale locale, String text, String pluralText, long n) {
		if ( ! loadLocale( locale ) )
			return text;
		return resources.get( locale ).trn( text, pluralText, n );
	}
	public static String trn(Locale locale, String text, String pluralText, long n, Object o) {
		if ( ! loadLocale( locale ) )
			return text;
		return resources.get( locale ).trn( text, pluralText, n, o );
	}
	public static String trn(Locale locale, String text, String pluralText, long n, Object o1, Object o2) {
		if ( ! loadLocale( locale ) )
			return text;
		return resources.get( locale ).trn( text, pluralText, n, o1, o2 );
	}
	public static String trn(Locale locale, String text, String pluralText, long n, Object o1, Object o2, Object o3) {
		if ( ! loadLocale( locale ) )
			return text;
		return resources.get( locale ).trn( text, pluralText, n, o1, o2, o3 );
	}
	public static String trn(Locale locale, String text, String pluralText, long n, Object o1, Object o2, Object o3, Object o4) {
		if ( ! loadLocale( locale ) )
			return text;
		return resources.get( locale ).trn( text, pluralText, n, o1, o2, o3, o4 );
	}
	public static String trn(Locale locale, String text, String pluralText, long n, Object[] objects) {
		if ( ! loadLocale( locale ) )
			return text;
		return resources.get( locale ).trn( text, pluralText, n, objects );
	}
	/* trn(..) and trn(..Object) functions */
	public static String trn(String text, String pluralText, long n) {
		return trn(defaultLocale, text, pluralText, n);
	}
	public static String trn(String text, String pluralText, long n, Object o) {
		return trn(defaultLocale, text, pluralText, n, o);
	}
	public static String trn(String text, String pluralText, long n, Object o1, Object o2) {
		return trn(defaultLocale, text, pluralText, n, o1, o2);
	}
	public static String trn(String text, String pluralText, long n, Object o1, Object o2, Object o3) {
		return trn(defaultLocale, text, pluralText, n, o1, o2, o3);
	}
	public static String trn(String text, String pluralText, long n, Object o1, Object o2, Object o3, Object o4) {
		return trn(defaultLocale, text, pluralText, n, o1, o2, o3, o4);
	}
	public static String trn(String text, String pluralText, long n, Object[] objects) {
		return trn(defaultLocale, text, pluralText, n, objects);
	}
}

