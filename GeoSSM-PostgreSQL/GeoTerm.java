import java.sql.*;
import java.util.*;

/********************************************************************************************
 * Class for representing Geo GeoTerms
 * Programmer: Francisco Couto 
 * Date: April 2010
 ********************************************************************************************/

public class GeoTerm implements GeoEntity
{
    public long id;
    public String type; //saber ser tem tipo especifico como: RUA,  PTA, ou se null = ZON NT1...
    public String name;
    public String ascii_name;
    public String cap_name;
    public double freq;
    public float hfreq;
    public double prob;
    public double ic;
    public double rel_ic;
	
    private String infoTable;
		
    //External constructor (from interface)	
    public GeoTerm(long newid, String newInfoTable) throws Exception
    {
	infoTable = newInfoTable;
	
	ResultSet result = GeoSSM.geonetpt.query(
					  "SELECT s.f_id, b.t_id, a.n_name, a.n_ascii_name, a.n_cap_name,s.freq, s.hfreq, s.prob, s.info_content, s.rel_info"
					  + " FROM adm_name a, " + infoTable + " s, adm_feature b"
					  + " WHERE s.f_id = "
					  + newid
					  + " AND  s.f_id = b.f_id AND b.n_id = a.n_id;");
		
		
					  if(result.next())
					      {
						  id = result.getInt("f_id");
						  type = result.getString("t_id");
						  name = result.getString("n_name");
						  ascii_name = result.getString("n_ascii_name");
						  cap_name = result.getString("n_cap_name");
						  freq = result.getDouble("freq");
						  hfreq = result.getFloat("hfreq");
						  prob = result.getDouble("prob");
						  //ic = result.getDouble("info_content");
						  //rel_ic = result.getDouble("rel_info");
						  ic = result.getDouble("rel_info");
					      }
					  else throw new SQLException("newid " + newid + " not found");
					  result.close();
					  }
	
	    //Internal constructor
         public GeoTerm(long newId, double newIc, String newInfoTable) throws Exception
	    {
		id = newId;
		ic = newIc;
		infoTable = newInfoTable;
	    }
	
	//Retrieve id
	public long getId()
	    {
		return id;
	    }
	
	//Retrieve name
	public String getName()
	    {
		return name;
	    }
	
	//Retrieve ic
	public double getIC()
	    {
		return ic;
	    }
	
	//Retrieve ancestral GeoTerms (from DataBase)
	public Vector<GeoTerm> getAncestors() throws Exception
	    {
		Vector<GeoTerm> toReturn = new Vector<GeoTerm>(0,1);

		ResultSet result = GeoSSM.geonetpt.query(
				"SELECT s.f_id, s.rel_info " +
				"FROM ssm_graphpath g, " + infoTable + " s  " +
				"WHERE g.f_id2 = " + id + " AND g.f_id1 = s.f_id " +
				"ORDER BY rel_info DESC;");
		while(result.next())
		    toReturn.add(new GeoTerm(result.getLong("f_id"),result.getDouble("rel_info"),infoTable));
		result.close();
		return toReturn;
	    }	
	
	//Get the MICA of this GeoTerm and another
	public GeoTerm getMICA(GeoTerm t) throws Exception {
		
		GeoTerm mica = null;
		ResultSet result = GeoSSM.geonetpt.query("SELECT DISTINCT s.f_id,s.rel_info, (p1.distance+p2.distance) as dist FROM " + 
						  "ssm_graphpath p1, ssm_graphpath p2, " + infoTable + " s WHERE p1.f_id2 = " +
						  id + " AND p2.f_id2 = " + t.id + " AND p1.f_id1 = p2.f_id1 AND " +
						  "p1.f_id1 = s.f_id ORDER BY rel_info DESC, dist ASC;");
		if (result.next()) {
			mica = new GeoTerm(result.getLong("f_id"),result.getDouble("rel_info"),infoTable);
			result.close();
		}
		return mica;
	}
    
	//Get all common ancestors of this GeoTerm and another
	public Vector<GeoTerm> getCmAncestors(GeoTerm t) throws Exception
	    {
		Vector<GeoTerm> toReturn = new Vector<GeoTerm>(0,1);

		ResultSet result = GeoSSM.geonetpt.query("SELECT DISTINCT s.f_id, s.rel_info FROM " +
						  "ssm_graphpath p1, ssm_graphpath p2, " + infoTable + " s WHERE p1.f_id2 = " +
						  id + " AND p2.f_id2 = " + t.id + " AND p1.f_id1 = p2.f_id1 AND " + 
						  "p1.f_id1 = s.f_id");
		while(result.next())
		    toReturn.add(new GeoTerm(result.getLong("f_id"),result.getDouble("rel_info"),infoTable));
		result.close();
		return toReturn;
	    }
    
