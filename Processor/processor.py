import os #verifica el path
import pandas as pd #pandas para dataframe
import logger_setup #la configuracion de log, asi como la libreria logging
import matplotlib.pyplot as plt #plt para graficar

#                 ===============Variables Globales=================

#MAPPEO DE VALORES
GRADE_POINTS = {
    'A': 4.0,
    'B': 3.0,
    'C': 2.0,
    'D': 1.0,
    'F': 0.0
}

#ARCHIVOS
STATS_FILE = "KU_academic_stats_by_course.csv"
MASTER_GPA_FILE = "KU_academic_master_gpa.csv"
CHART_ENROLL_TOP10 = "KU_academic_chart_enrollment_top10.png"
CHART_GPA_DISTRIB = "KU_academic_chart_gpa_distribution.png"
CHART_PASSRATE_DEPT = "KU_academic_chart_passrate_by_dept.png"


#               ======================== FUNCIONES ==================================
# MAIN
def main():

    # NUEVO: inicializa el logger (usa logger_setup.init_logger())
    logger_setup.init_logger('processor')

    df_ext = cargar_archivo()  # devuelve (df, extension) o (None, None)
    if df_ext is None:
        print(" Error: archivo no encontrado o formato no soportado.")
        return

    df, extension = df_ext

    # NUEVO: validar y limpiar datos (pase el llamado para arriba)
    df = validar_datos(df)

    if df.empty:
        print("No hay datos válidos después de la validación.")
        logger_setup.log_message("No hay datos válidos después de la validación.", level="error")
        return

    # mapear
    mapear_valores(df)

    # calcular estadísticas por curso (Enrollments = estudiantes únicos por curso)
    stats_df = calcular_stats_por_curso(df)

    # Guarda archivo de estadísticas y log
    stats_df.to_csv(STATS_FILE, index=False)
    logger_setup.log_message(f"Archivo de estadísticas guardado: {STATS_FILE}")

    # NUEVO: calcular master GPA por estudiante y periodo y guardar
    master_gpa_df = calcular_master_gpa(df)
    master_gpa_df.to_csv(MASTER_GPA_FILE, index=False)
    logger_setup.log_message(f"Archivo master GPA guardado: {MASTER_GPA_FILE}")

    # generar las 3 gráficas requeridas y guardarlas !esto aun nose como desarrollarlo bien!
    generar_graficas(df, master_gpa_df, stats_df)

    # # Mostrar tabla de estadisticas en HTML y abrir (la que ya habias hecho)
    # try:
    #     stats_df.to_html('KU_stats_preview.html', index=False)
    #     # os.startfile sólo funciona en Windows; si usas otro SO, quita o reemplaza
    #     os.startfile('KU_stats_preview.html')
    # except Exception:
    #     pass

    # Esto sigue siento el menu para ejecutar solo para probar igual 
    ejecutar_menu(stats_df, master_gpa_df)


#=================OTRAS
#AQUI SE SUBE EL ARCHIVO Y LO VALIDA, ASI COMO RECOGE EL FORMATO=====================================
def cargar_archivo():
    path = input("Pon tu path: ").strip() #se sube el archivo

    #verifica que existe
    if not os.path.exists(path):
        print("El archivo no existe.")
        logger_setup.log_message(f"Archivo no encontrado: {path}", level="error")
        return None

    #recoge la extension del archivo
    extension = path.split(".")[-1].lower()

    #LEE EL ARCHIVO SEGUN SU EXTENSION
    try:
        if extension == "csv": #RETORNA UN DF SEGUN CSV
            df = pd.read_csv(path)
            return df, 'csv'
        elif extension == "json": #RETORNA UN DF SEGUN JSON
            df = pd.read_json(path)
            return df, 'json'
        else: #RETORNA None SI NO ES NINGUNO
            print("Formato no soportado. Solo CSV o JSON.")
            logger_setup.log_message(f"Formato no soportado: {extension}", level="error")
            return None
    except Exception as e: #RETORNA None EN CASO DE ERROR
        print("Error leyendo archivo:", e)
        logger_setup.log_message(f"Error leyendo archivo {path}: {e}", level="error")
        return None


