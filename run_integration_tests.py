#!/usr/bin/env python3
import sys
from parsers.dom_parser import HardenedDOMParser
from data_alchemist import DataAlchemist

# Mocking a corrupted DOM Node structure to test structural fallback safety
class MockCorruptedNode:
    def find(self, *args, **kwargs):
        raise AttributeError("Simulated unexpected DOM restructuring error.")

def test_pipeline_hardening():
    print("[+] Test 1: Testing DOM Parser resilience against total structural failures...")
    mock_node = MockCorruptedNode()
    result = HardenedDOMParser.extract_metrics_safely(mock_node)
    
    assert result["title"] == "Unknown Title"
    assert result["score"] == 0
    print("[PASS] DOM Parser caught exception gracefully and preserved isolation state.")

def test_alchemist_optimization():
    print("[+] Test 2: Testing Alchemist efficiency arrays...")
    mock_raw_data = [
        {"title": "Valid Post 1", "url": "https://test.one", "score": 100},
        {"title": "   ", "url": "https://corrupted.data", "score": 0}, # Should drop
        {"title": "Valid Post 2", "url": "https://test.two", "score": "not_an_int"} # Should adjust to 0
    ]
    
    processed = DataAlchemist.optimize_array_processing(mock_raw_data)
    assert len(processed) == 2
    assert processed[1]["score"] == 0
    print("[PASS] Data Alchemist filtered and structured dataset seamlessly.")

if __name__ == "__main__":
    try:
        test_pipeline_hardening()
        test_alchemist_optimization()
        print("\n==================================================")
        print("🎉 ALL REFINEMENT INTEGRATION TESTS PASSED NOMINALLY")
        print("==================================================")
    except AssertionError:
        print("[FAIL] Architecture tests failed validation checks.")
        sys.exit(1)
