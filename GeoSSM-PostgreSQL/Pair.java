
public class Pair {
	
	long t1;
	long t2;
	
	public Pair(long id1, long  id2) {
		this.t1 = id1;
		this.t2 = id2;
	}

	@Override
	public int hashCode() {
		final int prime = 31;
		int result = 1;
		result = prime * result + (int) (t1 ^ (t1 >>> 32));
		result = prime * result + (int) (t2 ^ (t2 >>> 32));
		return result;
	}
	
	@Override
	public boolean equals(Object obj) {
		
		if (this == obj)
			return true;
		
		if (obj == null)
			return false;
		
		if (getClass() != obj.getClass())
			return false;
		
		Pair other = (Pair) obj;
		
		if ( (t1 == other.t1 && t2 == other.t2) || (t1 == other.t2 && t2 == other.t1) ) {
			return true;
		}
		else return false;
	}
}
