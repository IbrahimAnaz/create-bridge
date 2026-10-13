import json

with open(r'C:\Users\ibrah\.gemini\antigravity\brain\2e73f15e-247d-43d2-bd07-0151c73e28d8\.system_generated\logs\transcript.jsonl', 'r', encoding='utf-8') as f:
    for line in f:
        obj = json.loads(line)
        idx = obj.get('step_index', 0)
        if 5635 <= idx <= 5645:
            c = str(obj.get('content', ''))
            print(f"Step {idx} ({obj.get('source')} / {obj.get('type')}): {c[:300]}")
