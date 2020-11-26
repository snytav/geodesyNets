from ._sample_observation_points import get_target_point_sampler
from ._mesh_conversion import create_mesh_from_cloud, create_mesh_from_model
from ._integration import ACC_ld
from ._mascon_labels import ACC_L

from matplotlib import pyplot as plt
import matplotlib as mpl
from matplotlib.lines import Line2D
import torch
import math
import numpy as np
import pyvista as pv
import pyvistaqt as pvqt
from tqdm import tqdm
from scipy.spatial.transform import Rotation as rotation
pv.set_plot_theme("night")


def plot_model_vs_cloud_mesh(model, gt_mesh, encoding, save_path=None):
    """Creates a side by side of the model and the ground truth mesh passed to this

    Args:
        model (torch nn): trained model
        gt_mesh (pyvista mesh): ground-truth mesh
        encoding (func): encoding function for the model
        save_path (str, optional): Pass to store plot, if none will display. Defaults to None.
    """
    model_mesh = create_mesh_from_model(
        model, encoding, rho_threshold=1.5e-2, plot_each_it=-1)

    p = pv.Plotter(shape=(1, 2))

    p.subplot(0, 0)
    p.show_grid()
    p.add_text("Model Prediction", font_size=12)
    p.add_mesh(model_mesh, color="grey", show_edges=False, smooth_shading=True)

    p.subplot(0, 1)
    p.show_grid()
    p.add_text("Ground Truth", font_size=12)
    p.add_mesh(gt_mesh, color="grey", show_edges=False, smooth_shading=True)

    if save_path is None:
        p.show()
    else:
        p.save_graphic(save_path, title="")
        p.close()


def plot_points(points, elev=45, azim=45):
    """Creates a 3D scatter plot of passed points.

    Args:
        points (torch tensor): Points to plot.
        elev (float): elevation of the 3D view
        azim (float): azimuth for the 3D view
    """
    fig = plt.figure()
    ax = fig.add_subplot(111, projection='3d')
    ax.view_init(elev=elev, azim=azim)
    ax.scatter(points[:, 0].cpu().numpy(),
               points[:, 1].cpu().numpy(),
               points[:, 2].cpu().numpy())
    ax.set_xlabel("X")
    ax.set_ylabel("Y")
    ax.set_zlabel("Z")
    ax.set_xlim([-1, 1])
    ax.set_ylim([-1, 1])
    ax.set_zlim([-1, 1])


def plot_model_mesh(model, encoding, interactive=False, rho_threshold=1.5e-2):
    """Plots the mesh generated from a model that predicts rho. Returns the mesh

    Args:
        model (Torch Model): Model to use
        encoding (Encoding function): The function used to encode points for the model
        interactive (bool, optional): Creates a separate window which you can use interactively. Defaults to True.
    """
    mesh = create_mesh_from_model(
        model, encoding, rho_threshold=rho_threshold, plot_each_it=-1)
    plot_mesh(mesh, smooth_shading=True,
              show_edges=False, interactive=interactive)
    return mesh


def plot_point_cloud_mesh(cloud, distance_threshold=0.125, use_top_k=1, interactive=False):
    """Display a mesh generated from a point cloud. Returns the mesh

    Args:
        cloud (torch tensor): The points that should be used to generate the mesh (3,N)
        distance_threshold (float): Distance threshold for the mesh generation algorithm. Use larger ones if mesh is broken up into.
        use_top_k (int): the number of nearest neighbours to be used for distance.
        interactive (bool): Creates a separate window which you can use interactively.
    """
    mesh = create_mesh_from_cloud(cloud.cpu().numpy(
    ), use_top_k=use_top_k, distance_threshold=distance_threshold, plot_each_it=-1)
    plot_mesh(mesh, smooth_shading=True,
              show_edges=False, interactive=interactive)
    return mesh


def plot_mesh(mesh, show_edges=True, smooth_shading=False, interactive=True, elev=45, azim=45):
    """Plots a mesh ()

    Args:
        mesh (pyvista mesh): mesh to plot
        show_edges (bool,): Show grid wires.
        smooth_shading (bool): Use smooth_shading.
        interactive (bool): Creates a separate window which you can use interactively.
    """
    # Plot mesh
    if interactive:
        p = pvqt.BackgroundPlotter()
    else:
        p = pv.Plotter()
    p.show_grid()
    p.add_mesh(mesh, color="grey", show_edges=show_edges,
               smooth_shading=smooth_shading)
    p.show()


