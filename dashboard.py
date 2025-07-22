import pandas as pd
from pymongo import MongoClient
import math
import matplotlib.pyplot as plt
from PIL import Image
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
from pymongo import MongoClient
import numpy as np

px.defaults.template = 'plotly_dark'
px.defaults.color_continuous_scale = 'reds'
# Koneksi ke MongoDB
client = MongoClient(st.secrets["MONGO_URI"])
db = client['GaitDB']
collection = db['gait_data']
zoom_level = 0.75

st.markdown(f"""
    <style>
        .main {{
            transform: scale({zoom_level});
            transform-origin: top left;
            width: {100/zoom_level}%;
        }}
    </style>
""", unsafe_allow_html=True)
# Membaca data dari MongoDB
cursor = collection.find()  # Mengambil semua dokumen
data = list(cursor)  # Mengonversi cursor menjadi list
if len(data) == 0:
    st.error("The database does not have gait analysis data. Please add or upload the data first.")
    st.stop() 
elif len(data) == 1:
    st.error("The database only has one gait analysis data. Please add or upload the data first.")
    st.stop()
# Normalisasi data untuk DataFrame
df = pd.json_normalize(data)
# Mengubah nama kolom untuk mempermudah akses
df.columns = df.columns.str.replace('Trial Information.', '')
df.columns = df.columns.str.replace('Subject Parameters.', '')
df.columns = df.columns.str.replace('Body Measurements.', '')
df.columns = df.columns.str.replace('Norm Kinematics.', '')

st.title("Dashboard Gait Analysis")
st.sidebar.title("Filter Data")
# Filter usia
min_age = df['Age'].min()
max_age = df['Age'].max()
age_range = st.sidebar.slider(
    'Filter by Age Range:',
    min_value=min_age,
    max_value=max_age,
    value=(min_age, max_age)  # Nilai default adalah keseluruhan rentang usia
)

# filter BMI
bmi = ["All BMI Classification"] + list(df["BMI Classification"].value_counts().keys().sort_values())
classbmi = st.sidebar.selectbox(label="BMI Classification", options=bmi)

# filter gender
gender_mapping = {
    "L": "Pria",
    "P": "Wanita"
}
df["Gender"] = df["Gender"].map(gender_mapping)
gend = ["All Gender"] + list(df["Gender"].value_counts().keys().sort_values())
gender = st.sidebar.selectbox(label="Gender", options=gend)

filtered_df = df[(df['Age'] >= age_range[0]) & (df['Age'] <= age_range[1])]
if classbmi != "All BMI Classification":
    filtered_df = filtered_df[filtered_df['BMI Classification'] == classbmi]
    if gender != "All Gender":
        filtered_df = filtered_df[filtered_df["Gender"] == gender]

if gender != "All Gender":
    filtered_df = filtered_df[filtered_df["Gender"] == gender]
    
if filtered_df.empty:
    st.error(f"Tidak terdapat data dengan jenis kelamin {gender} yang terklasifikasi {classbmi}")
