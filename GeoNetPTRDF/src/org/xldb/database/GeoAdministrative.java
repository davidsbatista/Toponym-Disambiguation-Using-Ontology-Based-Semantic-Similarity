package org.xldb.database;

/**
 * @author dsbatista
 *
 */

public class GeoAdministrative {

	public long f_id;
	
	public String t_id;
	public String n_cap_name;
	
	public long male_population;
	public long female_population;
	
	public GeoAdministrative(Long f_id, String t_id, String n_cap_name) {
		
		this.f_id = f_id;
		this.t_id = t_id;
		this.n_cap_name = n_cap_name;
	}
	
	public GeoAdministrative(Long f_id) {
		
		this.f_id = f_id;
	}
}
