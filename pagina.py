import streamlit as st
import psycopg2
import pandas as pd
import time
from datetime import date

st.set_page_config(page_title="Sistema Académico", page_icon="📚", layout="wide")

# ===================== CONEXIÓN A SUPABASE (versión recomendada) =====================
@st.cache_resource
def get_connection():
    return psycopg2.connect(
        host="db.ypoqacbyxmyycwrwfekm.supabase.co",
        port="5432",
        database="postgres",
        user="postgres",
        password="Aaronyalejandra12",   # ← Asegúrate que esta sea la contraseña correcta de Supabase
        sslmode="require"
    )

conn = get_connection()
cursor = conn.cursor()
# ===================== SIDEBAR CON ROLES Y SELECCIÓN DE MAESTRO =====================
st.sidebar.title("Sistema Académico")

# Selector de Rol
if 'rol_actual' not in st.session_state:
    st.session_state.rol_actual = "Admin"

rol = st.sidebar.selectbox(
    "Selecciona tu Rol",
    ["Admin", "Maestro", "Alumno"],
    index=["Admin", "Maestro", "Alumno"].index(st.session_state.rol_actual)
)
st.session_state.rol_actual = rol

# Si es Maestro, seleccionar cuál maestro es
if rol == "Maestro":
    cursor.execute("SELECT id_maestro, nombre, apellido_paterno FROM maestro ORDER BY nombre")
    maestros = cursor.fetchall()
    if maestros:
        maestro_sel = st.sidebar.selectbox(
            "Selecciona tu nombre (Maestro)",
            [f"{m[0]} - {m[1]} {m[2]}" for m in maestros]
        )
        st.session_state.maestro_id = int(maestro_sel.split(" - ")[0])
    else:
        st.sidebar.warning("No hay maestros registrados aún")
        st.session_state.maestro_id = None

st.sidebar.markdown("---")

# Menú según rol
if rol == "Admin":
    opciones = [
        "Dashboard",
        "Alumnos",
        "Maestros",
        "Materias",
        "Grupos e Inscripciones",
        "Unidades",
        "Configurar Actividades",
        "Registrar Calificaciones",
        "Ver Calificaciones y Cálculos",
        "Carga Masiva CSV"
    ]
elif rol == "Maestro":
    opciones = [
        "Dashboard",
        "Configurar Actividades",
        "Registrar Calificaciones",
        "Ver Calificaciones y Cálculos"
    ]
elif rol == "Alumno":
    opciones = [
        "Dashboard",
        "Ver Calificaciones y Cálculos"
    ]

pagina = st.sidebar.radio("Selecciona sección", opciones)
st.sidebar.caption(f"Rol actual: **{rol}**")
# ===================== DASHBOARD =====================
if pagina == "Dashboard":
    st.title("Dashboard")
    st.success("Todo funcionando")

# ===================== ALUMNOS (con mensajes y retraso de 2 segundos) =====================
elif pagina == "Alumnos":
    st.title("Gestión de Alumnos")

    tab1, tab2, tab3 = st.tabs(["Ver todos", "Inscribir Alumno", "Editar / Eliminar"])

    # ===================== VER TODOS =====================
    with tab1:
        st.subheader("Lista de Alumnos")
        cursor.execute("""
            SELECT id_alumno, matricula, nombre, apellido_paterno, apellido_materno, 
                   email, fecha_nacimiento 
            FROM alumno ORDER BY nombre
        """)
        df = pd.DataFrame(cursor.fetchall(), 
                         columns=["ID", "Matrícula", "Nombre", "Ape. Paterno", 
                                  "Ape. Materno", "Email", "Fecha Nacimiento"])
        st.dataframe(df, use_container_width=True, hide_index=True)

    # ===================== INSCRIBIR NUEVO ALUMNO =====================
    with tab2:
        st.subheader("Inscribir Nuevo Alumno")
        with st.form("nuevo_alumno", clear_on_submit=True):
            col1, col2 = st.columns(2)
            with col1:
                nombre = st.text_input("Nombre(s)*")
                apellido_paterno = st.text_input("Apellido Paterno*")
                apellido_materno = st.text_input("Apellido Materno")
            with col2:
                matricula = st.text_input("Matrícula* (máx 8 caracteres)", max_chars=8)
                email = st.text_input("Email*")
                fecha_nacimiento = st.date_input("Fecha de Nacimiento*", value=date(2005, 1, 1))

            if st.form_submit_button("Inscribir Alumno"):
                if not nombre.strip() or not apellido_paterno.strip() or not matricula.strip():
                    st.warning("Faltan datos obligatorios (Nombre, Apellido Paterno o Matrícula)")
                elif len(matricula.strip()) > 8:
                    st.warning("La matrícula no puede tener más de 8 caracteres")
                else:
                    try:
                        cursor.execute("""
                            INSERT INTO alumno 
                            (matricula, nombre, apellido_paterno, apellido_materno, email, fecha_nacimiento)
                            VALUES (%s, %s, %s, %s, %s, %s)
                        """, (matricula.strip(), nombre.strip(), apellido_paterno.strip(),
                              apellido_materno.strip() if apellido_materno else None,
                              email.strip(), fecha_nacimiento))
                        conn.commit()
                        st.success("Alumno inscrito correctamente")
                        time.sleep(2)          # ← 2 segundos de retraso
                        st.rerun()
                    except Exception:
                        conn.rollback()
                        st.rerun()

    # ===================== EDITAR / ELIMINAR =====================
    with tab3:
        st.subheader("Editar o Eliminar Alumno")
        cursor.execute("SELECT id_alumno, matricula, nombre, apellido_paterno FROM alumno ORDER BY nombre")
        alumnos = cursor.fetchall()

        if alumnos:
            seleccion = st.selectbox("Selecciona alumno", 
                                     [f"{a[0]} - {a[1]} - {a[2]} {a[3]}" for a in alumnos])
            id_alumno = int(seleccion.split(" - ")[0])

            cursor.execute("""
                SELECT matricula, nombre, apellido_paterno, apellido_materno, email, fecha_nacimiento 
                FROM alumno WHERE id_alumno = %s
            """, (id_alumno,))
            datos = cursor.fetchone()

            with st.form("editar_alumno"):
                col1, col2 = st.columns(2)
                with col1:
                    nueva_matricula = st.text_input("Matrícula", value=datos[0], max_chars=8)
                    nuevo_nombre = st.text_input("Nombre(s)", value=datos[1])
                    nuevo_ap_p = st.text_input("Apellido Paterno", value=datos[2])
                with col2:
                    nuevo_ap_m = st.text_input("Apellido Materno", value=datos[3] or "")
                    nuevo_email = st.text_input("Email", value=datos[4] or "")
                    nueva_fecha = st.date_input("Fecha de Nacimiento", value=datos[5])

                col1, col2 = st.columns(2)
                with col1:
                    if st.form_submit_button("Guardar cambios"):
                        try:
                            cursor.execute("""
                                UPDATE alumno 
                                SET matricula=%s, nombre=%s, apellido_paterno=%s,
                                    apellido_materno=%s, email=%s, fecha_nacimiento=%s
                                WHERE id_alumno=%s
                            """, (nueva_matricula, nuevo_nombre, nuevo_ap_p, 
                                  nuevo_ap_m if nuevo_ap_m else None, nuevo_email, nueva_fecha, id_alumno))
                            conn.commit()
                            st.success("Datos actualizados correctamente")
                            time.sleep(2)          # ← 2 segundos de retraso
                            st.rerun()
                        except Exception:
                            conn.rollback()
                            st.rerun()

                with col2:
                    if st.form_submit_button("Eliminar Alumno", type="secondary"):
                        if st.checkbox("¿Estás seguro de eliminar este alumno?"):
                            try:
                                cursor.execute("DELETE FROM alumno WHERE id_alumno = %s", (id_alumno,))
                                conn.commit()
                                st.success("Alumno eliminado correctamente")
                                time.sleep(2)          # ← 2 segundos de retraso
                                st.rerun()
                            except Exception:
                                conn.rollback()
                                st.rerun()
