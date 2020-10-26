"""
This module helps in the design and analysis of Artificial Neural Networks to represent the gravity field of celestial objects.
It was developed by the Advanced Conpcets team in the context of the project "ANNs for geodesy".
"""
import os

# Importing encodings for the spacial asteroid dimensions
from ._encodings import directional_encoding, positional_encoding, direct_encoding, spherical_coordinates

# Importing the losses
from ._losses import normalized_loss, mse_loss

# Importing the method to integrate the density rho(x,y,z) output of an ANN in the unit cube
from ._integration import ACC_ld, U_mc, U_ld, U_trap_opt, sobol_points

# Importing alpha shape methods
from ._hulls import alpha_shape

# Importing the plots
from ._plots import plot_mascon, plot_model_grid, plot_model_rejection
from ._plots import plot_mesh, plot_model_mesh, plot_point_cloud_mesh, plot_points
from ._plots import plot_model_vs_cloud_mesh

# Importing methods to sample points around asteroid
from ._sample_observation_points import get_target_point_sampler

# Importing the mesh_conversion methods
from ._mesh_conversion import create_mesh_from_cloud, create_mesh_from_model

# Import the labeling functions the mascons
from ._mascon_labels import U_L, ACC_L

# Import training utility functions
from ._train import init_network, train_on_batch

# Import utility functions
from ._utils import max_min_distance, enableCUDA

# Set main device by default to cpu if no other choice was made before
if "TORCH_DEVICE" not in os.environ:
    os.environ["TORCH_DEVICE"] = 'cpu'