def plot_mascon(mascon_points, mascon_masses=None, elev=45, azim=45, alpha=0.01, s=None, views_2d=True, save_path=None):
    """Plots a mascon model

    Args:
        mascon_points (2-D array-like): an (N, 3) array-like object containing the coordinates of the points
        mascon_masses (1-D array-like): a (N,) array-like object containing the values for the point masses
        elev (float): elevation of the starting 3D view
        azim (float): azimuth for the starting 3D view
        alpha (float): alpha for the mass visualization
        s (int): scale for the visualized masses

    """
    x = mascon_points[:, 0].cpu()
    y = mascon_points[:, 1].cpu()
    z = mascon_points[:, 2].cpu()

    if s is None:
        if mascon_masses is None:
            s = 1./len(mascon_points)
            s = s/max(s)*200
        else:
            s = mascon_masses.cpu() / sum(mascon_masses.cpu())
            s = s/max(s)*200

    # And we plot it
    fig = plt.figure(figsize=(6, 5), dpi=150, facecolor='white')
    if views_2d:
        ax = fig.add_subplot(221, projection='3d')
    else:
        ax = fig.add_subplot(111, projection='3d')

    # And visualize the masses
    D = 1.
    ax.scatter(x, y, z, alpha=alpha, s=s, c='k')
    ax.view_init(elev=elev, azim=azim)
    ax.set_xlim([-D, D])
    ax.set_ylim([-D, D])
    ax.set_zlim([-D, D])
    ax.set_axis_off()
    # X Rectangle
    ax.plot_wireframe(np.asarray([[0, 0], [0, 0]]), np.asarray([[D, D], [-D, -D]]),
                      np.asarray([[-D, D], [-D, D]]), color="red", linestyle="--", alpha=0.75)
    # Y Rectangle
    ax.plot_wireframe(np.asarray([[D, D], [-D, -D]]), np.asarray([[0, 0], [0, 0]]),
                      np.asarray([[-D, D], [-D, D]]), color="blue", linestyle="--", alpha=0.75)
    # Z Rectangle
    ax.plot_wireframe(np.asarray([[-D, D], [-D, D]]), np.asarray([[D, D], [-D, -D]]),
                      np.asarray([[0, 0], [0, 0]]), color="green", linestyle="--", alpha=0.75)

    if views_2d:
        ax2 = fig.add_subplot(222)
        ax2.scatter(x, y, color='k', s=s, alpha=alpha)
        ax2.set_xlim([-1, 1])
        ax2.set_ylim([-1, 1])
        ax2.set_xticks([])
        ax2.set_yticks([])
        ax2.set_aspect('equal', 'box')
        ax2.spines['left'].set_color('green')
        ax2.spines['right'].set_color('green')
        ax2.spines['top'].set_color('green')
        ax2.spines['bottom'].set_color('green')

        ax3 = fig.add_subplot(223)
        ax3.scatter(x, z, color='k', s=s, alpha=alpha)
        ax3.set_xlim([-1, 1])
        ax3.set_ylim([-1, 1])
        ax3.set_xticks([])
        ax3.set_yticks([])
        ax3.set_aspect('equal', 'box')
        ax3.spines['left'].set_color('blue')
        ax3.spines['right'].set_color('blue')
        ax3.spines['top'].set_color('blue')
        ax3.spines['bottom'].set_color('blue')

        ax4 = fig.add_subplot(224)
        ax4.scatter(y, z, color='k', s=s, alpha=alpha)
        ax4.set_xlim([-1, 1])
        ax4.set_ylim([-1, 1])
        ax4.set_xticks([])
        ax4.set_yticks([])
        ax4.set_aspect('equal', 'box')
        ax4.spines['left'].set_color('red')
        ax4.spines['right'].set_color('red')
        ax4.spines['top'].set_color('red')
        ax4.spines['bottom'].set_color('red')

    if save_path is not None:
        plt.savefig(save_path, dpi=150)


def plot_model_grid(model, encoding, N=20, bw=False, alpha=0.2, views_2d=True, c=1.):
    """Plots the neural model of the asteroid density in the [-1,1]**3 cube showing
    the density value on a grid.

    Args:
        model (callable (a,b)->1): neural model for the asteroid.
        encoding: the encoding for the neural inputs.
        N (int): grid size (N**3 points will be plotted).
        bw (bool): when True considers zero density as white and transparent. The final effect is a black and white plot
        alpha (float): alpha for the visualization
        views_2d (bool): activates also the 2d projections
        c (float, optional): Normalization constant. Defaults to 1.

    """

    # We create the grid
    x = torch.linspace(-1, 1, N)
    y = torch.linspace(-1, 1, N)
    z = torch.linspace(-1, 1, N)
    X, Y, Z = torch.meshgrid((x, y, z))

    # We compute the density on the grid points (no gradient as its only for plotting)
    nn_inputs = torch.cat(
        (X.reshape(-1, 1), Y.reshape(-1, 1), Z.reshape(-1, 1)), dim=1)
    nn_inputs = encoding(nn_inputs)
    RHO = model(nn_inputs).detach()*c

    # And we plot it
    fig = plt.figure()
    if views_2d:
        ax = fig.add_subplot(221, projection='3d')
    else:
        ax = fig.add_subplot(111, projection='3d')
    if bw:
        col = torch.cat((1-RHO, 1-RHO, 1-RHO, RHO), dim=1).cpu()
        alpha = None
    else:
        col = RHO.cpu()

    ax.scatter(X.reshape(-1, 1).cpu(), Y.reshape(-1, 1).cpu(), Z.reshape(-1, 1).cpu(),
               marker='.', c=col, s=100, alpha=alpha)
    ax.set_xlim([-1, 1])
    ax.set_ylim([-1, 1])
    ax.set_zlim([-1, 1])
    ax.view_init(elev=45., azim=45.)
    ax.axes.xaxis.set_ticklabels([])
    ax.axes.yaxis.set_ticklabels([])
    ax.axes.zaxis.set_ticklabels([])

    if views_2d:
        ax2 = fig.add_subplot(222)
        ax2.scatter(X.reshape(-1, 1)[:, 0].cpu(), Y.reshape(-1, 1)[:, 0].cpu(),
                    marker='.', c=col, s=100, alpha=alpha)
        ax2.set_xlim([-1, 1])
        ax2.set_ylim([-1, 1])
        ax2.set_xticks([])
        ax2.set_yticks([])
        ax2.set_aspect('equal', 'box')

        ax3 = fig.add_subplot(223)
        ax3.scatter(X.reshape(-1, 1)[:, 0].cpu(), Z.reshape(-1, 1)[:, 0].cpu(),
                    marker='.', c=col, s=100, alpha=alpha)
        ax3.set_xlim([-1, 1])
        ax3.set_ylim([-1, 1])
        ax3.set_xticks([])
        ax3.set_yticks([])
        ax3.set_aspect('equal', 'box')

        ax4 = fig.add_subplot(224)
        ax4.scatter(Z.reshape(-1, 1)[:, 0].cpu(), Y.reshape(-1, 1)[:, 0].cpu(),
                    marker='.', c=col, s=100, alpha=alpha)
        ax4.set_xlim([-1, 1])
        ax4.set_ylim([-1, 1])
        ax4.set_xticks([])
        ax4.set_yticks([])
        ax4.set_aspect('equal', 'box')