# ===================== MAESTROS (con mensajes y retraso de 2 segundos) =====================
elif pagina == "Maestros":
    st.title("Gestión de Maestros")
    tab1, tab2, tab3 = st.tabs(["Ver todos", "Registrar Maestro", "Editar / Eliminar"])

    # Cargar materias desde la base de datos
    cursor.execute("SELECT nombre FROM materia ORDER BY nombre")
    materias_db = [row[0] for row in cursor.fetchall()]

    # ===================== VER TODOS =====================
    with tab1:
        cursor.execute("""
            SELECT id_maestro, nombre, apellido_paterno, apellido_materno, 
                   telefono, email, especialidad 
            FROM maestro 
            ORDER BY nombre
        """)
        df = pd.DataFrame(cursor.fetchall(), 
                         columns=["ID", "Nombre", "Ape. Paterno", "Ape. Materno", 
                                  "Teléfono", "Email", "Especialidad"])
        st.dataframe(df, use_container_width=True, hide_index=True)

    # ===================== REGISTRAR NUEVO MAESTRO =====================
    with tab2:
        st.subheader("Registrar Nuevo Maestro")
        with st.form("nuevo_maestro", clear_on_submit=True):
            col1, col2 = st.columns(2)
            with col1:
                nombre = st.text_input("Nombre(s)")
                apellido_paterno = st.text_input("Apellido Paterno")
                apellido_materno = st.text_input("Apellido Materno")
            with col2:
                telefono = st.text_input("Teléfono (máx. 10 dígitos)", max_chars=10)
                email = st.text_input("Email")
                especialidad = st.multiselect("Materias que imparte", materias_db)

            if st.form_submit_button("Registrar Maestro"):
                if not nombre or not apellido_paterno or not telefono or not email or not especialidad:
                    st.warning("Faltan datos obligatorios")
                else:
                    esp_str = ", ".join(especialidad)
                    try:
                        cursor.execute("""
                            INSERT INTO maestro (nombre, apellido_paterno, apellido_materno, telefono, email, especialidad)
                            VALUES (%s, %s, %s, %s, %s, %s)
                        """, (nombre, apellido_paterno, apellido_materno, telefono, email, esp_str))
                        conn.commit()
                        st.success("Maestro registrado correctamente")
                        time.sleep(2)          # ← 2 segundos de retraso
                        st.rerun()
                    except Exception:
                        conn.rollback()
                        st.rerun()

    # ===================== EDITAR / ELIMINAR =====================
    with tab3:
        st.subheader("Editar o Eliminar Maestro")
        cursor.execute("SELECT id_maestro, nombre, apellido_paterno FROM maestro ORDER BY nombre")
        maestros = cursor.fetchall()
        if maestros:
            seleccion = st.selectbox("Selecciona maestro", [f"{m[0]} - {m[1]} {m[2]}" for m in maestros])
            id_maestro = int(seleccion.split(" - ")[0])

            cursor.execute("""
                SELECT nombre, apellido_paterno, apellido_materno, telefono, email, especialidad 
                FROM maestro WHERE id_maestro = %s
            """, (id_maestro,))
            datos = cursor.fetchone()

            with st.form("editar_maestro"):
                nuevo_nombre = st.text_input("Nombre(s)", value=datos[0])
                nuevo_ap_p = st.text_input("Apellido Paterno", value=datos[1])
                nuevo_ap_m = st.text_input("Apellido Materno", value=datos[2] or "")
                nuevo_tel = st.text_input("Teléfono", value=datos[3] or "")
                nuevo_email = st.text_input("Email", value=datos[4] or "")
                nueva_esp = st.multiselect("Materias", materias_db, 
                                          default=datos[5].split(", ") if datos[5] else [])

                col1, col2 = st.columns(2)
                with col1:
                    if st.form_submit_button("Guardar cambios"):
                        try:
                            cursor.execute("""
                                UPDATE maestro 
                                SET nombre=%s, apellido_paterno=%s, apellido_materno=%s,
                                    telefono=%s, email=%s, especialidad=%s 
                                WHERE id_maestro=%s
                            """, (nuevo_nombre, nuevo_ap_p, nuevo_ap_m, nuevo_tel, nuevo_email, ", ".join(nueva_esp), id_maestro))
                            conn.commit()
                            st.success("Cambios guardados correctamente")
                            time.sleep(2)          # ← 2 segundos de retraso
                            st.rerun()
                        except Exception:
                            conn.rollback()
                            st.rerun()

                with col2:
                    if st.form_submit_button("Eliminar", type="secondary"):
                        if st.checkbox("¿Estás seguro de eliminar este maestro?"):
                            try:
                                cursor.execute("DELETE FROM maestro WHERE id_maestro = %s", (id_maestro,))
                                conn.commit()
                                st.success("Maestro eliminado correctamente")
                                time.sleep(2)          # ← 2 segundos de retraso
                                st.rerun()
                            except Exception:
                                conn.rollback()
                                st.rerun()

