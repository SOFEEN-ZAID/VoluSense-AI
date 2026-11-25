
import streamlit as st
import numpy as np
import pandas as pd
import cv2
import plotly.express as px
from PIL import Image
from io import BytesIO

from volume_estimator import estimate_volume
from visualization import (
    create_point_cloud,
    create_mesh,
    calculate_dimensions
)
from database import save_measurement, get_measurements

st.set_page_config(
    page_title="VoluSense AI",
    page_icon="📦",
    layout="wide"
)

st.title("📦 VoluSense AI")
st.caption(
    "Intelligent 3D Reconstruction & Volume Estimation"
)

st.sidebar.title("Navigation")

mode = st.sidebar.radio(
    "Select Mode",
    [
        "Home",
        "AI Object Detection",
        "3D Reconstruction",
        "Measurement History",
        "Accuracy Analysis"
    ]
)

if mode == "Home":

    st.header("Welcome to VoluSense AI")

    st.write(
        "An intelligent computer vision platform for "
        "object detection, stereo reconstruction "
        "and volume estimation."
    )

    c1, c2, c3 = st.columns(3)

    c1.metric("Technology", "Stereo Vision")
    c2.metric("AI Model", "YOLO11")
    c3.metric("Visualization", "3D")

    st.subheader("System Workflow")

    st.code(
        "Image Capture → Camera Calibration → "
        "Depth Estimation → 3D Reconstruction → "
        "Volume Estimation"
    )

    st.subheader("3D Demonstration")

    st.info("Simulated sphere, not a real camera measurement.")

    u = np.linspace(0, 2 * np.pi, 100)
    v = np.linspace(0, np.pi, 60)

    x = 3 * np.outer(np.cos(u), np.sin(v))
    y = 3 * np.outer(np.sin(u), np.sin(v))
    z = 3 * np.outer(np.ones_like(u), np.cos(v))

    demo_cloud = np.column_stack([
        x.ravel(),
        y.ravel(),
        z.ravel()
    ])

    st.plotly_chart(
        create_mesh(demo_cloud),
        use_container_width=True
    )

elif mode == "AI Object Detection":

    st.header("AI Object Detection")

    uploaded = st.file_uploader(
        "Upload an object image",
        type=["jpg", "jpeg", "png"]
    )

    if uploaded:

        image = np.array(
            Image.open(uploaded).convert("RGB")
        )

        st.image(image, caption="Original Image")

        if st.button("Detect Object"):

            try:
                from ai_detector import detect_objects

                with st.spinner("Detecting objects..."):

                    bgr = cv2.cvtColor(
                        image, cv2.COLOR_RGB2BGR
                    )

                    annotated, detections = detect_objects(bgr)

                st.image(
                    cv2.cvtColor(
                        annotated, cv2.COLOR_BGR2RGB
                    ),
                    caption="AI Detection Result"
                )

                if detections:
                    st.dataframe(
                        pd.DataFrame(detections),
                        use_container_width=True
                    )
                else:
                    st.warning("No supported object detected.")

            except Exception as e:
                st.error(f"AI detection error: {e}")

