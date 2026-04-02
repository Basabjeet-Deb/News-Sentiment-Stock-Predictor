"""
Cache Manager - Cache frequently accessed data for faster performance
"""
import json
import os
from datetime import datetime, timedelta
from typing import Any, Optional
import pandas as pd


class CacheManager:
    """Manages caching of news, prices, and predictions"""
    
    def __init__(self, cache_dir: str = None):
        if cache_dir is None:
            current_dir = os.path.dirname(os.path.abspath(__file__))
            self.cache_dir = os.path.join(os.path.dirname(current_dir), "data", ".cache")
        else:
            self.cache_dir = cache_dir
        
        # Create cache directory if it doesn't exist
        os.makedirs(self.cache_dir, exist_ok=True)
        
        # Cache TTL (Time To Live) in seconds
        self.ttl = {
            'prices': 300,        # 5 minutes
            'news': 3600,         # 1 hour
            'predictions': 900,   # 15 minutes
            'sentiment': 3600,    # 1 hour
        }
    
    def _get_cache_path(self, key: str) -> str:
        """Get cache file path for a key"""
        return os.path.join(self.cache_dir, f"{key}.cache")
    
    def _get_metadata_path(self, key: str) -> str:
        """Get metadata file path for a key"""
        return os.path.join(self.cache_dir, f"{key}.meta")
    
    def _is_expired(self, key: str, ttl: int) -> bool:
        """Check if cache is expired"""
        meta_path = self._get_metadata_path(key)
        
        if not os.path.exists(meta_path):
            return True
        
        try:
            with open(meta_path, 'r') as f:
                metadata = json.load(f)
            
            cached_time = datetime.fromisoformat(metadata['timestamp'])
            expiry_time = cached_time + timedelta(seconds=ttl)
            
            return datetime.now() > expiry_time
        except:
            return True
    
    def get(self, key: str, data_type: str = 'json') -> Optional[Any]:
        """
        Get data from cache
        
        Args:
            key: Cache key (e.g., 'prices', 'news', 'predictions')
            data_type: 'json', 'csv', or 'dataframe'
        
        Returns:
            Cached data or None if expired/missing
        """
        cache_path = self._get_cache_path(key)
        
        # Check if cache exists
        if not os.path.exists(cache_path):
            return None
        
        # Check if expired
        ttl = self.ttl.get(key, 3600)  # Default 1 hour
        if self._is_expired(key, ttl):
            return None
        
        # Load from cache
        try:
            if data_type == 'json':
                with open(cache_path, 'r') as f:
                    return json.load(f)
            elif data_type == 'csv' or data_type == 'dataframe':
                return pd.read_csv(cache_path)
            else:
                with open(cache_path, 'r') as f:
                    return f.read()
        except Exception as e:
            print(f"Error loading cache for {key}: {e}")
            return None
    
    def set(self, key: str, data: Any, data_type: str = 'json'):
        """
        Save data to cache
        
        Args:
            key: Cache key
            data: Data to cache
            data_type: 'json', 'csv', or 'dataframe'
        """
        cache_path = self._get_cache_path(key)
        meta_path = self._get_metadata_path(key)
        
        try:
            # Save data
            if data_type == 'json':
                with open(cache_path, 'w') as f:
                    json.dump(data, f)
            elif data_type == 'dataframe' or data_type == 'csv':
                if isinstance(data, pd.DataFrame):
                    data.to_csv(cache_path, index=False)
                else:
                    raise ValueError("Data must be a DataFrame for csv/dataframe type")
            else:
                with open(cache_path, 'w') as f:
                    f.write(str(data))
            
            # Save metadata
            metadata = {
                'timestamp': datetime.now().isoformat(),
                'key': key,
                'data_type': data_type,
                'ttl': self.ttl.get(key, 3600)
            }
            with open(meta_path, 'w') as f:
                json.dump(metadata, f)
            
        except Exception as e:
            print(f"Error saving cache for {key}: {e}")
    
    def invalidate(self, key: str):
        """Invalidate (delete) cache for a key"""
        cache_path = self._get_cache_path(key)
        meta_path = self._get_metadata_path(key)
        
        if os.path.exists(cache_path):
            os.remove(cache_path)
        if os.path.exists(meta_path):
            os.remove(meta_path)
    
    def clear_all(self):
        """Clear all cache"""
        for file in os.listdir(self.cache_dir):
            file_path = os.path.join(self.cache_dir, file)
            if os.path.isfile(file_path):
                os.remove(file_path)
    
    def get_cache_info(self) -> dict:
        """Get information about all cached items"""
        info = {}
        
        for file in os.listdir(self.cache_dir):
            if file.endswith('.meta'):
                key = file.replace('.meta', '')
                meta_path = os.path.join(self.cache_dir, file)
                
                try:
                    with open(meta_path, 'r') as f:
                        metadata = json.load(f)
                    
                    cached_time = datetime.fromisoformat(metadata['timestamp'])
                    ttl = metadata.get('ttl', 3600)
                    expiry_time = cached_time + timedelta(seconds=ttl)
                    is_expired = datetime.now() > expiry_time
                    
                    info[key] = {
                        'cached_at': metadata['timestamp'],
                        'expires_at': expiry_time.isoformat(),
                        'ttl_seconds': ttl,
                        'is_expired': is_expired,
                        'data_type': metadata.get('data_type', 'unknown')
                    }
                except:
                    pass
        
        return info
    
    def print_cache_info(self):
        """Print cache information in readable format"""
        info = self.get_cache_info()
        
        print("\n" + "=" * 70)
        print("CACHE STATUS")
        print("=" * 70)
        
        if not info:
            print("No cached data")
        else:
            for key, data in info.items():
                status = "❌ Expired" if data['is_expired'] else "✅ Valid"
                print(f"\n{key}:")
                print(f"  Status: {status}")
                print(f"  Cached: {data['cached_at']}")
                print(f"  Expires: {data['expires_at']}")
                print(f"  TTL: {data['ttl_seconds']}s")
                print(f"  Type: {data['data_type']}")
        
        print("=" * 70 + "\n")


if __name__ == "__main__":
    # Test cache manager
    cache = CacheManager()
    
    # Test JSON cache
    test_data = {'test': 'data', 'timestamp': datetime.now().isoformat()}
    cache.set('test', test_data, 'json')
    
    # Retrieve
    retrieved = cache.get('test', 'json')
    print(f"Retrieved: {retrieved}")
    
    # Show cache info
    cache.print_cache_info()
    
    # Clear test cache
    cache.invalidate('test')
