import networkx as nx
import matplotlib.pyplot as plt
import pandas as pd
from datetime import datetime, timedelta
import numpy as np
import seaborn as sns
from matplotlib.patches import Rectangle, FancyBboxPatch
import matplotlib.patches as patches
import re

class HierarchicalWorkflowVisualizer:
    """
    Advanced visualization tools for hierarchical document workflows
    """
    
    def __init__(self, workflow_manager):
        self.wf = workflow_manager
        self.state_colors = {
            'draft': '#e3f2fd',      # Light blue
            'review': '#fff3e0',     # Light orange  
            'update': '#f3e5f5',     # Light purple
            'revise': '#fff8e1',     # Light yellow
            'approve': '#e8f5e8',    # Light green
            'reject': '#ffebee',     # Light red
            'withdraw': '#f5f5f5'    # Light gray
        }
    
    def plot_family_trees_grid(self, figsize=(19.2, 10.8)):
        """Create a grid showing all family trees"""
        root_docs = self.wf.get_root_documents()
        
        if not root_docs:
            print("No documents to visualize")
            return
        
        # Calculate grid dimensions
        n_trees = len(root_docs)
        cols = min(3, n_trees)
        rows = (n_trees + cols - 1) // cols
        
        fig, axes = plt.subplots(rows, cols, figsize=figsize)
        if rows == 1 and cols == 1:
            axes = [axes]
        elif rows == 1 or cols == 1:
            axes = axes.flatten()
        else:
            axes = axes.flatten()
        
        for i, root_doc in enumerate(root_docs):
            if i >= len(axes):
                break
                
            ax = axes[i]
            self._plot_single_family_tree(root_doc, ax)
        
        # Hide unused subplots
        for i in range(len(root_docs), len(axes)):
            axes[i].set_visible(False)
        
        plt.suptitle('Document Family Trees\n(Each tree shows a document and all its revisions)', 
                     fontsize=16, fontweight='bold')
        plt.tight_layout()
        return fig
    
    def _plot_single_family_tree(self, root_doc, ax):
        """Plot a single family tree with complete state transition flow"""
        # Create a comprehensive workflow graph showing all state transitions
        G = self._create_workflow_graph_for_family(root_doc)
        
        if len(G.nodes()) == 0:
            ax.text(0.5, 0.5, 'No data', ha='center', va='center', transform=ax.transAxes)
            ax.set_title(root_doc)
            return
        
        # Create hierarchical positions
        pos = self._calculate_workflow_positions(G, root_doc)
        
        # Draw edges with tree-style connections (zorder=1 for bottom layer)
        for edge in G.edges(data=True):
            from_node, to_node, edge_data = edge
            edge_type = edge_data.get('type', 'transition')
            
            if edge_type == 'revision':
                # Parent-child relationship: draw direct diagonal line
                from_pos = pos[from_node]
                to_pos = pos[to_node]
                
                # Draw direct diagonal line at calculated angle
                ax.plot([from_pos[0], to_pos[0]], 
                       [from_pos[1], to_pos[1]], 
                       'k-', linewidth=3, alpha=0.8, zorder=1)
            else:
                # State transition edge (within same document)
                ax.plot([pos[from_node][0], pos[to_node][0]], 
                       [pos[from_node][1], pos[to_node][1]], 
                       'k-', linewidth=3, alpha=0.8, zorder=1)
        
        # Draw nodes with higher zorder to ensure they're on top
        for node in G.nodes(data=True):
            node_id, node_data = node
            node_type = node_data.get('type', 'state')
            
            if node_type == 'document':
                # Document start node
                color = 'lightblue'
                size = 2000 * 2  # Increase by 50%
                edge_color = 'darkblue'
                # Draw white background circle first for better visibility
                ax.scatter(pos[node_id][0], pos[node_id][1], 
                          c='white', s=size*1.1, marker='o',
                          edgecolors='none', zorder=3)
                # Draw the actual node on top
                ax.scatter(pos[node_id][0], pos[node_id][1], 
                          c=color, s=size, marker='s',
                          edgecolors=edge_color, linewidth=3, zorder=4)
            else:
                # State node
                state = node_data.get('state')
                is_active = node_data.get('is_active', True)
                color = self.state_colors.get(state, 'white')
                size = 1200 * 2  # Increase by 50%
                alpha = 1.0 if is_active else 0.6
                edge_color = 'black' if is_active else 'red'
                
                # Draw white background circle first for better visibility
                ax.scatter(pos[node_id][0], pos[node_id][1], 
                          c='white', s=size*1.1, marker='o',
                          edgecolors='none', zorder=3)
                # Draw the actual node on top
                ax.scatter(pos[node_id][0], pos[node_id][1], 
                          c=color, s=size, alpha=alpha,
                          edgecolors=edge_color, linewidth=2, zorder=4)
            
            # Add labels on top of everything
            label = node_data.get('label', node_id)
            # Custom placement for document name
            if node_type == 'document':
                # Place document name above the start node
                doc_name = node_data.get('document', '')
                ax.annotate(doc_name, (pos[node_id][0], pos[node_id][1]),
                           xytext=(0, 40), textcoords='offset points',
                           ha='center', va='bottom', fontsize=11, fontweight='bold', zorder=5)
                # Place the rest of the label (e.g., [START]) at the node center
                rest_label = label.replace(doc_name, '').replace('\n', '').replace('[START]', '[START]') if doc_name in label else label
                ax.annotate(rest_label, pos[node_id],
                           ha='center', va='center', fontsize=10, fontweight='bold', zorder=5)
            elif node_type == 'state' and 'draft' in label and '(' in label:
                # Place document name to the left of draft node if shown
                # Extract document name from label
                match = re.search(r'\((.*?)\)', label)
                doc_name = match.group(1) if match else ''
                # Place state label at node center
                state_label = label.split('\n')[0]
                ax.annotate(state_label, pos[node_id],
                           ha='center', va='center', fontsize=10, fontweight='bold', zorder=5)
                if doc_name:
                    ax.annotate(doc_name, (pos[node_id][0], pos[node_id][1]),
                               xytext=(-40, 0), textcoords='offset points',
                               ha='right', va='center', fontsize=10, fontweight='bold', zorder=5)
            else:
                # Default: label at node center
                ax.annotate(label, pos[node_id], 
                           ha='center', va='center', fontsize=10, fontweight='bold',
                           zorder=5)
        
        ax.set_title(f'Complete Workflow: {root_doc}', fontsize=10, fontweight='bold')
        ax.set_aspect('equal')
        ax.axis('off')
    
    def _create_workflow_graph_for_family(self, root_doc):
        """Create a graph showing complete workflow for a document family"""
        import networkx as nx
        G = nx.DiGraph()
        
        # Get all documents in this family
        family_docs = [root_doc] + self.wf.get_document_descendants(root_doc)
        
        # Track final nodes for connecting child documents
        final_nodes = {}
        
        for doc_id in family_docs:
            if doc_id not in self.wf.document_logs:
                continue
                
            logs = self.wf.document_logs[doc_id]
            prev_node = None
            
            # For root document, add START node. For child documents, they'll connect to parent's revise node
            if self.wf.document_metadata[doc_id]['parent'] is None:
                # Root document gets a START node
                doc_start_node = f"{doc_id}_START"
                G.add_node(doc_start_node, 
                          type='document', 
                          label=f"{doc_id}\n[START]",
                          document=doc_id)
                prev_node = doc_start_node
            
            # Add state transition nodes with smart labeling
            for i, log in enumerate(logs):
                state_node = f"{doc_id}_STATE_{i}_{log['to_state']}"
                is_active = self.wf.document_metadata[doc_id]['is_active']
                
                # Smart labeling logic
                if log['to_state'] == 'draft' and i == 0 and prev_node and prev_node.endswith('_START'):
                    # Draft node following START node - no document name
                    label = f"{log['to_state']}"
                elif log['to_state'] != 'draft':
                    # Non-draft nodes - no document name
                    label = f"{log['to_state']}"
                else:
                    # Draft nodes not following START - include document name
                    label = f"{log['to_state']}\n({doc_id})"
                
                G.add_node(state_node,
                          type='state',
                          state=log['to_state'],
                          is_active=is_active,
                          label=label,
                          document=doc_id,
                          user=log['user_id'],
                          notes=log['notes'])
                
                if prev_node:
                    G.add_edge(prev_node, state_node, type='transition')
                
                prev_node = state_node
            
            # Store the final node for this document
            final_nodes[doc_id] = prev_node
        
        # Connect child documents directly to their parent's terminal node
        for doc_id in family_docs:
            parent_id = self.wf.document_metadata[doc_id]['parent']
            if parent_id and parent_id in final_nodes:
                # Find the first state node of the child and connect it directly to parent's final node
                child_logs = self.wf.document_logs[doc_id]
                if child_logs:
                    first_child_state = f"{doc_id}_STATE_0_{child_logs[0]['to_state']}"
                    parent_final = final_nodes[parent_id]
                    
                    if first_child_state in G.nodes() and parent_final:
                        G.add_edge(parent_final, first_child_state, type='revision')
        
        return G
    
    def _calculate_workflow_positions(self, G, root_doc):
        """Calculate positions for workflow graph nodes with proper scaling for 1920x1080"""
        pos = {}
        
        # Try to use networkx layout algorithms for better positioning
        try:
            # Use hierarchical layout if available
            import networkx as nx
            pos = nx.nx_agraph.graphviz_layout(G, prog='dot')
        except:
            # Fallback to manual positioning
            pos = self._manual_workflow_layout(G, root_doc)
        
        # Scale positions to fit 1920x1080 with proper margins
        if pos:
            pos = self._scale_positions(pos, target_width=18, target_height=9)
        
        return pos
    
    def _manual_workflow_layout(self, G, root_doc):
        """Manual layout for workflow graph in tree structure with angled branches"""
        pos = {}
        
        # Create a proper tree layout where child workflows branch at angles from parent
        def layout_document_tree(doc_id, start_x=0, start_y=0, base_branch_length=8):
            """Recursively layout document and its children with angled branches"""
            if doc_id not in self.wf.document_metadata:
                return start_x
            
            # Get nodes for this document
            doc_nodes = []
            for node, data in G.nodes(data=True):
                if data.get('document') == doc_id:
                    doc_nodes.append(node)
            
            # Sort nodes by state sequence
            doc_nodes.sort()
            
            # Position nodes for this document horizontally
            current_x = start_x
            for node in doc_nodes:
                pos[node] = (current_x, start_y)
                current_x += 4  # Horizontal spacing between states
            
            # Get the final node position for branching (parent terminating node)
            final_node_pos = (current_x - 4, start_y)  # Last node position
            
            # Layout children branching at angles from the final node
            children = self.wf.document_metadata[doc_id].get('children', [])
            if children:
                import math
                
                # Calculate angles for children
                num_children = len(children)
                base_angle = 45  # Base angle in degrees
                
                if num_children == 1:
                    # Single child: branch at -45 degrees (down and right)
                    angles = [-base_angle]
                else:
                    # Multiple children: alternate positive and negative angles
                    angles = []
                    for i in range(num_children):
                        # Reduce angle by 50% for each additional branch beyond the first two
                        if i < 2:
                            current_angle = base_angle
                        else:
                            current_angle = base_angle * (0.5 ** (i - 1))
                        
                        # Alternate positive and negative
                        if i % 2 == 0:
                            angles.append(-current_angle)  # Negative (down-right)
                        else:
                            angles.append(current_angle)   # Positive (up-right)
                
                # Position each child at the calculated angle
                for i, (child_doc, angle) in enumerate(zip(children, angles)):
                    # Calculate child position using angle
                    angle_rad = math.radians(angle)
                    branch_length = base_branch_length
                    
                    # Calculate end position of branch
                    child_start_x = final_node_pos[0] + branch_length * math.cos(angle_rad)
                    child_start_y = final_node_pos[1] + branch_length * math.sin(angle_rad)
                    
                    # Recursively layout the child document
                    max_x = layout_document_tree(child_doc, child_start_x, child_start_y, base_branch_length)
                    current_x = max(current_x, max_x)
            
            return current_x
        
        # Start layout from root document
        layout_document_tree(root_doc, 0, 0)
        
        return pos
    
    def _scale_positions(self, pos, target_width=18, target_height=9):
        """Scale positions to fit target dimensions"""
        if not pos:
            return pos
        
        # Get current bounds
        x_coords = [p[0] for p in pos.values()]
        y_coords = [p[1] for p in pos.values()]
        
        min_x, max_x = min(x_coords), max(x_coords)
        min_y, max_y = min(y_coords), max(y_coords)
        
        current_width = max_x - min_x if max_x != min_x else 1
        current_height = max_y - min_y if max_y != min_y else 1
        
        # Calculate scale factors
        scale_x = target_width / current_width
        scale_y = target_height / current_height
        
        # Apply scaling and centering
        scaled_pos = {}
        for node, (x, y) in pos.items():
            # Scale and center
            new_x = (x - min_x) * scale_x - target_width / 2
            new_y = (y - min_y) * scale_y - target_height / 2
            scaled_pos[node] = (new_x, new_y)
        
        return scaled_pos
    
    def _calculate_tree_positions(self, G, root):
        """Calculate positions for tree layout"""
        if len(G.nodes()) == 1:
            return {root: (0, 0)}
        
        # Use networkx hierarchy layout if available, otherwise manual
        try:
            pos = nx.nx_agraph.graphviz_layout(G, prog='dot')
        except:
            # Manual tree layout
            pos = {}
            levels = {}
            
            # BFS to assign levels
            queue = [(root, 0)]
            visited = {root}
            
            while queue:
                node, level = queue.pop(0)
                if level not in levels:
                    levels[level] = []
                levels[level].append(node)
                
                for child in G.successors(node):
                    if child not in visited:
                        queue.append((child, level + 1))
                        visited.add(child)
            
            # Assign positions
            for level, nodes in levels.items():
                for i, node in enumerate(nodes):
                    x = i - len(nodes) / 2 + 0.5
                    y = -level
                    pos[node] = (x, y)
        
        return pos
    
    def plot_revision_timeline(self, figsize=(16, 8)):
        """Create a timeline showing document creation and revisions"""
        fig, ax = plt.subplots(figsize=figsize)
        
        # Get all documents sorted by creation time
        docs_data = []
        for doc_id, metadata in self.wf.document_metadata.items():
            lineage = self.wf.get_document_lineage(doc_id)
            docs_data.append({
                'doc_id': doc_id,
                'creation_time': metadata['creation_time'],
                'current_state': metadata['current_state'],
                'is_active': metadata['is_active'],
                'parent': metadata['parent'],
                'revision_depth': len(lineage) - 1,
                'root_doc': lineage[0]
            })
        
        df = pd.DataFrame(docs_data).sort_values('creation_time')
        
        # Create timeline
        root_docs = df[df['parent'].isna()]['doc_id'].unique()
        root_colors = plt.cm.Set1(np.linspace(0, 1, len(root_docs)))
        root_color_map = {root: color for root, color in zip(root_docs, root_colors)}
        
        for i, (_, row) in enumerate(df.iterrows()):
            # Determine position and color
            y_pos = row['revision_depth']
            color = root_color_map[row['root_doc']]
            
            # Plot document creation
            marker = 'o' if row['is_active'] else 'X'
            size = 100 if row['is_active'] else 150
            alpha = 1.0 if row['is_active'] else 0.7
            
            ax.scatter(row['creation_time'], y_pos, 
                      c=[color], marker=marker, s=size, alpha=alpha,
                      edgecolors='black', linewidth=1)
            
            # Add label
            short_name = row['doc_id'].split('_')[-1] if '_' in row['doc_id'] else row['doc_id']
            ax.annotate(f"{short_name}\n({row['current_state']})", 
                       (row['creation_time'], y_pos),
                       xytext=(5, 5), textcoords='offset points',
                       fontsize=8, ha='left')
            
            # Draw line to parent if exists
            if pd.notna(row['parent']):
                parent_row = df[df['doc_id'] == row['parent']].iloc[0]
                ax.plot([parent_row['creation_time'], row['creation_time']],
                       [parent_row['revision_depth'], row['revision_depth']],
                       color=color, alpha=0.5, linewidth=2, linestyle='--')
        
        ax.set_xlabel('Creation Time', fontweight='bold')
        ax.set_ylabel('Revision Depth', fontweight='bold')
        ax.set_title('Document Creation Timeline\n(Connected lines show parent-child relationships)', 
                    fontweight='bold', fontsize=14)
        
        # Add legend for root documents
        legend_elements = [plt.scatter([], [], c=color, label=root, s=100) 
                          for root, color in root_color_map.items()]
        ax.legend(handles=legend_elements, title='Root Documents', 
                 bbox_to_anchor=(1.05, 1), loc='upper left')
        
        ax.grid(True, alpha=0.3)
        plt.tight_layout()
        return fig
    
    def plot_state_distribution_by_generation(self, figsize=(12, 8)):
        """Show state distribution across revision generations"""
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=figsize)
        
        # Prepare data
        data = []
        for doc_id, metadata in self.wf.document_metadata.items():
            lineage = self.wf.get_document_lineage(doc_id)
            data.append({
                'doc_id': doc_id,
                'generation': len(lineage) - 1,
                'state': metadata['current_state'],
                'is_active': metadata['is_active']
            })
        
        df = pd.DataFrame(data)
        
        # Plot 1: State distribution by generation
        state_gen_pivot = df.pivot_table(index='generation', columns='state', 
                                        values='doc_id', aggfunc='count', fill_value=0)
        
        state_gen_pivot.plot(kind='bar', stacked=True, ax=ax1, 
                           color=[self.state_colors[state] for state in state_gen_pivot.columns])
        ax1.set_title('Document States by Revision Generation', fontweight='bold')
        ax1.set_xlabel('Revision Generation (0=Root, 1=First Revision, etc.)', fontweight='bold')
        ax1.set_ylabel('Number of Documents', fontweight='bold')
        ax1.legend(title='Document State', bbox_to_anchor=(1.05, 1), loc='upper left')
        ax1.tick_params(axis='x', rotation=0)
        
        # Plot 2: Active vs Terminated by generation
        active_data = df.groupby('generation')['is_active'].agg(['sum', 'count']).reset_index()
        active_data['terminated'] = active_data['count'] - active_data['sum']
        
        x = active_data['generation']
        ax2.bar(x, active_data['sum'], label='Active', color='lightgreen', alpha=0.8)
        ax2.bar(x, active_data['terminated'], bottom=active_data['sum'], 
               label='Terminated', color='lightcoral', alpha=0.8)
        
        ax2.set_title('Active vs Terminated Documents by Generation', fontweight='bold')
        ax2.set_xlabel('Revision Generation', fontweight='bold')
        ax2.set_ylabel('Number of Documents', fontweight='bold')
        ax2.legend()
        
        plt.tight_layout()
        return fig
    
    def plot_document_lifecycle_analysis(self, figsize=(14, 10)):
        """Comprehensive lifecycle analysis"""
        fig = plt.figure(figsize=figsize)
        gs = fig.add_gridspec(3, 2, height_ratios=[1, 1, 1])
        
        # Get data
        genealogy_df = self.wf.export_genealogy_data()
        
        # Plot 1: Revision depth distribution
        ax1 = fig.add_subplot(gs[0, 0])
        depth_counts = genealogy_df['revision_depth'].value_counts().sort_index()
        bars1 = ax1.bar(depth_counts.index, depth_counts.values, 
                       color='skyblue', edgecolor='black', alpha=0.7)
        ax1.set_title('Distribution of Revision Depths', fontweight='bold')
        ax1.set_xlabel('Revision Depth')
        ax1.set_ylabel('Number of Documents')
        
        # Add value labels
        for bar, value in zip(bars1, depth_counts.values):
            ax1.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.05,
                    str(value), ha='center', va='bottom', fontweight='bold')
        
        # Plot 2: Children count distribution
        ax2 = fig.add_subplot(gs[0, 1])
        children_counts = genealogy_df['children_count'].value_counts().sort_index()
        bars2 = ax2.bar(children_counts.index, children_counts.values,
                       color='lightcoral', edgecolor='black', alpha=0.7)
        ax2.set_title('Distribution of Children per Document', fontweight='bold')
        ax2.set_xlabel('Number of Children')
        ax2.set_ylabel('Number of Documents')
        
        # Add value labels
        for bar, value in zip(bars2, children_counts.values):
            ax2.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.05,
                    str(value), ha='center', va='bottom', fontweight='bold')
        
        # Plot 3: State vs Activity status
        ax3 = fig.add_subplot(gs[1, :])
        state_activity = genealogy_df.groupby(['current_state', 'is_active']).size().unstack(fill_value=0)
        state_activity.plot(kind='bar', ax=ax3, color=['lightcoral', 'lightgreen'], alpha=0.8)
        ax3.set_title('Document States: Active vs Terminated', fontweight='bold')
        ax3.set_xlabel('Document State')
        ax3.set_ylabel('Number of Documents')
        ax3.legend(['Terminated', 'Active'])
        ax3.tick_params(axis='x', rotation=45)
        
        # Plot 4: Lineage complexity
        ax4 = fig.add_subplot(gs[2, :])
        
        # Show longest lineages
        lineage_lengths = genealogy_df.groupby('lineage')['revision_depth'].max().sort_values(ascending=False)
        top_lineages = lineage_lengths.head(10)
        
        y_pos = range(len(top_lineages))
        bars4 = ax4.barh(y_pos, top_lineages.values, color='mediumpurple', alpha=0.8)
        ax4.set_yticks(y_pos)
        ax4.set_yticklabels([lineage.split(' → ')[-1] for lineage in top_lineages.index], fontsize=9)
        ax4.set_xlabel('Revision Depth')
        ax4.set_title('Top 10 Longest Document Lineages\n(Shows final document in each chain)', fontweight='bold')
        
        # Add value labels
        for i, (bar, value) in enumerate(zip(bars4, top_lineages.values)):
            ax4.text(bar.get_width() + 0.05, bar.get_y() + bar.get_height()/2,
                    str(value), ha='left', va='center', fontweight='bold')
        
        plt.tight_layout()
        return fig

