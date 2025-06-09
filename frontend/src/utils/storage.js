class Storage {
  constructor(prefix = 'app_') {
    this.prefix = prefix;
    this.cache = new Map();
  }

  getKey(key) {
    return `${this.prefix}${key}`;
  }

  set(key, value, ttl = null) {
    const data = {
      value,
      timestamp: Date.now(),
      ttl
    };

    try {
      const serialized = JSON.stringify(data);
      localStorage.setItem(this.getKey(key), serialized);
      this.cache.set(key, data);
    } catch (error) {
      console.error('Error saving to localStorage:', error);
    }
  }

  get(key) {
    // Check cache first
    if (this.cache.has(key)) {
      const data = this.cache.get(key);
      if (!data.ttl || Date.now() - data.timestamp < data.ttl) {
        return data.value;
      }
      this.remove(key);
      return null;
    }

    try {
      const serialized = localStorage.getItem(this.getKey(key));
      if (!serialized) return null;

      const data = JSON.parse(serialized);
      
      // Check TTL
      if (data.ttl && Date.now() - data.timestamp > data.ttl) {
        this.remove(key);
        return null;
      }

      this.cache.set(key, data);
      return data.value;
    } catch (error) {
      console.error('Error reading from localStorage:', error);
      return null;
    }
  }

  remove(key) {
    try {
      localStorage.removeItem(this.getKey(key));
      this.cache.delete(key);
    } catch (error) {
      console.error('Error removing from localStorage:', error);
    }
  }

  clear() {
    try {
      Object.keys(localStorage)
        .filter(key => key.startsWith(this.prefix))
        .forEach(key => localStorage.removeItem(key));
      this.cache.clear();
    } catch (error) {
      console.error('Error clearing localStorage:', error);
    }
  }

  // Batch operations
  setMultiple(items) {
    items.forEach(({ key, value, ttl }) => this.set(key, value, ttl));
  }

  getMultiple(keys) {
    return keys.reduce((result, key) => {
      result[key] = this.get(key);
      return result;
    }, {});
  }

  removeMultiple(keys) {
    keys.forEach(key => this.remove(key));
  }
}

export default new Storage(); 