else:
    st.sidebar.markdown(f"**Total Records:** {len(filtered_df)}")
    # Pelvis
    percentage_cycle = pd.DataFrame(filtered_df['Percentage of Gait Cycle'].tolist())
    l_pelvis_angles = pd.DataFrame(filtered_df['LPelvisAngles_X'].tolist())
    r_pelvis_angles = pd.DataFrame(filtered_df['RPelvisAngles_X'].tolist())

    percentage_cycle.columns = [f"%cycle_{i}" for i in range(percentage_cycle.shape[1])]
    l_pelvis_angles.columns = [f"L_Pelvis_{i}" for i in range(l_pelvis_angles.shape[1])]
    r_pelvis_angles.columns = [f"R_Pelvis_{i}" for i in range(r_pelvis_angles.shape[1])]

    mean_l_pelvis = l_pelvis_angles.mean(axis=0).values
    std_l_pelvis = l_pelvis_angles.std(axis=0)/np.sqrt(l_pelvis_angles.shape[0])
    mean_r_pelvis = r_pelvis_angles.mean(axis=0).values
    std_r_pelvis = r_pelvis_angles.std(axis=0)/np.sqrt(r_pelvis_angles.shape[0])

    std_l_pelvis = std_l_pelvis.values if isinstance(std_l_pelvis, pd.Series) else std_l_pelvis
    std_r_pelvis = std_r_pelvis.values if isinstance(std_r_pelvis, pd.Series) else std_r_pelvis

    pelvis = pd.DataFrame({
        "%cycle": list(range(101)),
        'Mean_Lpelvis': mean_l_pelvis,
        'std_Lpelvis': std_l_pelvis,
        'Mean_Rpelvis': mean_r_pelvis,
        'std_Rpelvis': std_r_pelvis
    })

    ## Create the figure
    fig1 = go.Figure()

    ## Add mean and shading for Left Pelvis
    fig1.add_trace(go.Scatter(
        x=pelvis["%cycle"], 
        y=pelvis["Mean_Lpelvis"], 
        mode='lines',
        name='Left',
        line=dict(color='orange')
    ))
    fig1.add_trace(go.Scatter(
        x=pelvis["%cycle"], 
        y=pelvis["Mean_Lpelvis"] + pelvis["std_Lpelvis"], 
        mode='lines',
        name='Upper Bound (Left)',
        line=dict(color='orange', width=0),
        showlegend=False
    ))
    fig1.add_trace(go.Scatter(
        x=pelvis["%cycle"], 
        y=pelvis["Mean_Lpelvis"] - pelvis["std_Lpelvis"], 
        mode='lines',
        name='Lower Bound (Left)',
        line=dict(color='orange', width=0),
        fill='tonexty',  # Fill between this trace and the previous one
        fillcolor='rgba(255, 165, 0, 0.2)',
        showlegend=False
    ))

    ## Add mean and shading for Right Pelvis
    fig1.add_trace(go.Scatter(
        x=pelvis["%cycle"], 
        y=pelvis["Mean_Rpelvis"], 
        mode='lines',
        name='Right',
        line=dict(color='cyan')
    ))
    fig1.add_trace(go.Scatter(
        x=pelvis["%cycle"], 
        y=pelvis["Mean_Rpelvis"] + pelvis["std_Rpelvis"], 
        mode='lines',
        name='Upper Bound (Right)',
        line=dict(color='cyan', width=0),
        showlegend=False
    ))
    fig1.add_trace(go.Scatter(
        x=pelvis["%cycle"], 
        y=pelvis["Mean_Rpelvis"] - pelvis["std_Rpelvis"], 
        mode='lines',
        name='Lower Bound (Right)',
        line=dict(color='cyan', width=0),
        fill='tonexty',
        fillcolor='rgba(0, 255, 255, 0.2)',
        showlegend=False
    ))

    ## Update layout
    fig1.update_layout(
        title="Pelvis",
        xaxis_title="%Cycle",
        yaxis_title="Value",
        template="plotly",
        title_x=0.5,
        hovermode="x"
    )

    # Knee
    percentage_cycle = pd.DataFrame(filtered_df['Percentage of Gait Cycle'].tolist())
    l_knee_angles = pd.DataFrame(filtered_df['LKneeAngles_X'].tolist())
    r_knee_angles = pd.DataFrame(filtered_df['RKneeAngles_X'].tolist())

    percentage_cycle.columns = [f"%cycle_{i}" for i in range(percentage_cycle.shape[1])]
    l_knee_angles.columns = [f"L_Knee_{i}" for i in range(l_knee_angles.shape[1])]
    r_knee_angles.columns = [f"R_Knee_{i}" for i in range(r_knee_angles.shape[1])]

    mean_l_knee = l_knee_angles.mean(axis=0).values
    std_l_knee = l_knee_angles.std(axis=0) / np.sqrt(l_knee_angles.shape[0])
    mean_r_knee = r_knee_angles.mean(axis=0).values
    std_r_knee = r_knee_angles.std(axis=0) / np.sqrt(r_knee_angles.shape[0])

    std_l_knee = std_l_knee.values if isinstance(std_l_knee, pd.Series) else std_l_knee
    std_r_knee = std_r_knee.values if isinstance(std_r_knee, pd.Series) else std_r_knee

    knee = pd.DataFrame({
        "%cycle": list(range(101)),
        'Mean_Lknee': mean_l_knee,
        'std_Lknee': std_l_knee,
        'Mean_Rknee': mean_r_knee,
        'std_Rknee': std_r_knee
    })

    fig2 = go.Figure()

    fig2.add_trace(go.Scatter(
        x=knee["%cycle"], 
        y=knee["Mean_Lknee"], 
        mode='lines',
        name='Left',
        line=dict(color='orange')
    ))
    fig2.add_trace(go.Scatter(
        x=knee["%cycle"], 
        y=knee["Mean_Lknee"] + knee["std_Lknee"], 
        mode='lines',
        name='Upper Bound (Left)',
        line=dict(color='orange', width=0),
        showlegend=False
    ))
    fig2.add_trace(go.Scatter(
        x=knee["%cycle"], 
        y=knee["Mean_Lknee"] - knee["std_Lknee"], 
        mode='lines',
        name='Lower Bound (Left)',
        line=dict(color='orange', width=0),
        fill='tonexty',
        fillcolor='rgba(255, 165, 0, 0.2)',
        showlegend=False
    ))

    fig2.add_trace(go.Scatter(
        x=knee["%cycle"], 
        y=knee["Mean_Rknee"], 
        mode='lines',
        name='Right',
        line=dict(color='cyan')
    ))
    fig2.add_trace(go.Scatter(
        x=knee["%cycle"], 
        y=knee["Mean_Rknee"] + knee["std_Rknee"], 
        mode='lines',
        name='Upper Bound (Right)',
        line=dict(color='cyan', width=0),
        showlegend=False
    ))
    fig2.add_trace(go.Scatter(
        x=knee["%cycle"], 
        y=knee["Mean_Rknee"] - knee["std_Rknee"], 
        mode='lines',
        name='Lower Bound (Right)',
        line=dict(color='cyan', width=0),
        fill='tonexty',
        fillcolor='rgba(0, 255, 255, 0.2)',
        showlegend=False
    ))

    fig2.update_layout(
        title="Knee",
        xaxis_title="%Cycle",
        yaxis_title="Value",
        template="plotly_dark",
        title_x=0.5,
        hovermode="x"
    )


    # Hip
    # Ganti semua variabel pelvis menjadi hip
    l_hip_angles = pd.DataFrame(filtered_df['LHipAngles_X'].tolist())
    r_hip_angles = pd.DataFrame(filtered_df['RHipAngles_X'].tolist())

    l_hip_angles.columns = [f"L_Hip_{i}" for i in range(l_hip_angles.shape[1])]
    r_hip_angles.columns = [f"R_Hip_{i}" for i in range(r_hip_angles.shape[1])]

    mean_l_hip = l_hip_angles.mean(axis=0).values
    std_l_hip = l_hip_angles.std(axis=0) / np.sqrt(l_hip_angles.shape[0])
    mean_r_hip = r_hip_angles.mean(axis=0).values
    std_r_hip = r_hip_angles.std(axis=0) / np.sqrt(r_hip_angles.shape[0])

    std_l_hip = std_l_hip.values if isinstance(std_l_hip, pd.Series) else std_l_hip
    std_r_hip = std_r_hip.values if isinstance(std_r_hip, pd.Series) else std_r_hip

    hip = pd.DataFrame({
        "%cycle": list(range(101)),
        'Mean_Lhip': mean_l_hip,
        'std_Lhip': std_l_hip,
        'Mean_Rhip': mean_r_hip,
        'std_Rhip': std_r_hip
    })

    fig3 = go.Figure()

    fig3.add_trace(go.Scatter(
        x=hip["%cycle"], 
        y=hip["Mean_Lhip"], 
        mode='lines',
        name='Left',
        line=dict(color='orange')
    ))
    fig3.add_trace(go.Scatter(
        x=hip["%cycle"], 
        y=hip["Mean_Lhip"] + hip["std_Lhip"], 
        mode='lines',
        name='Upper Bound (Left)',
        line=dict(color='orange', width=0),
        showlegend=False
    ))
    fig3.add_trace(go.Scatter(
        x=hip["%cycle"], 
        y=hip["Mean_Lhip"] - hip["std_Lhip"], 
        mode='lines',
        name='Lower Bound (Left)',
        line=dict(color='orange', width=0),
        fill='tonexty',
        fillcolor='rgba(255, 165, 0, 0.2)',
        showlegend=False
    ))

    fig3.add_trace(go.Scatter(
        x=hip["%cycle"], 
        y=hip["Mean_Rhip"], 
        mode='lines',
        name='Right',
        line=dict(color='cyan')
    ))
    fig3.add_trace(go.Scatter(
        x=hip["%cycle"], 
        y=hip["Mean_Rhip"] + hip["std_Rhip"], 
        mode='lines',
        name='Upper Bound (Right)',
        line=dict(color='cyan', width=0),
        showlegend=False
    ))
    fig3.add_trace(go.Scatter(
        x=hip["%cycle"], 
        y=hip["Mean_Rhip"] - hip["std_Rhip"], 
        mode='lines',
        name='Lower Bound (Right)',
        line=dict(color='cyan', width=0),
        fill='tonexty',
        fillcolor='rgba(0, 255, 255, 0.2)',
        showlegend=False
    ))

    fig3.update_layout(
        title="Hip",
        xaxis_title="%Cycle",
        yaxis_title="Value",
        template="plotly_dark",
        title_x=0.5,
        hovermode="x"
    )

    # Ankle
    # Ganti semua variabel pelvis menjadi ankle
    l_ankle_angles = pd.DataFrame(filtered_df['LAnkleAngles_X'].tolist())
    r_ankle_angles = pd.DataFrame(filtered_df['RAnkleAngles_X'].tolist())

    l_ankle_angles.columns = [f"L_Ankle_{i}" for i in range(l_ankle_angles.shape[1])]
    r_ankle_angles.columns = [f"R_Ankle_{i}" for i in range(r_ankle_angles.shape[1])]

    mean_l_ankle = l_ankle_angles.mean(axis=0).values
    std_l_ankle = l_ankle_angles.std(axis=0) / np.sqrt(l_ankle_angles.shape[0])
    mean_r_ankle = r_ankle_angles.mean(axis=0).values
    std_r_ankle = r_ankle_angles.std(axis=0) / np.sqrt(r_ankle_angles.shape[0])

    std_l_ankle = std_l_ankle.values if isinstance(std_l_ankle, pd.Series) else std_l_ankle
    std_r_ankle = std_r_ankle.values if isinstance(std_r_ankle, pd.Series) else std_r_ankle

    ankle = pd.DataFrame({
        "%cycle": list(range(101)),
        'Mean_Lankle': mean_l_ankle,
        'std_Lankle': std_l_ankle,
        'Mean_Rankle': mean_r_ankle,
        'std_Rankle': std_r_ankle
    })

    fig4 = go.Figure()

    fig4.add_trace(go.Scatter(
        x=ankle["%cycle"], 
        y=ankle["Mean_Lankle"], 
        mode='lines',
        name='Left',
        line=dict(color='orange')
    ))
    fig4.add_trace(go.Scatter(
        x=ankle["%cycle"], 
        y=ankle["Mean_Lankle"] + ankle["std_Lankle"], 
        mode='lines',
        name='Upper Bound (Left)',
        line=dict(color='orange', width=0),
        showlegend=False
    ))
    fig4.add_trace(go.Scatter(
        x=ankle["%cycle"], 
        y=ankle["Mean_Lankle"] - ankle["std_Lankle"], 
        mode='lines',
        name='Lower Bound (Left)',
        line=dict(color='orange', width=0),
        fill='tonexty',
        fillcolor='rgba(255, 165, 0, 0.2)',
        showlegend=False
    ))

    fig4.add_trace(go.Scatter(
        x=ankle["%cycle"], 
        y=ankle["Mean_Rankle"], 
        mode='lines',
        name='Right',
        line=dict(color='cyan')
    ))
    fig4.add_trace(go.Scatter(
        x=ankle["%cycle"], 
        y=ankle["Mean_Rankle"] + ankle["std_Rankle"], 
        mode='lines',
        name='Upper Bound (Right)',
        line=dict(color='cyan', width=0),
        showlegend=False
    ))
    fig4.add_trace(go.Scatter(
        x=ankle["%cycle"], 
        y=ankle["Mean_Rankle"] - ankle["std_Rankle"], 
        mode='lines',
        name='Lower Bound (Right)',
        line=dict(color='cyan', width=0),
        fill='tonexty',
        fillcolor='rgba(0, 255, 255, 0.2)',
        showlegend=False
    ))

    fig4.update_layout(
        title="Ankle",
        xaxis_title="%Cycle",
        yaxis_title="Value",
        template="plotly_dark",
        title_x=0.5,
        hovermode="x"
    )
    tab1, tab2, tab3, tab4 = st.tabs(["PELVIS", "KNEE","HIP","ANKLE"])
    data = np.random.randn(10, 1)

    tab1.subheader("PELVIS")
    tab1.write('Pelvis(dalam bahasa Indonesia: panggul) adalah struktur tulang yang berbentuk cekungan di bawah perut, di antara tulang pinggul, dan di atas paha.')
    tab1.plotly_chart(fig1)

    tab2.subheader("KNEE")
    tab2.write('Knee (dalam bahasa Indonesia: lutut) adalah bagian tubuh manusia yang terletak di antara paha dan betis, berfungsi sebagai sendi yang menghubungkan tulang femur (paha) dengan tulang tibia (betis).')
    tab2.plotly_chart(fig2)

    tab3.subheader("HIP")
    tab3.write('Hip (dalam bahasa Indonesia: pinggul) adalah bagian tubuh yang terletak di bawah perut, menghubungkan tubuh bagian atas dengan kaki.')
    tab3.plotly_chart(fig3)

    tab4.subheader("ANKLE")
    tab4.write('Ankle (dalam bahasa Indonesia: pergelangan kaki) adalah sendi yang terletak di antara kaki bagian bawah (tulang tibia dan fibula) dan bagian atas kaki (tulang talus).')
    tab4.plotly_chart(fig4)