def plot_model_rejection(model, encoding, N=1500, views_2d=False, bw=False, alpha=0.2, crop_p=1e-2, s=50, save_path=None, c=1., progressbar=False, elev=45., azim=45.):
    """Plots the neural model of the asteroid density in the [-1,1]**3 cube interpreting the density
    as a probability distribution and performing a rejection sampling approach

    Args:
        model (callable (N,M)->1): neural model for the asteroid.
        encoding: the encoding for the neural inputs.
        N (int): number of points to be considered.
        views_2d (bool): activates also the 2d projections
        bw (bool): results in a black and white plot
        alpha (float): alpha for the visualization
        crop_p (float): all points below this density are rejected
        s (int): size of the non rejected points visualization
        save_path (str, optional): Pass to store plot, if none will display. Defaults to None.
        c (float, optional): Normalization constant. Defaults to 1.
        progressbar (bool optional): activates a progressbar. Defaults to False.
        elev (float): elevation of the 3D view
        azim (float): azimuth for the 3D view
    """
    torch.manual_seed(42)  # Seed torch to always get the same points
    points = []
    rho = []
    batch_size = 4096
    found = 0
    if progressbar:
        pbar = tqdm(desc="Sampling points...", total=N)
    while found < N:
        candidates = torch.rand(batch_size, 3) * 2 - 1
        nn_inputs = encoding(candidates)
        rho_candidates = model(nn_inputs).detach() * c
        mask = rho_candidates > (torch.rand(batch_size, 1) + crop_p)
        rho_candidates = rho_candidates[mask]
        candidates = [[it[0].item(), it[1].item(), it[2].item()]
                      for it, m in zip(candidates, mask) if m]
        if len(candidates) == 0:
            print("All points rejected! Plot is empty, try cropping less?")
            return
        points.append(torch.tensor(candidates))
        rho.append(rho_candidates)
        found += len(rho_candidates)
        if progressbar:
            pbar.update(len(rho_candidates))
    if progressbar:
        pbar.close()
    points = torch.cat(points, dim=0)[:N]  # concat and discard after N
    rho = torch.cat(rho, dim=0)[:N]  # concat and discard after N

    fig = plt.figure(figsize=(6, 5), dpi=150, facecolor='white')
    if views_2d:
        ax = fig.add_subplot(221, projection='3d')
    else:
        ax = fig.add_subplot(111, projection='3d')
    if bw:
        col = 'k'
    else:
        col = rho.cpu()
    # And we plot it
    ax.scatter(points[:, 0].cpu(), points[:, 1].cpu(), points[:, 2].cpu(),
               marker='.', c=col, s=s, alpha=alpha)
    ax.set_xlim([-1, 1])
    ax.set_ylim([-1, 1])
    ax.set_zlim([-1, 1])
    ax.view_init(elev=elev, azim=azim)
    ax.set_axis_off()

    # X Rectangle
    ax.plot_wireframe(np.asarray([[0, 0], [0, 0]]), np.asarray([[1, 1], [-1, -1]]),
                      np.asarray([[-1, 1], [-1, 1]]), color="red", linestyle="--", alpha=0.75)
    # Y Rectangle
    ax.plot_wireframe(np.asarray([[1, 1], [-1, -1]]), np.asarray([[0, 0], [0, 0]]),
                      np.asarray([[-1, 1], [-1, 1]]), color="blue", linestyle="--", alpha=0.75)
    # Z Rectangle
    ax.plot_wireframe(np.asarray([[-1, 1], [-1, 1]]), np.asarray([[1, 1], [-1, -1]]),
                      np.asarray([[0, 0], [0, 0]]), color="green", linestyle="--", alpha=0.75)

    if views_2d:
        ax2 = fig.add_subplot(222)
        ax2.scatter(points[:, 0].cpu(), points[:, 1].cpu(),
                    marker='.', c=col, s=s, alpha=alpha)
        ax2.set_xlim([-1, 1])
        ax2.set_ylim([-1, 1])
        ax2.set_xticks([])
        ax2.set_yticks([])
        ax2.set_aspect('equal', 'box')
        ax2.spines['bottom'].set_color('green')
        ax2.spines['top'].set_color('green')
        ax2.spines['right'].set_color('green')
        ax2.spines['left'].set_color('green')

        ax3 = fig.add_subplot(223)
        ax3.scatter(points[:, 0].cpu(), points[:, 2].cpu(),
                    marker='.', c=col, s=s, alpha=alpha)
        ax3.set_xlim([-1, 1])
        ax3.set_ylim([-1, 1])
        ax3.set_xticks([])
        ax3.set_yticks([])
        ax3.set_aspect('equal', 'box')
        ax3.spines['bottom'].set_color('blue')
        ax3.spines['top'].set_color('blue')
        ax3.spines['right'].set_color('blue')
        ax3.spines['left'].set_color('blue')

        ax4 = fig.add_subplot(224)
        ax4.scatter(points[:, 2].cpu(), points[:, 1].cpu(),
                    marker='.', c=col, s=s, alpha=alpha)
        ax4.set_xlim([-1, 1])
        ax4.set_ylim([-1, 1])
        ax4.set_xticks([])
        ax4.set_yticks([])
        ax4.set_aspect('equal', 'box')
        ax4.spines['bottom'].set_color('red')
        ax4.spines['top'].set_color('red')
        ax4.spines['right'].set_color('red')
        ax4.spines['left'].set_color('red')

    if save_path is not None:
        plt.savefig(save_path, dpi=150)