# ===================== MATERIAS (con mensajes y retraso de 2 segundos) =====================
elif pagina == "Materias":
    st.title("Gestión de Materias")

    tab1, tab2, tab3 = st.tabs(["Ver todos", "Nueva Materia", "Editar / Eliminar"])

    # ===================== VER TODOS =====================
    with tab1:
        st.subheader("Lista de Materias")
        cursor.execute("""
            SELECT 
                m.id_materia,
                m.codigo,
                m.nombre,
                STRING_AGG(DISTINCT maestro.nombre || ' ' || maestro.apellido_paterno, ', ') AS maestros
            FROM materia m
            LEFT JOIN grupo g ON g.id_materia = m.id_materia
            LEFT JOIN maestro ON maestro.id_maestro = g.id_maestro
            GROUP BY m.id_materia, m.codigo, m.nombre
            ORDER BY m.nombre
        """)
        df = pd.DataFrame(cursor.fetchall(), 
                         columns=["ID", "Código", "Nombre de la Materia", "Maestros que la imparten"])
        st.dataframe(df, use_container_width=True, hide_index=True)

    # ===================== NUEVA MATERIA =====================
    with tab2:
        st.subheader("Nueva Materia")
        with st.form("nueva_materia", clear_on_submit=True):
            codigo = st.text_input("Código de la materia *", max_chars=10)
            nombre = st.text_input("Nombre completo de la materia *")

            if st.form_submit_button("Guardar Materia"):
                if not codigo.strip() or not nombre.strip():
                    st.warning("Código y Nombre son obligatorios")
                else:
                    try:
                        cursor.execute("""
                            INSERT INTO materia (codigo, nombre)
                            VALUES (%s, %s)
                        """, (codigo.strip(), nombre.strip()))
                        conn.commit()
                        st.success("Materia agregada correctamente")
                        time.sleep(2)          # ← 2 segundos de retraso
                        st.rerun()
                    except Exception:
                        conn.rollback()
                        st.rerun()

    # ===================== EDITAR / ELIMINAR =====================
    with tab3:
        st.subheader("Editar o Eliminar Materia")
        cursor.execute("SELECT id_materia, codigo, nombre FROM materia ORDER BY nombre")
        materias = cursor.fetchall()

        if materias:
            seleccion = st.selectbox("Selecciona materia", 
                                     [f"{m[0]} - {m[1]} - {m[2]}" for m in materias])
            id_materia = int(seleccion.split(" - ")[0])

            cursor.execute("SELECT codigo, nombre FROM materia WHERE id_materia = %s", (id_materia,))
            datos = cursor.fetchone()

            with st.form("editar_materia"):
                nuevo_codigo = st.text_input("Código", value=datos[0], max_chars=10)
                nuevo_nombre = st.text_input("Nombre de la materia", value=datos[1])

                col1, col2 = st.columns(2)
                with col1:
                    if st.form_submit_button("Guardar cambios"):
                        try:
                            cursor.execute("""
                                UPDATE materia 
                                SET codigo = %s, nombre = %s
                                WHERE id_materia = %s
                            """, (nuevo_codigo.strip(), nuevo_nombre.strip(), id_materia))
                            conn.commit()
                            st.success("Cambios guardados correctamente")
                            time.sleep(2)          # ← 2 segundos de retraso
                            st.rerun()
                        except Exception:
                            conn.rollback()
                            st.rerun()

                with col2:
                    if st.form_submit_button("Eliminar Materia", type="secondary"):
                        if st.checkbox("¿Estás seguro de eliminar esta materia?"):
                            try:
                                cursor.execute("DELETE FROM materia WHERE id_materia = %s", (id_materia,))
                                conn.commit()
                                st.success("Materia eliminada correctamente")
                                time.sleep(2)          # ← 2 segundos de retraso
                                st.rerun()
                            except Exception:
                                conn.rollback()
                                st.rerun()