#CREA UNA NUEVA COLUMNA CON LOS VALORES DE LAS NOTAS 
def mapear_valores(df: pd.DataFrame) -> None:
    # ANTES: mapea letras a valores numéricos usando GRADE_POINTS
    # NUEVO: asignamos en copia para evitar SettingWithCopyWarning
    if 'Grade' in df.columns:
        df['Numerical_Grade'] = df['Grade'].map(GRADE_POINTS)
    else:
        # Si no hay Grade, no hacemos nada (evita errores)
        df['Numerical_Grade'] = pd.NA


#CREA LA GRAFICA SEGUN LOS ARCHIVO
def crear_grafica(df: pd.DataFrame, extension: str) -> None:  #TOMA EL DF PARA GENERAR EL GRAFICO

    if extension == 'csv':
        try:
            Ylabel = df['GPA'] #FILAS DE GPA
            xlabel = df['Student_Name'] #COLUMNAS DE ESTUDIANTES

            plt.bar(xlabel, Ylabel) #TOMA GPA Y ESTUDIANTES
            plt.xticks(rotation=45) #GIRA LOS NOMBRECITOS PARA QUE SE VEA BONITO (SE VE POR LA VERGA)
            plt.tight_layout() #LO APRETA😏
            plt.show() #LO MUESTRA

        except Exception as e: #EXCEPTO B;A BLA ME ABURRI DE COMENTAR
            print("Error al crear gráfica:", e)
    elif extension == 'json':
        try:
            #1.Definir los ejes X y Y
            if 'Numerical_Grade' not in df.columns:
                df = df.copy()
                df['Numerical_Grade'] = df['Grade'].map(GRADE_POINTS)

            y_axis = df['Numerical_Grade']
            number_of_students = range(len(df['Student_Name']))

            #2.Crear el tamaño de la ventana y las barras
            plt.figure(figsize=(10,5.3))
            plt.bar(number_of_students, y_axis)

            #3.Configurar los textos a mostrar
            plt.xticks(number_of_students, df['Student_Name'],
                       fontsize=5,
                       rotation=90)
            plt.ylabel("Grade in GPA")
            plt.xlabel("Students (might have to zoom a lil bit😂😂)")

            #4.Ajustar y mostrar
            plt.tight_layout()
            plt.show()

        except Exception as E:
            print("error wey", E)


# aca se crea el validar datos que ya teniamos
# Esta función valida cada fila del dataframe según:
# - Créditos entre 1 y 5
# - Nota dentro del set permitido (GRADE_POINTS)
# - Campus dentro de los reconocidos
# Además registra en el log cada fila descartada y por qué