def plot_gradients_per_layer(model):
    """Plots mean and max gradients per layer currently stored in model params. Inspired by https://github.com/alwynmathew/gradflow-check

    Args:
        model (torch model): Trained network
    """
    named_params = model.named_parameters()
    fig = plt.figure()
    avg_gradient, max_gradient, layers = [], [], []
    for name, parameter in named_params:
        if(parameter.requires_grad) and ("bias" not in name):
            layers.append(name)
            avg_gradient.append(parameter.grad.abs().mean())
            max_gradient.append(parameter.grad.abs().max())
    plt.bar(np.arange(len(max_gradient)),
            max_gradient, alpha=0.5, lw=1, color="lime")
    plt.bar(np.arange(len(max_gradient)),
            avg_gradient, alpha=0.5, lw=1, color="b")
    plt.hlines(0, 0, len(avg_gradient)+1, lw=2, color="k")
    plt.xticks(range(0, len(avg_gradient), 1), layers, rotation="vertical")
    plt.xlim(left=-0.5, right=len(avg_gradient))
    # plt.ylim(bottom=-0.001, top=0.02)  # zoom in on the lower gradient regions
    plt.xlabel("Layer Name")
    plt.ylabel("Average Gradient")
    plt.grid(True)
    plt.legend([Line2D([0], [0], color="lime", lw=4),
                Line2D([0], [0], color="b", lw=4),
                Line2D([0], [0], color="k", lw=4)], ['max-gradient', 'mean-gradient', 'zero-gradient'])

    plt.tight_layout()


def plot_model_vs_mascon_rejection(model, encoding, points, masses=None, N=2500, alpha=0.075, crop_p=1e-2, s=100, save_path=None, c=1., backcolor=[0.15, 0.15, 0.15], progressbar=False, elev=45., azim=45.):
    """Plots both the mascon and model rejection in one figure for direct comparison
    Args:
        model (callable (N,M)->1): neural model for the asteroid.
        encoding: the encoding for the neural inputs.
        points (2-D array-like): an (N, 3) array-like object containing the coordinates of the points
        masses (1-D array-like): a (N,) array-like object containing the values for the point masses
        N (int): number of points to be considered.
        views_2d (bool): activates also the 2d projections
        alpha (float): alpha for the visualization
        crop_p (float): all points below this density are rejected
        s (int): size of the non rejected points visualization
        save_path (str, optional): Pass to store plot, if none will display. Defaults to None.
        c (float, optional): Normalization constant. Defaults to 1.
        progressbar (bool, optional): activates a progressbar. Defaults to False.
        backcolor (list, optional): Plot background color. Defaults to [0.15, 0.15, 0.15].
        elev (float): elevation of the 3D view
        azim (float): azimuth for the 3D view
    """

    # Mascon masses
    x = points[:, 0].cpu()
    y = points[:, 1].cpu()
    z = points[:, 2].cpu()

    s = 22000 / len(points)

    if masses is None:
        normalized_masses = s
    else:
        normalized_masses = masses / sum(masses)
        normalized_masses = (normalized_masses * s * len(x)).cpu()

    torch.manual_seed(42)  # Seed torch to always get the same points
    points = []
    rho = []
    batch_size = 4096
    found = 0
    if progressbar:
        pbar = tqdm(desc="Sampling points...", total=N)
    while found < N:
        candidates = torch.rand(batch_size, 3) * 2 - 1
        nn_inputs = encoding(candidates)
        rho_candidates = model(nn_inputs).detach() * c
        mask = rho_candidates > (torch.rand(batch_size, 1) + crop_p)
        rho_candidates = rho_candidates[mask]
        candidates = [[it[0].item(), it[1].item(), it[2].item()]
                      for it, m in zip(candidates, mask) if m]
        if len(candidates) == 0:
            print("All points rejected! Plot is empty, try cropping less?")
            return
        points.append(torch.tensor(candidates))
        rho.append(rho_candidates)
        found += len(rho_candidates)
        if progressbar:
            pbar.update(len(rho))
    if progressbar:
        pbar.close()
    points = torch.cat(points, dim=0)[:N]  # concat and discard after N
    rho = torch.cat(rho, dim=0)[:N]  # concat and discard after N

    fig = plt.figure(dpi=150, facecolor=backcolor)
    ax = fig.add_subplot(221, projection='3d')
    ax.set_facecolor(backcolor)
    col = 'cornflowerblue'

    # And we plot it
    ax.scatter(x, y, z, color='k', s=normalized_masses, alpha=0.5)
    ax.scatter(points[:, 0].cpu(), points[:, 1].cpu(), points[:, 2].cpu(),
               marker='.', c=col, s=s, alpha=alpha)
    ax.set_xlim([-1, 1])
    ax.set_ylim([-1, 1])
    ax.set_zlim([-1, 1])
    ax.view_init(elev=elev, azim=azim)
    ax.axes.xaxis.set_ticklabels([])
    ax.axes.yaxis.set_ticklabels([])
    ax.axes.zaxis.set_ticklabels([])
    # X Rectangle
    ax.plot_wireframe(np.asarray([[0, 0], [0, 0]])+offset, np.asarray([[1, 1], [-1, -1]]),
                      np.asarray([[-1, 1], [-1, 1]]), color="red", linestyle="--", alpha=0.75)
    # Y Rectangle
    ax.plot_wireframe(np.asarray([[1, 1], [-1, -1]]), np.asarray([[0, 0], [0, 0]])+offset,
                      np.asarray([[-1, 1], [-1, 1]]), color="blue", linestyle="--", alpha=0.75)
    # Z Rectangle
    ax.plot_wireframe(np.asarray([[-1, 1], [-1, 1]]), np.asarray([[1, 1], [-1, -1]]),
                      np.asarray([[0, 0], [0, 0]])+offset, color="green", linestyle="--", alpha=0.75)

    ax2 = fig.add_subplot(222)
    ax2.set_facecolor(backcolor)
    ax2.scatter(x, y, color='k', s=normalized_masses, alpha=0.5)
    ax2.scatter(points[:, 0].cpu(), points[:, 1].cpu(),
                marker='.', c=col, s=s, alpha=alpha)
    ax2.set_xlim([-1, 1])
    ax2.set_ylim([-1, 1])
    ax2.set_xticks([])
    ax2.set_yticks([])
    ax2.set_aspect('equal', 'box')

    ax3 = fig.add_subplot(223)
    ax3.set_facecolor(backcolor)
    ax3.scatter(x, z, color='k', s=normalized_masses, alpha=0.5)
    ax3.scatter(points[:, 0].cpu(), points[:, 2].cpu(),
                marker='.', c=col, s=s, alpha=alpha)
    ax3.set_xlim([-1, 1])
    ax3.set_ylim([-1, 1])
    ax3.set_xticks([])
    ax3.set_yticks([])
    ax3.set_aspect('equal', 'box')

    ax4 = fig.add_subplot(224)
    ax4.set_facecolor(backcolor)
    ax4.scatter(y, z, color='k', s=normalized_masses, alpha=0.5)
    ax4.scatter(points[:, 1].cpu(), points[:, 2].cpu(),
                marker='.', c=col, s=s, alpha=alpha)
    ax4.set_xlim([-1, 1])
    ax4.set_ylim([-1, 1])
    ax4.set_xticks([])
    ax4.set_yticks([])
    ax4.set_aspect('equal', 'box')

    if save_path is not None:
        plt.savefig(save_path, dpi=150)