# ===================== GRUPOS E INSCRIPCIONES (con retraso de 2 segundos) =====================
elif pagina == "Grupos e Inscripciones":
    st.title("Grupos e Inscripciones")

    tab1, tab2, tab3 = st.tabs(["Ver Grupos", "Crear Nuevo Grupo", "Inscripciones"])

    # ===================== VER GRUPOS =====================
    with tab1:
        st.subheader("Lista de Grupos")
        try:
            cursor.execute("""
                SELECT 
                    g.id_grupo,
                    m.nombre AS materia,
                    COALESCE(maestro.nombre || ' ' || maestro.apellido_paterno, 'Sin maestro') AS maestro,
                    g.nombre_grupo,
                    g.periodo,
                    COUNT(i.id_inscripcion) AS alumnos_inscritos
                FROM grupo g
                JOIN materia m ON g.id_materia = m.id_materia
                LEFT JOIN maestro ON g.id_maestro = maestro.id_maestro
                LEFT JOIN inscripcion i ON i.id_grupo = g.id_grupo
                GROUP BY g.id_grupo, m.nombre, maestro.nombre, maestro.apellido_paterno, g.nombre_grupo, g.periodo
                ORDER BY m.nombre, g.nombre_grupo
            """)
            df = pd.DataFrame(cursor.fetchall(), 
                             columns=["ID", "Materia", "Maestro", "Nombre Grupo", "Periodo", "Alumnos inscritos"])
            st.dataframe(df, use_container_width=True, hide_index=True)
        except Exception:
            st.rerun()

    # ===================== CREAR NUEVO GRUPO =====================
    with tab2:
        st.subheader("Crear Nuevo Grupo")
        with st.form("nuevo_grupo", clear_on_submit=True):
            cursor.execute("SELECT id_materia, nombre FROM materia ORDER BY nombre")
            materias = cursor.fetchall()
            cursor.execute("SELECT id_maestro, nombre, apellido_paterno FROM maestro ORDER BY nombre")
            maestros = cursor.fetchall()

            materia_sel = st.selectbox("Materia", [f"{m[0]} - {m[1]}" for m in materias])
            maestro_sel = st.selectbox("Maestro", [f"{ma[0]} - {ma[1]} {ma[2]}" for ma in maestros] + ["Sin asignar"])
            nombre_grupo = st.text_input("Nombre del Grupo (ej: MAT-A)")
            periodo = st.text_input("Periodo (ej: 2026-1)")

            if st.form_submit_button("Crear Grupo"):
                if not nombre_grupo.strip() or not periodo.strip():
                    st.warning("Faltan datos: Nombre del Grupo y Periodo son obligatorios")
                else:
                    id_materia = int(materia_sel.split(" - ")[0])
                    id_maestro = int(maestro_sel.split(" - ")[0]) if maestro_sel != "Sin asignar" else None
                    try:
                        cursor.execute("""
                            INSERT INTO grupo (id_materia, id_maestro, nombre_grupo, periodo)
                            VALUES (%s, %s, %s, %s)
                        """, (id_materia, id_maestro, nombre_grupo.strip(), periodo.strip()))
                        conn.commit()
                        st.success("Grupo creado correctamente")
                        time.sleep(2)          # ← 2 segundos de retraso
                        st.rerun()
                    except Exception:
                        conn.rollback()
                        st.rerun()

    # ===================== INSCRIPCIONES =====================
    with tab3:
        st.subheader("Inscripciones de Alumnos")

        cursor.execute("SELECT id_grupo, nombre_grupo FROM grupo ORDER BY nombre_grupo")
        grupos = cursor.fetchall()
        grupo_sel = st.selectbox("Selecciona Grupo", [f"{g[0]} - {g[1]}" for g in grupos])
        id_grupo = int(grupo_sel.split(" - ")[0])

        st.write("**Alumnos inscritos en este grupo:**")
        cursor.execute("""
            SELECT a.matricula, a.nombre, a.apellido_paterno, a.apellido_materno
            FROM inscripcion i
            JOIN alumno a ON i.id_alumno = a.id_alumno
            WHERE i.id_grupo = %s
        """, (id_grupo,))
        df_inscritos = pd.DataFrame(cursor.fetchall(), 
                                   columns=["Matrícula", "Nombre", "Ape. Paterno", "Ape. Materno"])
        st.dataframe(df_inscritos, use_container_width=True, hide_index=True)

        st.write("**Inscribir nuevo alumno**")
        with st.form("inscribir_alumno", clear_on_submit=True):
            cursor.execute("SELECT id_alumno, matricula, nombre, apellido_paterno FROM alumno ORDER BY nombre")
            alumnos = cursor.fetchall()
            alumno_sel = st.selectbox("Alumno", [f"{a[0]} - {a[1]} - {a[2]} {a[3]}" for a in alumnos])

            if st.form_submit_button("Inscribir Alumno"):
                id_alumno = int(alumno_sel.split(" - ")[0])
                try:
                    cursor.execute("""
                        INSERT INTO inscripcion (id_alumno, id_grupo)
                        VALUES (%s, %s)
                    """, (id_alumno, id_grupo))
                    conn.commit()
                    st.success("Alumno inscrito correctamente en el grupo")
                    time.sleep(2)          # ← 2 segundos de retraso
                    st.rerun()
                except Exception as e:
                    conn.rollback()
                    if "unique" in str(e).lower() or "duplicate" in str(e).lower():
                        st.warning("Este alumno ya está inscrito en este grupo")
                    else:
                        st.error("Error al inscribir alumno")

                        
# ===================== UNIDADES =====================
elif pagina == "Unidades":
    st.title("Gestión de Unidades")

    tab1, tab2, tab3 = st.tabs(["Ver todas las Unidades", "Crear Nueva Unidad", "Editar / Eliminar Unidad"])

    # ===================== VER TODAS LAS UNIDADES =====================
    with tab1:
        st.subheader("Lista de Unidades")
        cursor.execute("""
            SELECT 
                u.id_unidad,
                g.nombre_grupo AS grupo,
                u.numero,
                u.nombre,
                COUNT(c.id_config_evaluacion) AS actividades_configuradas
            FROM unidad u
            JOIN grupo g ON u.id_grupo = g.id_grupo
            LEFT JOIN config_evaluacion c ON c.id_unidad = u.id_unidad
            GROUP BY u.id_unidad, g.nombre_grupo, u.numero, u.nombre
            ORDER BY g.nombre_grupo, u.numero
        """)
        df = pd.DataFrame(cursor.fetchall(), 
                         columns=["ID", "Grupo", "Número", "Nombre de Unidad", "Actividades configuradas"])
        st.dataframe(df, use_container_width=True, hide_index=True)

    # ===================== CREAR NUEVA UNIDAD =====================
    with tab2:
        st.subheader("Crear Nueva Unidad")
        with st.form("nueva_unidad", clear_on_submit=True):
            # Cargar grupos
            cursor.execute("SELECT id_grupo, nombre_grupo FROM grupo ORDER BY nombre_grupo")
            grupos = cursor.fetchall()
            grupo_sel = st.selectbox("Grupo al que pertenece la unidad", [f"{g[0]} - {g[1]}" for g in grupos])

            numero = st.number_input("Número de Unidad", min_value=1, max_value=10, value=1, step=1)
            nombre_unidad = st.text_input("Nombre de la Unidad (ej: Unidad 1 - Derivadas)")

            if st.form_submit_button("Crear Unidad"):
                if not grupo_sel:
                    st.warning("Debes seleccionar un Grupo")
                else:
                    id_grupo = int(grupo_sel.split(" - ")[0])
                    try:
                        cursor.execute("""
                            INSERT INTO unidad (id_grupo, numero, nombre)
                            VALUES (%s, %s, %s)
                        """, (id_grupo, numero, nombre_unidad.strip() if nombre_unidad else None))
                        conn.commit()
                        st.success("Unidad creada correctamente")
                        time.sleep(2)
                        st.rerun()
                    except Exception:
                        conn.rollback()
                        st.rerun()

    # ===================== EDITAR / ELIMINAR UNIDAD =====================
    with tab3:
        st.subheader("Editar o Eliminar Unidad")
        cursor.execute("""
            SELECT u.id_unidad, g.nombre_grupo, u.numero, u.nombre 
            FROM unidad u
            JOIN grupo g ON u.id_grupo = g.id_grupo
            ORDER BY g.nombre_grupo, u.numero
        """)
        unidades = cursor.fetchall()

        if unidades:
            seleccion = st.selectbox("Selecciona Unidad", 
                                     [f"{u[0]} - {u[1]} - Unidad {u[2]} - {u[3] or 'Sin nombre'}" for u in unidades])
            id_unidad = int(seleccion.split(" - ")[0])

            cursor.execute("SELECT numero, nombre FROM unidad WHERE id_unidad = %s", (id_unidad,))
            datos = cursor.fetchone()

            with st.form("editar_unidad"):
                nuevo_numero = st.number_input("Número de Unidad", min_value=1, max_value=10, value=datos[0], step=1)
                nuevo_nombre = st.text_input("Nombre de la Unidad", value=datos[1] or "")

                col1, col2 = st.columns(2)
                with col1:
                    if st.form_submit_button("Guardar cambios"):
                        try:
                            cursor.execute("""
                                UPDATE unidad 
                                SET numero = %s, nombre = %s
                                WHERE id_unidad = %s
                            """, (nuevo_numero, nuevo_nombre.strip() if nuevo_nombre else None, id_unidad))
                            conn.commit()
                            st.success("Unidad actualizada correctamente")
                            time.sleep(2)
                            st.rerun()
                        except Exception:
                            conn.rollback()
                            st.rerun()

                with col2:
                    if st.form_submit_button("Eliminar Unidad", type="secondary"):
                        if st.checkbox("¿Estás seguro de eliminar esta unidad?"):
                            try:
                                cursor.execute("DELETE FROM unidad WHERE id_unidad = %s", (id_unidad,))
                                conn.commit()
                                st.success("Unidad eliminada correctamente")
                                time.sleep(2)
                                st.rerun()
                            except Exception:
                                conn.rollback()
                                st.rerun()
