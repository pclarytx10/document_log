#!/usr/bin/env python3
"""
Test script to verify document workflow without visualization dependencies
"""

from parent_child_state_changes import HierarchicalDocumentWorkflowManager

def test_policy_workflow():
    """Test the Policy Doc 001 journey with multiple children"""
    
    wf = HierarchicalDocumentWorkflowManager()
    
    print("Policy Doc 001 Journey:")
    print("======================")
    
    # Step 1: Charlie creates Policy Doc 001 → Draft
    wf.create_document('Policy Doc 001', user_id='Charlie', notes='Initial policy document created')
    print("1. Charlie creates Policy Doc 001 → Draft")
    
    # Step 2: Charlie submits for review → Review
    wf.log_state_change('Policy Doc 001', 'draft', 'review', 'Charlie', 'Submitted for initial review')
    print("2. Charlie submits for review → Review")
    
    # Step 3: Alice reviews and requests updates → Update
    wf.log_state_change('Policy Doc 001', 'review', 'update', 'Alice', 'Needs updates after review')
    print("3. Alice reviews and requests updates → Update")
    
    # Step 4: Charlie resubmits updated version → Review
    wf.log_state_change('Policy Doc 001', 'update', 'review', 'Charlie', 'Updated version submitted for review')
    print("4. Charlie resubmits updated version → Review")
    
    # Step 5: Alice reviews and requests major revisions → Revise (terminates Policy Doc 001, creates child)
    revision_result = wf.log_state_change('Policy Doc 001', 'review', 'revise', 'Alice', 'Major revisions needed, creating new version')
    print("5. Alice reviews and requests major revisions → Revise (terminates Policy Doc 001, creates child)")
    
    print("\nChild Document Journey (Policy Doc 002 in business terms):")
    print("=========================================================")
    
    # Step 6: System automatically creates child document → Draft
    child_doc_002_id = revision_result['child_document']
    print(f"6. System automatically creates child document → Draft ({child_doc_002_id})")
    
    # Step 7: Charlie submits revised version → Review
    wf.log_state_change(child_doc_002_id, 'draft', 'review', 'Charlie', 'Revised version ready for review')
    print("7. Charlie submits revised version → Review")
    
    # Step 8: Alice reviews and rejects → Reject
    wf.log_state_change(child_doc_002_id, 'review', 'reject', 'Alice', 'Still not meeting requirements, rejected')
    print("8. Alice reviews and rejects → Reject")
    
    print("\nChild Document Journey (Policy Doc 003 in business terms):")
    print("=========================================================")
    
    # Step 9: Charlie creates a new child document draft from Parent 001 → Draft
    child_doc_003_id = wf.create_document('Policy Doc 003', parent_id='Policy Doc 001', user_id='Charlie', notes='New draft based on Policy Doc 001 after rejection of first revision')
    print(f"9. Charlie creates a new child document draft from Parent 001 → Draft ({child_doc_003_id})")
    
    # Step 10: Charlie submits revised version → Review
    wf.log_state_change(child_doc_003_id, 'draft', 'review', 'Charlie', 'New revised version ready for review')
    print("10. Charlie submits revised version → Review")
    
    # Step 11: Alice reviews and grants final approval → Approve
    wf.log_state_change(child_doc_003_id, 'review', 'approve', 'Alice', 'Final approval granted')
    print("11. Alice reviews and grants final approval → Approve")
    
    print("\nDocument Verification:")
    print("=====================")
    print(f"Root documents: {wf.get_root_documents()}")
    print(f"All documents: {list(wf.document_metadata.keys())}")
    print(f"Active documents: {wf.get_active_documents()}")
    
    # Simple text-based family tree
    print("\nFamily Tree (Text-based):")
    print("=========================")
    for root in wf.get_root_documents():
        print_family_tree_text(wf, root, 0)
    
    # Complete workflow visualization
    print("\nComplete Workflow Visualization:")
    print("===============================")
    for root in wf.get_root_documents():
        print_complete_workflow_tree(wf, root)
    
    # Show detailed workflow transitions
    print("\nDetailed Workflow Transitions:")
    print("==============================")
    detailed_df = wf.export_detailed_workflow_data()
    print(detailed_df[['document_id', 'parent', 'workflow_path', 'final_state', 'is_active', 'document_lineage']].to_string(index=False))
    
    # Show document states
    print("\nDocument Details:")
    print("================")
    for doc_id in wf.document_metadata:
        meta = wf.document_metadata[doc_id]
        logs = wf.document_logs[doc_id]
        print(f"{doc_id}:")
        print(f"  Final State: {meta['current_state']}")
        print(f"  Active: {meta['is_active']}")
        print(f"  Parent: {meta['parent']}")
        print(f"  Children: {meta['children']}")
        print(f"  Transition History:")
        for i, log in enumerate(logs, 1):
            from_state = log['from_state'] or 'START'
            to_state = log['to_state']
            user = log['user_id']
            notes = log['notes']
            print(f"    {i}. {from_state} → {to_state} (by {user}): {notes}")
        print()

def print_family_tree_text(wf, doc_id, indent=0):
    """Print a simple text-based family tree"""
    prefix = "  " * indent
    state = wf.get_document_current_state(doc_id)
    is_active = wf.document_metadata[doc_id]['is_active']
    status = "ACTIVE" if is_active else "TERMINATED"
    print(f"{prefix}├─ {doc_id} [{state}] ({status})")
    
    # Print children
    children = wf.document_metadata[doc_id].get('children', [])
    for child in children:
        print_family_tree_text(wf, child, indent + 1)

def print_complete_workflow_tree(wf, root_doc):
    """Print complete workflow showing all state transitions"""
    print(f"\n{root_doc} Complete Workflow:")
    print("-" * (len(root_doc) + 20))
    
    # Get all documents in family
    family_docs = [root_doc] + wf.get_document_descendants(root_doc)
    
    def print_doc_workflow(doc_id, is_child=False, parent_doc=None):
        logs = wf.document_logs[doc_id]
        is_active = wf.document_metadata[doc_id]['is_active']
        status = "ACTIVE" if is_active else "TERMINATED"
        
        if not is_child:
            print(f"\n{doc_id} ({status}):")
            print("  START")
        else:
            print(f"\n{doc_id} ({status}) - Child of {parent_doc}:")
            print("  [Branches from parent's 'revise' state]")
        
        for i, log in enumerate(logs, 1):
            from_state = log['from_state'] or 'START'
            to_state = log['to_state']
            user = log['user_id']
            
            print(f"    ↓ ({user})")
            print(f"  {i}. {to_state}")
            
            # Show revision branch point and continue with children
            if to_state == 'revise':
                children = wf.document_metadata[doc_id].get('children', [])
                if children:
                    for child in children:
                        print(f"    ├── CREATES CHILD DOCUMENT: {child}")
                        print_doc_workflow(child, is_child=True, parent_doc=doc_id)
    
    # Start with root document
    print_doc_workflow(root_doc)

if __name__ == "__main__":
    test_policy_workflow()