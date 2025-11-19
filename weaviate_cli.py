#!/usr/bin/env python3
"""
Interactive Weaviate CLI Viewer
Navigate your Weaviate database from the command line
"""
import requests
import json
from typing import Optional

WEAVIATE_URL = "http://localhost:8080"

def print_header(text):
    print("\n" + "="*80)
    print(f"  {text}")
    print("="*80)

def print_menu(options):
    print("\nOptions:")
    for key, desc in options.items():
        print(f"  [{key}] {desc}")
    choice = input("\nSelect option: ").strip()
    return choice

def view_collections():
    """List all collections"""
    print_header("📚 COLLECTIONS")
    try:
        response = requests.get(f"{WEAVIATE_URL}/v1/schema")
        schema = response.json()

        for i, cls in enumerate(schema.get('classes', []), 1):
            print(f"\n{i}. {cls['class']}")
            print(f"   Description: {cls.get('description', 'N/A')}")
            print(f"   Properties: {len(cls.get('properties', []))}")
            print(f"   Multi-tenancy: {'Yes' if cls['multiTenancyConfig']['enabled'] else 'No'}")

        return [cls['class'] for cls in schema.get('classes', [])]
    except Exception as e:
        print(f"❌ Error: {e}")
        return []

def count_objects(collection):
    """Count objects in collection"""
    try:
        query = f"""{{
            Aggregate {{
                {collection} {{
                    meta {{ count }}
                }}
            }}
        }}"""

        response = requests.post(
            f"{WEAVIATE_URL}/v1/graphql",
            json={"query": query}
        )
        data = response.json()
        count = data['data']['Aggregate'][collection][0]['meta']['count']
        return count
    except:
        return 0

def browse_collection(collection):
    """Browse objects in a collection"""
    print_header(f"📄 BROWSING: {collection}")

    # Get count
    count = count_objects(collection)
    print(f"\n📊 Total objects: {count}")

    limit = input("\nHow many to display? [default: 10]: ").strip() or "10"

    # Determine fields based on collection
    if collection == "Documents":
        fields = "filename text_content category uploader_name created_at"
    elif collection == "Machinery":
        fields = "name manufacturer model serial_number"
    else:
        fields = "_additional { id }"

    query = f"""{{
        Get {{
            {collection}(limit: {limit}) {{
                {fields}
                _additional {{ id }}
            }}
        }}
    }}"""

    try:
        response = requests.post(
            f"{WEAVIATE_URL}/v1/graphql",
            json={"query": query}
        )
        data = response.json()
        objects = data['data']['Get'][collection]

        if not objects:
            print("\n⚠️  No objects found")
            return

        for i, obj in enumerate(objects, 1):
            print(f"\n{'─'*80}")
            print(f"Object {i} - ID: {obj['_additional']['id']}")
            print('─'*80)

            for key, value in obj.items():
                if key == '_additional':
                    continue

                # Truncate long text
                if isinstance(value, str) and len(value) > 200:
                    value = value[:200] + "..."

                print(f"  {key:20s}: {value}")

        print(f"\n{'─'*80}")

    except Exception as e:
        print(f"❌ Error: {e}")

def search_collection():
    """Search across a collection"""
    print_header("🔍 SEARCH")

    collection = input("Collection [Documents/Machinery]: ").strip() or "Documents"
    query_text = input("Search query: ").strip()

    if not query_text:
        print("❌ Query cannot be empty")
        return

    limit = input("Max results [default: 5]: ").strip() or "5"

    # Determine fields
    if collection == "Documents":
        fields = "filename text_content category uploader_name"
    else:
        fields = "name manufacturer model serial_number"

    query = f"""{{
        Get {{
            {collection}(
                hybrid: {{
                    query: "{query_text}"
                    alpha: 0.75
                }}
                limit: {limit}
            ) {{
                {fields}
                _additional {{
                    id
                    score
                }}
            }}
        }}
    }}"""

    try:
        response = requests.post(
            f"{WEAVIATE_URL}/v1/graphql",
            json={"query": query}
        )
        data = response.json()
        results = data['data']['Get'][collection]

        if not results:
            print("\n⚠️  No results found")
            return

        print(f"\n🎯 Found {len(results)} results:\n")

        for i, obj in enumerate(results, 1):
            score = obj['_additional']['score']
            print(f"\n{'─'*80}")
            print(f"Result {i} - Score: {score:.4f}")
            print('─'*80)

            for key, value in obj.items():
                if key == '_additional':
                    continue

                if isinstance(value, str) and len(value) > 200:
                    value = value[:200] + "..."

                print(f"  {key:20s}: {value}")

        print(f"\n{'─'*80}")

    except Exception as e:
        print(f"❌ Error: {e}")

def custom_graphql():
    """Execute custom GraphQL query"""
    print_header("⚡ CUSTOM GRAPHQL")

    print("\nExample queries:")
    print("1. Get Documents: {Get{Documents(limit:5){filename}}}")
    print("2. Count: {Aggregate{Documents{meta{count}}}}")
    print("3. Search: {Get{Documents(hybrid:{query:\"excavator\" alpha:0.75}){filename}}}")

    print("\nEnter your query (or 'back' to return):")
    lines = []
    while True:
        line = input()
        if line.strip().lower() == 'back':
            return
        lines.append(line)
        if line.strip().endswith('}') and lines[0].strip().startswith('{'):
            break

    query = '\n'.join(lines)

    try:
        response = requests.post(
            f"{WEAVIATE_URL}/v1/graphql",
            json={"query": query}
        )
        data = response.json()
        print("\n" + "="*80)
        print(json.dumps(data, indent=2))
        print("="*80)
    except Exception as e:
        print(f"❌ Error: {e}")

def main():
    # Check connection
    try:
        response = requests.get(f"{WEAVIATE_URL}/v1/.well-known/ready", timeout=5)
        if response.status_code != 200:
            print("❌ Weaviate is not ready")
            return
    except Exception as e:
        print(f"❌ Cannot connect to Weaviate at {WEAVIATE_URL}")
        print(f"   Error: {e}")
        return

    print("\n" + "="*80)
    print("  🗄️  WEAVIATE INTERACTIVE CLI")
    print("="*80)
    print("✅ Connected to Weaviate")

    collections = []

    while True:
        print_header("MAIN MENU")

        choice = print_menu({
            '1': 'View Collections',
            '2': 'Browse Collection Data',
            '3': 'Search',
            '4': 'Custom GraphQL Query',
            'q': 'Quit'
        })

        if choice == '1':
            collections = view_collections()
            input("\nPress Enter to continue...")

        elif choice == '2':
            if not collections:
                collections = view_collections()

            print("\nAvailable collections:")
            for i, c in enumerate(collections, 1):
                print(f"  {i}. {c}")

            coll_choice = input("\nSelect collection name or number: ").strip()

            # Handle numeric selection
            if coll_choice.isdigit():
                idx = int(coll_choice) - 1
                if 0 <= idx < len(collections):
                    coll_choice = collections[idx]

            if coll_choice in collections:
                browse_collection(coll_choice)
            else:
                print("❌ Invalid collection")

            input("\nPress Enter to continue...")

        elif choice == '3':
            search_collection()
            input("\nPress Enter to continue...")

        elif choice == '4':
            custom_graphql()
            input("\nPress Enter to continue...")

        elif choice.lower() == 'q':
            print("\n👋 Goodbye!")
            break

        else:
            print("❌ Invalid choice")

if __name__ == "__main__":
    main()