# ===================== CONFIGURAR ACTIVIDADES (con filtro por rol Maestro) =====================
elif pagina == "Configurar Actividades":
    st.title("Configurar Actividades")
    st.markdown("**Asigna actividades y ponderaciones por unidad** (suma debe ser exactamente 100%)")

    # Filtrar grupos según rol
    if st.session_state.rol_actual == "Maestro" and 'maestro_id' in st.session_state:
        st.info(f"Solo puedes configurar tus propios grupos")
        cursor.execute("""
            SELECT id_grupo, nombre_grupo 
            FROM grupo 
            WHERE id_maestro = %s 
            ORDER BY nombre_grupo
        """, (st.session_state.maestro_id,))
    else:
        # Admin ve todos los grupos
        cursor.execute("SELECT id_grupo, nombre_grupo FROM grupo ORDER BY nombre_grupo")

    grupos = cursor.fetchall()

    if not grupos:
        st.warning("No hay grupos disponibles para ti.")
    else:
        grupo_sel = st.selectbox("Grupo", [f"{g[0]} - {g[1]}" for g in grupos])
        id_grupo = int(grupo_sel.split(" - ")[0])

        # Seleccionar Unidad
        cursor.execute("SELECT id_unidad, numero, nombre FROM unidad WHERE id_grupo = %s ORDER BY numero", (id_grupo,))
        unidades = cursor.fetchall()

        if not unidades:
            st.warning("No hay unidades creadas para este grupo.")
        else:
            unidad_sel = st.selectbox("Unidad", [f"{u[0]} - Unidad {u[1]} ({u[2] or 'Sin nombre'})" for u in unidades])
            id_unidad = int(unidad_sel.split(" - ")[0])

            # Mostrar actividades actuales
            st.subheader("Actividades actuales de la unidad")
            cursor.execute("""
                SELECT c.id_config_evaluacion, a.nombre, c.ponderacion 
                FROM config_evaluacion c
                JOIN actividad a ON c.id_actividad = a.id_actividad
                WHERE c.id_unidad = %s
            """, (id_unidad,))
            df_act = pd.DataFrame(cursor.fetchall(), columns=["id_config_evaluacion", "Actividad", "Ponderación (%)"])

            if not df_act.empty:
                suma = float(df_act["Ponderación (%)"].sum())

                st.dataframe(df_act[["Actividad", "Ponderación (%)"]], use_container_width=True, hide_index=True)

                if abs(suma - 100) < 0.01:
                    st.success(f"Suma perfecta: 100%")
                elif suma < 100:
                    st.warning(f"Faltan **{100 - suma:.1f}%** para llegar al 100%")
                else:
                    st.error(f"Sobran **{suma - 100:.1f}%**")

                st.progress(min(suma / 100, 1.0))
                st.caption(f"Suma actual: **{suma:.2f}%**")

                # Editar y Eliminar
                st.subheader("Editar o Eliminar actividad")
                for idx, row in df_act.iterrows():
                    col1, col2, col3 = st.columns([3, 1, 1])
                    with col1:
                        st.write(f"**{row['Actividad']}** — {row['Ponderación (%)']}%")
                    with col2:
                        if st.button("Editar", key=f"edit_{row['id_config_evaluacion']}"):
                            st.session_state.edit_id = row['id_config_evaluacion']
                            st.session_state.edit_ponderacion = row['Ponderación (%)']
                    with col3:
                        if st.button("Eliminar", key=f"del_{row['id_config_evaluacion']}"):
                            try:
                                cursor.execute("DELETE FROM config_evaluacion WHERE id_config_evaluacion = %s", (row['id_config_evaluacion'],))
                                conn.commit()
                                st.success("Actividad eliminada")
                                time.sleep(2)
                                st.rerun()
                            except Exception:
                                conn.rollback()
                                st.rerun()

                # Formulario de edición
                if 'edit_id' in st.session_state:
                    st.subheader("Editar ponderación")
                    with st.form("editar_ponderacion"):
                        nueva_ponderacion = st.number_input("Nueva ponderación (%)", 
                                                           min_value=0.0, max_value=100.0, 
                                                           value=float(st.session_state.edit_ponderacion), step=0.5)
                        if st.form_submit_button("Guardar cambio"):
                            try:
                                cursor.execute("""
                                    UPDATE config_evaluacion 
                                    SET ponderacion = %s 
                                    WHERE id_config_evaluacion = %s
                                """, (nueva_ponderacion, st.session_state.edit_id))
                                conn.commit()
                                st.success("Ponderación actualizada")
                                time.sleep(2)
                                del st.session_state.edit_id
                                del st.session_state.edit_ponderacion
                                st.rerun()
                            except Exception:
                                conn.rollback()
                                st.rerun()

            # ===================== AGREGAR NUEVA ACTIVIDAD =====================
            st.subheader("Agregar nueva actividad")
            with st.form("agregar_actividad", clear_on_submit=True):
                col1, col2 = st.columns(2)
                with col1:
                    nombre_actividad = st.text_input("Nombre de la actividad", "Examen")
                with col2:
                    ponderacion = st.number_input("Ponderación (%)", min_value=0.0, max_value=100.0, value=30.0, step=0.5)

                if st.form_submit_button("Agregar actividad"):
                    if ponderacion <= 0:
                        st.warning("La ponderación debe ser mayor a 0")
                    else:
                        cursor.execute("SELECT id_actividad FROM actividad WHERE nombre = %s LIMIT 1", (nombre_actividad,))
                        act = cursor.fetchone()
                        if not act:
                            cursor.execute("INSERT INTO actividad (nombre) VALUES (%s) RETURNING id_actividad", (nombre_actividad,))
                            id_actividad = cursor.fetchone()[0]
                        else:
                            id_actividad = act[0]

                        try:
                            cursor.execute("""
                                INSERT INTO config_evaluacion (id_unidad, id_actividad, ponderacion)
                                VALUES (%s, %s, %s)
                            """, (id_unidad, id_actividad, ponderacion))
                            conn.commit()
                            st.success("Actividad agregada correctamente")
                            time.sleep(2)
                            st.rerun()
                        except Exception:
                            conn.rollback()
                            st.rerun()