def validar_datos(df: pd.DataFrame) -> pd.DataFrame:
    """
    Valida filas según el enunciado:
    - Credits entre 1 y 5
    - Grade solo A,B,C,D,F
    - Campus dentro de un conjunto válido
    - Si falla, se loguea y se descarta la fila
    """

    df = df.copy()

    # Valores válidos para los campus

    valid_campus = {"Fort Lauderdale", "Orlando", "Miami", "Tampa", "Online"} #(EDDYYY mira si estas son los validos si porfa)
    # Notas válidas extraídas del diccionario GRADE_POINTS
    valid_grades = set(GRADE_POINTS.keys())

    # Asegurarnos de que las columnas existen; si faltan, loguear y devolver vacío
    required_cols = ['Credits', 'Grade', 'Campus']
    for col in required_cols:
        if col not in df.columns:
            logger_setup.log_message(f"Columna requerida faltante: {col}", level="error")
            return pd.DataFrame()  # vacío
        
     # Mask es una serie booleana que indica qué filas son validas
    # asumiendo que todas las filas son válidas    
    mask = pd.Series(True, index=df.index)
     #  Creamos un diccionario para acumular los errores fila por fila 
    # razones_fila[idx] será un DICCIONARIOS con todos los errores encontrados en esa fila
    razones_fila = {idx: [] for idx in df.index}

    #  Detecta filas donde Credits NO está entre 1 y 5
    malos_credits = ~df['Credits'].between(1, 5)
    # Por cada fila inválida agregamos el motivo a razones_fila
    for idx in df[malos_credits].index:

        razones_fila[idx].append(f"Créditos fuera de rango: {df.at[idx, 'Credits']}")
        #Si la fila tiene mal crédito, ya no es válida
    mask &= ~malos_credits

    # Grade
    # Detecta notas que NO están dentro del set permitido
    malos_grade = ~df['Grade'].isin(valid_grades)
    for idx in df[malos_grade].index:
        razones_fila[idx].append(f"Nota inválida: {df.at[idx, 'Grade']}")
    mask &= ~malos_grade

    # Campus
    malos_campus = ~df['Campus'].isin(valid_campus)
    for idx in df[malos_campus].index:
        razones_fila[idx].append(f"Campus inválido: {df.at[idx, 'Campus']}")
    mask &= ~malos_campus

    # Si una fila no pasó alguna validación, se registra en el log
    for idx, razones in razones_fila.items():
        if not mask.get(idx, False) and razones:
            msg = f"Fila {idx} descartada. Motivos: " + "; ".join(razones)
            logger_setup.log_message(msg, level="warning")

    df_valid = df[mask].copy()
    logger_setup.log_message(f"Filas válidas después de la validación: {len(df_valid)}")
    return df_valid


def exterminate_duplicates(df: pd.DataFrame) -> pd.DataFrame:
    """
    Elimina filas duplicadas basadas en Student_ID + Course_ID + Academic_Term.
    Devuelve df limpio y registra las filas descartadas.
    """
    # Hacemos una copia del dataframe para evitar modificar el original directamente.
    # Esto es buena práctica para no cambiar datos sin querer.
    df = df.copy()
# Antes de buscar duplicados, verificamos que existan las columnas necesarias.
    # Porque si alguna no existe, el programa daría error.
    if not all(col in df.columns for col in ['Student_ID', 'Course_ID', 'Academic_Term']):
        # Si faltan columnas clave, no hacemos nada pero lo logueamos
        logger_setup.log_message("No se encontraron columnas para detectar duplicados (Student_ID/Course_ID/Academic_Term)", level="warning")
        return df
# df.duplicated() marca TRUE en cada fila que ya apareció antes con la misma
    # combinación de columnas dadas.
    #
    # subset=... significa que dos filas se consideran igual si tienen:
    # el mismo Student_ID
    # mismo Course_ID
    # mismo Academic_Term
    #
    # tipo : 
    # Si un estudiante está repetido dos veces en el mismo curso y periodo,
    # la segunda fila será marcada como duplicada.
    df['Duplicado'] = df.duplicated(subset=['Student_ID', 'Course_ID', 'Academic_Term'])
    # Obtenemos los índices de las filas que salieron como duplicadas
    filas = df[df['Duplicado']].index
# Aquí recorremos uno por uno los duplicados detectados
    # y guardamos un mensaje en el log del tipo:
    # "Fila tal sale el numero duplicada eliminada."
    for idx in filas:
        logger_setup.log_message(
            f"Fila {idx} duplicada eliminada.",
            level="warning"
        )
# Quitamos del dataframe todas las filas duplicadas detectadas arriba
    df = df.drop(index=filas)
    # También quitamos la columna auxiliar "Duplicado"
    df = df.drop(columns=['Duplicado'])
    return df