def plot_model_vs_mascon_contours(model, encoding, mascon_points, mascon_masses=None, N=2500, crop_p=1e-2, s=100, save_path=None, c=1., backcolor=[0.15, 0.15, 0.15], progressbar=False, offset=0.0, heatmap=False, mascon_alpha=0.05):
    """Plots both the mascon and model contours in one figure for direct comparison

    Args:
        model (callable (N,M)->1): neural model for the asteroid.
        encoding: the encoding for the neural inputs.
        mascon_points (2-D array-like): an (N, 3) array-like object containing the coordinates of the mascon points.
        mascon_masses (1-D array-like): a (N,) array-like object containing the values for the mascon masses.
        N (int): number of points to be considered.
        views_2d (bool): activates also the 2d projections.
        crop_p (float): all points below this density are rejected.
        s (int): size of the non rejected points visualization.
        save_path (str, optional): Pass to store plot, if none will display. Defaults to None.
        c (float, optional): Normalization constant. Defaults to 1.
        backcolor (list, optional): Plot background color. Defaults to [0.15, 0.15, 0.15].
        progressbar (bool, optional): activates a progressbar. Defaults to False.
        offset (float): an offset to apply to the plane in the direction of the section normal
        heatmap (bool): determines if contour lines or heatmap are displayed
        mascon_alpha (float): alpha of the overlaid mascon model. Defaults to 0.05.
    """

    # Mascon masses
    x = mascon_points[:, 0].cpu()
    y = mascon_points[:, 1].cpu()
    z = mascon_points[:, 2].cpu()

    s = 22000 / len(mascon_points)

    if mascon_masses is None:
        normalized_masses = torch.tensor(
            [1./len(mascon_points)] * len(mascon_points))
    else:
        normalized_masses = mascon_masses / sum(mascon_masses)
    normalized_masses = (normalized_masses * s * len(x)).cpu()

    torch.manual_seed(42)  # Seed torch to always get the same points
    points = []
    rho = []
    batch_size = 4096
    found = 0
    if progressbar:
        pbar = tqdm(desc="Sampling points...", total=N)
    while found < N:
        candidates = torch.rand(batch_size, 3) * 2 - 1
        nn_inputs = encoding(candidates)
        rho_candidates = model(nn_inputs).detach() * c
        mask = rho_candidates > (torch.rand(batch_size, 1) + crop_p)
        rho_candidates = rho_candidates[mask]
        candidates = [[it[0].item(), it[1].item(), it[2].item()]
                      for it, m in zip(candidates, mask) if m]
        if len(candidates) == 0:
            print("All points rejected! Plot is empty, try cropping less?")
            return
        points.append(torch.tensor(candidates))
        rho.append(rho_candidates)
        found += len(rho_candidates)
        if progressbar:
            pbar.update(len(rho_candidates))
    if progressbar:
        pbar.close()
    points = torch.cat(points, dim=0)[:N]  # concat and discard after N
    rho = torch.cat(rho, dim=0)[:N]  # concat and discard after N

    levels = np.linspace(0., 1., 10)
    levels = np.asarray(levels) * \
        np.max(rho.cpu().detach().numpy())  # normalize scale

    fig = plt.figure(figsize=(6, 5), dpi=150, facecolor='white')
    ax = fig.add_subplot(221, projection='3d')
    # ax.set_facecolor(backcolor)
    rejection_col = 'yellow'
    mascon_color = "green"

    # And we plot it
    ax.scatter(x, y, z, color='k', s=normalized_masses, alpha=0.01)
    ax.scatter(points[:, 0].cpu(), points[:, 1].cpu(), points[:, 2].cpu(),
               marker='.', c=rejection_col, s=s, alpha=0.05)
    ax.set_xlim([-1, 1])
    ax.set_ylim([-1, 1])
    ax.set_zlim([-1, 1])
    ax.view_init(elev=45., azim=45.)
    ax.tick_params(labelsize=7)
    ax.set_xlabel("X", fontsize=9)
    ax.set_ylabel("Y", fontsize=9)
    ax.set_zlabel("Z", fontsize=9)

    # X Rectangle
    ax.plot_wireframe(np.asarray([[0, 0], [0, 0]])+offset, np.asarray([[1, 1], [-1, -1]]),
                      np.asarray([[-1, 1], [-1, 1]]), color="red", linestyle="--", alpha=0.75)
    # Y Rectangle
    ax.plot_wireframe(np.asarray([[1, 1], [-1, -1]]), np.asarray([[0, 0], [0, 0]])+offset,
                      np.asarray([[-1, 1], [-1, 1]]), color="blue", linestyle="--", alpha=0.75)
    # Z Rectangle
    ax.plot_wireframe(np.asarray([[-1, 1], [-1, 1]]), np.asarray([[1, 1], [-1, -1]]),
                      np.asarray([[0, 0], [0, 0]])+offset, color="green", linestyle="--", alpha=0.75)
    ax.set_title("3D View", fontsize=7)

    mascon_slice_thickness = 0.05

    ax2 = fig.add_subplot(222)
    # ax2.set_facecolor(backcolor)
    mask = torch.logical_and(z - offset < mascon_slice_thickness,
                             z - offset > -mascon_slice_thickness)
    _ = plot_model_contours(model, encoding, section=np.array(
        [0, 0, 1]), axes=ax2, levels=levels, c=c, offset=offset, heatmap=heatmap)
    ax2.scatter(x[mask], y[mask], color=mascon_color,
                s=normalized_masses[mask], alpha=mascon_alpha)

    ax2.set_xlim([-1, 1])
    ax2.set_ylim([-1, 1])
    ax2.tick_params(labelsize=7, color="green")
    ax2.set_xlabel("X", fontsize=9)
    ax2.set_ylabel("Y", fontsize=9)
    ax2.spines['bottom'].set_color('green')
    ax2.spines['top'].set_color('green')
    ax2.spines['right'].set_color('green')
    ax2.spines['left'].set_color('green')
    ax2.set_title("X-Y cross section (green slice)", fontsize=7)
    ax2.set_aspect('equal', 'box')

    ax3 = fig.add_subplot(223)
    # ax3.set_facecolor(backcolor)
    mask = torch.logical_and(y - offset < mascon_slice_thickness,
                             y - offset > -mascon_slice_thickness)
    _ = plot_model_contours(model, encoding, section=np.array(
        [0, 1, 0]), axes=ax3, levels=levels, c=c, offset=offset, heatmap=heatmap)
    ax3.scatter(x[mask], z[mask], color=mascon_color,
                s=normalized_masses[mask], alpha=mascon_alpha)

    ax3.set_xlim([-1, 1])
    ax3.set_ylim([-1, 1])
    ax3.set_xlabel("X", fontsize=9)
    ax3.set_ylabel("Z", fontsize=9)
    ax3.set_title("X-Z cross section (blue slice)", fontsize=7)
    ax3.tick_params(labelsize=7, color="blue")
    ax3.spines['bottom'].set_color('blue')
    ax3.spines['top'].set_color('blue')
    ax3.spines['right'].set_color('blue')
    ax3.spines['left'].set_color('blue')
    ax3.set_aspect('equal', 'box')

    ax4 = fig.add_subplot(224)
    # ax4.set_facecolor(backcolor)
    mask = torch.logical_and(x - offset < mascon_slice_thickness,
                             x - offset > -mascon_slice_thickness)
    _ = plot_model_contours(model, encoding, section=np.array(
        [1, 0, 0]), axes=ax4, levels=levels, c=c, offset=offset, heatmap=heatmap)
    ax4.scatter(z[mask], y[mask], color=mascon_color,
                s=normalized_masses[mask], alpha=mascon_alpha)
    ax4.set_xlim([-1, 1])
    ax4.set_ylim([-1, 1])
    ax4.set_xlabel("Y", fontsize=9)
    ax4.set_ylabel("Z", fontsize=9)
    ax4.set_title("Y-Z cross section (red slice)", fontsize=7)
    ax4.tick_params(labelsize=7, color="red")
    ax4.spines['bottom'].set_color('red')
    ax4.spines['top'].set_color('red')
    ax4.spines['right'].set_color('red')
    ax4.spines['left'].set_color('red')
    ax4.set_aspect('equal', 'box')

    plt.tight_layout()

    if save_path is not None:
        plt.savefig(save_path, dpi=150)

    return ax


