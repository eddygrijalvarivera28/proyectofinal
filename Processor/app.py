import streamlit as st
import pandas as pd
from processor import *
import logger_setup
import os
from time import sleep
#CONFIGURES THE PAGE HEADER
st.set_page_config(page_title="Keiser University Processor", 
                       layout="wide",
                       page_icon=':poop:'
                       )

# Para simular, solo estos correos estan permitidos
VALID_USERS = {
    "profesor1@keiseruniversity.edu": "12345",
    "admin@keiseruniversity.edu": "keiser2024",
    "eddygrijalva@keiseruniversity.edu":"caca"
}
ALLOWED_DOMAIN = "@keiseruniversity.edu" #ONLY THIS DOMAIN IS ALLOWED

#CHECKS IF THE USER ITS LOGGED AND IF THE EMAIL EXISTS
#IF NOT, THEY ARE DEFINED IN THE SESSION_STATE
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "user_email" not in st.session_state:
    st.session_state.user_email = ""

    
if "logger_running" not in st.session_state:
    logger_setup.init_logger()
    st.session_state.logger_running = True

# Pantalla de sign in
def login_screen():
    #SCREEN BACKGROUND IMAGE WITH CSS
    st.markdown("""
    <style>
    [data-testid="stAppViewContainer"] {
                background-image: url(https://blogger.googleusercontent.com/img/a/AVvXsEivmjUrZtV3G3SVzcklhXkMHb1004mDO0J1y91_ZZZd87LPuNhrG6p_sDOvBFQGY59lCTEoTnCCgUyXoFhPXfImKNXXxuvm1WiDVBHm4-Gb6Bb0U96gtqujxQyjFXlyeGfzuaTU6Rxjgf0iqdUSmAVQf-rWw04LwK6wqBaosWs5X234W-YVsVnIMt6_bOQ=w1214-h451);
                background-size: 60% 60%;
                background-repeat: no-repeat;
                background-color: rgba(16, 21, 35, 0.1);
                background-position: center
                }
    </style>
                """,unsafe_allow_html=True)
    
    #TEXT SHOWED            
    st.title("Keiser University - Academic Portal")
    st.subheader("Professor Login")
    
    #TEXT INPUT TO WRITE MAIL AND PASSWORD
    email = st.text_input("Institutional mail",
                          placeholder='Email',
                          icon=':material/mail:')
    
    password = st.text_input("Password",
                              type="password",
                              placeholder='Password',
                             icon=":material/lock:")
    
    #CHECKS THE INPUT WHEN BUTTON IS PRESSED
    if st.button("Log In"):
        #CHECKS IF THE EMAIL IS NOT THE ALLOWED DOMAIN
        if not email.endswith(ALLOWED_DOMAIN):
            st.error(f"Only emails from {ALLOWED_DOMAIN} are allowed")
            logger_setup.log_message(f"Intento de login con dominio inválido: {email}", level="warning")
            return
        #GRANTS ACCESS WHEN LOG IN INFO IS VALID
        if email in VALID_USERS and VALID_USERS[email] == password:
            st.session_state.logged_in = True
            st.session_state.user_email = email
            st.success(f"Access granted. Welcome back Tony Stark {email}")
            sleep(1)
            logger_setup.log_message(f"{email} LOGGED IN 👀") #TELLS THE LOG WHO LOGGED IN
            st.rerun()
        else: #NOT VALID INPUT
            st.error("Wrong Credentials. Try again.")
            logger_setup.log_message(f"Intento de login fallido: {email}", level="warning")

