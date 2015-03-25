/**
 * 
 */
package org.xldb.database;

/**
 * @author dsbatista
 *
 */

public class Alignment {
	
	public String f_id;
	public String f_id_name;
	public String geonet_type;
	public String woeid;
	public String woeid_name;
	public String geoplanet_type;
	
	public Alignment(String f_id, String f_id_name, String woeid, String woeid_name){
		
		this.f_id = f_id;
		this.f_id_name = f_id_name; 
		this.woeid = woeid;
		this.woeid_name = woeid_name;
		
	}
	
	public Alignment(String f_id, String f_id_name, String woeid, String woeid_name,String geonet_type, String geoplanet_type){
		
		this.f_id = f_id;
		this.f_id_name = f_id_name;
		this.geonet_type = geonet_type;
		this.woeid = woeid;
		this.woeid_name = woeid_name;
		this.geoplanet_type = geoplanet_type;
		
	}

}
