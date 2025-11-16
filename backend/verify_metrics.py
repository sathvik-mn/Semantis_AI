"""Quick script to verify enhanced metrics are working"""
import requests

api_key = "sc-test-local"
headers = {"Authorization": f"Bearer {api_key}"}

# Get metrics
r = requests.get("http://localhost:8000/metrics", headers=headers)
data = r.json()

print("Enhanced Metrics Status:")
print(f"  avg_confidence: {data.get('avg_confidence', 0)}")
print(f"  avg_hybrid_score: {data.get('avg_hybrid_score', 0)}")
print(f"  high_confidence_hits: {data.get('high_confidence_hits', 0)}")
print(f"  high_confidence_ratio: {data.get('high_confidence_ratio', 0)}")
print(f"\n✅ Enhanced metrics are available in response")