elif mode == "3D Reconstruction":

    st.header("Real Stereo Reconstruction")

    st.info(
        "Use images captured with the same calibrated "
        "camera positions and settings."
    )

    calibration_file = st.file_uploader(
        "Upload Calibration File",
        type=["npz"]
    )

    c1, c2 = st.columns(2)

    with c1:
        left_file = st.file_uploader(
            "Left Camera Image",
            type=["jpg", "jpeg", "png"],
            key="left"
        )

    with c2:
        right_file = st.file_uploader(
            "Right Camera Image",
            type=["jpg", "jpeg", "png"],
            key="right"
        )

    name = st.text_input("Object Name", "Apple")

    actual = st.number_input(
        "Actual Measured Volume (cm³)",
        min_value=0.0,
        value=0.0
    )

    if st.button("Generate 3D Model", type="primary"):

        st.session_state.pop("result", None)

        if not all([
            calibration_file,
            left_file,
            right_file
        ]):
            st.error("Please upload all three files.")

        else:

            try:

                with st.spinner("Generating 3D reconstruction..."):

                    left = cv2.cvtColor(
                        np.array(
                            Image.open(left_file).convert("RGB")
                        ),
                        cv2.COLOR_RGB2BGR
                    )

                    right = cv2.cvtColor(
                        np.array(
                            Image.open(right_file).convert("RGB")
                        ),
                        cv2.COLOR_RGB2BGR
                    )

                    with np.load(
                        BytesIO(calibration_file.getvalue()),
                        allow_pickle=False
                    ) as data:

                        calibration = dict(data)

                    result = estimate_volume(
                        left, right, calibration
                    )

                    dimensions = calculate_dimensions(
                        result["cloud"]
                    )

                    st.session_state["result"] = result
                    st.session_state["dimensions"] = dimensions
                    st.session_state["object_name"] = name
                    st.session_state["actual"] = actual
                    st.session_state["saved"] = False

                st.success("Reconstruction completed!")

            except Exception as e:
                st.error(f"Processing error: {e}")

    if "result" in st.session_state:

        result = st.session_state["result"]
        dimensions = st.session_state["dimensions"]
        actual_value = st.session_state["actual"]
        object_name = st.session_state["object_name"]

        estimated = float(result["volume"])

        st.subheader(f"Results: {object_name}")

        m1, m2, m3 = st.columns(3)

        m1.metric(
            "Estimated Volume",
            f"{estimated:.2f} cm³"
        )

        if actual_value > 0:

            error = (
                abs(estimated - actual_value)
                / actual_value * 100
            )

            m2.metric(
                "Actual Volume",
                f"{actual_value:.2f} cm³"
            )

            m3.metric("Error", f"{error:.2f}%")

        else:
            m2.metric("Actual Volume", "Not entered")
            m3.metric("Error", "N/A")

        tab1, tab2, tab3, tab4 = st.tabs([
            "3D Point Cloud",
            "3D Surface Mesh",
            "Depth & Segmentation",
            "Dimensions"
        ])

        with tab1:

            st.plotly_chart(
                create_point_cloud(result["cloud"]),
                use_container_width=True
            )

        with tab2:

            st.plotly_chart(
                create_mesh(result["cloud"]),
                use_container_width=True
            )

            st.caption(
                "Approximate convex hull of visible 3D points, "
                "not a complete object scan."
            )

        with tab3:

            disparity = np.maximum(
                result["disparity"], 0
            )

            normalized = cv2.normalize(
                disparity,
                None,
                0,
                255,
                cv2.NORM_MINMAX
            ).astype(np.uint8)

            heatmap = cv2.applyColorMap(
                normalized,
                cv2.COLORMAP_JET
            )

            a, b = st.columns(2)

            a.image(
                cv2.cvtColor(
                    heatmap, cv2.COLOR_BGR2RGB
                ),
                caption="Disparity Heatmap"
            )

            b.image(
                result["object_mask"],
                caption="Object Segmentation"
            )

        with tab4:

            for label, value in dimensions.items():
                st.metric(label, value)

            st.caption(
                "Dimensions are camera-axis extents "
                "of the reconstructed points."
            )

        if actual_value > 0:

            if st.button(
                "Save Measurement",
                disabled=st.session_state["saved"]
            ):

                save_measurement(
                    object_name,
                    estimated,
                    actual_value
                )

                st.session_state["saved"] = True
                st.success("Measurement saved permanently!")

elif mode == "Measurement History":

    st.header("Measurement History")

    df = get_measurements()

    if df.empty:
        st.info("No measurements saved yet.")

    else:

        st.dataframe(
            df,
            use_container_width=True
        )

        st.download_button(
            "Download CSV Report",
            df.to_csv(index=False),
            file_name="volusense_report.csv",
            mime="text/csv"
        )

elif mode == "Accuracy Analysis":

    st.header("Accuracy Analysis")

    df = get_measurements()

    if df.empty:

        st.warning(
            "Save real measurements before "
            "running accuracy analysis."
        )

    else:

        difference = (
            df["estimated_volume"]
            - df["actual_volume"]
        )

        mae = np.mean(np.abs(difference))
        rmse = np.sqrt(np.mean(difference ** 2))
        mape = df["error"].mean()

        c1, c2, c3 = st.columns(3)

        c1.metric("MAE", f"{mae:.2f} cm³")
        c2.metric("RMSE", f"{rmse:.2f} cm³")
        c3.metric("MAPE", f"{mape:.2f}%")

        fig = px.bar(
            df,
            x="object_name",
            y=[
                "actual_volume",
                "estimated_volume"
            ],
            barmode="group",
            title="Actual vs Estimated Volume"
        )

        st.plotly_chart(
            fig,
            use_container_width=True
        )

        fig2 = px.line(
            df.sort_values("id"),
            x="id",
            y="error",
            markers=True,
            title="Measurement Error Analysis"
        )

        st.plotly_chart(
            fig2,
            use_container_width=True
        )

st.divider()

st.caption(
    "VoluSense AI | Python | OpenCV | YOLO | "
    "Stereo Vision | Streamlit"
)
