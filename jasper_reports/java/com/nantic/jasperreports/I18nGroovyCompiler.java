package com.nantic.jasperreports;

import net.sf.jasperreports.engine.JRDefaultScriptlet;
import net.sf.jasperreports.engine.design.JRCompilationUnit;
import net.sf.jasperreports.compilers.JRGroovyCompiler;
import net.sf.jasperreports.engine.JRException;
import net.sf.jasperreports.engine.design.JRSourceCompileTask;
import net.sf.jasperreports.engine.design.JRCompilationSourceCode;
import net.sf.jasperreports.engine.JRExpression;
import net.sf.jasperreports.engine.design.JRDefaultCompilationSourceCode;
import net.sf.jasperreports.engine.design.JRDesignExpression;
import net.sf.jasperreports.engine.JRExpressionChunk;
import net.sf.jasperreports.engine.design.JRDesignExpressionChunk;
import net.sf.jasperreports.engine.JRReport;

import java.util.ArrayList;

public class I18nGroovyCompiler extends JRGroovyCompiler {
	static public String lastGeneratedSourceCode = "";
	static private String newFunction = 
		"public String tr(Locale locale, String text) {\n" +
			"return i18n.tr(locale, text);\n" +
		"}\n" +
		"public String tr(Locale locale, String text, Object o) {\n" +
			"return i18n.tr(locale, text, o);\n" +
		"}\n" +
		"public String tr(Locale locale, String text, Object o1, Object o2) {\n" +
			"return i18n.tr(locale, text, o1, o2);\n" +
		"}\n" +
		"public String tr(Locale locale, String text, Object o1, Object o2, Object o3) {\n" +
			"return i18n.tr(locale, text, o1, o2, o3);\n" +
		"}\n" +
		"public String tr(Locale locale, String text, Object o1, Object o2, Object o3, Object o4) {\n" +
			"return i18n.tr(locale, text, o1, o2, o3, o4);\n" +
		"}\n" +
		"public String tr(Locale locale, String text, Object[] objects) {\n" +
			"return i18n.tr(locale, text, objects);\n" +
		"}\n" +
		"public String tr(String text) {\n" +
			"return i18n.tr(text);\n" +
		"}\n" +
		"public String tr(String text, Object o) {\n" +
			"return i18n.tr(text, o);\n" +
		"}\n" +
		"public String tr(String text, Object o1, Object o2) {\n" +
			"return i18n.tr(text, o1, o2);\n" +
		"}\n" +
		"public String tr(String text, Object o1, Object o2, Object o3) {\n" +
			"return i18n.tr(text, o1, o2, o3);\n" +
		"}\n" +
		"public String tr(String text, Object o1, Object o2, Object o3, Object o4) {\n" +
			"return i18n.tr(text, o1, o2, o3, o4);\n" +
		"}\n" +
		"public String tr(String text, Object[] objects) {\n" +
			"return i18n.tr(text, objects);\n" +
		"}\n" +
		"public String trn(Locale locale, String text, String pluralText, long n) {\n" +
			"return i18n.tr(locale, text, pluralText, n);\n" +
		"}\n" +
		"public String trn(Locale locale, String text, String pluralText, long n, Object o) {\n" +
			"return i18n.tr(locale, text, pluralText, n, o);\n" +
		"}\n" +
		"public String trn(Locale locale, String text, String pluralText, long n, Object o1, Object o2) {\n" +
			"return i18n.tr(locale, text, pluralText, n, o1, o2);\n" +
		"}\n" +
		"public String trn(Locale locale, String text, String pluralText, long n, Object o1, Object o2, Object o3) {\n" +
			"return i18n.tr(locale, text, pluralText, n, o1, o2, o3);\n" +
		"}\n" +
		"public String trn(Locale locale, String text, String pluralText, long n, Object o1, Object o2, Object o3, Object o4) {\n" +
			"return i18n.tr(locale, text, pluralText, n, o1, o2, o3, o4);\n" +
		"}\n" +
		"public String trn(Locale locale, String text, String pluralText, long n, Object[] objects) {\n" +
			"return i18n.trn(locale, text, pluralText, n, objects);\n" +
		"}\n" +
		"public String trn(String text, String pluralText, long n) {\n" +
			"return i18n.trn(text, pluralText, n);\n" +
		"}\n" +
		"public String trn(String text, String pluralText, long n, Object o) {\n" +
			"return i18n.trn(text, pluralText, n, o);\n" +
		"}\n" +
		"public String trn(String text, String pluralText, long n, Object o1, Object o2) {\n" +
			"return i18n.trn(text, pluralText, n, o1, o2);\n" +
		"}\n" +
		"public String trn(String text, String pluralText, long n, Object o1, Object o2, Object o3) {\n" +
			"return i18n.trn(text, pluralText, n, o1, o2, o3);\n" +
		"}\n" +
		"public String trn(String text, String pluralText, long n, Object o1, Object o2, Object o3, Object o4) {\n" +
			"return i18n.trn(text, pluralText, n, o1, o2, o3, o4);\n" +
		"}\n" +
		"public String trn(String text, String pluralText, long n, Object[] objects) {\n" +
			"return i18n.trn(text, pluralText, n, objects);\n" +
		"}\n" +
		"public String trl(String localeCode, String text) {\n" +
			"return i18n.trl(localeCode, text);\n" +
		"}\n" +
		"public String trl(String localeCode, String text, Object o) {\n" +
			"return i18n.trl(localeCode, text, o);\n" +
		"}\n" +
		"public String trl(String localeCode, String text, Object o1, Object o2) {\n" +
			"return i18n.trl(localeCode, text, o1, o2);\n" +
		"}\n" +
		"public String trl(String localeCode, String text, Object o1, Object o2, Object o3) {\n" +
			"return i18n.trl(localeCode, text, o1, o2, o3);\n" +
		"}\n" +
		"public String trl(String localeCode, String text, Object o1, Object o2, Object o3, Object o4) {\n" +
			"return i18n.trl(localeCode, text, o1, o2, o3, o4);\n" +
		"}\n" +
		"public String trl(String localeCode, String text, Object[] objects) {\n" +
			"return i18n.trl(localeCode, text, objects);\n" +
		"}\n";

