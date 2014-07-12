/********************************************************************************************
 * Class for print a ssm result in XML
 * Programmer: Francisco Couto 
 * Date: April 2010
 ********************************************************************************************/
 
public class ToXML {

	public static String ontology = "geo-net-pt-02";
	public static String entity1;
	public static String entity2;
	public static String score;

	public static String addPair(GeoEntity entity1, GeoEntity entity2, String score){

		String pair="<ssm:Pair>"+"\n"+
		"<ssm:Sim>"+"\n"+
		"<ssm:entity1> \n"+ entity1.toXML() +"</ssm:entity1> \n"+
		"<ssm:entity2> \n"+ entity2.toXML() +"</ssm:entity2> \n"+
		"<ssm:score rdf:datatype='http://www.w3.org/2001/XMLSchema#float'>"+score+"</ssm:score> \n"+
		"</ssm:Sim> \n"+
		"</ssm:Pair> \n";

		return pair;
	}
	
	public static String addAnnotation(GeoEntity entity){
		
		String annotation="<gnpt02:entity> \n"+ entity.toXML() +"</gnpt02:entity> \n";
		return annotation;
		
	}
	

	public static String header(String measure, String entity_type){

		String header="<?xml version=\"1.0\"?> \n <rdf:RDF \n"+
		"xmlns:rdf=\"http://www.w3.org/1999/02/22-rdf-syntax-ns#\" \n"+
		"xmlns:xsd=\"http://www.w3.org/2001/XMLSchema#\" \n"+
		"xmlns:gnpt02=\"http://xldb.di.fc.ul.pt/xldb/publications/2009/10/geo-net-pt-02#\" \n"+
		"xmlns:dcterms=\"http://purl.org/dc/terms#\" \n"+
		"xmlns:ssm=\"http://xldb.di.fc.ul.pt/ssm#\"> \n"+
		"<ssm:SemanticSimilarity> \n"+
		"<ssm:ontology rdf:datatype='http://www.w3.org/2001/XMLSchema#string'>"+ontology+"</ssm:ontology> \n"+
		"<ssm:measure rdf:datatype='http://www.w3.org/2001/XMLSchema#string'>"+measure+"</ssm:measure> \n";


		return header;
	}
	
	public static String header(){

		String header="<?xml version=\"1.0\"?> \n <rdf:RDF \n"+
		"xmlns:rdf=\"http://www.w3.org/1999/02/22-rdf-syntax-ns#\" \n"+
		"xmlns:xsd=\"http://www.w3.org/2001/XMLSchema#\" \n"+
		"xmlns:gnpt02=\"http://xldb.di.fc.ul.pt/xldb/publications/2009/10/geo-net-pt-02#\" \n"+
		"xmlns:dcterms=\"http://purl.org/dc/terms#\"> \n"+
		"<entities> \n";
		return header;
	}

	public static String footer_ids(){

		String footer="</entities> \n"+
		"</rdf:RDF>";
		return footer;
	}
	
	
	public static String footer(){

		String footer="</ssm:SemanticSimilarity> \n"+
		"</rdf:RDF>";
		return footer;
	}


	public static String roundValue(double ssmValue)
    {
	    //Round ssm value multiplied by 1000 so that 3 digits are preserved
		long rounded = Math.round(ssmValue*1000);
		
		//Divide rounded value by 10 to obtain a % with 1 decimal case
	    double value = rounded/1000.0;
		
	  
		return value+"";
    }	

}
