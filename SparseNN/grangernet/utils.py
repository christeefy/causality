import numpy as np
from graphviz import Digraph

from pathlib import Path

import matplotlib.pyplot as plt

def causal_heatmap(W, var_names, mode, ord=2, threshold=0.1, dst=None, file_header=None, ext='png'):
    '''
    Visualise calculated weights as 
    a heatmap.
    
    When mode is 'joint', it outputs a 
    (p_effect x p_cause) heatmap. 

    When mode is 'joint_threshold', similar map as 'joint'
    it produces except values are thresholded to binary values. 

    When mode is 'ind', it produces a 
    (p_cause x K) heatmap for each individual p_effect.

    
    Inputs:
        W:            A np array of size (p_effect x p_cause x K)
        df:           A pd dataframe containing column labels
        mode:         Visualisation mode {'joint', 'ind', 'joint_threshold'}
        ord :         The order of the norm
        dst:          Destination to save file
        file_header:  String to be appended to each filename
        ext:          Format to save file
        
    Returns:
        A plt heatmap.
    '''
    assert mode in ['joint', 'ind', 'joint_threshold']
    
    # Infer dimensions
    p, K = W[0].shape

    # Calculate norm on axis 2
    _W_norm = np.linalg.norm(W, ord=ord, axis=2)

    # Infer autocorrelation setting (Boolean) of analysis
    autocorrelation_setting = _has_autocorrelation(W)
    print('Autocorrelation during analysis: {}'.format(autocorrelation_setting))
    
    if mode == 'joint':        
        # Visualise causality
        plt.figure(figsize=(p, p))
        plt.imshow(_W_norm, cmap='Greys')
        plt.xlabel('Cause\n', fontsize=16)
        plt.xticks(range(p), var_names)
        plt.ylabel('Response', fontsize=16)
        plt.yticks(range(p), var_names)
        ax = plt.gca()
        ax.xaxis.set_label_position('top')
        ax.xaxis.tick_top()
        
        # Set white to 0
        plt.clim(vmin=0)
        plt.pause(0.001)
        
        # Output image to file if dst is not None
        if dst is not None:
            assert dst[-1] == '/'

        	# Create path if itdoes not exist
            Path(dst).mkdir(exist_ok=True, parents=True)

            plt.savefig(dst + file_header + '_overall.' + ext, bbox_inches='tight')

    elif mode == 'joint_threshold':
        # Get tuple containing index of values above threshold
        idx_above = np.where(_W_norm >= threshold * np.max(_W_norm))
        idx_below = np.where(_W_norm < threshold * np.max(_W_norm))
        
        # Thresold appropriate values to 0 or 1
        _W_norm[idx_above] = 1
        _W_norm[idx_below] = 0

        # Visualise causality
        plt.figure(figsize=(p, p))
        plt.imshow(_W_norm, cmap='Greys')
        plt.xlabel('Cause\n', fontsize=16)
        plt.xticks(range(p), var_names)
        plt.ylabel('Response', fontsize=16)
        plt.yticks(range(p), var_names)
        ax = plt.gca()
        ax.xaxis.set_label_position('top')
        ax.xaxis.tick_top()
        
        # Set white to 0
        plt.clim(vmin=0)
        plt.pause(0.001)
        
        # Output image to file if dst is not None
        if dst is not None:
            assert dst[-1] == '/'

            # Create path if itdoes not exist
            Path(dst).mkdir(exist_ok=True, parents=True)

            plt.savefig(dst + file_header + '_overall.' + ext, bbox_inches='tight')
        
    elif mode == 'ind':
        for (var, row) in zip(var_names, W):
            plt.figure(figsize=(K, p))
            plt.imshow(row.T, cmap='Greys')
            plt.xlabel('Causes to {}\n'.format(var), fontsize=16)
            plt.xticks(range(p), var_names)
            plt.ylabel('Time Lag', fontsize=16)
            plt.yticks(range(K), range(1, K + 1))
            ax = plt.gca()
            ax.xaxis.set_label_position('top')
            ax.xaxis.tick_top()

            # Set white to 0
            plt.clim(vmin=0, vmax=np.max(_W_norm))

            # Output image to file if dst is not None
            if dst is not None:
                assert dst[-1] == '/'

                # Create path if itdoes not exist
                Path(dst).mkdir(exist_ok=True, parents=True)

                plt.savefig('{}{}_{}.{}'.format(dst, file_header, var, ext), bbox_inches='tight')

            print()
            plt.pause(0.001)
    

def causal_graph(W, var_names, threshold=0.1, use_circo_layout=None, dst=None, filename='graph'):
    '''
    Construct a causal graph using the graphviz module.

    Inputs:
        W:                FCNN layer 1 weights as a np array (p x p x K)
        var_names:        List of variable names
        threshold:        Minimum pct of max value of W to consider a positive causal connection
        use_circo_layout: Boolean on whether to use circo layout. Default is None, 
                          which infers based on whether W contains autocorrelation.
        dst:              File save location
        filename:         Filename
    '''
    # Calculate L2-norm of W
    _W_norm = np.linalg.norm(W, axis=-1)

    # Create causal directed graph
    dot = Digraph()

    # Remove margin and let nodes flow from left to right
    dot.graph_attr['margin'] = '0'
    dot.graph_attr['rankdir'] = 'LR'
    if not _has_autocorrelation(W):
        dot.graph_attr['layout'] = 'circo'

    # Create nodes
    for var in var_names:
        dot.node(var, var)

    # Create a function to zip np.where results
    zipper = lambda x: zip(x[0], x[1])

    # Create edges
    for (effect, cause) in zipper(np.where(_W_norm >= threshold * np.max(_W_norm))):
        # Obtain relative weight of element
        _weight = _W_norm[effect, cause] / np.max(_W_norm)
        dot.edge(var_names[cause], var_names[effect], penwidth=str(5 * _weight), arrowsize='1')

    # Save file (optional)
    if dst is not None:
        dot.render(filename, dst, view=False, cleanup=True)

    return dot


def save_results(filename, dst, W, hparams, W_submod=None):
    '''
    Save computation results to dst/filename using np.savez. 
    W and hparams will be saved as 'W' and 'hparams'
    respectively. 
    '''
    # Create dst folder if it does not exist
    Path(dst).mkdir(exist_ok=True, parents=True)

    if W_submod is None:
        np.savez('{}/{}.npz'.format(dst, filename), W=W, hparams=hparams)
    else:
        np.savez('{}/{}.npz'.format(dst, filename), W=W, W_submod=W_submod, hparams=hparams)
    

def load_results(src):
    '''
    Load results from src.
    Returns subsequent W and hparams.
    '''
    file = np.load('{}.npz'.format(src))
    
    W = file['W']
    hparams = file['hparams'].item()
    
    if 'W_submod' in file.keys():
        W_submod = file['W_submod']
        return W, W_submod, hparams
    
    return W, hparams


def _has_autocorrelation(W):
    '''
    Checks whether W (p x p x K) was calculated with 
    or without the autocorrelation setting
    during training. 

    Returns a Boolean.
    '''

    # Compute the L2 norm
    W_norm = np.linalg.norm(W, axis=-1)

    return not np.all(np.diag(W_norm) == 0)
