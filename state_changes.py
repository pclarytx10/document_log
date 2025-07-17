import networkx as nx
import matplotlib.pyplot as plt
import pandas as pd
from datetime import datetime, timedelta
import numpy as np
from collections import defaultdict
import seaborn as sns
from matplotlib.patches import FancyBboxPatch
import random

# Set style for better looking plots
plt.style.use('seaborn-v0_8')
np.random.seed(42)
random.seed(42)

class DocumentStateVisualizer:
    def __init__(self):
        self.state_colors = {
            'draft': '#e3f2fd',      # Light blue
            'review': '#fff3e0',     # Light orange  
            'update': '#f3e5f5',     # Light purple
            'revise': '#fff8e1',     # Light yellow
            'approve': '#e8f5e8',    # Light green
            'reject': '#ffebee',     # Light red
            'withdraw': '#f5f5f5'    # Light gray
        }
        
    def create_sample_data(self):
        """Create sample document state change data"""
        documents = []
        base_date = datetime(2024, 1, 1)
        
        # Document 1: Smooth approval
        doc1 = [
            {'doc_id': 'DOC001', 'state': 'draft', 'timestamp': base_date, 'user': 'Alice'},
            {'doc_id': 'DOC001', 'state': 'review', 'timestamp': base_date + timedelta(days=2), 'user': 'Alice'},
            {'doc_id': 'DOC001', 'state': 'approve', 'timestamp': base_date + timedelta(days=5), 'user': 'Bob'}
        ]
        
        # Document 2: Multiple revisions
        doc2 = [
            {'doc_id': 'DOC002', 'state': 'draft', 'timestamp': base_date + timedelta(days=1), 'user': 'Charlie'},
            {'doc_id': 'DOC002', 'state': 'review', 'timestamp': base_date + timedelta(days=3), 'user': 'Charlie'},
            {'doc_id': 'DOC002', 'state': 'revise', 'timestamp': base_date + timedelta(days=6), 'user': 'Bob'},
            {'doc_id': 'DOC002', 'state': 'review', 'timestamp': base_date + timedelta(days=10), 'user': 'Charlie'},
            {'doc_id': 'DOC002', 'state': 'revise', 'timestamp': base_date + timedelta(days=12), 'user': 'Bob'},
            {'doc_id': 'DOC002', 'state': 'review', 'timestamp': base_date + timedelta(days=16), 'user': 'Charlie'},
            {'doc_id': 'DOC002', 'state': 'approve', 'timestamp': base_date + timedelta(days=18), 'user': 'Bob'}
        ]
        
        # Document 3: Rejected
        doc3 = [
            {'doc_id': 'DOC003', 'state': 'draft', 'timestamp': base_date + timedelta(days=2), 'user': 'David'},
            {'doc_id': 'DOC003', 'state': 'review', 'timestamp': base_date + timedelta(days=4), 'user': 'David'},
            {'doc_id': 'DOC003', 'state': 'reject', 'timestamp': base_date + timedelta(days=7), 'user': 'Bob'}
        ]
        
        # Document 4: Withdrawn
        doc4 = [
            {'doc_id': 'DOC004', 'state': 'draft', 'timestamp': base_date + timedelta(days=3), 'user': 'Eve'},
            {'doc_id': 'DOC004', 'state': 'review', 'timestamp': base_date + timedelta(days=5), 'user': 'Eve'},
            {'doc_id': 'DOC004', 'state': 'withdraw', 'timestamp': base_date + timedelta(days=8), 'user': 'Eve'}
        ]
        
        # Document 5: Update cycle
        doc5 = [
            {'doc_id': 'DOC005', 'state': 'draft', 'timestamp': base_date + timedelta(days=1), 'user': 'Frank'},
            {'doc_id': 'DOC005', 'state': 'review', 'timestamp': base_date + timedelta(days=3), 'user': 'Frank'},
            {'doc_id': 'DOC005', 'state': 'approve', 'timestamp': base_date + timedelta(days=6), 'user': 'Bob'},
            {'doc_id': 'DOC005', 'state': 'update', 'timestamp': base_date + timedelta(days=15), 'user': 'Frank'},
            {'doc_id': 'DOC005', 'state': 'review', 'timestamp': base_date + timedelta(days=17), 'user': 'Frank'},
            {'doc_id': 'DOC005', 'state': 'approve', 'timestamp': base_date + timedelta(days=19), 'user': 'Bob'}
        ]
        
        return pd.DataFrame(doc1 + doc2 + doc3 + doc4 + doc5)

    def plot_document_timelines(self, df):
        """Create timeline visualization of document state changes"""
        fig, ax = plt.subplots(figsize=(14, 8))
        
        documents = df['doc_id'].unique()
        y_positions = {doc: i for i, doc in enumerate(documents)}
        
        for doc in documents:
            doc_data = df[df['doc_id'] == doc].sort_values('timestamp')
            
            for i, (_, row) in enumerate(doc_data.iterrows()):
                # Plot state as a point
                ax.scatter(row['timestamp'], y_positions[doc], 
                          c=self.state_colors[row['state']], 
                          s=200, 
                          edgecolors='black', 
                          linewidth=1,
                          zorder=3)
                
                # Add state label
                ax.annotate(row['state'], 
                           (row['timestamp'], y_positions[doc]), 
                           xytext=(5, 5), 
                           textcoords='offset points',
                           fontsize=9,
                           fontweight='bold')
                
                # Draw line to next state
                if i < len(doc_data) - 1:
                    next_row = doc_data.iloc[i + 1]
                    ax.plot([row['timestamp'], next_row['timestamp']], 
                           [y_positions[doc], y_positions[doc]], 
                           'k--', 
                           alpha=0.5, 
                           linewidth=2)
        
        # Customize plot
        ax.set_yticks(range(len(documents)))
        ax.set_yticklabels(documents)
        ax.set_xlabel('Timeline', fontsize=12, fontweight='bold')
        ax.set_ylabel('Documents', fontsize=12, fontweight='bold')
        ax.set_title('Document State Change Timeline', fontsize=16, fontweight='bold')
        ax.grid(True, alpha=0.3)
        
        # Add legend
        legend_elements = [plt.scatter([], [], c=color, s=100, edgecolors='black', label=state.title()) 
                          for state, color in self.state_colors.items()]
        ax.legend(handles=legend_elements, bbox_to_anchor=(1.05, 1), loc='upper left')
        
        plt.tight_layout()
        return fig

    def plot_state_transition_flow(self, df):
        """Create a flow diagram showing document paths through states"""
        fig, ax = plt.subplots(figsize=(12, 10))
        
        # Create a graph for each document's path
        G = nx.DiGraph()
        
        # Track transitions for each document
        doc_paths = defaultdict(list)
        for doc in df['doc_id'].unique():
            doc_data = df[df['doc_id'] == doc].sort_values('timestamp')
            states = doc_data['state'].tolist()
            doc_paths[doc] = states
            
            # Add edges for this document's path
            for i in range(len(states) - 1):
                G.add_edge(f"{states[i]}_{i}", f"{states[i+1]}_{i+1}", doc_id=doc)
        
        # Create a simpler visualization showing all unique transitions
        transition_graph = nx.DiGraph()
        transition_counts = defaultdict(int)
        
        for doc in df['doc_id'].unique():
            doc_data = df[df['doc_id'] == doc].sort_values('timestamp')
            states = doc_data['state'].tolist()
            
            for i in range(len(states) - 1):
                from_state = states[i]
                to_state = states[i + 1]
                transition_graph.add_edge(from_state, to_state)
                transition_counts[(from_state, to_state)] += 1
        
        # Position nodes in a logical workflow layout
        pos = {
            'draft': (0, 0),
            'review': (2, 0),
            'revise': (1, -1),
            'update': (3, -1),
            'approve': (4, 0),
            'reject': (2, -2),
            'withdraw': (0, -2)
        }
        
        # Draw nodes
        for node in transition_graph.nodes():
            nx.draw_networkx_nodes(transition_graph, pos, 
                                 nodelist=[node],
                                 node_color=self.state_colors[node],
                                 node_size=2000,
                                 edgecolors='black',
                                 linewidths=2)
        
        # Draw edges with thickness based on frequency
        for edge in transition_graph.edges():
            from_state, to_state = edge
            count = transition_counts[edge]
            nx.draw_networkx_edges(transition_graph, pos,
                                 edgelist=[edge],
                                 width=count * 2,
                                 alpha=0.7,
                                 edge_color='gray',
                                 arrowsize=20,
                                 arrowstyle='->')
        
        # Draw labels
        nx.draw_networkx_labels(transition_graph, pos, font_size=10, font_weight='bold')
        
        # Add edge labels with counts
        edge_labels = {edge: str(transition_counts[edge]) for edge in transition_graph.edges()}
        nx.draw_networkx_edge_labels(transition_graph, pos, edge_labels, font_size=8)
        
        ax.set_title('Document State Transition Flow\n(Edge thickness = frequency)', 
                    fontsize=16, fontweight='bold')
        ax.axis('off')
        
        plt.tight_layout()
        return fig

    def plot_state_duration_analysis(self, df):
        """Analyze and plot time spent in each state"""
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 6))
        
        # Calculate time spent in each state
        state_durations = []
        
        for doc in df['doc_id'].unique():
            doc_data = df[df['doc_id'] == doc].sort_values('timestamp')
            
            for i in range(len(doc_data) - 1):
                current_state = doc_data.iloc[i]['state']
                duration = (doc_data.iloc[i + 1]['timestamp'] - doc_data.iloc[i]['timestamp']).days
                state_durations.append({'state': current_state, 'duration': duration, 'doc_id': doc})
        
        duration_df = pd.DataFrame(state_durations)
        
        # Box plot of durations by state
        if not duration_df.empty:
            sns.boxplot(data=duration_df, x='state', y='duration', ax=ax1)
            ax1.set_title('Time Spent in Each State (Days)', fontweight='bold')
            ax1.set_xlabel('State', fontweight='bold')
            ax1.set_ylabel('Duration (Days)', fontweight='bold')
            ax1.tick_params(axis='x', rotation=45)
        
        # State frequency chart
        state_counts = df['state'].value_counts()
        bars = ax2.bar(state_counts.index, state_counts.values, 
                      color=[self.state_colors[state] for state in state_counts.index],
                      edgecolor='black', linewidth=1)
        
        ax2.set_title('Frequency of Each State', fontweight='bold')
        ax2.set_xlabel('State', fontweight='bold')
        ax2.set_ylabel('Count', fontweight='bold')
        ax2.tick_params(axis='x', rotation=45)
        
        # Add value labels on bars
        for bar, value in zip(bars, state_counts.values):
            ax2.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.1, 
                    str(value), ha='center', va='bottom', fontweight='bold')
        
        plt.tight_layout()
        return fig

    def plot_document_journey_map(self, df):
        """Create a journey map showing individual document paths"""
        fig, ax = plt.subplots(figsize=(16, 10))
        
        documents = df['doc_id'].unique()
        
        # Create a subplot for each document
        n_docs = len(documents)
        colors = plt.cm.Set3(np.linspace(0, 1, n_docs))
        
        y_offset = 0
        for i, (doc, color) in enumerate(zip(documents, colors)):
            doc_data = df[df['doc_id'] == doc].sort_values('timestamp')
            
            # Plot the journey for this document
            x_positions = range(len(doc_data))
            y_positions = [y_offset] * len(doc_data)
            
            # Draw the path
            ax.plot(x_positions, y_positions, 'o-', 
                   color=color, linewidth=3, markersize=12, 
                   label=doc, alpha=0.8)
            
            # Add state labels
            for j, (_, row) in enumerate(doc_data.iterrows()):
                ax.annotate(row['state'], 
                           (j, y_offset), 
                           xytext=(0, 15), 
                           textcoords='offset points',
                           ha='center', 
                           fontsize=9, 
                           fontweight='bold',
                           bbox=dict(boxstyle='round,pad=0.3', 
                                   facecolor=self.state_colors[row['state']], 
                                   alpha=0.8))
                
                # Add user info
                ax.annotate(f"({row['user']})", 
                           (j, y_offset), 
                           xytext=(0, -20), 
                           textcoords='offset points',
                           ha='center', 
                           fontsize=7, 
                           style='italic')
            
            y_offset += 1
        
        ax.set_xlabel('Transition Sequence', fontsize=12, fontweight='bold')
        ax.set_ylabel('Documents', fontsize=12, fontweight='bold')
        ax.set_title('Document Journey Map\n(Shows the path each document took through states)', 
                    fontsize=16, fontweight='bold')
        ax.set_yticks(range(len(documents)))
        ax.set_yticklabels(documents)
        ax.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
        ax.grid(True, alpha=0.3)
        
        plt.tight_layout()
        return fig

    def generate_all_visualizations(self):
        """Generate all visualization examples"""
        # Create sample data
        df = self.create_sample_data()
        
        print("Generating Document State Change Visualizations...")
        print("=" * 50)
        
        # Generate all plots
        fig1 = self.plot_document_timelines(df)
        fig1.suptitle('Example 1: Document Timeline View', fontsize=18, fontweight='bold', y=0.98)
        
        fig2 = self.plot_state_transition_flow(df)
        fig2.suptitle('Example 2: State Transition Flow', fontsize=18, fontweight='bold', y=0.95)
        
        fig3 = self.plot_state_duration_analysis(df)
        fig3.suptitle('Example 3: State Duration Analysis', fontsize=18, fontweight='bold', y=0.98)
        
        fig4 = self.plot_document_journey_map(df)
        fig4.suptitle('Example 4: Document Journey Map', fontsize=18, fontweight='bold', y=0.95)
        
        plt.show()
        
        # Print summary statistics
        print("\nSample Data Summary:")
        print(f"Total Documents: {df['doc_id'].nunique()}")
        print(f"Total State Changes: {len(df)}")
        print(f"States Used: {df['state'].unique()}")
        print(f"Users Involved: {df['user'].unique()}")
        
        return df

# Run the visualization examples
if __name__ == "__main__":
    visualizer = DocumentStateVisualizer()
    sample_data = visualizer.generate_all_visualizations()
    
    # Display the raw data
    print("\nSample Data:")
    print(sample_data.to_string(index=False))