def create_complex_example():
    """Create a complex example following the Policy Doc 001 journey with multiple children"""
    from parent_child_state_changes import HierarchicalDocumentWorkflowManager
    
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
    
    # Step 11: Charlie withdraws Doc 003 → Withdraw
    wf.log_state_change(child_doc_003_id, 'review', 'withdraw', 'Charlie', 'Withdrawing document due to new approach')
    print("11. Charlie withdraws Doc 003 → Withdraw")
    
    print("\nChild Document Journey (Policy Doc 004 in business terms):")
    print("=========================================================")
    
    # Step 12: Charlie creates a new child document draft from Parent 002 → Draft
    child_doc_004_id = wf.create_document('Policy Doc 004', parent_id=child_doc_002_id, user_id='Charlie', notes='New draft based on rejected Policy Doc 002 with improvements')
    print(f"12. Charlie creates a new child document draft from Parent 002 → Draft ({child_doc_004_id})")
    
    # Step 13: Charlie submits revised version → Review
    wf.log_state_change(child_doc_004_id, 'draft', 'review', 'Charlie', 'Improved version ready for review')
    print("13. Charlie submits revised version → Review")
    
    # Step 14: Alice reviews and grants final approval → Approve
    wf.log_state_change(child_doc_004_id, 'review', 'approve', 'Alice', 'Final approval granted')
    print("14. Alice reviews and grants final approval → Approve")
    
    print("\nWorkflow Summary:")
    print("================")
    print("Policy Doc 001: Draft → Review → Update → Review → Revise (TERMINATED)")
    print(f"{child_doc_002_id}: Draft → Review → Reject (TERMINATED)")
    print(f"{child_doc_003_id}: Draft → Review → Approve (ACTIVE)")
    print(f"\nParent-Child Relationships:")
    print(f"  Policy Doc 001 → {child_doc_002_id} (REJECTED)")
    print(f"  Policy Doc 001 → {child_doc_003_id} (APPROVED)")
    
    # Add debugging info and simple text visualization
    print("\nDocument Verification:")
    print("=====================")
    print(f"Root documents: {wf.get_root_documents()}")
    print(f"All documents: {list(wf.document_metadata.keys())}")
    print(f"Active documents: {wf.get_active_documents()}")
    
    # Simple text-based family tree
    print("\nFamily Tree (Text-based):")
    print("=========================")
    for root in wf.get_root_documents():
        _print_family_tree_text(wf, root, 0)
    
    return wf