	public I18nGroovyCompiler() {
		super();
	}

	protected JRCompilationSourceCode generateSourceCode(JRSourceCompileTask sourceTask) throws JRException {
		JRCompilationSourceCode superCode = super.generateSourceCode(sourceTask);
		String code = superCode.getCode();

		String newImport = "import com.nantic.jasperreports.i18n;";

		code = code.replace( "import java.net", newImport + "\nimport java.net" );
		code = code.replace( "void customizedInit", newFunction + "\n\nvoid customizedInit" );
		JRDesignExpression ee;
		JRExpression[] expressions = new JRExpression[sourceTask.getExpressions().size()];
		int i = -1;
		for (Object o : sourceTask.getExpressions() ) {
			JRExpression e = (JRExpression)o;
			i++;

			ee = new JRDesignExpression();
			ee.setValueClass( e.getValueClass() );
			ee.setValueClassName( e.getValueClassName() );
			ee.setText( e.getText().replaceAll( "_\\(", "a(" ) );
			ee.setId( e.getId() );
			if ( e.getChunks() != null ) {
				for (Object chunk : e.getChunks() ) {
					JRDesignExpressionChunk newChunk = new JRDesignExpressionChunk();
					newChunk.setType( ((JRExpressionChunk)chunk).getType() );
					newChunk.setText( ((JRExpressionChunk)chunk).getText() );
					ee.addChunk( newChunk );
				}
			}
			expressions[i] = ee;
		}
		JRDefaultCompilationSourceCode newCode = new JRDefaultCompilationSourceCode( code, expressions );
		// Store last generated source code so it can be extracted
		lastGeneratedSourceCode = code;
		return newCode;
	}

	protected void checkLanguage(String language) throws JRException {
		if ( 
			!JRReport.LANGUAGE_GROOVY.equals(language)
			&& !JRReport.LANGUAGE_JAVA.equals(language) 
			&& !language.equals("i18ngroovy") 
			)
		{
			throw new JRException(
				"Language \"" + language
				+ "\" not supported by this report compiler.\n"
				+ "Expecting \"i18ngroovy\", \"groovy\" or \"java\" instead."
			);
		}
	}
}