# ==================== MAIN APP ====================
def main_app():
    
    
    # --- Header with Logo ---
    col1, col2 = st.columns([1,6],gap=None,vertical_alignment="center")
    with col1:
        st.image('https://kuli.b-cdn.net/wp-content/uploads/2023/01/logoredondo.png',
                 use_container_width=True)
    with col2:
        st.markdown("""
            <link href='https://fonts.googleapis.com/css2?family=Lilita+One&display=swap' rel='stylesheet'>
            <h1 style="
                text-align:center; 
                color:#FFFFFF;
                font-family: Lilita One, sans-serif;
                font-weight: 400;
                font-size: 40px;        
            ">
                <i><strong>KEISER UNIVERSITY GRADE PROCESSOR</i></strong>
            </h1>
        """, unsafe_allow_html=True)
    st.markdown("---")

    # Upload del file
    uploaded_file = st.file_uploader("Upload CSV o JSON file", type=["csv","json"])

    if uploaded_file:
        try:
            extension = uploaded_file.name.split(".")[-1].lower() #RECCOGE LA EXTENSION
            if extension == "csv":
                df = pd.read_csv(uploaded_file)
            else:
                df = pd.read_json(uploaded_file)

            st.success(f"Archivo subido correctamente: {uploaded_file.name}")
            
            if 'file_uploaded' not in st.session_state: #EVITA LOGGEAR LO MISMO
                logger_setup.log_message(f"Archivo subido: {uploaded_file.name}")
                st.session_state.file_uploaded = True

            # Validacion de datos
            if 'data_validation' not in st.session_state:
                st.session_state.data_validation = validar_datos(df)
            
            df_valid = st.session_state.data_validation # EVITA LOGGEAR LO MISMO
            
            if df_valid.empty:
                #SI SE SUBE UN ARCHIVO CON FORMATO CORRECTO PERO SIN DATOS ESTUDIANTILES ERROR ERRROR ERRROR EROROR EOROROR
                st.error("No hay filas válidas después de la validación!") 
            else:
                st.success(f"Filas válidas: {len(df_valid)}")
                mapear_valores(df_valid) #MAPEA VALORES LETRAS NUMEROS

                # STATS
                stats_df = calcular_stats_por_curso(df_valid)
                master_gpa_df = calcular_master_gpa(df_valid)

                #MENU 
                st.sidebar.title("☰ Menu")
                section = st.sidebar.radio("Go to:", ["Data Frames", "Charts", "Log"])

                if section == "Data Frames": #SECCION DE DATAFRAMES
                    st.subheader("Estadísticas por Curso")
                    st.dataframe(stats_df)

                    st.subheader("Master GPA por Estudiante")
                    st.dataframe(master_gpa_df)
                elif section == "Charts": #SECCION DE GRAFICAS
                    st.subheader("Gráficas")
                    try:
                        if 'graficas_hechas' not in st.session_state:
                            generar_graficas(df_valid, master_gpa_df, stats_df)
                            st.session_state.graficas_hechas = True
                        st.success("Gráficas generadas exitosamente!")
                        st.image("KU_academic_chart_enrollment_top10.png", caption="Top 10 Enrollment", use_container_width=True)
                        st.image("KU_academic_chart_gpa_distribution.png", caption="GPA Distribution", use_container_width=True)
                        st.image("KU_academic_chart_passrate_by_dept.png", caption="Pass Rate by Department", use_container_width=True)
                    except Exception as e:
                        st.error(f"Error generando gráficas: {e}")
                        st.subheader("Gráficas")

                elif section == "Log": #SECCION DE LOG
                    st.subheader("Últimos mensajes del log")
                    if os.path.exists(logger_setup.LOG_FILE):
                        with open(logger_setup.LOG_FILE, "r", encoding="utf-8") as f:
                            log_lines = f.readlines()[-50:]
                            lines = []
                            for line in log_lines:
                                splitted_line = line.split('-')
                                time, level, message = splitted_line
                                lines.append({
                                    "Time":time,
                                    "Level":level,
                                    "Message":message
                                })
                            else:
                                log = pd.DataFrame(lines)
                                st.dataframe(log,hide_index=True)

        except Exception as e:
            st.error(f"Error leyendo archivo: {e}")

if not st.session_state.logged_in:
        login_screen()
else:
    main_app()  


