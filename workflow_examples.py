import networkx as nx
import matplotlib.pyplot as plt
import pandas as pd
from datetime import datetime, timedelta
import numpy as np

def create_workflow_scenarios():
    """Create specific workflow scenario examples"""
    
    # Scenario 1: Fast Track Document (Ideal Flow)
    fast_track = [
        {'doc': 'POLICY-001', 'from': None, 'to': 'draft', 'day': 0, 'notes': 'Created by legal team'},
        {'doc': 'POLICY-001', 'from': 'draft', 'to': 'review', 'day': 1, 'notes': 'Ready for review'},
        {'doc': 'POLICY-001', 'from': 'review', 'to': 'approve', 'day': 3, 'notes': 'Approved by manager'}
    ]
    
    # Scenario 2: Revision Loop (Common Reality)
    revision_cycle = [
        {'doc': 'MANUAL-042', 'from': None, 'to': 'draft', 'day': 0, 'notes': 'Initial draft'},
        {'doc': 'MANUAL-042', 'from': 'draft', 'to': 'review', 'day': 2, 'notes': 'Submitted for review'},
        {'doc': 'MANUAL-042', 'from': 'review', 'to': 'revise', 'day': 5, 'notes': 'Needs major changes'},
        {'doc': 'MANUAL-042', 'from': 'revise', 'to': 'review', 'day': 12, 'notes': 'Revised version submitted'},
        {'doc': 'MANUAL-042', 'from': 'review', 'to': 'revise', 'day': 14, 'notes': 'Minor corrections needed'},
        {'doc': 'MANUAL-042', 'from': 'revise', 'to': 'review', 'day': 16, 'notes': 'Final corrections made'},
        {'doc': 'MANUAL-042', 'from': 'review', 'to': 'approve', 'day': 18, 'notes': 'Finally approved'}
    ]
    
    # Scenario 3: Update Cycle (Post-Approval Changes)
    update_cycle = [
        {'doc': 'PROC-123', 'from': None, 'to': 'draft', 'day': 0, 'notes': 'Created'},
        {'doc': 'PROC-123', 'from': 'draft', 'to': 'review', 'day': 1, 'notes': 'Quick review'},
        {'doc': 'PROC-123', 'from': 'review', 'to': 'approve', 'day': 3, 'notes': 'Approved'},
        {'doc': 'PROC-123', 'from': 'approve', 'to': 'update', 'day': 30, 'notes': 'Regulatory change requires update'},
        {'doc': 'PROC-123', 'from': 'update', 'to': 'review', 'day': 32, 'notes': 'Updated version ready'},
        {'doc': 'PROC-123', 'from': 'review', 'to': 'approve', 'day': 34, 'notes': 'Update approved'}
    ]
    
    # Scenario 4: Rejection and Withdrawal
    rejection_scenario = [
        {'doc': 'PROP-789', 'from': None, 'to': 'draft', 'day': 0, 'notes': 'Proposal drafted'},
        {'doc': 'PROP-789', 'from': 'draft', 'to': 'review', 'day': 3, 'notes': 'Submitted'},
        {'doc': 'PROP-789', 'from': 'review', 'to': 'reject', 'day': 7, 'notes': 'Out of scope'}
    ]
    
    withdrawal_scenario = [
        {'doc': 'TEMP-456', 'from': None, 'to': 'draft', 'day': 0, 'notes': 'Started draft'},
        {'doc': 'TEMP-456', 'from': 'draft', 'to': 'review', 'day': 2, 'notes': 'Submitted'},
        {'doc': 'TEMP-456', 'from': 'review', 'to': 'withdraw', 'day': 5, 'notes': 'Author withdrew due to new requirements'}
    ]
    
    return fast_track + revision_cycle + update_cycle + rejection_scenario + withdrawal_scenario

