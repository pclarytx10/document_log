import networkx as nx
import matplotlib.pyplot as plt
import pandas as pd
from datetime import datetime
from collections import defaultdict
import json
import uuid

class HierarchicalDocumentWorkflowManager:
    """
    Manages document state transitions with parent-child relationships
    where 'revise' creates new child documents
    """
    
    def __init__(self):
        # Create directed graph for workflow states
        self.workflow_graph = nx.DiGraph()
        # Create directed graph for document genealogy (parent-child relationships)
        self.genealogy_graph = nx.DiGraph()
        # Store document logs with parent information
        self.document_logs = defaultdict(list)
        # Store document metadata (parent, current_state, creation_info)
        self.document_metadata = {}
        self.setup_workflow()
    
    def setup_workflow(self):
        """Define the document workflow states and transitions"""
        
        # Define states with metadata
        states = {
            'draft': {'initial': True, 'terminal': False, 'color': 'lightblue'},
            'review': {'initial': False, 'terminal': False, 'color': 'yellow'},
            'update': {'initial': False, 'terminal': False, 'color': 'orange'},
            'revise': {'initial': False, 'terminal': True, 'color': 'pink', 'spawns_child': True},
            'approve': {'initial': False, 'terminal': True, 'color': 'lightgreen'},
            'reject': {'initial': False, 'terminal': True, 'color': 'lightcoral'},
            'withdraw': {'initial': False, 'terminal': True, 'color': 'lightgray'}
        }
        
        # Add nodes with attributes
        for state, attrs in states.items():
            self.workflow_graph.add_node(state, **attrs)
        
        # Define valid transitions
        transitions = [
            ('draft', 'review', {'action': 'submit_for_review'}),
            ('review', 'approve', {'action': 'approve_document'}),
            ('review', 'reject', {'action': 'reject_document'}),
            ('review', 'revise', {'action': 'request_revisions', 'creates_child': True}),
            ('review', 'update', {'action': 'request_update_from_review'}),
            ('approve', 'update', {'action': 'request_update'}),
            ('update', 'review', {'action': 'submit_updated_version'}),
            ('draft', 'withdraw', {'action': 'withdraw_draft'}),
            ('review', 'withdraw', {'action': 'withdraw_from_review'}),
            ('update', 'withdraw', {'action': 'withdraw_during_update'})
        ]
        
        # Add edges with attributes
        for from_state, to_state, attrs in transitions:
            self.workflow_graph.add_edge(from_state, to_state, **attrs)
    
    def create_document(self, document_id, parent_id=None, user_id=None, notes=None):
        """
        Create a new document (root or child)
        """
        if document_id in self.document_metadata:
            raise ValueError(f"Document {document_id} already exists")
        
        # Create document metadata
        self.document_metadata[document_id] = {
            'parent': parent_id,
            'created_by': user_id,
            'creation_time': datetime.now(),
            'current_state': 'draft',
            'children': [],
            'is_active': True
        }
        
        # Add to genealogy graph
        self.genealogy_graph.add_node(document_id)
        if parent_id:
            self.genealogy_graph.add_edge(parent_id, document_id, relationship='revision')
            # Update parent's children list
            if parent_id in self.document_metadata:
                self.document_metadata[parent_id]['children'].append(document_id)
        
        # Log initial state
        self.log_state_change(document_id, None, 'draft', user_id, notes or 'Document created')
        
        return document_id
    
    def log_state_change(self, document_id, from_state, to_state, user_id=None, notes=None):
        """
        Log a state change for a document, handling revise → child creation
        """
        if document_id not in self.document_metadata:
            raise ValueError(f"Document {document_id} does not exist")
        
        # Validate transition (except for initial creation)
        if from_state is not None and not self.is_valid_transition(from_state, to_state):
            raise ValueError(f"Invalid transition from {from_state} to {to_state}")
        
        # Create log entry
        log_entry = {
            'timestamp': datetime.now(),
            'from_state': from_state,
            'to_state': to_state,
            'user_id': user_id,
            'notes': notes
        }
        
        self.document_logs[document_id].append(log_entry)
        
        # Update document metadata
        self.document_metadata[document_id]['current_state'] = to_state
        
        # Handle terminal states
        if to_state in self.workflow_graph.nodes():
            state_attrs = self.workflow_graph.nodes[to_state]
            if state_attrs.get('terminal', False):
                # Mark document as inactive for all terminal states
                self.document_metadata[document_id]['is_active'] = False
                
                # Handle special case: revise state creates child
                if to_state == 'revise':
                    return self._handle_revision(document_id, user_id, notes)
        
        return log_entry
    
    def _handle_revision(self, document_id, user_id=None, notes=None):
        """
        Handle revision: terminate current document and create child
        """
        # Document is already marked as inactive by the terminal state handler
        
        # Generate child document ID
        child_id = f"{document_id}_rev_{len(self.document_metadata[document_id]['children']) + 1}"
        
        # Create child document
        child_notes = f"Revision of {document_id}. {notes or ''}"
        self.create_document(child_id, parent_id=document_id, user_id=user_id, notes=child_notes)
        
        return {
            'action': 'revision_created',
            'parent_document': document_id,
            'child_document': child_id,
            'timestamp': datetime.now()
        }
    
    def is_valid_transition(self, from_state, to_state):
        """Check if a state transition is valid"""
        return self.workflow_graph.has_edge(from_state, to_state)
    
    def get_possible_next_states(self, current_state):
        """Get all possible next states from current state"""
        return list(self.workflow_graph.successors(current_state))
    
    def get_document_current_state(self, document_id):
        """Get the current state of a document"""
        if document_id not in self.document_metadata:
            return None
        return self.document_metadata[document_id]['current_state']
    
    def get_document_lineage(self, document_id):
        """Get the complete lineage (ancestors) of a document"""
        lineage = []
        current = document_id
        
        while current:
            lineage.append(current)
            parent = self.document_metadata.get(current, {}).get('parent')
            current = parent
            
        return list(reversed(lineage))  # Root to current
    
    def get_document_descendants(self, document_id):
        """Get all descendants (children, grandchildren, etc.) of a document"""
        if document_id not in self.genealogy_graph:
            return []
        
        return list(nx.descendants(self.genealogy_graph, document_id))
    
    def get_root_documents(self):
        """Get all root documents (documents without parents)"""
        return [doc_id for doc_id, metadata in self.document_metadata.items() 
                if metadata['parent'] is None]
    
    def get_active_documents(self):
        """Get all currently active documents"""
        return [doc_id for doc_id, metadata in self.document_metadata.items() 
                if metadata['is_active']]
    
    def get_document_family_tree(self, root_document_id):
        """Get the complete family tree starting from a root document"""
        if root_document_id not in self.genealogy_graph:
            return nx.DiGraph()
        
        # Get subgraph containing root and all descendants
        descendants = nx.descendants(self.genealogy_graph, root_document_id)
        family_nodes = [root_document_id] + list(descendants)
        return self.genealogy_graph.subgraph(family_nodes).copy()
    
    def visualize_workflow(self, figsize=(12, 8)):
        """Visualize the workflow state machine"""
        plt.figure(figsize=figsize)
        
        # Get node colors based on state type
        node_colors = [self.workflow_graph.nodes[node]['color'] for node in self.workflow_graph.nodes()]
        
        # Create layout
        pos = nx.spring_layout(self.workflow_graph, k=2, iterations=50)
        
        # Draw the graph
        nx.draw(self.workflow_graph, pos, 
                with_labels=True, 
                node_color=node_colors,
                node_size=2000,
                font_size=10,
                font_weight='bold',
                arrows=True,
                arrowsize=20,
                edge_color='gray')
        
        # Highlight revise state (creates children)
        revise_pos = {k: v for k, v in pos.items() if k == 'revise'}
        if revise_pos:
            nx.draw_networkx_nodes(self.workflow_graph, revise_pos,
                                 nodelist=['revise'],
                                 node_color='red',
                                 node_size=2200,
                                 alpha=0.3)
        
        # Add edge labels
        edge_labels = nx.get_edge_attributes(self.workflow_graph, 'action')
        nx.draw_networkx_edge_labels(self.workflow_graph, pos, edge_labels, font_size=8)
        
        plt.title("Document Workflow State Machine\n(Red outline = Creates Child Document)", 
                 size=16, weight='bold')
        plt.axis('off')
        plt.tight_layout()
        plt.show()
    
    def visualize_genealogy(self, root_document_id=None, figsize=(14, 10)):
        """Visualize document genealogy tree"""
        if root_document_id:
            G = self.get_document_family_tree(root_document_id)
            title = f"Document Family Tree: {root_document_id}"
        else:
            G = self.genealogy_graph
            title = "Complete Document Genealogy"
        
        if len(G.nodes()) == 0:
            print("No documents to visualize")
            return
        
        plt.figure(figsize=figsize)
        
        # Create hierarchical layout
        try:
            pos = nx.nx_agraph.graphviz_layout(G, prog='dot')
        except:
            # Fallback to spring layout if graphviz not available
            pos = nx.spring_layout(G, k=3, iterations=50)
        
        # Color nodes by current state
        node_colors = []
        for node in G.nodes():
            state = self.get_document_current_state(node)
            state_color = self.workflow_graph.nodes[state]['color'] if state else 'white'
            node_colors.append(state_color)
        
        # Determine node shapes (active vs inactive)
        active_nodes = [node for node in G.nodes() if self.document_metadata[node]['is_active']]
        inactive_nodes = [node for node in G.nodes() if not self.document_metadata[node]['is_active']]
        
        # Draw inactive nodes with dashed border
        if inactive_nodes:
            nx.draw_networkx_nodes(G, pos, nodelist=inactive_nodes,
                                 node_color=[node_colors[list(G.nodes()).index(node)] for node in inactive_nodes],
                                 node_size=1500, alpha=0.6, 
                                 edgecolors='red', linewidths=2, linestyle='--')
        
        # Draw active nodes with solid border
        if active_nodes:
            nx.draw_networkx_nodes(G, pos, nodelist=active_nodes,
                                 node_color=[node_colors[list(G.nodes()).index(node)] for node in active_nodes],
                                 node_size=1500, 
                                 edgecolors='black', linewidths=2)
        
        # Draw edges
        nx.draw_networkx_edges(G, pos, edge_color='gray', arrows=True, arrowsize=20)
        
        # Draw labels
        nx.draw_networkx_labels(G, pos, font_size=8, font_weight='bold')
        
        # Add state labels
        state_labels = {}
        for node in G.nodes():
            state = self.get_document_current_state(node)
            state_labels[node] = f"\n({state})"
        
        # Offset state labels
        state_pos = {node: (pos[node][0], pos[node][1] - 0.1) for node in pos}
        nx.draw_networkx_labels(G, state_pos, state_labels, font_size=7, font_style='italic')
        
        plt.title(title + "\n(Dashed border = Terminated, Solid = Active)", size=14, weight='bold')
        plt.axis('off')
        plt.tight_layout()
        plt.show()
    
    def analyze_genealogy_patterns(self):
        """Analyze patterns in document genealogy"""
        analysis = {
            'total_documents': len(self.document_metadata),
            'root_documents': len(self.get_root_documents()),
            'active_documents': len(self.get_active_documents()),
            'terminated_documents': len([d for d in self.document_metadata.values() if not d['is_active']]),
        }
        
        # Calculate revision depths
        revision_depths = []
        for doc_id in self.document_metadata:
            lineage = self.get_document_lineage(doc_id)
            revision_depths.append(len(lineage) - 1)  # Subtract 1 for root
        
        analysis['max_revision_depth'] = max(revision_depths) if revision_depths else 0
        analysis['avg_revision_depth'] = sum(revision_depths) / len(revision_depths) if revision_depths else 0
        
        # Count children per document
        children_counts = [len(meta['children']) for meta in self.document_metadata.values()]
        analysis['max_children'] = max(children_counts) if children_counts else 0
        analysis['avg_children'] = sum(children_counts) / len(children_counts) if children_counts else 0
        
        return analysis
    
    def export_genealogy_data(self):
        """Export genealogy data to DataFrame"""
        data = []
        for doc_id, metadata in self.document_metadata.items():
            lineage = self.get_document_lineage(doc_id)
            data.append({
                'document_id': doc_id,
                'parent': metadata['parent'],
                'current_state': metadata['current_state'],
                'is_active': metadata['is_active'],
                'created_by': metadata['created_by'],
                'creation_time': metadata['creation_time'],
                'revision_depth': len(lineage) - 1,
                'children_count': len(metadata['children']),
                'lineage': ' → '.join(lineage)
            })
        
        return pd.DataFrame(data)
    
    def export_detailed_workflow_data(self):
        """Export detailed workflow data showing all state transitions for each document"""
        data = []
        for doc_id, logs in self.document_logs.items():
            metadata = self.document_metadata[doc_id]
            lineage = self.get_document_lineage(doc_id)
            
            # Create state transition sequence
            transitions = []
            for log in logs:
                if log['from_state'] is None:
                    transitions.append(log['to_state'])
                else:
                    transitions.append(f"{log['from_state']}→{log['to_state']}")
            
            # Get complete workflow path
            workflow_path = ' | '.join(transitions)
            
            data.append({
                'document_id': doc_id,
                'parent': metadata['parent'],
                'workflow_path': workflow_path,
                'final_state': metadata['current_state'],
                'is_active': metadata['is_active'],
                'created_by': metadata['created_by'],
                'creation_time': metadata['creation_time'],
                'revision_depth': len(lineage) - 1,
                'children_count': len(metadata['children']),
                'document_lineage': ' → '.join(lineage),
                'total_transitions': len(logs)
            })
        
        return pd.DataFrame(data)