def plot_model_mascon_acceleration(sample, model, encoding, mascon_points, mascon_masses, plane="XY", altitude=0.1, save_path=None, c=1., N=5000, logscale=False):
    """Plots the relative error of the computed acceleration between mascon model and neural network

    Args:
        sample (str): Path to sample mesh
        model (callable (N,M)->1): neural model for the asteroid.
        encoding: the encoding for the neural inputs.
        mascon_points (2-D array-like): an (N, 3) array-like object containing the coordinates of the mascon points.
        mascon_masses (1-D array-like): a (N,) array-like object containing the values for the mascon masses.
        plane (str, optional): Either "XY","XZ" or "YZ". Defines  cross section. Defaults to "XY".
        altitude (float, optional): Altitude to compute error at. Defaults to 0.1.
        save_path (str, optional): Pass to store plot, if none will display. Defaults to None.
        c (float, optional): Normalization constant. Defaults to 1.
        N (int, optional): Number of points to sample. Defaults to 5000.
        logscale (bool, optional): Logscale errors. Defaults to False.

    Raises:
        ValueError: On wrong input

    Returns:
        plt.Figure: created plot
    """
    print("Sampling points at altitude")
    points = get_target_point_sampler(N, method="altitude", bounds=[
                                      altitude], limit_shape_to_asteroid=sample, replace=False)()

    print("Got ", len(points), " points.")
    if plane == "XY":
        cut_dim = 2
        cut_dim_name = "z"
        x_dim = 0
        y_dim = 1
    elif plane == "XZ":
        cut_dim = 1
        cut_dim_name = "y"
        x_dim = 0
        y_dim = 2
    elif plane == "YZ":
        cut_dim = 0
        cut_dim_name = "x"
        x_dim = 1
        y_dim = 2
    else:
        raise ValueError("Plane has to be either XY, XZ or YZ")

    # Left and Right refer to values < 0 and > 0 in the non-crosssection dimension

    print("Splitting in left / right hemisphere")
    points_left = points[points[:, cut_dim] < 0]
    points_right = points[points[:, cut_dim] > 0]

    print("Left: ", len(points_left), " points.")
    print("Right: ", len(points_right), " points.")

    model_values_left = torch.zeros([len(points_left), 3])
    model_values_right = torch.zeros([len(points_right), 3])

    label_values_left = torch.zeros([len(points_left), 3])
    label_values_right = torch.zeros([len(points_right), 3])

    model_values_left, label_values_left, relative_error_left = [], [], []
    model_values_right, label_values_right, relative_error_right = [], [], []

    # Compute accelerations in left points, then right points
    # for both network and mascon model
    batch_size = 100
    for idx in range((len(points_left) // batch_size)+1):
        indices = list(range(idx*batch_size,
                             np.minimum((idx+1)*batch_size, len(points_left))))

        label_values_left.append(
            ACC_L(points_left[indices], mascon_points, mascon_masses).detach())
        model_values_left.append(
            (ACC_ld(points_left[indices], model, encoding, N=200000)*c).detach())

        torch.cuda.empty_cache()

    for idx in range((len(points_right) // batch_size)+1):
        indices = list(range(idx*batch_size,
                             np.minimum((idx+1)*batch_size, len(points_right))))

        label_values_right.append(
            ACC_L(points_right[indices], mascon_points, mascon_masses).detach())
        model_values_right.append(
            (ACC_ld(points_right[indices], model, encoding, N=200000)*c).detach())

        torch.cuda.empty_cache()

    # Accumulate all results
    label_values_left = torch.cat(label_values_left)
    model_values_left = torch.cat(model_values_left)
    label_values_right = torch.cat(label_values_right)
    model_values_right = torch.cat(model_values_right)

    # Compute relative errors for each hemisphere (left, right)
    relative_error_left = (torch.sum(torch.abs(model_values_left - label_values_left), dim=1) /
                           torch.sum(torch.abs(label_values_left+1e-8), dim=1)).cpu().numpy()
    relative_error_right = (torch.sum(torch.abs(model_values_right - label_values_right), dim=1) /
                            torch.sum(torch.abs(label_values_right+1e-8), dim=1)).cpu().numpy()

    if logscale:
        relative_error_left = np.log(relative_error_left)
        relative_error_right = np.log(relative_error_right)

    # Get X,Y coordinates of analyzed points
    X_left = points_left[:, x_dim].cpu().numpy()
    Y_left = points_left[:, y_dim].cpu().numpy()

    X_right = points_right[:, x_dim].cpu().numpy()
    Y_right = points_right[:, y_dim].cpu().numpy()

    # Plot left side stuff
    fig = plt.figure(figsize=(10, 4), dpi=100, facecolor='white')
    fig.suptitle("Relative acceleration error in " +
                 plane + " cross section", fontsize=12)
    ax = fig.add_subplot(121, facecolor="black")

    p = ax.scatter(X_left, Y_left, c=relative_error_left,
                   cmap="plasma", alpha=1.0, s=int(N * 0.0005+0.5))

    cb = plt.colorbar(p, ax=ax)
    cb.ax.tick_params(labelsize=7)
    if logscale:
        cb.set_label('Log(Relative Error)', rotation=270, labelpad=15)
    else:
        cb.set_label('Relative Error', rotation=270, labelpad=15)
    ax.set_xlim([-1, 1])
    ax.set_ylim([-1, 1])
    ax.set_xlabel(plane[0], fontsize=9)
    ax.set_ylabel(plane[1], fontsize=9)
    ax.set_title(cut_dim_name + " < 0")
    ax.tick_params(labelsize=7)
    ax.set_aspect('equal', 'box')
    ax.annotate("Label Acc. Mag=" + str(torch.mean(torch.sum(torch.abs(label_values_left), dim=1)).cpu().numpy()) +
                "\n" + "Model Acc. Mag=" +
                str(torch.mean(
                    torch.sum(torch.abs(model_values_left), dim=1)).cpu().numpy()),
                (-0.95, 0.8), fontsize=8, color="white")

    # Plot right side stuff
    ax = fig.add_subplot(122, facecolor="black")

    p = ax.scatter(X_right, Y_right, c=relative_error_right,
                   cmap="plasma", alpha=1.0, s=int(N * 0.0005+0.5))
    cb = plt.colorbar(p, ax=ax)
    cb.ax.tick_params(labelsize=7)
    if logscale:
        cb.set_label('Log(Relative Error)', rotation=270, labelpad=15)
    else:
        cb.set_label('Relative Error', rotation=270, labelpad=15)
    ax.set_xlim([-1, 1])
    ax.set_ylim([-1, 1])
    ax.set_xlabel(plane[0], fontsize=9)
    ax.set_ylabel(plane[1], fontsize=9)
    ax.set_title(cut_dim_name + " > 0")
    ax.tick_params(labelsize=7)
    ax.set_aspect('equal', 'box')
    ax.annotate("Label Acc. Mag=" + str(torch.mean(torch.sum(torch.abs(label_values_right), dim=1)).cpu().numpy()) +
                "\n" + "Model Acc. Mag=" +
                str(torch.mean(
                    torch.sum(torch.abs(model_values_right), dim=1)).cpu().numpy()),
                (-0.95, 0.8), fontsize=8, color="white")

    plt.tight_layout()

    if save_path is not None:
        plt.savefig(save_path, dpi=150)

    return ax, label_values_right


def plot_model_contours(model, encoding, heatmap=False, section=np.array([0, 0, 1]), N=100, save_path=None, offset=0., axes=None, c=1., levels=[0.001, 0.01, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7]):
    """Takes a mass density model and plots the density contours of its section with
       a 2D plane

    Args:
        model (callable (N,M)->1): neural model for the asteroid.
        encoding: the encoding for the neural inputs.
        section (Numpy array (3)): the section normal (can also be not of unitary magnitude)
        N (int): number of points in each axis of the 2D grid
        save_path (str, optional): Pass to store plot, if none will display. Defaults to None.
        offset (float): an offset to apply to the plane in the direction of the section normal
        axes (matplolib axes): the axes where to plot. Defaults to None, in which case axes are created.
        levels (list optional): the contour levels to be plotted. Defaults to [0.001, 0.01, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7].
    """
    # Builds a 2D grid on the z = 0 plane
    x, y = np.meshgrid(np.linspace(-1, 1, N), np.linspace(-1, 1, N))
    x = np.reshape(x, (-1,))
    y = np.reshape(y, (-1,))
    z = np.zeros(N**2)
    p = np.zeros((N**2, 3))
    p[:, 0] = x
    p[:, 1] = y
    p[:, 2] = z

    # The cross product between the vertical and the desired direction ...
    section = section / np.linalg.norm(section)
    cp = np.cross(np.array([0, 0, 1]), section)
    # safeguard against singularity
    if np.linalg.norm(cp) > 1e-8:
        # ... allows to find the rotation  amount ...
        sint = np.linalg.norm(cp)
        # ... and the axis ...
        axis = cp
        # ... which we transform into a rotation vector (scipy convention)
        rotvec = axis * (np.arcsin(sint))
    else:
        rotvec = np.array([0., 0., 0.])
    # ... used to build the rotation matrix
    Rm = rotation.from_rotvec(rotvec).as_matrix()
    # We rotate the points ...
    newp = [np.dot(Rm.transpose(), p[i, :]) for i in range(N**2)]
    # ... and translate
    newp = newp + section * offset
    # ... and compute them
    inp = encoding(torch.tensor(newp, dtype=torch.float32))
    rho = model(inp) * c
    Z = rho.reshape((N, N)).cpu().detach().numpy()

    X, Y = np.meshgrid(np.linspace(-1, 1, N), np.linspace(-1, 1, N))
    if axes is None:
        fig = plt.figure()
        ax = fig.add_subplot(111)
    else:
        ax = axes

    if heatmap:
        p = ax.contourf(X, Y, Z, cmap="Greys", levels=levels)
        cb = plt.colorbar(p, ax=ax)
    else:
        cmap = mpl.cm.viridis
        p = ax.contour(X, Y, Z, cmap=cmap, levels=levels)
        norm = mpl.colors.BoundaryNorm(levels, cmap.N)
        cb = plt.colorbar(mpl.cm.ScalarMappable(norm=norm, cmap=cmap), ax=ax)
        cb.ax.tick_params(labelsize=7)
    cb.set_label('Density', rotation=270, labelpad=15)

    if save_path is not None:
        plt.savefig(save_path, dpi=150)

    if axes is None:
        return ax
