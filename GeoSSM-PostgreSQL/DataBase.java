import java.sql.Connection;
import java.sql.DriverManager;
import java.sql.ResultSet;
import java.sql.SQLException;
import java.sql.Statement;

public class DataBase
{
    //PSQL connection variables
    public Connection con = null;
    public Statement state = null;
    
    //Default constructor
    
	public DataBase(String server, String db, String user, String pwd) {
		String url ="jdbc:postgresql://" + server + "/" + db;
		System.out.println("Connecting to: " + url);
		String userid = user;
    	String password = pwd;
    	
    	try {
			Class.forName("org.postgresql.Driver");
		} catch (ClassNotFoundException cnfe) {
			System.out.println("Couldn't find the driver!");
			System.out.println("Let's print a stack trace, and exit.");
			cnfe.printStackTrace();
			System.exit(1);
		}
		
    	try {
    		con = DriverManager.getConnection(url, userid, password);
		// System.out.println("CONECTED TO GEO DATABASE");

    	} catch(SQLException ex) {
    		System.err.println("SQLException: " + ex.getMessage());
    	}
	}
	
	//Query the database
	public ResultSet query(String q) throws Exception
	{
	    // System.out.println("SQL query: " + q);
		state = con.createStatement();
		return state.executeQuery(q);
	}

	//Update the database
	public void update(String u) throws Exception
	{
	    // System.out.println("SQL update: " + u);
		state = con.createStatement();
		state.executeUpdate(u);
	}

	//Closes the connection
	public void close() throws Exception
	{
	    state.close();
	    con.close();
    }
}