# Example usage demonstrating the hierarchical workflow
def demonstrate_hierarchical_workflow():
    """Demonstrate the hierarchical workflow with parent-child relationships"""
    
    wf = HierarchicalDocumentWorkflowManager()
    
    # Create root document
    wf.create_document('DOC001', user_id='alice', notes='Initial policy document')
    
    # Normal workflow progression
    wf.log_state_change('DOC001', 'draft', 'review', 'alice', 'Ready for review')
    
    # Revision creates child document and terminates parent
    revision_result = wf.log_state_change('DOC001', 'review', 'revise', 'bob', 'Major changes needed')
    print(f"Revision created: {revision_result}")
    
    # Work on the child document
    child_doc = revision_result['child_document']
    wf.log_state_change(child_doc, 'draft', 'review', 'alice', 'Revised version ready')
    
    # Another revision cycle
    revision_result_2 = wf.log_state_change(child_doc, 'review', 'revise', 'bob', 'Minor corrections needed')
    grandchild_doc = revision_result_2['child_document']
    
    # Final approval
    wf.log_state_change(grandchild_doc, 'draft', 'review', 'alice', 'Final version')
    wf.log_state_change(grandchild_doc, 'review', 'approve', 'bob', 'Approved!')
    
    # Create another root document for comparison
    wf.create_document('DOC002', user_id='charlie', notes='Different document')
    wf.log_state_change('DOC002', 'draft', 'review', 'charlie')
    wf.log_state_change('DOC002', 'review', 'approve', 'bob', 'Quick approval')
    
    return wf

if __name__ == "__main__":
    # Run demonstration
    workflow = demonstrate_hierarchical_workflow()
    
    print("=== Genealogy Analysis ===")
    analysis = workflow.analyze_genealogy_patterns()
    for key, value in analysis.items():
        print(f"{key}: {value}")
    
    print("\n=== Document Status ===")
    genealogy_df = workflow.export_genealogy_data()
    print(genealogy_df[['document_id', 'parent', 'current_state', 'is_active', 'lineage']].to_string(index=False))
    
    print("\n=== Root Documents ===")
    print(workflow.get_root_documents())
    
    print("\n=== Active Documents ===")
    print(workflow.get_active_documents())
    
    # Visualizations
    print("\n=== Generating Visualizations ===")
    workflow.visualize_workflow()
    workflow.visualize_genealogy()
    workflow.visualize_genealogy('DOC001')  # Show just one family tree