# ===================== REGISTRAR CALIFICACIONES (con filtro por rol Maestro) =====================
elif pagina == "Registrar Calificaciones":
    st.title("Registrar Calificaciones")
    st.markdown("**Registra calificaciones individuales por alumno y actividad**")

    # Filtrar grupos según rol
    if st.session_state.rol_actual == "Maestro" and 'maestro_id' in st.session_state:
        st.info(f"Solo puedes registrar calificaciones en tus propios grupos")
        cursor.execute("""
            SELECT id_grupo, nombre_grupo 
            FROM grupo 
            WHERE id_maestro = %s 
            ORDER BY nombre_grupo
        """, (st.session_state.maestro_id,))
    else:
        # Admin ve todos los grupos
        cursor.execute("SELECT id_grupo, nombre_grupo FROM grupo ORDER BY nombre_grupo")

    grupos = cursor.fetchall()

    if not grupos:
        st.warning("No hay grupos disponibles para ti.")
    else:
        grupo_sel = st.selectbox("Grupo", [f"{g[0]} - {g[1]}" for g in grupos])
        id_grupo = int(grupo_sel.split(" - ")[0])

        # Seleccionar Unidad
        cursor.execute("SELECT id_unidad, numero, nombre FROM unidad WHERE id_grupo = %s ORDER BY numero", (id_grupo,))
        unidades = cursor.fetchall()
        if not unidades:
            st.warning("No hay unidades en este grupo.")
        else:
            unidad_sel = st.selectbox("Unidad", [f"{u[0]} - Unidad {u[1]} ({u[2] or 'Sin nombre'})" for u in unidades])
            id_unidad = int(unidad_sel.split(" - ")[0])

            # Obtener actividades
            cursor.execute("""
                SELECT c.id_config_evaluacion, a.nombre, c.ponderacion
                FROM config_evaluacion c
                JOIN actividad a ON c.id_actividad = a.id_actividad
                WHERE c.id_unidad = %s
                ORDER BY a.nombre
            """, (id_unidad,))
            actividades = cursor.fetchall()

            if not actividades:
                st.warning("No hay actividades configuradas en esta unidad.")
            else:
                # Seleccionar Alumno (solo los inscritos en el grupo)
                cursor.execute("""
                    SELECT a.id_alumno, a.matricula, a.nombre, a.apellido_paterno, a.apellido_materno
                    FROM inscripcion i
                    JOIN alumno a ON i.id_alumno = a.id_alumno
                    WHERE i.id_grupo = %s
                    ORDER BY a.nombre
                """, (id_grupo,))
                alumnos = cursor.fetchall()

                if not alumnos:
                    st.warning("No hay alumnos inscritos en este grupo.")
                else:
                    alumno_sel = st.selectbox(
                        "Alumno",
                        [f"{a[0]} - {a[1]} - {a[2]} {a[3]} {a[4] or ''}".strip() for a in alumnos]
                    )
                    id_alumno = int(alumno_sel.split(" - ")[0])

                    st.subheader(f"Calificaciones de {alumno_sel.split(' - ')[2]}")

                    # Inputs de calificaciones
                    calificaciones = {}
                    for id_config_evaluacion, nombre_act, ponderacion in actividades:
                        calif = st.number_input(
                            f"{nombre_act} ({float(ponderacion)}%)",
                            min_value=0.0,
                            max_value=100.0,
                            value=0.0,
                            step=0.5,
                            key=f"calif_{id_alumno}_{id_config_evaluacion}"
                        )
                        calificaciones[id_config_evaluacion] = calif

                    # Cálculo en tiempo real
                    total_ponderado = 0.0
                    for id_config_evaluacion, calif in calificaciones.items():
                        for act in actividades:
                            if act[0] == id_config_evaluacion:
                                total_ponderado += calif * (float(act[2]) / 100)
                                break

                    st.success(f"**Calificación de la Unidad (promedio ponderado):** {total_ponderado:.2f}")

                    # Guardar
                    if st.button("Guardar calificaciones de este alumno"):
                        try:
                            for id_config_evaluacion, calif in calificaciones.items():
                                cursor.execute("""
                                    INSERT INTO resultado (id_config_evaluacion, id_alumno, calificacion)
                                    VALUES (%s, %s, %s)
                                    ON CONFLICT (id_config_evaluacion, id_alumno) 
                                    DO UPDATE SET calificacion = %s
                                """, (id_config_evaluacion, id_alumno, calif, calif))
                            conn.commit()
                            st.success("Calificaciones guardadas correctamente")
                            time.sleep(2)
                            st.rerun()
                        except Exception as e:
                            conn.rollback()
                            st.error(f"Error al guardar: {e}")
