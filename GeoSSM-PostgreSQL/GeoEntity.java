/********************************************************************************************
 * Class for a generic interface of GeoName and GeoTerm
 * Programmer: Francisco Couto 
 * Date: April 2010
 ********************************************************************************************/
 
public interface GeoEntity
{
    public String getName();
    public double SSM(GeoEntity e, String measure, String infoTable) throws Exception;
    public String toXML();
}