def plot_scenario_comparison():
    """Create a comparison view of different workflow scenarios"""
    scenarios = create_workflow_scenarios()
    df = pd.DataFrame(scenarios)
    
    fig, axes = plt.subplots(2, 3, figsize=(18, 12))
    axes = axes.flatten()
    
    # Group by document
    docs = df['doc'].unique()
    
    state_colors = {
        'draft': '#87CEEB',    # Sky blue
        'review': '#FFD700',   # Gold
        'update': '#DDA0DD',   # Plum
        'revise': '#F0E68C',   # Khaki
        'approve': '#90EE90',  # Light green
        'reject': '#FFA07A',   # Light salmon
        'withdraw': '#D3D3D3'  # Light gray
    }
    
    # Plot each document's journey
    for i, doc in enumerate(docs):
        if i >= len(axes):
            break
            
        ax = axes[i]
        doc_data = df[df['doc'] == doc].copy()
        
        # Create timeline
        days = doc_data['day'].tolist()
        states = doc_data['to'].tolist()
        
        # Plot state changes
        for j, (day, state) in enumerate(zip(days, states)):
            # Plot point
            ax.scatter(day, 0, c=state_colors[state], s=300, 
                      edgecolors='black', linewidth=2, zorder=3)
            
            # Add state label
            ax.annotate(state, (day, 0), xytext=(0, 25), 
                       textcoords='offset points', ha='center',
                       fontweight='bold', fontsize=10,
                       bbox=dict(boxstyle='round,pad=0.3', 
                               facecolor=state_colors[state], alpha=0.8))
            
            # Add day label
            ax.annotate(f'Day {day}', (day, 0), xytext=(0, -25), 
                       textcoords='offset points', ha='center',
                       fontsize=9, style='italic')
            
            # Draw connecting lines
            if j < len(days) - 1:
                ax.plot([day, days[j+1]], [0, 0], 'k--', alpha=0.5, linewidth=2)
        
        # Customize each subplot
        ax.set_title(f'{doc}\n({len(doc_data)} state changes, {days[-1]} days total)', 
                    fontweight='bold', fontsize=12)
        ax.set_ylim(-0.5, 0.5)
        ax.set_xlim(-1, max(days) + 1)
        ax.set_yticks([])
        ax.set_xlabel('Days', fontweight='bold')
        ax.grid(True, alpha=0.3)
        ax.spines['left'].set_visible(False)
        ax.spines['right'].set_visible(False)
        ax.spines['top'].set_visible(False)
    
    # Hide unused subplots
    for i in range(len(docs), len(axes)):
        axes[i].set_visible(False)
    
    plt.suptitle('Document Workflow Scenarios Comparison', fontsize=16, fontweight='bold')
    plt.tight_layout()
    return fig

def plot_workflow_network():
    """Create a network graph showing the complete workflow"""
    fig, ax = plt.subplots(figsize=(12, 10))
    
    # Create workflow graph
    G = nx.DiGraph()
    
    # Add all possible transitions based on your workflow table
    transitions = [
        ('draft', 'review', {'color': 'blue', 'style': 'solid'}),
        ('review', 'approve', {'color': 'green', 'style': 'solid'}),
        ('review', 'reject', {'color': 'red', 'style': 'solid'}),
        ('review', 'revise', {'color': 'orange', 'style': 'solid'}),
        ('revise', 'review', {'color': 'purple', 'style': 'dashed'}),
        ('approve', 'update', {'color': 'brown', 'style': 'solid'}),
        ('update', 'review', {'color': 'pink', 'style': 'dashed'}),
        ('draft', 'withdraw', {'color': 'gray', 'style': 'solid'}),
        ('review', 'withdraw', {'color': 'gray', 'style': 'solid'}),
        ('revise', 'withdraw', {'color': 'gray', 'style': 'solid'})
    ]
    
    for from_state, to_state, attrs in transitions:
        G.add_edge(from_state, to_state, **attrs)
    
    # Define positions for a clear layout
    pos = {
        'draft': (0, 0),
        'review': (2, 0),
        'revise': (1, -2),
        'update': (3, -1),
        'approve': (4, 0),
        'reject': (2, -3),
        'withdraw': (0, -3)
    }
    
    # Node styling
    node_colors = {
        'draft': '#87CEEB',
        'review': '#FFD700',
        'update': '#DDA0DD',
        'revise': '#F0E68C',
        'approve': '#90EE90',
        'reject': '#FFA07A',
        'withdraw': '#D3D3D3'
    }
    
    # Draw nodes
    for node in G.nodes():
        nx.draw_networkx_nodes(G, pos, nodelist=[node], 
                             node_color=node_colors[node],
                             node_size=2000, edgecolors='black', linewidths=2)
    
    # Draw edges with different colors and styles
    for edge in G.edges(data=True):
        from_node, to_node, attrs = edge
        style = attrs.get('style', 'solid')
        color = attrs.get('color', 'black')
        
        nx.draw_networkx_edges(G, pos, edgelist=[(from_node, to_node)],
                             edge_color=color, style=style, width=2,
                             arrowsize=20, arrowstyle='->')
    
    # Draw labels
    nx.draw_networkx_labels(G, pos, font_size=11, font_weight='bold')
    
    # Add legend for edge types
    legend_lines = [
        plt.Line2D([0], [0], color='blue', linewidth=2, label='Normal flow'),
        plt.Line2D([0], [0], color='purple', linewidth=2, linestyle='--', label='Return flow'),
        plt.Line2D([0], [0], color='green', linewidth=2, label='Approval'),
        plt.Line2D([0], [0], color='red', linewidth=2, label='Rejection'),
        plt.Line2D([0], [0], color='gray', linewidth=2, label='Withdrawal')
    ]
    ax.legend(handles=legend_lines, loc='upper left', bbox_to_anchor=(0, 1))
    
    ax.set_title('Complete Document Workflow Network\n(All possible state transitions)', 
                fontsize=16, fontweight='bold')
    ax.axis('off')
    
    plt.tight_layout()
    return fig