# ===================== VER CALIFICACIONES Y CÁLCULOS (con modificación manual de calif_final) =====================
elif pagina == "Ver Calificaciones y Cálculos":
    st.title("Ver Calificaciones y Cálculos")
    st.markdown("**Transparencia matemática completa** – Promedio ponderado, bonus y calificación final")

    # Filtrar grupos según rol
    if st.session_state.rol_actual == "Maestro" and 'maestro_id' in st.session_state:
        st.info(f"🔹 Modo Maestro: Solo puedes ver calificaciones de tus propios grupos")
        cursor.execute("""
            SELECT id_grupo, nombre_grupo 
            FROM grupo 
            WHERE id_maestro = %s 
            ORDER BY nombre_grupo
        """, (st.session_state.maestro_id,))
    else:
        cursor.execute("SELECT id_grupo, nombre_grupo FROM grupo ORDER BY nombre_grupo")

    grupos = cursor.fetchall()

    if not grupos:
        st.warning("No hay grupos disponibles para ti.")
    else:
        grupo_sel = st.selectbox("Grupo", [f"{g[0]} - {g[1]}" for g in grupos])
        id_grupo = int(grupo_sel.split(" - ")[0])

        # Seleccionar Alumno
        cursor.execute("""
            SELECT a.id_alumno, a.matricula, a.nombre, a.apellido_paterno, a.apellido_materno
            FROM inscripcion i
            JOIN alumno a ON i.id_alumno = a.id_alumno
            WHERE i.id_grupo = %s
            ORDER BY a.nombre
        """, (id_grupo,))
        alumnos = cursor.fetchall()

        if not alumnos:
            st.warning("No hay alumnos inscritos en este grupo.")
        else:
            alumno_sel = st.selectbox(
                "Alumno",
                [f"{a[0]} - {a[1]} - {a[2]} {a[3]} {a[4] or ''}".strip() for a in alumnos]
            )
            id_alumno = int(alumno_sel.split(" - ")[0])

            # ===================== CÁLCULO POR UNIDAD =====================
            st.subheader("Cálculo por Unidad")

            cursor.execute("""
                SELECT u.id_unidad, u.numero, u.nombre
                FROM unidad u
                WHERE u.id_grupo = %s
                ORDER BY u.numero
            """, (id_grupo,))
            unidades = cursor.fetchall()

            for id_unidad, numero, nombre_unidad in unidades:
                st.write(f"**Unidad {numero} — {nombre_unidad or 'Sin nombre'}**")

                cursor.execute("""
                    SELECT a.nombre, c.ponderacion, r.calificacion
                    FROM config_evaluacion c
                    JOIN actividad a ON c.id_actividad = a.id_actividad
                    LEFT JOIN resultado r ON r.id_config_evaluacion = c.id_config_evaluacion 
                                         AND r.id_alumno = %s
                    WHERE c.id_unidad = %s
                    ORDER BY a.nombre
                """, (id_alumno, id_unidad))
                df_unidad = pd.DataFrame(cursor.fetchall(), columns=["Actividad", "Ponderación (%)", "Calificación"])

                if df_unidad.empty:
                    st.info("No hay calificaciones registradas en esta unidad")
                else:
                    df_unidad["Ponderación (%)"] = df_unidad["Ponderación (%)"].astype(float)
                    df_unidad["Calificación"] = df_unidad["Calificación"].fillna(0).astype(float)
                    df_unidad["Contribución"] = df_unidad["Calificación"] * (df_unidad["Ponderación (%)"] / 100)

                    st.dataframe(df_unidad, use_container_width=True, hide_index=True)

                    calif_unidad = float(df_unidad["Contribución"].sum())
                    st.success(f"**Calificación de la Unidad:** {calif_unidad:.2f}")

                # Bonus por unidad (solo Admin y Maestro)
                if st.session_state.rol_actual in ["Admin", "Maestro"]:
                    st.write("**Bonus por unidad**")
                    with st.form(f"bonus_unidad_{id_unidad}", clear_on_submit=True):
                        bonus = st.number_input("Bonus por unidad", min_value=0.0, value=0.0, step=0.5)
                        justificacion = st.text_area("Justificación del bonus", "Participación destacada")

                        if st.form_submit_button("Aplicar / Actualizar Bonus"):
                            try:
                                cursor.execute("""
                                    INSERT INTO calificacion_final 
                                    (id_inscripcion, id_unidad, calif_calculada, bonus, justificacion, es_modificada)
                                    SELECT i.id_inscripcion, %s, %s, %s, %s, TRUE
                                    FROM inscripcion i 
                                    WHERE i.id_alumno = %s AND i.id_grupo = %s
                                    ON CONFLICT (id_inscripcion, id_unidad)
                                    DO UPDATE SET 
                                        bonus = %s, justificacion = %s, es_modificada = TRUE, fecha_modificacion = CURRENT_TIMESTAMP
                                """, (id_unidad, calif_unidad, bonus, justificacion, id_alumno, id_grupo, bonus, justificacion))
                                conn.commit()
                                st.success("Bonus por unidad aplicado/actualizado")
                                time.sleep(2)
                                st.rerun()
                            except Exception as e:
                                conn.rollback()
                                st.error(f"Error: {e}")

            # ===================== CALIFICACIÓN FINAL DE LA MATERIA =====================
            st.subheader("Calificación Final de la Materia")

            cursor.execute("""
                SELECT AVG(cf.calif_calculada)
                FROM calificacion_final cf
                JOIN inscripcion i ON cf.id_inscripcion = i.id_inscripcion
                WHERE i.id_alumno = %s AND i.id_grupo = %s AND cf.id_unidad IS NOT NULL
            """, (id_alumno, id_grupo))
            promedio = cursor.fetchone()[0]
            promedio = float(promedio) if promedio is not None else 0.0

            st.success(f"**Promedio Final Calculado:** {promedio:.2f}")

            # ===================== BONUS FINAL =====================
            if st.session_state.rol_actual in ["Admin", "Maestro"]:
                with st.form("bonus_final", clear_on_submit=True):
                    bonus_final = st.number_input("Bonus Final de la Materia", min_value=0.0, value=0.0, step=0.5)
                    justificacion_final = st.text_area("Justificación del bonus final", "Esfuerzo extra en el semestre")

                    if st.form_submit_button("Aplicar Bonus Final"):
                        try:
                            cursor.execute("""
                                INSERT INTO calificacion_final 
                                (id_inscripcion, id_unidad, calif_calculada, bonus, calif_final, justificacion, es_modificada)
                                SELECT i.id_inscripcion, NULL, %s, %s, %s, %s, TRUE
                                FROM inscripcion i 
                                WHERE i.id_alumno = %s AND i.id_grupo = %s
                                ON CONFLICT (id_inscripcion, id_unidad)
                                DO UPDATE SET 
                                    bonus = %s, calif_final = %s, justificacion = %s, 
                                    es_modificada = TRUE, fecha_modificacion = CURRENT_TIMESTAMP
                            """, (promedio, bonus_final, promedio + bonus_final, justificacion_final, 
                                  id_alumno, id_grupo, bonus_final, promedio + bonus_final, justificacion_final))
                            conn.commit()
                            st.success("Bonus final aplicado correctamente")
                            time.sleep(2)
                            st.rerun()
                        except Exception as e:
                            conn.rollback()
                            st.error(f"Error: {e}")

            # ===================== MODIFICACIÓN MANUAL DE CALIFICACIÓN FINAL (Docente) =====================
            if st.session_state.rol_actual in ["Admin", "Maestro"]:
                st.subheader("✏️ Modificar Calificación Final Manualmente")
                with st.form("modificar_calif_final", clear_on_submit=True):
                    nueva_calif_final = st.number_input(
                        "Nueva Calificación Final (0-100)", 
                        min_value=0.0, max_value=100.0, 
                        value=promedio, step=0.5
                    )
                    justificacion_manual = st.text_area(
                        "Justificación de la modificación", 
                        "Modificación por revisión de evidencias"
                    )

                    if st.form_submit_button("💾 Guardar Calificación Final Modificada"):
                        try:
                            cursor.execute("""
                                INSERT INTO calificacion_final 
                                (id_inscripcion, id_unidad, calif_calculada, calif_final, justificacion, es_modificada)
                                SELECT i.id_inscripcion, NULL, %s, %s, %s, TRUE
                                FROM inscripcion i 
                                WHERE i.id_alumno = %s AND i.id_grupo = %s
                                ON CONFLICT (id_inscripcion, id_unidad)
                                DO UPDATE SET 
                                    calif_final = %s,
                                    justificacion = %s,
                                    es_modificada = TRUE,
                                    fecha_modificacion = CURRENT_TIMESTAMP
                            """, (promedio, nueva_calif_final, justificacion_manual, 
                                  id_alumno, id_grupo, nueva_calif_final, justificacion_manual))
                            conn.commit()
                            st.success("✅ Calificación final modificada correctamente")
                            time.sleep(2)
                            st.rerun()
                        except Exception as e:
                            conn.rollback()
                            st.error(f"Error: {e}")
            else:
                st.info("Los alumnos no pueden modificar la calificación final.")