def _print_family_tree_text(wf, doc_id, indent=0):
    """Print a simple text-based family tree"""
    prefix = "  " * indent
    state = wf.get_document_current_state(doc_id)
    is_active = wf.document_metadata[doc_id]['is_active']
    status = "ACTIVE" if is_active else "TERMINATED"
    print(f"{prefix}├─ {doc_id} [{state}] ({status})")
    
    # Print children
    children = wf.document_metadata[doc_id].get('children', [])
    for child in children:
        _print_family_tree_text(wf, child, indent + 1)
    

def run_hierarchical_examples():
    """Run all hierarchical workflow visualizations"""
    print("Creating Complex Hierarchical Document Workflow Example...")
    print("=" * 60)
    
    # Create complex example
    wf = create_complex_example()
    
    # Create visualizer
    viz = HierarchicalWorkflowVisualizer(wf)
    
    print("Generating visualizations...")
    
    # Generate all visualizations
    fig1 = viz.plot_family_trees_grid()
    #fig2 = viz.plot_revision_timeline()  
    #fig3 = viz.plot_state_distribution_by_generation()
    #fig4 = viz.plot_document_lifecycle_analysis()
    
    plt.show()
    
    # Print analysis
    print("\n" + "="*50)
    print("HIERARCHICAL WORKFLOW ANALYSIS")
    print("="*50)
    
    analysis = wf.analyze_genealogy_patterns()
    for key, value in analysis.items():
        print(f"{key}: {value}")
    
    print(f"\nRoot Documents: {wf.get_root_documents()}")
    print(f"Active Documents: {wf.get_active_documents()}")
    
    # Show detailed workflow table
    print("\n" + "="*60)
    print("DETAILED WORKFLOW TRANSITIONS TABLE")
    print("="*60)
    detailed_df = wf.export_detailed_workflow_data()
    print(detailed_df[['document_id', 'parent', 'workflow_path', 'final_state', 'is_active', 'document_lineage']].to_string(index=False))
    
    # Show genealogy table
    print("\n" + "="*50)
    print("DOCUMENT GENEALOGY SUMMARY")
    print("="*50)
    df = wf.export_genealogy_data()
    print(df[['document_id', 'parent', 'current_state', 'is_active', 'revision_depth', 'lineage']].to_string(index=False))
    
    return wf, viz

if __name__ == "__main__":
    workflow, visualizer = run_hierarchical_examples()