import java.sql.ResultSet;
import java.util.HashMap;
import java.util.HashSet;
import java.util.Iterator;
import java.util.Map;
import java.util.Vector;

import org.apache.commons.codec.binary.Base64;

import java.io.FileInputStream;
import java.io.InputStream;
import java.util.Properties;

/********************************************************************************************
 * Class for specific MySQL Access for GeoSSM functionalities
 * Programmer: Francisco Couto 
 * Date: April 2010
 *
 * java GeoSSM 'ssm_adm_name_term_freq_n_cap_name' terms - GI 12/20
 * java GeoSSM 'ssm_adm_name_term_freq_n_cap_name' terms - AC 12/20
 *  
 * java GeoSSM 'ssm_adm_name_term_freq_n_cap_name' names 2 GI alentejo/aljustrel 
 * java GeoSSM 'ssm_adm_name_term_freq_n_cap_name' names 8 AC alentejo/aljustrel 
 *
 * java GeoSSM 'ssm_adm_name_term_freq_n_cap_name' ids 2 alentejo
 ********************************************************************************************/

public class GeoSSM extends ToXML
{

    public static DataBase geonetpt;
    
    /**
     * @param args
     */
    public static void main(String[] args) {
    	    	
    	try {
    		
    		Base64 base64code = new Base64();
    		   		
    		Properties prop = new Properties();
    	    String fileName = "database.config";
    	    InputStream is = new FileInputStream(fileName);

    	    prop.load(is);

    		String server = prop.getProperty("server");
    		String database = prop.getProperty("database");
    		String username = prop.getProperty("username");
    		String password = prop.getProperty("password");
    		
    		geonetpt = new DataBase(server,database,username,password);
	    		
    		String infoTable = args[0]; // 
			String inputType = args[1]; // (names/terms/ids) 
			String termsPerName = args[2]; // number of terms selected per each name

    		if (inputType.equalsIgnoreCase("ids")) {
    			String placenameEnconded = args[3]; // placename to get the ids from
    			byte[] decodedName = base64code.decodeBase64(placenameEnconded);
    			String placeName = new String(decodedName, "UTF-8");
    			
    			HashSet<GeoTerm> terms = new HashSet<GeoTerm>();
    			
    			GeoName gn = new GeoName(placeName, infoTable, Integer.parseInt(termsPerName));	
			    terms.addAll(gn.getAllTerms());
			    
			    String xml=header();
			    
			    for (GeoTerm geoTerm : terms) {
			    	xml += addAnnotation(geoTerm);
				}
				xml+=footer_ids();
				System.out.println(xml);
    		}
    		
    		else {	
    			String ssmMeasure = args[3]; // (AC/RM/RG/LM/LG/JM/JG/GI/UI)  AC=ancestors; Resnik, Resnik w/ GraSM, Lin, Lin w/ GraSM, JiangConrath, JiangConrath w/ GraSM, SimGIC, SimUI 
				String entities = args[4]; // names or ids separated by '/'
				
				//Process the input type
				
				//System.out.println("placenames(encoded): " + entities);
				byte[] decodedBytes = base64code.decodeBase64(entities);
				String placeNames = new String(decodedBytes, "UTF-8");
				//System.out.println("placenames(decoded): " + placeNames);
				
				String[] termsNames = placeNames.split("/");
								
				HashSet<GeoTerm> terms = new HashSet<GeoTerm>();
				
				if (inputType.equals("names")) {
					for (int i = 0; i < termsNames.length; i++) {
						GeoName gn = new GeoName(termsNames[i], infoTable, Integer.parseInt(termsPerName));	
					    terms.addAll(gn.getAllTerms());	
					}
				}
				else if (inputType.equals("terms")) {
					for (int i = 0; i < termsNames.length; i++) {
						long tid = Long.parseLong(termsNames[i]);
						terms.add(new GeoTerm(tid, infoTable));
					}
					
				} else System.out.println("Error: illegal input Type!");
				
				//Process the query
				if (ssmMeasure.equals("AC"))
					getAncestors(terms,infoTable);
				else getSSM(terms,ssmMeasure,infoTable);
				geonetpt.close();
    		}
    	}
    	catch(Exception e) {
    		System.out.println("Error: " + e);
	    }	
    }
	
    	
    //Returns all terms that significantly represent a set of GeoTerms
    public static void getAncestors(HashSet<GeoTerm> terms, String infoTable) throws Exception {
	
		//Create temporary table
		String tempTable = "Temp_getAncestors_" + System.currentTimeMillis();		
		geonetpt.update("DROP TABLE IF EXISTS " + tempTable + ";");
		String query = "CREATE TEMPORARY TABLE " + tempTable + " (id INTEGER PRIMARY KEY, ";
		Iterator<GeoTerm> term = terms.iterator();
		String attributes = "";	
		
		while(term.hasNext()) {
			
		    GeoTerm t = (GeoTerm)term.next();
		    String attribute = "t_" + t.id;	
		    attributes += "+"+attribute;
		    query += "t_" + t.id + " INTEGER NOT NULL DEFAULT 0,";
		    
		}
		
		query += "score FLOAT NOT NULL DEFAULT '0');"; 
		geonetpt.update(query);
			
		term = terms.iterator();
			
		while (term.hasNext()) {
			
		    GeoTerm t = (GeoTerm) term.next();
		    Vector<GeoTerm> ancestors = t.getAncestors();
		    Iterator<GeoTerm> ancestor = ancestors.iterator();
		    
		    while (ancestor.hasNext()) {
				GeoTerm a = (GeoTerm)ancestor.next();
										
				//Populate the table with all terms assigned to the proteins
				try {
				    geonetpt.update("INSERT INTO " + tempTable + " (id,score,t_"+ t.id +") " + 
						    " VALUES ("+ a.id +","+ a.rel_ic +","+ 1 +")" );
				}
				catch(Exception e) {
				    // The ancestor was already added
				    geonetpt.update("UPDATE " + tempTable + " SET  t_"+ t.id +" = 1 " + 
						    " WHERE id = "+ a.id);
				}
		    }
	}		
	
	int count = terms.size();					

	//Update score
	geonetpt.update("UPDATE " + tempTable + "  SET score = 1.0*(" + attributes + ")/" + count);
	
	//Delete redundant entries (ancestral terms with same ocurrence as their descendents)
	String tempTable2 = "Temp_getAncestors2_" + System.currentTimeMillis();
	geonetpt.update("CREATE TEMPORARY TABLE " + tempTable2 + " AS (SELECT * FROM " + tempTable + ");");
	query = "DELETE FROM " + tempTable + " r WHERE EXISTS (SELECT t.id" + 
	    " FROM " + tempTable2 + " t, ssm_graphpath gp WHERE gp.f_id2 = t.id AND gp.f_id1 = r.id";
	term = terms.iterator();
	while(term.hasNext()) {	
	    GeoTerm t = (GeoTerm)term.next();
	    String attribute = "t_" + t.id;
	    query += " AND t." + attribute + " = r." + attribute;
	}
	query += " AND t.id != r.id);";
	geonetpt.update(query);
	geonetpt.update("DROP TABLE " + tempTable2 + ";");
	
	//Retrieve the information
	String xml=header("AC", "term");	
	ResultSet result = geonetpt.query("SELECT id, score FROM " + tempTable +
					  " WHERE score > 0 ORDER BY score DESC;");
	xml+="<results>\n";
	while(result.next())
	    {
		int termId = result.getInt("id");
		double score = result.getDouble("score");
		GeoTerm t = new GeoTerm(termId, infoTable);
		xml+="<result>\n" + t.toXML() + "<score>" + score + "</score>\n</result>\n";		
	    }
	xml+="</results>\n";
	result.close();
	geonetpt.update("DROP TABLE " + tempTable + ";");

	xml+=footer();
	System.out.println(xml);
    }
	