def calcular_stats_por_curso(df: pd.DataFrame) -> pd.DataFrame:
    """
    Genera KU_academic_stats_by_course con:
    - Course_ID, Course_Name, Department
    - Enrollments (número de Student_ID únicos)
    - Average_GPA (promedio de GradePoints)
    - Pass_Rate (% de aprobados: Grade != 'F')
    - Highest_Grade, Lowest_Grade (letra)
    """
    df = df.copy()

    # Mapear Grade a puntos (asumimos Grade validado)
    df['GradePoints'] = df['Grade'].map(GRADE_POINTS)

    # Enrollment como cantidad de student_id únicos por curso
    grouped = df.groupby(['Course_ID', 'Course_Name', 'Department'], as_index=False).agg(
        Enrollments=('Student_ID', 'count'),
        Average_GPA=('GradePoints', 'mean'),
        Pass_Count=('Grade', lambda s: (s != 'F').sum()),
        Highest_GradePoints=('GradePoints', 'max'),
        Lowest_GradePoints=('GradePoints', 'min')
    )

    # Pass rate en porcentaje
    grouped['Pass_Rate'] = ((grouped['Pass_Count'] / grouped['Enrollments']) * 100).round(2)

    # Convertir puntos a letra con mapping inverso
    inv_grade = {v: k for k, v in GRADE_POINTS.items()}

    # Round Average_GPA a 2 decimales
    grouped['Average_GPA'] = grouped['Average_GPA'].round(2)

    grouped['Highest_Grade'] = grouped['Highest_GradePoints'].map(inv_grade)
    grouped['Lowest_Grade'] = grouped['Lowest_GradePoints'].map(inv_grade)

    # Limpiar columnas auxiliares
    grouped = grouped.drop(columns=['Pass_Count', 'Highest_GradePoints', 'Lowest_GradePoints'])

    # Orden consistente: por Department y Course_ID (así te salen agrupadas como la profe probablemente)
    grouped = grouped.sort_values(['Department', 'Course_ID']).reset_index(drop=True)

    return grouped


def calcular_master_gpa(df: pd.DataFrame) -> pd.DataFrame:
    """
    Genera archivo master de GPA por estudiante y término:
    Student_ID, Student_Name, Major, Academic_Term, Total_Credits, Term_GPA
    """
    df = df.copy()
    df['GradePoints'] = df['Grade'].map(GRADE_POINTS)
    df['QualityPoints'] = df['GradePoints'] * df['Credits']

    group_cols = ['Student_ID', 'Student_Name', 'Major', 'Academic_Term']
    g = df.groupby(group_cols, as_index=False).agg(
        Total_Credits=('Credits', 'sum'),
        Sum_QP=('QualityPoints', 'sum')
    )
    g['Term_GPA'] = (g['Sum_QP'] / g['Total_Credits']).round(3)
    g = g.drop(columns=['Sum_QP'])
    g = g.sort_values(by='Term_GPA', ascending=False)
    return g


