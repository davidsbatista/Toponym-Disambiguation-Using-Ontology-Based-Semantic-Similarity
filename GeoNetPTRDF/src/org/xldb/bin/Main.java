package org.xldb.bin;

import java.io.FileInputStream;
import java.io.FileOutputStream;
import java.io.IOException;
import java.net.URLEncoder;
import java.util.ArrayList;
import java.util.Properties;

import org.xldb.database.Alignment;
import org.xldb.database.GNPYGPalign;

import com.hp.hpl.jena.rdf.model.Model;
import com.hp.hpl.jena.rdf.model.ModelFactory;
import com.hp.hpl.jena.rdf.model.Property;
import com.hp.hpl.jena.rdf.model.Resource;

/**
 * @author dsbatista
 * 
 */
public class Main {

	/**
	 * @param args
	 * @throws Exception
	 */

	static String server = new String();
	static String database = new String();
	static String username = new String();
	static String password = new String();

	public static void postalCodesAlignment() throws Exception {

		GNPYGPalign db = new GNPYGPalign(server, database, username, password);
		ArrayList<Alignment> postalCodesalignments = db
				.getPostalCodesAlignments();

		// create a Model
		Model model = ModelFactory.createDefaultModel();

		String geonetpt02 = "http://xldb.di.fc.ul.pt/xldb/publications/2009/10/geo-net-pt-02#";
		String geoplanet = "http://where.yahooapis.com/v1/place/";

		model.setNsPrefix("gnpt02", geonetpt02);
		model.setNsPrefix("gplnt", geoplanet);

		String skosURI = "http://www.w3.org/2004/02/skos/core#";
		String dctermsURI = "http://purl.org/dc/terms/#";

		model.setNsPrefix("skos", skosURI);
		model.setNsPrefix("dc", dctermsURI);

		String rdfsURI = "http://www.w3.org/2000/01/rdf-schema#";
		model.setNsPrefix("rdfs", rdfsURI);

		Property broaderMatch = model.createProperty(skosURI + "broaderMatch");
		Property identifier = model.createProperty(dctermsURI + "identifier");
		Property prefLabel = model.createProperty(skosURI + "prefLabel");

		for (Alignment alignment : postalCodesalignments) {

			Resource f_id = model.createResource(geonetpt02 + alignment.f_id);
			Resource woeid = model.createResource(geoplanet + alignment.woeid);
			woeid.addProperty(prefLabel, alignment.woeid_name + " ("
					+ alignment.geoplanet_type + ")");
			woeid.addProperty(identifier, alignment.woeid);

			model.add(f_id, broaderMatch, woeid);
		}

		// now write the model in XML form to a file
		try {			
		     FileOutputStream foutTTL = new FileOutputStream("GeoNetPT02-yahoo-alignment-postal-codes.TTL");
		     model.write(foutTTL,"TURTLE");
		     
		     FileOutputStream foutRDF = new FileOutputStream("GeoNetPT02-yahoo-alignment-postal-codes.RDF");     
		     model.write(foutRDF,"RDF/XML-ABBREV");
		     
		     FileOutputStream foutN3 = new FileOutputStream("GeoNetPT02-yahoo-alignment-postal-codes.N3");     
		     model.write(foutN3,"N-TRIPLE");

		} catch (IOException e) {
			System.out.println("Exception caught" + e.getMessage());
		}
	}

	public static void placesAlignment() throws Exception {
		
		GNPYGPalign db = new GNPYGPalign(server,database,username,password);
		ArrayList<Alignment> alignments = db.getAlignments();
				
		//create a Model
		Model model = ModelFactory.createDefaultModel();
		
		String geonetpt02 = "http://xldb.di.fc.ul.pt/xldb/publications/2009/10/geo-net-pt-02#";
		String geoplanet = "http://where.yahooapis.com/v1/place/";
		
		model.setNsPrefix( "gnpt02", geonetpt02 );
		model.setNsPrefix( "gplnt", geoplanet );
		

		String skosURI = "http://www.w3.org/2004/02/skos/core#";
		String dctermsURI = "http://purl.org/dc/terms/#";

		model.setNsPrefix( "skos", skosURI );
		model.setNsPrefix( "dc", dctermsURI );

		
		String rdfsURI = "http://www.w3.org/2000/01/rdf-schema#";
		model.setNsPrefix( "rdfs", rdfsURI );
		
		Property closeMatch = model.createProperty( skosURI + "closeMatch" );
		Property prefLabel = model.createProperty( skosURI + "prefLabel" );
		Property identifier = model.createProperty( dctermsURI + "identifier"); 
		
		System.out.println(alignments.size());
		
		for (Alignment alignment : alignments) {
			
			String featureNameLowerCase =  alignment.f_id_name.toLowerCase();			
			String spacesTranslated = featureNameLowerCase.replaceAll(" ", "_");
			String encodedName = URLEncoder.encode(spacesTranslated,"UTF-8");
			String URI = encodedName + "-AF" + alignment.f_id;
			
			Resource f_id = model.createResource(geonetpt02 + URI);
			
			Resource woeid = model.createResource(geoplanet + alignment.woeid);			
			woeid.addProperty(prefLabel, alignment.woeid_name + " (" + alignment.geoplanet_type + ")");
			woeid.addProperty(identifier, alignment.woeid);
			
			model.add( f_id, closeMatch, woeid);
		}
	
		//now write the model in XML form to a file
		try {			
		     FileOutputStream foutTTL = new FileOutputStream("GeoNetPT02-yahoo-alignment-places.TTL");
		     model.write(foutTTL,"TURTLE");
		     
		     FileOutputStream foutRDF = new FileOutputStream("GeoNetPT02-yahoo-alignment-places.RDF");     
		     model.write(foutRDF,"RDF/XML-ABBREV");
		     
		     FileOutputStream foutN3 = new FileOutputStream("GeoNetPT02-yahoo-alignment-places.N3");     
		     model.write(foutN3,"N-TRIPLE");

		} catch(IOException e) {
			System.out.println("Exception caught"+e.getMessage());
			}

	}

	public static void main(String[] args) throws Exception {

		Properties props = new Properties();

		// try retrieve data from file
		try {

			props.load(new FileInputStream("options.conf"));

			server = props.getProperty("server");
			database = props.getProperty("database");
			username = props.getProperty("username");
			password = props.getProperty("password");

		}

		catch (IOException e) {
			e.printStackTrace();
		}

		long start = System.currentTimeMillis();

		placesAlignment();
		postalCodesAlignment();

		long end = System.currentTimeMillis();
		System.out.println("Execution time was " + (end - start) + " ms.");

	}
}