    public static void getSSM(HashSet<GeoTerm> terms, String measure, String infoTable) throws Exception {

		//Setup result header
		String xml = header(measure, "term");
		Iterator<GeoTerm> term1 = terms.iterator();
		
		/* 2D hashmap to keep the pairs already calculated */
		Map <Long,Map<Long,Boolean>> map2d = new HashMap<Long,Map<Long,Boolean>>();
		
		for (GeoTerm geoTerm : terms) {
			Map <Long,Boolean> hashtable = new HashMap<Long, Boolean>();
			for (GeoTerm geoTermOther : terms) {
				hashtable.put(geoTermOther.id, false);
			}
			map2d.put(geoTerm.id, hashtable);
		}
		
		while(term1.hasNext()) {
				
		    GeoTerm t1 = (GeoTerm) term1.next();
		    Iterator<GeoTerm> term2 = terms.iterator();
		    
		    while(term2.hasNext()) {
		    	
		    	GeoTerm t2 = (GeoTerm) term2.next();
		    	
		    	/* see if pair was already calculated */
		    	if (!(map2d.get(t1.id).get(t2.id) || map2d.get(t2.id).get(t1.id))){
		    		
		    		xml += addPair(t1, t2, roundValue(t1.SSM(t2,measure,infoTable)));
					
		    		/* add the pairs to the already calculated */
		    		Map <Long,Boolean> hashtable1 = map2d.get(t1.id);
		    		hashtable1.put(t2.id, true);
		    		
		    		Map <Long,Boolean> hashtable2 = map2d.get(t1.id);
		    		hashtable2.put(t2.id, true);
		    	}
		    }
		}		
		xml+=footer();
		System.out.println(xml);
    }
}