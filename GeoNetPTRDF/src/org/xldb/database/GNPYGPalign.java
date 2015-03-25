/**
 * 
 */
package org.xldb.database;

import java.sql.Connection;
import java.sql.DriverManager;
import java.sql.PreparedStatement;
import java.sql.ResultSet;
import java.sql.SQLException;
import java.sql.Statement;
import java.util.ArrayList;

/**
 * @author dsbatista
 *
 */
public class GNPYGPalign {
	
	//PSQL connection variables
	public Connection connection = null;
    public Statement state = null;

    public GNPYGPalign(String server, String database, String username, String password) throws Exception {

    	try {
			Class.forName("org.postgresql.Driver");
			
		} catch (ClassNotFoundException cnfe) {
			System.out.println("Couldn't find the driver!");
			System.out.println("Let's print a stack trace, and exit.");
			cnfe.printStackTrace();
			System.exit(1);
		}

    	try {
    		connection = DriverManager.getConnection("jdbc:postgresql://" + server + '/' + database, username, password);
			System.out.println("Connected to " + server + '/' + database);

    	} catch(SQLException ex) {
    		System.err.println("SQLException: " + ex.getMessage());
    	}

	}
    
    public ArrayList<Alignment> getPostalCodesAlignments() throws Exception{
    	
    	String SQL = 
	    	"SELECT postal_code_matches.f_id, geonet.n_cap_name as geonet_n_cap_name, geonet.t_id as geonet_type, postal_code_matches.woeid, geoplanet.n_cap_name as geoplanet_name, geoplanet.t_id as geoplanet_type " +
	    	"FROM postal_code_matches, geoplanet, geonet " +
	    	"WHERE postal_code_matches.woeid = geoplanet.woeid " +
	    	"AND geonet.f_id = postal_code_matches.f_id";

    	PreparedStatement pstmt = connection.prepareStatement(SQL);
    	
    	ArrayList<Alignment> alignments = new ArrayList<Alignment>();    	
    	ResultSet resultSet = null;
    	
    	try {
    		
    		resultSet = pstmt.executeQuery();
    		
    		while (resultSet.next()) {
	
				String f_id =  resultSet.getString("f_id");
				String f_id_name = resultSet.getString("geonet_n_cap_name");
				String f_id_type = resultSet.getString("geonet_type");
		        
				String woeid = resultSet.getString("woeid");
		        String woeid_name = resultSet.getString("geoplanet_name");
		        String woeid_type = resultSet.getString("geoplanet_type");
		        alignments.add(new Alignment(f_id, f_id_name, woeid, woeid_name,f_id_type,woeid_type));
		        
		    }
			
		} finally {
		        if (resultSet != null) try { resultSet.close(); } catch (SQLException logOrIgnore) {}
		        if (pstmt != null) try { pstmt.close(); } catch (SQLException logOrIgnore) {}
		        //if (connection != null) try { connection.close(); } catch (SQLException logOrIgnore) {}
		    }
	
		return alignments;
    	
    }

    public ArrayList<Alignment> getAlignments() throws Exception{
    	
    	String SQL = 
	    	"SELECT good_matches.f_id, geonet.n_cap_name as geonet_n_cap_name, geonet.t_id as geonet_type, good_matches.woeid, geoplanet.n_cap_name as geoplanet_name, geoplanet.t_id as geoplanet_type " +
	    	"FROM good_matches, geoplanet, geonet " +
	    	"WHERE good_matches.woeid = geoplanet.woeid " +
	    	"AND geonet.f_id = good_matches.f_id";
    		
    	
    	PreparedStatement pstmt = connection.prepareStatement(SQL);
    	
    	ArrayList<Alignment> alignments = new ArrayList<Alignment>();    	
    	ResultSet resultSet = null;
    	
    	try {
    		
    		resultSet = pstmt.executeQuery();
    		
    		while (resultSet.next()) {
	
				String f_id =  resultSet.getString("f_id");
				String f_id_name = resultSet.getString("geonet_n_cap_name");
				String f_id_type = resultSet.getString("geonet_type");
		        
				String woeid = resultSet.getString("woeid");
		        String woeid_name = resultSet.getString("geoplanet_name");
		        String woeid_type = resultSet.getString("geoplanet_type");
		        alignments.add(new Alignment(f_id, f_id_name, woeid, woeid_name,f_id_type,woeid_type));
		        
		    }
			
		} finally {
		        if (resultSet != null) try { resultSet.close(); } catch (SQLException logOrIgnore) {}
		        if (pstmt != null) try { pstmt.close(); } catch (SQLException logOrIgnore) {}
		        //if (connection != null) try { connection.close(); } catch (SQLException logOrIgnore) {}
		    }
	
		return alignments;
    	
    }

}