def plot_state_statistics():
    """Create statistics visualization from the scenarios"""
    scenarios = create_workflow_scenarios()
    df = pd.DataFrame(scenarios)
    
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 6))
    
    # State frequency
    state_counts = df['to'].value_counts()
    colors = ['#87CEEB', '#FFD700', '#90EE90', '#F0E68C', '#DDA0DD', '#FFA07A', '#D3D3D3']
    
    bars1 = ax1.bar(state_counts.index, state_counts.values, 
                   color=colors[:len(state_counts)], edgecolor='black', linewidth=1)
    ax1.set_title('State Frequency Across All Documents', fontweight='bold')
    ax1.set_ylabel('Number of Times Entered', fontweight='bold')
    ax1.tick_params(axis='x', rotation=45)
    
    # Add value labels
    for bar, value in zip(bars1, state_counts.values):
        ax1.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.05,
                str(value), ha='center', va='bottom', fontweight='bold')
    
    # Document complexity (number of state changes)
    doc_complexity = df.groupby('doc').size().sort_values(ascending=False)
    
    bars2 = ax2.bar(range(len(doc_complexity)), doc_complexity.values, 
                   color='skyblue', edgecolor='black', linewidth=1)
    ax2.set_title('Document Complexity\n(Number of State Changes)', fontweight='bold')
    ax2.set_ylabel('Number of State Changes', fontweight='bold')
    ax2.set_xlabel('Documents (sorted by complexity)', fontweight='bold')
    ax2.set_xticks(range(len(doc_complexity)))
    ax2.set_xticklabels(doc_complexity.index, rotation=45)
    
    # Add value labels
    for i, (bar, value) in enumerate(zip(bars2, doc_complexity.values)):
        ax2.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.05,
                str(value), ha='center', va='bottom', fontweight='bold')
    
    plt.tight_layout()
    return fig

# Generate all example visualizations
if __name__ == "__main__":
    print("Creating Document State Change Example Graphs...")
    print("=" * 55)
    
    # Create the visualizations
    fig1 = plot_scenario_comparison()
    fig2 = plot_workflow_network() 
    fig3 = plot_state_statistics()
    
    plt.show()
    
    # Print scenario data
    scenarios = create_workflow_scenarios()
    df = pd.DataFrame(scenarios)
    
    print("\nScenario Summary:")
    print("-" * 40)
    for doc in df['doc'].unique():
        doc_data = df[df['doc'] == doc]
        total_days = doc_data['day'].max()
        final_state = doc_data.iloc[-1]['to']
        print(f"{doc}: {len(doc_data)} changes, {total_days} days, ended in '{final_state}'")