	//Get the common ancestors' IC by the GraSM approach
	private double GraSM(GeoTerm t) throws Exception
	    {
		Vector ancestors = getCmAncestors(t);
		if(ancestors.size() == 0)
		    return 0;
		if(ancestors.size() == 1)
		    return ((GeoTerm)ancestors.get(0)).ic;

		double grasm = 0;
		boolean check;
		Vector<GeoTerm> distAncestors = new Vector<GeoTerm>(0,1);	    

		for(int i = 0; i < ancestors.size(); i++)
		    {		
			GeoTerm ancestor1 = (GeoTerm)ancestors.get(i);
			check = true;
			for(int j = 0; j < distAncestors.size() && check; j++)
			    {
				GeoTerm ancestor2 = (GeoTerm)distAncestors.get(j);
				check = (areDisjoint(ancestor1,ancestor2) ||
					 t.areDisjoint(ancestor1,ancestor2));
			    }
			if(check)
			    {
				distAncestors.add(ancestor1);
				grasm += ancestor1.ic;
			    }
		    }
		return grasm/distAncestors.size();
	    }
    
	//Check if two ancestors of this GeoTerm are disjoint (for grasmIC)
	private boolean areDisjoint(GeoTerm ancestor1, GeoTerm ancestor2) throws Exception
	    {
		int paths = ancestor1.numPaths(ancestor2);
		if(paths == 0)
		    return true;
		int paths1 = numPaths(ancestor1);
	  	int paths2 = numPaths(ancestor2);
	  	return ((paths1-paths) >= paths2);
	    }
    
	//Get the number of paths between this GeoTerm and one of its ancestors
	private int numPaths(GeoTerm t) throws Exception
	    {

		ResultSet result = GeoSSM.geonetpt.query("SELECT COUNT(*) as npaths FROM ssm_graphpath WHERE" +
						  " f_id1=" + t.id + " AND f_id2=" + id + ";");
		if(result.next())
		    return result.getInt("npaths");
		result.close();
		return 0;
	    }

	//Auxiliary method to sum all IC of a vector of GeoTerms	
	public static double sumIC(Vector<GeoTerm> GeoTerms)
	    {
		double sum = 0;
		for(int i = 0; i < GeoTerms.size(); i++)
		    sum += GeoTerms.get(i).ic;
		return sum;
	    }
    	
	//Compute similarity with another GeoTerm (from DataBase)
	public double SSM(GeoEntity e, String measure, String newInfoTable) throws Exception {
		
		GeoTerm t = (GeoTerm) e;
		
		if (equals(t))
			return 1;
	 
		infoTable = newInfoTable;	

		if (measure.equals("GI")) {
			
			double intersection = sumIC(getCmAncestors(t));
			double union = sumIC(getAncestors()) + sumIC(t.getAncestors()) - intersection;
			
			return intersection/union;
		}
		
		if (measure.equals("UI")) {
			
			double intersection = getCmAncestors(t).size();
			double union = getAncestors().size() + (t.getAncestors()).size() - intersection;
			
			return intersection/union;
		}
		
		double ancestorIC = 0;
	
	    //to decide if the IC of the MICA should be used or the GraSM 
		if (measure.endsWith("G"))			
			ancestorIC = GraSM(t);
		else {
			GeoTerm mica = getMICA(t);
			// GeoTerm mica might come with null value, if one of the terms is (Portugal,418745)
			if (mica == null) 
				ancestorIC = 0;
			else ancestorIC = mica.ic;
		}
		
		/* Lin Measure */
		if (measure.startsWith("L"))  			
  			return (2*ancestorIC)/(ic + t.ic);
		
		/* Jang and Conrath*/
  		if (measure.startsWith("J"))
  			return 1 + ancestorIC - ( ic + t.ic ) / 2;
  		
  		/* Resnik */
		else return ancestorIC;
	    }
	
	//Two GeoTerms are equal if they have the same id
	public boolean equals(Object other)
	    {
		return id == ((GeoTerm)other).getId();
	    }

	//Returns html table row with each attribute in a column
	public String toString()
	    {	
		return cap_name; 
	    }

	public String toXML()
	    {	
		String tag="<gnpt02:term rdf:about=\"http://xldb.di.fc.ul.pt/xldb/publications/2009/10/geo-net-pt-02#"+id+"\"> \n "+
		    "<gnpt02:type>"+type+"</gnpt02:type> \n "+
		    "<dcterms:title>"+toString()+"</dcterms:title> \n "+
		    "</gnpt02:term> \n";
		
		return tag;
	    }
    }
