import networkx as nx
import matplotlib.pyplot as plt
import pandas as pd
from datetime import datetime, timedelta
import numpy as np
import seaborn as sns
from matplotlib.patches import Rectangle, FancyBboxPatch
import matplotlib.patches as patches

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
    
    def plot_family_trees_grid(self, figsize=(16, 12)):
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
        """Plot a single family tree on given axes"""
        G = self.wf.get_document_family_tree(root_doc)
        
        if len(G.nodes()) == 0:
            ax.text(0.5, 0.5, 'No data', ha='center', va='center', transform=ax.transAxes)
            ax.set_title(root_doc)
            return
        
        # Create hierarchical positions
        pos = self._calculate_tree_positions(G, root_doc)
        
        # Color nodes by state and activity
        for node in G.nodes():
            state = self.wf.get_document_current_state(node)
            is_active = self.wf.document_metadata[node]['is_active']
            
            # Choose color and style
            color = self.state_colors.get(state, 'white')
            edge_color = 'black' if is_active else 'red'
            edge_style = '-' if is_active else '--'
            alpha = 1.0 if is_active else 0.6
            
            ax.scatter(pos[node][0], pos[node][1], 
                      c=color, s=800, alpha=alpha,
                      edgecolors=edge_color, linewidth=2)
            
            # Add labels
            short_name = node.split('_')[-1] if '_' in node else node
            ax.annotate(f"{short_name}\n({state})", pos[node], 
                       ha='center', va='center', fontsize=8, fontweight='bold')
        
        # Draw edges
        for edge in G.edges():
            x1, y1 = pos[edge[0]]
            x2, y2 = pos[edge[1]]
            ax.plot([x1, x2], [y1, y2], 'k-', alpha=0.5, linewidth=2)
            ax.annotate('', xy=(x2, y2), xytext=(x1, y1),
                       arrowprops=dict(arrowstyle='->', color='gray', lw=1.5))
        
        ax.set_title(f"Family Tree: {root_doc}", fontweight='bold', fontsize=10)
        ax.set_aspect('equal')
        ax.axis('off')
    
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
    """Create a complex example with multiple document families"""
    from parent_child_state_changes import HierarchicalDocumentWorkflowManager
    
    wf = HierarchicalDocumentWorkflowManager()
    
    # Family 1: Policy document with multiple revisions
    wf.create_document('POLICY-001', user_id='alice', notes='Initial HR policy')
    wf.log_state_change('POLICY-001', 'draft', 'review', 'alice')
    revision1 = wf.log_state_change('POLICY-001', 'review', 'revise', 'bob', 'Legal review needed')
    
    child1 = revision1['child_document']
    wf.log_state_change(child1, 'draft', 'review', 'alice')
    revision2 = wf.log_state_change(child1, 'review', 'revise', 'bob', 'Minor corrections')
    
    grandchild1 = revision2['child_document']
    wf.log_state_change(grandchild1, 'draft', 'review', 'alice')
    wf.log_state_change(grandchild1, 'review', 'approve', 'bob')
    
    # Family 2: Manual that gets rejected
    wf.create_document('MANUAL-042', user_id='charlie', notes='User manual draft')
    wf.log_state_change('MANUAL-042', 'draft', 'review', 'charlie')
    wf.log_state_change('MANUAL-042', 'review', 'reject', 'bob', 'Out of scope')
    
    # Family 3: Quick approval
    wf.create_document('PROC-123', user_id='david', notes='Simple procedure')
    wf.log_state_change('PROC-123', 'draft', 'review', 'david')
    wf.log_state_change('PROC-123', 'review', 'approve', 'bob')
    
    # Post-approval update
    wf.log_state_change('PROC-123', 'approve', 'update', 'david', 'Regulatory change')
    wf.log_state_change('PROC-123', 'update', 'review', 'david')
    wf.log_state_change('PROC-123', 'review', 'approve', 'bob')
    
    # Family 4: Complex revision tree
    wf.create_document('GUIDE-456', user_id='eve', notes='Training guide')
    wf.log_state_change('GUIDE-456', 'draft', 'review', 'eve')
    
    # Multiple revision branches
    rev1 = wf.log_state_change('GUIDE-456', 'review', 'revise', 'bob', 'Content issues')
    child2 = rev1['child_document']
    wf.log_state_change(child2, 'draft', 'review', 'eve')
    
    rev2 = wf.log_state_change(child2, 'review', 'revise', 'bob', 'Format issues')
    grandchild2 = rev2['child_document']
    wf.log_state_change(grandchild2, 'draft', 'review', 'eve')
    wf.log_state_change(grandchild2, 'review', 'approve', 'bob')
    
    return wf

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
    fig2 = viz.plot_revision_timeline()  
    fig3 = viz.plot_state_distribution_by_generation()
    fig4 = viz.plot_document_lifecycle_analysis()
    
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
    
    # Show genealogy table
    print("\n" + "="*50)
    print("DOCUMENT GENEALOGY TABLE")
    print("="*50)
    df = wf.export_genealogy_data()
    print(df[['document_id', 'parent', 'current_state', 'is_active', 'revision_depth', 'lineage']].to_string(index=False))
    
    return wf, viz

if __name__ == "__main__":
    workflow, visualizer = run_hierarchical_examples()