<<<<<<< HEAD
"""
Test Script for Project Samarth
Run this to verify all queries work before demo
"""

from data_collector import DataCollector
from query_engine_2 import QueryEngine
import os

# Sample test queries
TEST_QUERIES = [
    "Compare average annual rainfall in Punjab and Haryana for the last 5 years and list top 3 most produced crops",
    "Which district has highest wheat production in Punjab?",
    "Analyze rice production trend in UP over last decade and correlate with rainfall",
    "What are three data-backed arguments for promoting drought-resistant crops?"
]

def test_system():
    """Run comprehensive system test"""
    
    print("=" * 60)
    print("PROJECT SAMARTH - SYSTEM TEST")
    print("=" * 60)
    
    # Get API key
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("\n❌ Error: GEMINI_API_KEY not set")
        print("Set it with: export GEMINI_API_KEY='your_key'")
        return False
    
    # Load data
    print("\n📊 Loading data...")
    try:
        collector = DataCollector()
        data = collector.get_all_data()
        print(f"✅ Crop production records: {len(data['crop_production'])}")
        print(f"✅ Rainfall records: {len(data['rainfall'])}")
    except Exception as e:
        print(f"❌ Data loading failed: {e}")
        return False
    
    # Initialize engine
    print("\n🤖 Initializing query engine...")
    try:
        engine = QueryEngine(api_key, data)
        print("✅ Query engine ready")
    except Exception as e:
        print(f"❌ Engine initialization failed: {e}")
        return False
    
    # Test queries
    print("\n🧪 Testing sample queries...\n")
    passed = 0
    failed = 0
    
    for i, query in enumerate(TEST_QUERIES, 1):
        print(f"\n{'='*60}")
        print(f"Test {i}/{len(TEST_QUERIES)}")
        print(f"Q: {query}")
        print('-' * 60)
        
        try:
            result = engine.answer_question(query)
            
            if result.get('answer'):
                print("✅ PASSED")
                print(f"Answer preview: {result['answer'][:200]}...")
                print(f"Sources: {len(result.get('sources', []))}")
                passed += 1
            else:
                print("❌ FAILED - No answer generated")
                failed += 1
                
        except Exception as e:
            print(f"❌ FAILED - Error: {e}")
            failed += 1
    
    # Summary
    print(f"\n{'='*60}")
    print("TEST SUMMARY")
    print(f"{'='*60}")
    print(f"✅ Passed: {passed}/{len(TEST_QUERIES)}")
    print(f"❌ Failed: {failed}/{len(TEST_QUERIES)}")
    print(f"Success Rate: {(passed/len(TEST_QUERIES)*100):.1f}%")
    
    if passed == len(TEST_QUERIES):
        print("\n🎉 ALL TESTS PASSED! System ready for demo.")
        return True
    else:
        print("\n⚠️  Some tests failed. Review errors above.")
        return False

if __name__ == "__main__":
    success = test_system()
=======
"""
Test Script for Project Samarth
Run this to verify all queries work before demo
"""

from data_collector import DataCollector
from query_engine_2 import QueryEngine
import os

# Sample test queries
TEST_QUERIES = [
    "Compare average annual rainfall in Punjab and Haryana for the last 5 years and list top 3 most produced crops",
    "Which district has highest wheat production in Punjab?",
    "Analyze rice production trend in UP over last decade and correlate with rainfall",
    "What are three data-backed arguments for promoting drought-resistant crops?"
]

def test_system():
    """Run comprehensive system test"""
    
    print("=" * 60)
    print("PROJECT SAMARTH - SYSTEM TEST")
    print("=" * 60)
    
    # Get API key
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("\n❌ Error: GEMINI_API_KEY not set")
        print("Set it with: export GEMINI_API_KEY='your_key'")
        return False
    
    # Load data
    print("\n📊 Loading data...")
    try:
        collector = DataCollector()
        data = collector.get_all_data()
        print(f"✅ Crop production records: {len(data['crop_production'])}")
        print(f"✅ Rainfall records: {len(data['rainfall'])}")
    except Exception as e:
        print(f"❌ Data loading failed: {e}")
        return False
    
    # Initialize engine
    print("\n🤖 Initializing query engine...")
    try:
        engine = QueryEngine(api_key, data)
        print("✅ Query engine ready")
    except Exception as e:
        print(f"❌ Engine initialization failed: {e}")
        return False
    
    # Test queries
    print("\n🧪 Testing sample queries...\n")
    passed = 0
    failed = 0
    
    for i, query in enumerate(TEST_QUERIES, 1):
        print(f"\n{'='*60}")
        print(f"Test {i}/{len(TEST_QUERIES)}")
        print(f"Q: {query}")
        print('-' * 60)
        
        try:
            result = engine.answer_question(query)
            
            if result.get('answer'):
                print("✅ PASSED")
                print(f"Answer preview: {result['answer'][:200]}...")
                print(f"Sources: {len(result.get('sources', []))}")
                passed += 1
            else:
                print("❌ FAILED - No answer generated")
                failed += 1
                
        except Exception as e:
            print(f"❌ FAILED - Error: {e}")
            failed += 1
    
    # Summary
    print(f"\n{'='*60}")
    print("TEST SUMMARY")
    print(f"{'='*60}")
    print(f"✅ Passed: {passed}/{len(TEST_QUERIES)}")
    print(f"❌ Failed: {failed}/{len(TEST_QUERIES)}")
    print(f"Success Rate: {(passed/len(TEST_QUERIES)*100):.1f}%")
    
    if passed == len(TEST_QUERIES):
        print("\n🎉 ALL TESTS PASSED! System ready for demo.")
        return True
    else:
        print("\n⚠️  Some tests failed. Review errors above.")
        return False

if __name__ == "__main__":
    success = test_system()
>>>>>>> 682e4b9c (Initial commit of Project Samarth)
    exit(0 if success else 1)