
import numpy as np
import plotly.graph_objects as go
from scipy.spatial import ConvexHull


def clean_points(points):

    points = np.asarray(points).reshape(-1, 3)

    points = points[
        np.isfinite(points).all(axis=1)
    ]

    if len(points) < 4:
        raise ValueError("Not enough valid 3D points.")

    return points


def create_point_cloud(points):

    points = clean_points(points)

    if len(points) > 20000:
        rng = np.random.default_rng(42)

        indices = rng.choice(
            len(points), 20000, replace=False
        )

        points = points[indices]

    fig = go.Figure(
        data=[
            go.Scatter3d(
                x=points[:, 0],
                y=points[:, 1],
                z=points[:, 2],
                mode="markers",
                marker=dict(
                    size=2,
                    color=points[:, 2],
                    colorscale="Viridis",
                    opacity=0.85,
                    colorbar=dict(title="Depth")
                )
            )
        ]
    )

    fig.update_layout(
        title="Interactive 3D Point Cloud",
        template="plotly_dark",
        height=600,
        scene=dict(
            xaxis_title="X (cm)",
            yaxis_title="Y (cm)",
            zaxis_title="Z (cm)",
            aspectmode="data"
        )
    )

    return fig


def create_mesh(points):

    points = clean_points(points)

    hull = ConvexHull(points)

    faces = hull.simplices

    fig = go.Figure(
        data=[
            go.Mesh3d(
                x=points[:, 0],
                y=points[:, 1],
                z=points[:, 2],
                i=faces[:, 0],
                j=faces[:, 1],
                k=faces[:, 2],
                color="cyan",
                opacity=0.8
            )
        ]
    )

    fig.update_layout(
        title="3D Convex Hull Surface",
        template="plotly_dark",
        height=600,
        scene=dict(
            aspectmode="data",
            xaxis_title="X (cm)",
            yaxis_title="Y (cm)",
            zaxis_title="Z (cm)"
        )
    )

    return fig


def calculate_dimensions(points):

    points = clean_points(points)

    dimensions = np.ptp(points, axis=0)

    hull = ConvexHull(points)

    return {
        "Width (cm)": round(float(dimensions[0]), 2),
        "Height (cm)": round(float(dimensions[1]), 2),
        "Depth (cm)": round(float(dimensions[2]), 2),
        "Volume (cm3)": round(float(hull.volume), 2),
        "Surface Area (cm2)": round(float(hull.area), 2)
    }
