#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test for responsive design improvements
"""

import sys
import os
import unittest

# Add the project root to the path
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

class TestResponsiveDesignImprovements(unittest.TestCase):
    """Test cases for responsive design improvements"""
    
    def setUp(self):
        """Set up test fixtures before each test method."""
        from responsive_design import AdvancedResponsiveDesign
        self.responsive = AdvancedResponsiveDesign(1920, 1080)
    
    def test_cache_management(self):
        """Test cache management improvements."""
        # Test that cache cleanup works
        initial_cache_size = sum(len(cache) for cache in self.responsive._unified_cache.values())
        
        # Add some items to cache
        for i in range(50):
            self.responsive._unified_cache['fonts'][i] = i * 2
        
        # Check cache size increased
        new_cache_size = sum(len(cache) for cache in self.responsive._unified_cache.values())
        self.assertGreater(new_cache_size, initial_cache_size)
        
        # Test cache cleanup
        self.responsive.clear_caches()
        
        # Check cache is cleared
        cleared_cache_size = sum(len(cache) for cache in self.responsive._unified_cache.values())
        self.assertEqual(cleared_cache_size, 0)
    
    def test_performance_profile(self):
        """Test performance profile functionality."""
        # Test that we get a valid performance profile
        profile = self.responsive.get_performance_settings()
        self.assertIsInstance(profile, dict)
        self.assertIn("fps_target", profile)
        self.assertIn("enable_shadows", profile)
    
    def test_rendering_optimizations(self):
        """Test rendering optimizations."""
        # Test that we get rendering optimizations
        optimizations = self.responsive.get_rendering_optimizations()
        self.assertIsInstance(optimizations, dict)
        self.assertIn("enable_shadows", optimizations)
        self.assertIn("enable_animations", optimizations)
        self.assertIn("render_quality", optimizations)

def run_responsive_tests():
    """Run responsive design tests."""
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(TestResponsiveDesignImprovements))
    
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    return result.wasSuccessful()

if __name__ == "__main__":
    success = run_responsive_tests()
    sys.exit(0 if success else 1)