# ===================== CARGA MASIVA POR CSV =====================
elif pagina == "Carga Masiva CSV":
    st.title("Carga Masiva por CSV")
    st.markdown("**Sube archivos CSV para cargar datos rápidamente** (Alumnos, Materias, Grupos, Inscripciones)")

    tipo_carga = st.selectbox(
        "¿Qué tipo de datos vas a cargar?",
        ["Alumnos", "Materias", "Grupos", "Inscripciones"]
    )

    uploaded_file = st.file_uploader("Selecciona tu archivo CSV", type=["csv"])

    if uploaded_file is not None:
        df = pd.read_csv(uploaded_file)
        st.subheader("Vista previa del archivo")
        st.dataframe(df, use_container_width=True)

        if st.button(f"Importar {tipo_carga}"):
            try:
                if tipo_carga == "Alumnos":
                    for _, row in df.iterrows():
                        cursor.execute("""
                            INSERT INTO alumno (matricula, nombre, apellido_paterno, apellido_materno, email, fecha_nacimiento)
                            VALUES (%s, %s, %s, %s, %s, %s)
                            ON CONFLICT (matricula) DO NOTHING
                        """, (
                            str(row.get('matricula', '')).strip(),
                            str(row.get('nombre', '')).strip(),
                            str(row.get('apellido_paterno', '')).strip(),
                            str(row.get('apellido_materno', '')).strip() or None,
                            str(row.get('email', '')).strip() or None,
                            row.get('fecha_nacimiento') if pd.notna(row.get('fecha_nacimiento')) else None
                        ))
                
                elif tipo_carga == "Materias":
                    for _, row in df.iterrows():
                        cursor.execute("""
                            INSERT INTO materia (codigo, nombre)
                            VALUES (%s, %s)
                            ON CONFLICT (codigo) DO NOTHING
                        """, (
                            str(row.get('codigo', '')).strip(),
                            str(row.get('nombre', '')).strip()
                        ))

                elif tipo_carga == "Grupos":
                    for _, row in df.iterrows():
                        cursor.execute("""
                            INSERT INTO grupo (id_materia, id_maestro, nombre_grupo, periodo)
                            VALUES (%s, %s, %s, %s)
                            ON CONFLICT DO NOTHING
                        """, (
                            row.get('id_materia'),
                            row.get('id_maestro'),
                            str(row.get('nombre_grupo', '')).strip(),
                            str(row.get('periodo', '')).strip()
                        ))

                elif tipo_carga == "Inscripciones":
                    for _, row in df.iterrows():
                        cursor.execute("""
                            INSERT INTO inscripcion (id_alumno, id_grupo)
                            VALUES (%s, %s)
                            ON CONFLICT DO NOTHING
                        """, (row.get('id_alumno'), row.get('id_grupo')))

                conn.commit()
                st.success(f"{tipo_carga} cargados correctamente desde CSV")
                time.sleep(2)
                st.rerun()

            except Exception as e:
                conn.rollback()
                st.error(f"Error durante la carga: {e}")
