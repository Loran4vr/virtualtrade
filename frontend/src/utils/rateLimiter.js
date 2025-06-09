class RateLimiter {
  constructor(maxRequests = 100, timeWindow = 60000) {
    this.maxRequests = maxRequests;
    this.timeWindow = timeWindow;
    this.requests = new Map();
  }

  canMakeRequest(key) {
    const now = Date.now();
    const userRequests = this.requests.get(key) || [];
    
    // Remove expired requests
    const validRequests = userRequests.filter(
      timestamp => now - timestamp < this.timeWindow
    );
    
    if (validRequests.length >= this.maxRequests) {
      return false;
    }
    
    validRequests.push(now);
    this.requests.set(key, validRequests);
    return true;
  }

  getRemainingRequests(key) {
    const now = Date.now();
    const userRequests = this.requests.get(key) || [];
    const validRequests = userRequests.filter(
      timestamp => now - timestamp < this.timeWindow
    );
    return this.maxRequests - validRequests.length;
  }

  getTimeUntilReset(key) {
    const now = Date.now();
    const userRequests = this.requests.get(key) || [];
    if (userRequests.length === 0) return 0;
    
    const oldestRequest = Math.min(...userRequests);
    const resetTime = oldestRequest + this.timeWindow;
    return Math.max(0, resetTime - now);
  }

  reset(key) {
    this.requests.delete(key);
  }
}

export default RateLimiter; 