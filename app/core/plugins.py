"""
Plugin system for dynamic loading and extension
"""
import importlib
import inspect
from typing import Any, Dict, List, Optional, Type, Callable
from pathlib import Path
import sys

from .logging import get_logger
from .config import settings

logger = get_logger(__name__)

class PluginInterface:
    """Base interface for all plugins"""
    
    def __init__(self, name: str, version: str = "1.0.0"):
        self.name = name
        self.version = version
        self.enabled = True
    
    def initialize(self) -> bool:
        """Initialize the plugin"""
        raise NotImplementedError
    
    def cleanup(self) -> None:
        """Cleanup the plugin"""
        raise NotImplementedError
    
    def get_info(self) -> Dict[str, Any]:
        """Get plugin information"""
        return {
            "name": self.name,
            "version": self.version,
            "enabled": self.enabled
        }

class PluginManager:
    """Plugin manager for loading and managing plugins"""
    
    def __init__(self):
        self.plugins: Dict[str, PluginInterface] = {}
        self.plugin_paths: List[Path] = []
        self._load_plugin_paths()
    
    def _load_plugin_paths(self) -> None:
        """Load plugin paths from configuration"""
        plugin_paths = getattr(settings, 'PLUGIN_PATHS', [])
        if plugin_paths:
            for path_str in plugin_paths:
                path = Path(path_str)
                if path.exists():
                    self.plugin_paths.append(path)
                    if str(path) not in sys.path:
                        sys.path.append(str(path))
    
    def load_plugin(self, plugin_path: str) -> Optional[PluginInterface]:
        """Load a plugin from a file path"""
        try:
            # Import the plugin module
            spec = importlib.util.spec_from_file_location("plugin", plugin_path)
            if spec is None or spec.loader is None:
                logger.error(f"Could not load plugin from {plugin_path}")
                return None
            
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            
            # Find the plugin class
            plugin_class = None
            for name, obj in inspect.getmembers(module):
                if (inspect.isclass(obj) and 
                    issubclass(obj, PluginInterface) and 
                    obj != PluginInterface):
                    plugin_class = obj
                    break
            
            if plugin_class is None:
                logger.error(f"No plugin class found in {plugin_path}")
                return None
            
            # Create plugin instance
            plugin = plugin_class()
            if plugin.initialize():
                self.plugins[plugin.name] = plugin
                logger.info(f"Loaded plugin: {plugin.name} v{plugin.version}")
                return plugin
            else:
                logger.error(f"Failed to initialize plugin: {plugin.name}")
                return None
                
        except Exception as e:
            logger.error(f"Error loading plugin from {plugin_path}: {e}")
            return None
    
    def load_plugins_from_directory(self, directory: Path) -> List[PluginInterface]:
        """Load all plugins from a directory"""
        loaded_plugins = []
        
        if not directory.exists():
            logger.warning(f"Plugin directory does not exist: {directory}")
            return loaded_plugins
        
        for plugin_file in directory.glob("*.py"):
            if plugin_file.name.startswith("__"):
                continue
            
            plugin = self.load_plugin(str(plugin_file))
            if plugin:
                loaded_plugins.append(plugin)
        
        return loaded_plugins
    
    def load_all_plugins(self) -> List[PluginInterface]:
        """Load all plugins from configured paths"""
        loaded_plugins = []
        
        for plugin_path in self.plugin_paths:
            if plugin_path.is_file():
                plugin = self.load_plugin(str(plugin_path))
                if plugin:
                    loaded_plugins.append(plugin)
            elif plugin_path.is_dir():
                plugins = self.load_plugins_from_directory(plugin_path)
                loaded_plugins.extend(plugins)
        
        return loaded_plugins
    
    def get_plugin(self, name: str) -> Optional[PluginInterface]:
        """Get a plugin by name"""
        return self.plugins.get(name)
    
    def enable_plugin(self, name: str) -> bool:
        """Enable a plugin"""
        plugin = self.get_plugin(name)
        if plugin:
            plugin.enabled = True
            logger.info(f"Enabled plugin: {name}")
            return True
        return False
    
    def disable_plugin(self, name: str) -> bool:
        """Disable a plugin"""
        plugin = self.get_plugin(name)
        if plugin:
            plugin.enabled = False
            logger.info(f"Disabled plugin: {name}")
            return True
        return False
    
    def unload_plugin(self, name: str) -> bool:
        """Unload a plugin"""
        plugin = self.get_plugin(name)
        if plugin:
            plugin.cleanup()
            del self.plugins[name]
            logger.info(f"Unloaded plugin: {name}")
            return True
        return False
    
    def get_all_plugins(self) -> Dict[str, PluginInterface]:
        """Get all loaded plugins"""
        return self.plugins.copy()
    
    def cleanup_all(self) -> None:
        """Cleanup all plugins"""
        for plugin in self.plugins.values():
            try:
                plugin.cleanup()
            except Exception as e:
                logger.error(f"Error cleaning up plugin {plugin.name}: {e}")
        
        self.plugins.clear()
        logger.info("All plugins cleaned up")

# Global plugin manager instance
plugin_manager = PluginManager()

def initialize_plugins() -> List[PluginInterface]:
    """Initialize all plugins"""
    logger.info("Initializing plugins...")
    return plugin_manager.load_all_plugins()

def cleanup_plugins() -> None:
    """Cleanup all plugins"""
    logger.info("Cleaning up plugins...")
    plugin_manager.cleanup_all()

def get_plugin(name: str) -> Optional[PluginInterface]:
    """Get a plugin by name"""
    return plugin_manager.get_plugin(name)

def get_all_plugins() -> Dict[str, PluginInterface]:
    """Get all loaded plugins"""
    return plugin_manager.get_all_plugins()