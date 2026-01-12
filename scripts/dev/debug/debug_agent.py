"""Debug script to test agent behavior."""

from agents.coordinator import coordinator
from shared.db import get_collection, TASKS_COLLECTION, PROJECTS_COLLECTION

print("="*60)
print("DEBUG: Testing Agent vs Direct Database Query")
print("="*60)

# Test 1: Direct database query
print("\n1. Direct Database Query:")
tasks_collection = get_collection(TASKS_COLLECTION)
projects_collection = get_collection(PROJECTS_COLLECTION)

task_count = tasks_collection.count_documents({})
project_count = projects_collection.count_documents({})

print(f"   Tasks in database: {task_count}")
print(f"   Projects in database: {project_count}")

# Show a few tasks
print("\n   Sample tasks:")
for task in tasks_collection.find({}).limit(3):
    print(f"   - {task['title']} (status: {task['status']})")

# Test 2: Agent query
print("\n2. Testing Agent with 'What tasks do I have?'")
print("   Calling coordinator.process()...")

try:
    response = coordinator.process("What tasks do I have?", conversation_history=None)
    print(f"\n   Agent Response:\n   {response}")
except Exception as e:
    print(f"\n   ✗ Error: {e}")
    import traceback
    traceback.print_exc()

# Test 3: Direct worklog agent call
print("\n3. Testing Worklog Agent directly:")
from agents.worklog import worklog_agent

try:
    result = worklog_agent.execute_tool("list_tasks", {})
    print(f"   Tool result: {result}")
    print(f"   Success: {result.get('success')}")
    print(f"   Count: {result.get('count')}")
    if result.get('tasks'):
        print(f"   First task: {result['tasks'][0]['title']}")
except Exception as e:
    print(f"   ✗ Error: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "="*60)
