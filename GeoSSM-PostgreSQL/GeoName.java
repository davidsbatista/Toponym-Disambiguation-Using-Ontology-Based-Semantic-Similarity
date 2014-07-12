import java.sql.*;
import java.util.*;

/********************************************************************************************
 * Class for representing GeoName
 * Programmer: Francisco Couto 
 * Date: April 2010
 ********************************************************************************************/

public class GeoName implements GeoEntity
{
    private String name;
    private String infoTable;
    private static int termsPerName = 2;

    public GeoName(String newName, String newInfoTable, int newTermsPerName) throws Exception									       
    {
	name = newName;
	infoTable = newInfoTable;
	termsPerName=newTermsPerName;
		
    }
	
    //Retrieve name
    public String getName()
    {
	return name;
    }
	
    //Retrieve all annotated terms (from the database)
    public Vector<GeoTerm> getAllTerms() throws Exception
    {
	Vector<GeoTerm> toReturn = new Vector<GeoTerm>(0,1);
	ResultSet result = GeoSSM.geonetpt.query(
					  "SELECT s.f_id, b.t_id, a.n_name, a.n_ascii_name, a.n_cap_name,s.freq, s.hfreq, s.prob, s.info_content, s.rel_info"
					  + " FROM adm_name a, " + infoTable + " s, adm_feature b"
					  + " WHERE a.n_name = '"+ name.toLowerCase() + "' "
					  + " AND  b.n_id = a.n_id AND s.f_id=b.f_id ORDER BY s.rel_info ASC LIMIT "+ termsPerName +";");
	while(result.next())
	    toReturn.add(new GeoTerm(result.getLong("f_id"),infoTable));
	result.close();
	return toReturn;
    }
	
	
    //Compute semantic similarity with another name (from DataBase)
    public double SSM(GeoEntity e, String measure, String newInfoTable) throws Exception
    {
		
	GeoName n = (GeoName) e;
		
	if(equals(n))
	    return 1;
	    
	infoTable = newInfoTable;	
		
	Vector<GeoTerm> terms1, terms2;

	terms1 = getAllTerms();
	terms2 = n.getAllTerms();
	if(terms1.size()==0 || terms2.size()==0)
	    return 0;

	    
	if(measure.equals("GI") || measure.equals("UI"))
	    {
		double shared = 0;
		double joined = 0;
		if(measure.equals("GI"))
		    {
			for(int i = 0; i < terms1.size(); i++)
			    {
			    	if(terms2.contains(terms1.get(i)))
				    shared += terms1.get(i).getIC();
		    		else
				    joined += terms1.get(i).getIC();
			    }
	    		joined += GeoTerm.sumIC(terms2);
		    }
    		else
		    {
	    		for(int i = 0; i < terms1.size(); i++)
			    {
		    	   	if(terms2.contains(terms1.get(i)))
				    shared++;
		    		else
				    joined++;
			    }
		    	joined += terms2.size();
		    } 
		return shared/joined;
	    }
	    

	double sim1 = 0, sim2 = 0, simBest, simTemp;
	GeoTerm temp = null;
   	    
	for(int i = 0; i < terms1.size(); i++)
	    {
		simBest = 0;
		temp = terms1.get(i);
		    
		for(int j = 0; j < terms2.size(); j++)
		    {
		    	simTemp = temp.SSM(terms2.get(j),measure,infoTable);
			if(simTemp > simBest)
			    simBest = simTemp;
		    }
		sim1 += simBest;
   	    }
	sim1 /= terms1.size();
	for(int i = 0; i < terms2.size(); i++)
	    {
		simBest = 0;
		temp = terms2.get(i);
		    
		for(int j = 0; j < terms1.size(); j++)
		    {
		    	simTemp = temp.SSM(terms1.get(j),measure,infoTable);
			if(simTemp > simBest)
			    simBest = simTemp;
		    }
		sim2 += simBest;
   	    }
	sim2 /= terms2.size();
	return (sim1+sim2)/2;
    }
    
    //Two names are equal if they have the same name
    public boolean equals(Object other)
    {
	return name.equals(((GeoName)other).getName());
    }

    //Returns html table row with each attribute in a column
    public String toString()
    {	
	return name; 
    }

    public String toXML()
    {	
	return "<geoname>" + name + "</geoname>"; 
    }

}
