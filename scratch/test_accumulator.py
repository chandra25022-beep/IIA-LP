"""Test accumulator pipeline directly"""
import sys, os
sys.path.insert(0, 'backend')
from app.config import DB_CAPTURE, DB_INSURANCE, DB_REGISTRATION, DB_THEFT, DB_MINISTRY
from app.integration.context_engine import ContextDiscoveryEngine, UnstructuredSearchEngine, ContextAccumulator

plate = 'DL7CQ1939'

# Step 1: local capture
capture_ctx = ContextDiscoveryEngine.discover_capture_context(DB_CAPTURE, plate)
print('capture_ctx found:', capture_ctx.get('found'))

# Step 2: local insurance + registration (fallback)
ins_ctx = ContextDiscoveryEngine.discover_insurance_context(DB_INSURANCE, plate)
reg_ctx = ContextDiscoveryEngine.discover_registration_context(DB_REGISTRATION, plate)
print('insurance found:', ins_ctx.get('found'))
print('registration found:', reg_ctx.get('found'))

# Step 3: local theft + ministry (fallback)
theft_ctx = ContextDiscoveryEngine.discover_theft_context(DB_THEFT, plate)
min_ctx = ContextDiscoveryEngine.discover_ministry_context(DB_MINISTRY, plate)
print('theft found:', theft_ctx.get('found'))
print('ministry found:', min_ctx.get('found'))

# Accumulate
all_contexts = [capture_ctx, ins_ctx, reg_ctx, theft_ctx, min_ctx]
eng = UnstructuredSearchEngine()
acc = ContextAccumulator(eng)
result = acc.accumulate_context(plate, all_contexts)
print()
print('=== ACCUMULATED RESULT ===')
print('nodes_queried:', result.get('nodes_queried'))
print('fk_tables_joined:', result.get('fk_tables_joined'))
print('structured_results keys:', list(result.get('structured_results', {}).keys()))
print('unstructured_results count:', len(result.get('unstructured_results', [])))
print('context_summary length:', len(result.get('context_summary', '')))
if result.get('unstructured_results'):
    for doc in result['unstructured_results'][:3]:
        print(f"  Doc: {doc.get('document')}, score: {doc.get('relevance_score')}")
print()
print('context_summary:')
print(result.get('context_summary', ''))