def generar_graficas(df_valid: pd.DataFrame, master_gpa_df: pd.DataFrame, stats_df: pd.DataFrame) -> None:
    """
    Crea y guarda:
    - CHART_ENROLL_TOP10: Top 10 cursos por enrollment
    - CHART_GPA_DISTRIB: distribución de GPA (categorías)
    - CHART_PASSRATE_DEPT: pass vs failed por departamento (stacked horizontal)
    """
    # 1) Top 10 cursos por matrícula (usamos stats_df ya calculado)
    try:
        top10 = stats_df.sort_values('Enrollments', ascending=False).head(10)
        plt.figure(figsize=(10, 5))
        plt.bar(top10['Course_Name'], top10['Enrollments'])
        plt.xticks(rotation=45, ha="right")
        plt.title("Top 10 courses by enrollment")
        plt.tight_layout()
        plt.savefig(CHART_ENROLL_TOP10)
        plt.close()
        logger_setup.log_message(f"Gráfica guardada: {CHART_ENROLL_TOP10}")
    except Exception as e:
        logger_setup.log_message(f"Error generando CHART_ENROLL_TOP10: {e}", level="error")

    # 2) Distribución de GPA (≈4.0, 3.0–3.49, <3.0) usando master_gpa_df
    try:
        gpa = master_gpa_df['Term_GPA']
        cat_4 = (gpa >= 3.5).sum()
        cat_3 = ((gpa >= 3.0) & (gpa < 3.5)).sum()
        cat_low = (gpa < 3.0).sum()

        labels = ['≈4.0', '3.0–3.49', '<3.0']
        sizes = [cat_4, cat_3, cat_low]

        plt.figure()
        plt.pie(sizes, labels=labels, autopct='%1.1f%%')
        plt.title("GPA distribution")
        plt.tight_layout()
        plt.savefig(CHART_GPA_DISTRIB)
        plt.close()
        logger_setup.log_message(f"Gráfica guardada: {CHART_GPA_DISTRIB}")
    except Exception as e:
        logger_setup.log_message(f"Error generando CHART_GPA_DISTRIB: {e}", level="error")

    # 3) Tasa de aprobación por departamento (stacked bar horizontal)
    try:
        df_work = df_valid.copy()
        df_work['Aprobado'] = df_work['Grade'] != 'F'
        dept = df_work.groupby('Department')['Aprobado'].agg(['sum', 'count']).reset_index()
        dept['Passed'] = dept['sum']
        dept['Failed'] = dept['count'] - dept['sum']

        plt.figure(figsize=(10, 6))
        y = dept['Department']
        plt.barh(y, dept['Passed'], label='Passed')
        plt.barh(y, dept['Failed'], left=dept['Passed'], label='Failed')
        plt.xlabel("Students")
        plt.title("Pass rate by department")
        plt.legend()
        plt.tight_layout()
        plt.savefig(CHART_PASSRATE_DEPT)
        plt.close()
        logger_setup.log_message(f"Gráfica guardada: {CHART_PASSRATE_DEPT}")
    except Exception as e:
        logger_setup.log_message(f"Error generando CHART_PASSRATE_DEPT: {e}", level="error")

# EL DF QUE HICE ARRIBA, SE DESARROLLA ACA
def ejecutar_menu(stats_df: pd.DataFrame, master_gpa_df: pd.DataFrame) -> None:
    """
    Menú de texto simple basado en la propuesta del enunciado.
    """
    while True:
        print("\nUniversity Data Processor")
        print("1) Preview stats by course (head, 20 rows)")
        print("2) Preview GPA by student & term (head, 20 rows)")
        print("3) Preview best GPA by major (top 20)")
        print("4) Preview best GPA by period (top 20)")
        print("5) List all chart files")
        print("6) View log (last 50 lines)")
        print("7) Exit")

        opcion = input("Elige una opción: ").strip()

        if opcion == "1":
            print(stats_df.head(20).to_string(index=False))

        elif opcion == "2":
            print(master_gpa_df.head(20).to_string(index=False))

        elif opcion == "3":
            df_sorted = master_gpa_df.sort_values('Term_GPA', ascending=False)
            top_by_major = df_sorted.groupby('Major').head(20)
            print(top_by_major.to_string(index=False))

        elif opcion == "4":
            df_sorted = master_gpa_df.sort_values(['Academic_Term', 'Term_GPA'], ascending=[True, False])
            print(df_sorted.head(20).to_string(index=False))

        elif opcion == "5":
            print("Charts generados:")
            print(f"- {CHART_ENROLL_TOP10}")
            print(f"- {CHART_GPA_DISTRIB}")
            print(f"- {CHART_PASSRATE_DEPT}")

        elif opcion == "6":
            try:
                with open(logger_setup.LOG_FILE, "r", encoding="utf-8") as f:
                    lines = f.readlines()
                print("Últimas 50 líneas del log:")
                for line in lines[-50:]:
                    print(line.rstrip())
            except FileNotFoundError:
                print("Log file no encontrado.")

        elif opcion == "7":
            print("Saliendo del menú...")
            break
        else:
            print("Opción inválida.")


# llamada final, igual que tu original
if __name__ == "__main__":
    main()





