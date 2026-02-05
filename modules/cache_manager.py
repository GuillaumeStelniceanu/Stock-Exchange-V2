#modules/cache_manager.py
import json
import pickle
import hashlib
import time
from datetime import datetime, timedelta
from typing import Any, Optional, Dict
import logging
import os

logger = logging.getLogger(__name__)

class CacheManager:
    """Gestionnaire de cache avancé"""
    
    def __init__(self, cache_dir: str = ".cache", default_ttl: int = 300):
        """
        Initialise le gestionnaire de cache
        
        Args:
            cache_dir: Répertoire pour stocker le cache
            default_ttl: Time To Live par défaut en secondes
        """
        self.cache_dir = cache_dir
        self.default_ttl = default_ttl
        self.memory_cache = {}
        
        # Créer le répertoire de cache si nécessaire
        os.makedirs(cache_dir, exist_ok=True)
        
        # Nettoyer le cache expiré au démarrage
        self._clean_expired()
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        Récupère une valeur du cache
        
        Args:
            key: Clé du cache
            default: Valeur par défaut si non trouvée
        
        Returns:
            La valeur mise en cache ou la valeur par défaut
        """
        # D'abord vérifier le cache mémoire
        if key in self.memory_cache:
            item = self.memory_cache[key]
            if self._is_valid(item):
                logger.debug(f"Cache mémoire hit pour {key}")
                return item['value']
            else:
                del self.memory_cache[key]
        
        # Ensuite vérifier le cache disque
        cache_file = self._get_cache_file(key)
        if os.path.exists(cache_file):
            try:
                with open(cache_file, 'rb') as f:
                    item = pickle.load(f)
                
                if self._is_valid(item):
                    logger.debug(f"Cache disque hit pour {key}")
                    
                    # Mettre aussi en cache mémoire pour les prochaines lectures
                    self.memory_cache[key] = item
                    
                    return item['value']
                else:
                    # Supprimer le fichier expiré
                    os.remove(cache_file)
                    
            except (pickle.PickleError, EOFError, FileNotFoundError) as e:
                logger.warning(f"Erreur lors de la lecture du cache pour {key}: {str(e)}")
        
        logger.debug(f"Cache miss pour {key}")
        return default
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """
        Met une valeur en cache
        
        Args:
            key: Clé du cache
            value: Valeur à mettre en cache
            ttl: Time To Live en secondes (None pour utiliser la valeur par défaut)
        """
        if ttl is None:
            ttl = self.default_ttl
        
        item = {
            'value': value,
            'timestamp': time.time(),
            'ttl': ttl
        }
        
        # Mettre en cache mémoire
        self.memory_cache[key] = item
        
        # Mettre en cache disque
        try:
            cache_file = self._get_cache_file(key)
            with open(cache_file, 'wb') as f:
                pickle.dump(item, f)
            
            logger.debug(f"Valeur mise en cache pour {key} (TTL: {ttl}s)")
            
        except Exception as e:
            logger.error(f"Erreur lors de l'écriture du cache pour {key}: {str(e)}")
    
    def delete(self, key: str) -> bool:
        """
        Supprime une valeur du cache
        
        Args:
            key: Clé à supprimer
        
        Returns:
            True si supprimé, False sinon
        """
        deleted = False
        
        # Supprimer du cache mémoire
        if key in self.memory_cache:
            del self.memory_cache[key]
            deleted = True
        
        # Supprimer du cache disque
        cache_file = self._get_cache_file(key)
        if os.path.exists(cache_file):
            try:
                os.remove(cache_file)
                deleted = True
            except OSError as e:
                logger.error(f"Erreur lors de la suppression du cache pour {key}: {str(e)}")
        
        if deleted:
            logger.debug(f"Cache supprimé pour {key}")
        
        return deleted
    
    def clear(self) -> None:
        """Vide tout le cache"""
        # Vider le cache mémoire
        self.memory_cache.clear()
        
        # Vider le cache disque
        try:
            for filename in os.listdir(self.cache_dir):
                file_path = os.path.join(self.cache_dir, filename)
                try:
                    if os.path.isfile(file_path):
                        os.remove(file_path)
                except Exception as e:
                    logger.error(f"Erreur lors de la suppression de {file_path}: {str(e)}")
            
            logger.info("Cache entièrement vidé")
            
        except Exception as e:
            logger.error(f"Erreur lors du vidage du cache: {str(e)}")
    
    def get_stats(self) -> Dict[str, Any]:
        """Retourne les statistiques du cache"""
        memory_count = len(self.memory_cache)
        
        try:
            disk_count = len([f for f in os.listdir(self.cache_dir) 
                            if os.path.isfile(os.path.join(self.cache_dir, f))])
        except:
            disk_count = 0
        
        # Calculer la taille du cache disque
        total_size = 0
        try:
            for filename in os.listdir(self.cache_dir):
                filepath = os.path.join(self.cache_dir, filename)
                if os.path.isfile(filepath):
                    total_size += os.path.getsize(filepath)
        except:
            total_size = 0
        
        return {
            'memory_entries': memory_count,
            'disk_entries': disk_count,
            'total_size_bytes': total_size,
            'total_size_mb': total_size / (1024 * 1024),
            'default_ttl': self.default_ttl,
            'cache_dir': os.path.abspath(self.cache_dir)
        }
    
    def _get_cache_file(self, key: str) -> str:
        """Génère le chemin du fichier de cache pour une clé"""
        # Hasher la clé pour créer un nom de fichier sécurisé
        key_hash = hashlib.md5(key.encode()).hexdigest()
        return os.path.join(self.cache_dir, f"{key_hash}.cache")
    
    def _is_valid(self, item: Dict) -> bool:
        """Vérifie si un élément de cache est toujours valide"""
        if not item:
            return False
        
        timestamp = item.get('timestamp', 0)
        ttl = item.get('ttl', self.default_ttl)
        
        return time.time() - timestamp < ttl
    
    def _clean_expired(self) -> None:
        """Nettoie les éléments de cache expirés"""
        expired_count = 0
        
        try:
            for filename in os.listdir(self.cache_dir):
                file_path = os.path.join(self.cache_dir, filename)
                
                if os.path.isfile(file_path) and filename.endswith('.cache'):
                    try:
                        with open(file_path, 'rb') as f:
                            item = pickle.load(f)
                        
                        if not self._is_valid(item):
                            os.remove(file_path)
                            expired_count += 1
                            
                    except (pickle.PickleError, EOFError):
                        # Fichier corrompu, le supprimer
                        os.remove(file_path)
                        expired_count += 1
            
            if expired_count > 0:
                logger.info(f"{expired_count} fichiers de cache expirés nettoyés")
                
        except Exception as e:
            logger.error(f"Erreur lors du nettoyage du cache: {str(e)}")
    
    def cache_decorator(self, ttl: Optional[int] = None):
        """
        Décorateur pour mettre en cache les résultats de fonctions
        
        Args:
            ttl: Time To Live en secondes
        """
        def decorator(func):
            def wrapper(*args, **kwargs):
                # Créer une clé de cache basée sur la fonction et ses arguments
                cache_key = self._generate_cache_key(func.__name__, args, kwargs)
                
                # Essayer de récupérer du cache
                cached_result = self.get(cache_key)
                if cached_result is not None:
                    return cached_result
                
                # Exécuter la fonction
                result = func(*args, **kwargs)
                
                # Mettre en cache le résultat
                self.set(cache_key, result, ttl)
                
                return result
            
            return wrapper
        
        return decorator
    
    def _generate_cache_key(self, func_name: str, args: tuple, kwargs: dict) -> str:
        """Génère une clé de cache unique"""
        # Convertir les arguments en chaîne
        args_str = str(args)
        kwargs_str = str(sorted(kwargs.items()))
        
        # Combiner pour créer la clé
        key_string = f"{func_name}:{args_str}:{kwargs_str}"
        
        # Hasher pour obtenir une clé de longueur fixe
        return hashlib.md5(key_string.encode()).hexdigest()