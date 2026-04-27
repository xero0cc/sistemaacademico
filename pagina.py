import streamlit as st
import psycopg2
import pandas as pd
import time
from datetime import date
from streamlit_option_menu import option_menu

# ===================== CONEXIÓN A SUPABASE =====================
@st.cache_resource
def get_connection():
    return psycopg2.connect(
        host="aws-1-us-west-2.pooler.supabase.com",
        port="6543",
        database="postgres",
        user="postgres.ypoqacbyxmyycwrwfekm",
        password="Aaronyalejandra12",
        sslmode="require"
    )

conn = get_connection()
cursor = conn.cursor()

# ===================== INICIALIZACIÓN DE SESIÓN =====================
if 'usuario' not in st.session_state:
    st.session_state.usuario = None  # None = no hay sesión

# ===================== PANTALLA DE LOGIN =====================
if st.session_state.usuario is None:
    st.title("Sistema de Registro y Cálculo de Resultados Académicos")
    st.subheader("Iniciar Sesión")

    opcion = st.selectbox("Tipo de usuario", ["Alumno", "Maestro", "Admin"])

    if opcion == "Admin":
        if st.button("Entrar como Administrador"):
            st.session_state.usuario = {
                "id": 0, 
                "rol": "Admin", 
                "nombre": "Administrador"
            }
            st.session_state.rol_actual = "Admin"
            st.session_state.pagina = "Dashboard"
            st.rerun()

    elif opcion == "Alumno":
        matricula = st.text_input("Matrícula")
        nip = st.text_input("NIP", type="password")
        
        if st.button("Iniciar Sesión como Alumno"):
            cursor.execute("""
                SELECT id_alumno, nombre, apellido_paterno, apellido_materno, rol
                FROM alumno 
                WHERE matricula = %s AND nip = %s
            """, (matricula, nip))
            resultado = cursor.fetchone()
            
            if resultado:
                st.session_state.usuario = {
                    "id": resultado[0],
                    "rol": resultado[4],
                    "nombre": f"{resultado[1]} {resultado[2]} {resultado[3] or ''}".strip()
                }
                st.session_state.rol_actual = resultado[4]
                st.session_state.pagina = "Dashboard"
                st.rerun()
            else:
                st.error("Matrícula o NIP incorrectos")

    elif opcion == "Maestro":
        clave = st.text_input("Clave del maestro")
        nip = st.text_input("NIP", type="password")
        
        if st.button("Iniciar Sesión como Maestro"):
            cursor.execute("""
                SELECT id_maestro, nombre, apellido_paterno, apellido_materno, rol
                FROM maestro 
                WHERE clave = %s AND nip = %s
            """, (clave, nip))
            resultado = cursor.fetchone()
            
            if resultado:
                st.session_state.usuario = {
                    "id": resultado[0],
                    "rol": resultado[4],
                    "nombre": f"{resultado[1]} {resultado[2]} {resultado[3] or ''}".strip()
                }
                st.session_state.rol_actual = resultado[4]
                st.session_state.maestro_id = resultado[0]   # ← Muy importante
                st.session_state.pagina = "Dashboard"
                st.rerun()
            else:
                st.error("Clave o NIP incorrectos")

    st.stop()  # Detiene la ejecución hasta que se inicie sesión
# ===================== SIDEBAR CON OPTION MENU =====================
nombre = st.session_state.usuario.get('nombre', 'Usuario')
rol = st.session_state.usuario.get('rol', '')

with st.sidebar:
    st.title("Sistema Académico")

    # ==================== POPOVER DEL USUARIO ====================
    with st.popover(f"{nombre}", use_container_width=True):
        if rol != "Admin":
            if st.button("Ver Perfil", use_container_width=True):
                st.session_state.pagina = "Perfil"
                st.rerun()
        
        if st.button("Cerrar sesión", type="secondary", use_container_width=True):
            for key in list(st.session_state.keys()):
                if key not in ["usuario"]:
                    del st.session_state[key]
            st.session_state.usuario = None
            st.rerun()

    # ==================== OPTION MENU POR ROL ====================
    if rol == "Admin":
        opciones = [
            "Dashboard", "Alumnos", "Maestros", "Materias", "Grupos e Inscripciones",
            "Unidades", "Criterios de Evaluación", "Actividades y Calificaciones",
            "Calificaciones", "Carga Masiva CSV"
        ]
        icons = ["house", "people", "person-badge", "book", "people-fill", 
                "list-ul", "clipboard-check", "pencil-square", "graph-up", "cloud-upload"]

    elif rol == "Maestro":
        opciones = ["Dashboard", "Actividades y Calificaciones", "Calificaciones"]
        icons = ["house", "pencil-square", "graph-up"]

    else:  # Alumno
        opciones = ["Dashboard", "Actividades y Calificaciones", "Mis Calificaciones"]
        icons = ["house", "pencil-square", "graph-up"]

    # Control de página
    if "pagina" not in st.session_state or st.session_state.pagina not in opciones + ["Perfil"]:
        st.session_state.pagina = "Dashboard"

    # Mostrar Option Menu SOLO si NO estamos en Perfil
    if st.session_state.pagina != "Perfil":
        pagina_seleccionada = option_menu(
            menu_title=None,
            options=opciones,
            icons=icons,
            menu_icon="menu-button-wide",
            default_index=opciones.index(st.session_state.pagina) if st.session_state.pagina in opciones else 0,
            key="main_option_menu",
            styles={
                "container": {"padding": "0!important", "background-color": "transparent"},
                "nav-link": {"font-size": "15px", "text-align": "left", "margin": "4px", "border-radius": "6px"},
                "nav-link-selected": {"background-color": "#2C3E50", "color": "white"},
            }
        )
        st.session_state.pagina = pagina_seleccionada
    else:
        if st.button("← Volver al menú principal", use_container_width=True):
            st.session_state.pagina = "Dashboard"
            st.rerun()

# ===================== VARIABLE 'pagina' =====================
pagina = st.session_state.pagina
# ===================== DASHBOARD =====================
if pagina == "Dashboard":
    st.title("Dashboard")
    st.success("Todo funcionando")


# ===================== ALUMNOS =====================
elif pagina == "Alumnos":
    st.title("Gestión de Alumnos")

    tab1, tab2, tab3 = st.tabs(["Ver todos", "Inscribir Alumno", "Editar / Eliminar"])

    # ===================== VER TODOS =====================
    with tab1:
        st.subheader("Lista de Alumnos")
        cursor.execute("""
            SELECT id_alumno, matricula, nip, nombre, apellido_paterno, apellido_materno, 
                   email, telefono, fecha_nacimiento 
            FROM alumno 
            ORDER BY nombre
        """)
        df = pd.DataFrame(cursor.fetchall(), 
                         columns=["ID", "Matrícula", "NIP", "Nombre", "Ape. Paterno", 
                                  "Ape. Materno", "Email", "Teléfono", "Fecha Nacimiento"])
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
                email = st.text_input("Email")
                telefono = st.text_input("Teléfono")
                fecha_nacimiento = st.date_input("Fecha de Nacimiento*", value=date(2005, 1, 1))

            # NIP generado automáticamente
            nip_generado = fecha_nacimiento.strftime("%Y%m%d")

            if st.form_submit_button("Inscribir Alumno"):
                if not nombre.strip() or not apellido_paterno.strip():
                    st.warning("Faltan datos obligatorios (Nombre y Apellido Paterno)")
                else:
                    try:
                        # Capitalizar primera letra de cada palabra
                        nombre = nombre.strip().title()
                        apellido_paterno = apellido_paterno.strip().title()
                        apellido_materno = apellido_materno.strip().title() if apellido_materno.strip() else None

                        # Generar matrícula automática
                        cursor.execute("""
                            SELECT MAX(CAST(matricula AS INTEGER)) 
                            FROM alumno 
                            WHERE matricula LIKE '2000000%'
                        """)
                        max_mat = cursor.fetchone()[0]
                        nueva_matricula = str(max_mat + 1) if max_mat else "20000001"

                        cursor.execute("""
                            INSERT INTO alumno 
                            (matricula, nip, nombre, apellido_paterno, apellido_materno, 
                             email, telefono, fecha_nacimiento)
                            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                        """, (nueva_matricula, nip_generado, nombre, apellido_paterno,
                              apellido_materno, 
                              email.strip() if email else None,
                              telefono.strip() if telefono else None,
                              fecha_nacimiento))
                        
                        conn.commit()
                        st.success(f"Alumno inscrito correctamente - Matrícula: {nueva_matricula} | NIP: {nip_generado}")
                        time.sleep(1.5)
                        st.rerun()
                    except Exception as e:
                        conn.rollback()
                        st.error(f"Error al inscribir: {e}")
    # ===================== EDITAR / ELIMINAR =====================
    with tab3:
        st.subheader("Editar o Eliminar Alumno")
        cursor.execute("""
            SELECT id_alumno, matricula, nombre, apellido_paterno 
            FROM alumno ORDER BY nombre
        """)
        alumnos = cursor.fetchall()

        if alumnos:
            seleccion = st.selectbox("Selecciona alumno", 
                                     [f"{a[0]} - {a[1]} - {a[2]} {a[3]}" for a in alumnos])
            id_alumno = int(seleccion.split(" - ")[0])

            cursor.execute("""
                SELECT matricula, nip, nombre, apellido_paterno, apellido_materno, 
                       email, fecha_nacimiento, telefono 
                FROM alumno WHERE id_alumno = %s
            """, (id_alumno,))
            datos = cursor.fetchone()

            with st.form("editar_alumno"):
                col1, col2 = st.columns(2)
                with col1:
                    st.text_input("Matrícula", value=datos[0], disabled=True)
                    nuevo_nombre = st.text_input("Nombre(s)", value=datos[2])
                    nuevo_ap_p = st.text_input("Apellido Paterno", value=datos[3])
                    nuevo_ap_m = st.text_input("Apellido Materno", value=datos[4] or "")
                with col2:
                    nuevo_nip = st.text_input("NIP", value=datos[1] or "")
                    nuevo_email = st.text_input("Email", value=datos[5] or "")
                    nuevo_telefono = st.text_input("Teléfono", value=datos[7] or "")
                    nueva_fecha = st.date_input("Fecha de Nacimiento", value=datos[6])

                col1, col2 = st.columns(2)
                with col1:
                    if st.form_submit_button("Guardar cambios"):
                        try:
                            # Capitalizar nombres
                            nuevo_nombre = nuevo_nombre.strip().title()
                            nuevo_ap_p = nuevo_ap_p.strip().title()
                            nuevo_ap_m = nuevo_ap_m.strip().title() if nuevo_ap_m.strip() else None

                            cursor.execute("""
                                UPDATE alumno 
                                SET nip = %s, 
                                    nombre = %s, 
                                    apellido_paterno = %s,
                                    apellido_materno = %s, 
                                    email = %s, 
                                    telefono = %s,
                                    fecha_nacimiento = %s
                                WHERE id_alumno = %s
                            """, (nuevo_nip, nuevo_nombre, nuevo_ap_p, nuevo_ap_m, 
                                  nuevo_email, nuevo_telefono, nueva_fecha, id_alumno))
                            
                            conn.commit()
                            st.success("Datos actualizados correctamente")
                            time.sleep(1.5)
                            st.rerun()
                        except Exception as e:
                            conn.rollback()
                            st.error(f"Error al actualizar: {e}")

                with col2:
                    if st.form_submit_button("Eliminar Alumno", type="secondary"):
                        if st.checkbox("¿Estás seguro de eliminar este alumno? Esta acción es irreversible."):
                            try:
                                cursor.execute("DELETE FROM alumno WHERE id_alumno = %s", (id_alumno,))
                                conn.commit()
                                st.success("Alumno eliminado correctamente")
                                time.sleep(1.5)
                                st.rerun()
                            except Exception:
                                conn.rollback()
                                st.error("Error al eliminar el alumno")
# ===================== MAESTROS (corregido y mejorado) =====================
elif pagina == "Maestros":
    st.title("Gestión de Maestros")
    tab1, tab2, tab3 = st.tabs(["Ver todos", "Registrar Maestro", "Editar / Eliminar"])

    # Cargar materias desde la base de datos
    cursor.execute("SELECT nombre FROM materia ORDER BY nombre")
    materias_db = [row[0] for row in cursor.fetchall()]

    # ===================== VER TODOS =====================
    with tab1:
        st.subheader("Lista de Maestros")
        cursor.execute("""
            SELECT id_maestro, clave, nip, nombre, apellido_paterno, apellido_materno, 
                   telefono, email, especialidad, fecha_nacimiento 
            FROM maestro 
            ORDER BY nombre
        """)
        df = pd.DataFrame(cursor.fetchall(), 
                         columns=["ID", "Clave", "NIP", "Nombre", "Ape. Paterno", "Ape. Materno", 
                                  "Teléfono", "Email", "Especialidad", "Fecha Nacimiento"])
        st.dataframe(df, use_container_width=True, hide_index=True)

    # ===================== REGISTRAR NUEVO MAESTRO =====================
    with tab2:
        st.subheader("Registrar Nuevo Maestro")
        with st.form("nuevo_maestro", clear_on_submit=True):
            col1, col2 = st.columns(2)
            with col1:
                nombre = st.text_input("Nombre(s)*")
                apellido_paterno = st.text_input("Apellido Paterno*")
                apellido_materno = st.text_input("Apellido Materno")
                fecha_nacimiento = st.date_input("Fecha de Nacimiento*", value=date(1980, 1, 1))
            with col2:
                telefono = st.text_input("Teléfono (máx. 10 dígitos)", max_chars=10)
                email = st.text_input("Email*")
                especialidad = st.multiselect("Maestria", materias_db)

            if st.form_submit_button("Registrar Maestro"):
                if not nombre or not apellido_paterno or not email or not especialidad:
                    st.warning("Faltan datos obligatorios")
                else:
                    esp_str = ", ".join(especialidad)
                    nip_generado = fecha_nacimiento.strftime("%Y%m%d")

                    # Generar clave automática
                    cursor.execute("SELECT MAX(CAST(clave AS INTEGER)) FROM maestro WHERE clave LIKE '1%'")
                    max_clave = cursor.fetchone()[0]
                    clave_generada = str(max_clave + 1) if max_clave else "10000001"

                    try:
                        cursor.execute("""
                            INSERT INTO maestro 
                            (nombre, apellido_paterno, apellido_materno, telefono, email, especialidad, clave, nip, fecha_nacimiento)
                            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                        """, (nombre, apellido_paterno, apellido_materno, telefono, email, esp_str, 
                              clave_generada, nip_generado, fecha_nacimiento))
                        conn.commit()
                        st.success(f"Maestro registrado correctamente")
                        time.sleep(2)
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
                SELECT nombre, apellido_paterno, apellido_materno, telefono, email, especialidad, clave, nip, fecha_nacimiento 
                FROM maestro WHERE id_maestro = %s
            """, (id_maestro,))
            datos = cursor.fetchone()

            with st.form("editar_maestro"):
                col1, col2 = st.columns(2)
                with col1:
                    st.text_input("Clave (no editable)", value=datos[6], disabled=True)
                    nuevo_nombre = st.text_input("Nombre(s)", value=datos[0])
                    nuevo_ap_p = st.text_input("Apellido Paterno", value=datos[1])
                    nuevo_ap_m = st.text_input("Apellido Materno", value=datos[2] or "")
                with col2:
                    nuevo_nip = st.text_input("NIP", value=datos[7] or "")
                    nuevo_tel = st.text_input("Teléfono", value=datos[3] or "")
                    nuevo_email = st.text_input("Email", value=datos[4] or "")
                    nueva_fecha = st.date_input("Fecha de Nacimiento", value=datos[8])
                    nueva_esp = st.multiselect("Maestria", materias_db, 
                                              default=datos[5].split(", ") if datos[5] else [])

                col1, col2 = st.columns(2)
                with col1:
                    if st.form_submit_button("Guardar cambios"):
                        try:
                            cursor.execute("""
                                UPDATE maestro 
                                SET nombre=%s, apellido_paterno=%s, apellido_materno=%s,
                                    telefono=%s, email=%s, especialidad=%s, nip=%s, fecha_nacimiento=%s
                                WHERE id_maestro=%s
                            """, (nuevo_nombre, nuevo_ap_p, nuevo_ap_m, nuevo_tel, nuevo_email, 
                                  ", ".join(nueva_esp), nuevo_nip, nueva_fecha, id_maestro))
                            conn.commit()
                            st.success("Cambios guardados correctamente")
                            time.sleep(2)
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
                                time.sleep(1.5)
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
                         columns=["ID", "Código", "Nombre de la Materia", "Maestro con maestría"])
        st.dataframe(df, use_container_width=True, hide_index=True)

        # ===================== NUEVA MATERIA =====================
    with tab2:
        st.subheader("Nueva Materia")
        with st.form("nueva_materia", clear_on_submit=True):
            nombre = st.text_input("Nombre completo de la materia *").strip()

            if st.form_submit_button("Guardar Materia"):
                if not nombre:
                    st.warning("El nombre de la materia es obligatorio")
                else:
                    try:
                        # ==================== GENERACIÓN AUTOMÁTICA DE CÓDIGO ====================
                        palabras = nombre.split()
                        codigo_base = []

                        for palabra in palabras:
                            p = palabra.strip().upper()
                            if len(p) > 3 and p not in ["DE", "LA", "EL", "LOS", "LAS", "Y", "O", "EN", "CON", "PARA", "POR"]:
                                codigo_base.append(p[:3])

                        codigo_sin_numero = "-".join(codigo_base)

                        # Generar número secuencial
                        cursor.execute("""
                            SELECT COUNT(*) 
                            FROM materia 
                            WHERE codigo LIKE %s
                        """, (codigo_sin_numero + "%",))
                        conteo = cursor.fetchone()[0]

                        codigo_final = f"{codigo_sin_numero}-{str(conteo + 1).zfill(2)}"

                        # Insertar
                        cursor.execute("""
                            INSERT INTO materia (codigo, nombre)
                            VALUES (%s, %s)
                        """, (codigo_final, nombre.title()))
                        
                        conn.commit()
                        st.success(f"Materia agregada correctamente - Código: **{codigo_final}**")
                        time.sleep(1.5)
                        st.rerun()

                    except Exception as e:
                        conn.rollback()
                        st.error(f"Error al guardar la materia: {e}")
    # ===================== EDITAR / ELIMINAR =====================
    with tab3:
        st.subheader("Editar o Eliminar Materia")
        cursor.execute("SELECT id_materia, codigo, nombre FROM materia ORDER BY nombre")
        materias = cursor.fetchall()

        if materias:
            seleccion = st.selectbox("Selecciona materia", 
                                     [f"{m[0]} - {m[1]} - {m[2]}" for m in materias])
            id_materia = int(seleccion.split(" - ")[0])

            cursor.execute("""
                SELECT codigo, nombre 
                FROM materia 
                WHERE id_materia = %s
            """, (id_materia,))
            datos = cursor.fetchone()

            with st.form("editar_materia"):
                nuevo_codigo = st.text_input("Código", value=datos[0], max_chars=10).strip().upper()
                nuevo_nombre = st.text_input("Nombre de la materia", value=datos[1]).strip()

                col1, col2 = st.columns(2)
                with col1:
                    if st.form_submit_button("Guardar cambios"):
                        if not nuevo_codigo or not nuevo_nombre:
                            st.warning("Código y Nombre son obligatorios")
                        else:
                            try:
                                cursor.execute("""
                                    UPDATE materia 
                                    SET codigo = %s, nombre = %s
                                    WHERE id_materia = %s
                                """, (nuevo_codigo, nuevo_nombre.title(), id_materia))
                                conn.commit()
                                st.success("Materia actualizada correctamente")
                                time.sleep(1.5)
                                st.rerun()
                            except Exception as e:
                                conn.rollback()
                                st.error(f"Error al actualizar: {e}")

                with col2:
                    if st.form_submit_button("Eliminar Materia", type="secondary"):
                        # Verificar si tiene grupos
                        cursor.execute("""
                            SELECT COUNT(*) FROM grupo WHERE id_materia = %s
                        """, (id_materia,))
                        conteo = cursor.fetchone()[0]

                        if conteo > 0:
                            st.error(f"No se puede eliminar. Esta materia tiene {conteo} grupo(s) asignado(s).")
                        else:
                            if st.checkbox("¿Estás seguro de eliminar esta materia? Esta acción es irreversible."):
                                try:
                                    cursor.execute("DELETE FROM materia WHERE id_materia = %s", (id_materia,))
                                    conn.commit()
                                    st.success("Materia eliminada correctamente")
                                    time.sleep(1.5)
                                    st.rerun()
                                except Exception as e:
                                    conn.rollback()
                                    st.error(f"Error al eliminar: {e}")
# ===================== GRUPOS E INSCRIPCIONES =====================
elif pagina == "Grupos e Inscripciones":
    st.title("Grupos e Inscripciones")

    tab1, tab2, tab3, tab4 = st.tabs(["Ver Grupos", "Crear Nuevo Grupo", "Inscripciones", "Editar / Eliminar"])

    # ===================== VER GRUPOS =====================
    with tab1:
        st.subheader("Lista de Grupos")
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
            GROUP BY g.id_grupo, m.nombre, maestro.nombre, maestro.apellido_paterno, 
                     g.nombre_grupo, g.periodo
            ORDER BY g.periodo DESC, m.nombre, g.nombre_grupo
        """)
        df = pd.DataFrame(cursor.fetchall(), 
                         columns=["ID", "Materia", "Maestro", "Nombre del Grupo", "Periodo", "Alumnos inscritos"])
        st.dataframe(df, use_container_width=True, hide_index=True)

    # ===================== CREAR NUEVO GRUPO =====================
    with tab2:
        st.subheader("Crear Nuevo Grupo")
        with st.form("nuevo_grupo", clear_on_submit=True):
            cursor.execute("SELECT id_materia, nombre FROM materia ORDER BY nombre")
            materias = cursor.fetchall()
            cursor.execute("SELECT id_maestro, nombre, apellido_paterno FROM maestro ORDER BY nombre")
            maestros = cursor.fetchall()

            materia_sel = st.selectbox("Materia", [f"{m[0]} - {m[1]}" for m in materias])
            maestro_sel = st.selectbox("Maestro", 
                                      [f"{ma[0]} - {ma[1]} {ma[2]}" for ma in maestros] + ["Sin asignar"])

            current_year = date.today().year
            year = st.selectbox("Año", [current_year, current_year + 1, current_year + 2], index=1)
            tipo_periodo = st.selectbox("Tipo de periodo", ["ene-jun", "ago-dic", "verano"])

            if tipo_periodo == "ene-jun":
                periodo = f"ene-jun/{year}"
            elif tipo_periodo == "ago-dic":
                periodo = f"ago-dic/{year}"
            else:
                periodo = f"verano/{year}"

            st.caption(f"Periodo: **{periodo}**")

            if st.form_submit_button("Crear Grupo"):
                id_materia = int(materia_sel.split(" - ")[0])
                id_maestro = int(maestro_sel.split(" - ")[0]) if maestro_sel != "Sin asignar" else None

                try:
                    # Crear el grupo
                    cursor.execute("""
                        SELECT nombre_grupo 
                        FROM grupo 
                        WHERE id_materia = %s AND periodo = %s 
                        ORDER BY nombre_grupo DESC LIMIT 1
                    """, (id_materia, periodo))
                    ultimo = cursor.fetchone()

                    materia_nombre = materia_sel.split(" - ")[1].strip().upper()
                    palabras = materia_nombre.split()
                    codigo_base = "-".join([p[:3] for p in palabras if len(p) > 2])

                    if ultimo and ultimo[0].startswith(codigo_base):
                        ultima_letra = ultimo[0][-1]
                        siguiente_letra = chr(ord(ultima_letra) + 1)
                        nombre_grupo = f"{codigo_base}-{siguiente_letra}"
                    else:
                        nombre_grupo = f"{codigo_base}-A"

                    cursor.execute("""
                        INSERT INTO grupo (id_materia, id_maestro, nombre_grupo, periodo)
                        VALUES (%s, %s, %s, %s) RETURNING id_grupo
                    """, (id_materia, id_maestro, nombre_grupo, periodo))
                    id_grupo_nuevo = cursor.fetchone()[0]

                    # ==================== CREAR 3 UNIDADES AUTOMÁTICAMENTE ====================
                    for num in range(1, 4):
                        cursor.execute("""
                            INSERT INTO unidad (id_grupo, numero, nombre)
                            VALUES (%s, %s, %s)
                        """, (id_grupo_nuevo, num, f"Unidad {num}"))

                    conn.commit()
                    st.success(f"Grupo **{nombre_grupo}** creado correctamente con 3 unidades")
                    time.sleep(1.5)
                    st.rerun()

                except Exception as e:
                    conn.rollback()
                    st.error(f"Error al crear grupo: {e}")
    # ===================== INSCRIPCIONES =====================
    with tab3:
        st.subheader("Gestión de Inscripciones")

        cursor.execute("SELECT id_grupo, nombre_grupo, periodo FROM grupo ORDER BY periodo DESC, nombre_grupo")
        grupos = cursor.fetchall()
        grupo_sel = st.selectbox("Selecciona Grupo", 
                                [f"{g[0]} - {g[1]} ({g[2]})" for g in grupos])
        id_grupo = int(grupo_sel.split(" - ")[0])

        # ===================== ALUMNOS INSCRITOS =====================
        st.subheader("Alumnos inscritos")
        cursor.execute("""
            SELECT i.id_inscripcion, a.matricula, a.nombre, a.apellido_paterno, a.apellido_materno
            FROM inscripcion i
            JOIN alumno a ON i.id_alumno = a.id_alumno
            WHERE i.id_grupo = %s
            ORDER BY a.nombre
        """, (id_grupo,))
        inscritos_data = cursor.fetchall()
        
        df_inscritos = pd.DataFrame(inscritos_data, 
                                   columns=["id_inscripcion", "Matrícula", "Nombre", "Apellido Paterno", "Apellido Materno"])
        
        st.dataframe(df_inscritos.drop(columns=["id_inscripcion"]), 
                    use_container_width=True, hide_index=True)

        # ===================== DAR DE BAJA =====================
        if not df_inscritos.empty:
            st.divider()
            st.subheader("Dar de baja (desinscribir)")

            with st.form("dar_baja_form", clear_on_submit=True):
                # Multiselect para dar de baja
                baja_options = [
                    f"{row[0]} - {row[1]} - {row[2]} {row[3]}" 
                    for row in inscritos_data
                ]
                
                alumnos_baja = st.multiselect(
                    "Selecciona alumno(s) para dar de baja",
                    options=baja_options,
                    default=[]
                )

                if st.form_submit_button("Dar de Baja", type="secondary"):
                    if not alumnos_baja:
                        st.warning("Debes seleccionar al menos un alumno")
                    else:
                        exito = 0
                        for alum_str in alumnos_baja:
                            id_inscripcion = int(alum_str.split(" - ")[0])
                            try:
                                cursor.execute("""
                                    DELETE FROM inscripcion 
                                    WHERE id_inscripcion = %s
                                """, (id_inscripcion,))
                                exito += 1
                            except Exception:
                                pass  # Si falla uno, continuamos con los demás

                        conn.commit()
                        if exito > 0:
                            st.success(f"Se dieron de baja {exito} alumno(s) correctamente")
                        time.sleep(1.5)
                        st.rerun()

        # ===================== INSCRIBIR NUEVOS ALUMNOS =====================
        st.divider()
        st.subheader("Inscribir nuevos alumnos")
        with st.form("inscribir_alumnos", clear_on_submit=True):
            cursor.execute("""
                SELECT id_alumno, matricula, nombre, apellido_paterno, apellido_materno 
                FROM alumno 
                ORDER BY nombre
            """)
            alumnos = cursor.fetchall()

            alumnos_sel = st.multiselect(
                "Selecciona uno o varios alumnos para inscribir",
                options=[f"{a[0]} - {a[1]} - {a[2]} {a[3]}" for a in alumnos],
                default=[]
            )

            if st.form_submit_button("Inscribir Alumnos Seleccionados"):
                if not alumnos_sel:
                    st.warning("Debes seleccionar al menos un alumno")
                else:
                    exito = 0
                    duplicados = 0
                    for alum_str in alumnos_sel:
                        id_alumno = int(alum_str.split(" - ")[0])
                        try:
                            cursor.execute("""
                                INSERT INTO inscripcion (id_alumno, id_grupo)
                                VALUES (%s, %s)
                            """, (id_alumno, id_grupo))
                            exito += 1
                        except Exception:
                            duplicados += 1

                    conn.commit()
                    if exito > 0:
                        st.success(f"Se inscribieron {exito} alumno(s) correctamente")
                    if duplicados > 0:
                        st.warning(f"{duplicados} alumno(s) ya estaban inscritos")
                    time.sleep(1.5)
                    st.rerun()
    # ===================== EDITAR / ELIMINAR =====================
    with tab4:
        st.subheader("Editar o Eliminar Grupo")

        cursor.execute("""
            SELECT g.id_grupo, m.nombre as materia, g.nombre_grupo, g.periodo,
                   COALESCE(maestro.nombre || ' ' || maestro.apellido_paterno, 'Sin maestro') as maestro
            FROM grupo g
            JOIN materia m ON g.id_materia = m.id_materia
            LEFT JOIN maestro ON g.id_maestro = maestro.id_maestro
            ORDER BY g.periodo DESC, m.nombre, g.nombre_grupo
        """)
        grupos = cursor.fetchall()

        if grupos:
            seleccion = st.selectbox("Selecciona grupo", 
                                    [f"{g[0]} - {g[1]} - {g[2]} ({g[3]})" for g in grupos])
            id_grupo = int(seleccion.split(" - ")[0])

            cursor.execute("""
                SELECT g.nombre_grupo, g.periodo, g.id_maestro, m.nombre as materia
                FROM grupo g
                JOIN materia m ON g.id_materia = m.id_materia
                WHERE g.id_grupo = %s
            """, (id_grupo,))
            datos = cursor.fetchone()

            with st.form("editar_grupo"):
                nuevo_nombre = st.text_input("Nombre del Grupo", value=datos[0])
                
                cursor.execute("SELECT id_maestro, nombre, apellido_paterno FROM maestro ORDER BY nombre")
                maestros = cursor.fetchall()
                maestro_actual = datos[2]
                maestro_options = [f"{ma[0]} - {ma[1]} {ma[2]}" for ma in maestros] + ["Sin asignar"]
                maestro_sel = st.selectbox("Maestro", maestro_options, 
                                          index=next((i for i, opt in enumerate(maestro_options) if str(maestro_actual) in opt), 0))

                nuevo_periodo = st.text_input("Periodo", value=datos[1])

                col1, col2 = st.columns(2)
                with col1:
                    if st.form_submit_button("Guardar cambios"):
                        try:
                            id_maestro_nuevo = int(maestro_sel.split(" - ")[0]) if maestro_sel != "Sin asignar" else None
                            cursor.execute("""
                                UPDATE grupo 
                                SET nombre_grupo = %s, 
                                    id_maestro = %s,
                                    periodo = %s
                                WHERE id_grupo = %s
                            """, (nuevo_nombre.strip().upper(), id_maestro_nuevo, nuevo_periodo, id_grupo))
                            conn.commit()
                            st.success("Grupo actualizado correctamente")
                            time.sleep(1.5)
                            st.rerun()
                        except Exception as e:
                            conn.rollback()
                            st.error(f"Error al actualizar: {e}")

                with col2:
                    if st.form_submit_button("Eliminar Grupo", type="secondary"):
                        cursor.execute("SELECT COUNT(*) FROM inscripcion WHERE id_grupo = %s", (id_grupo,))
                        inscritos = cursor.fetchone()[0]

                        if inscritos > 0:
                            st.error(f"No se puede eliminar. Este grupo tiene {inscritos} alumno(s) inscrito(s).")
                        else:
                            if st.checkbox("¿Estás seguro de eliminar este grupo? Esta acción es irreversible."):
                                try:
                                    cursor.execute("DELETE FROM grupo WHERE id_grupo = %s", (id_grupo,))
                                    conn.commit()
                                    st.success("Grupo eliminado correctamente")
                                    time.sleep(1.5)
                                    st.rerun()
                                except Exception as e:
                                    conn.rollback()
                                    st.error("Error al eliminar el grupo")
# ===================== UNIDADES =====================
elif pagina == "Unidades":
    st.title("Gestión de Unidades")

    tab1, tab2, tab3 = st.tabs(["Ver todas las Unidades", "Crear Nueva Unidad", "Editar / Eliminar"])

    # ===================== VER TODAS =====================
    with tab1:
        st.subheader("Lista de Unidades")
        cursor.execute("""
            SELECT 
                u.id_unidad,
                g.nombre_grupo AS grupo,
                m.nombre AS materia,
                u.numero,
                u.nombre,
                COUNT(c.id_config_evaluacion) AS actividades
            FROM unidad u
            JOIN grupo g ON u.id_grupo = g.id_grupo
            JOIN materia m ON g.id_materia = m.id_materia
            LEFT JOIN config_evaluacion c ON c.id_unidad = u.id_unidad
            GROUP BY u.id_unidad, g.nombre_grupo, m.nombre, u.numero, u.nombre
            ORDER BY g.nombre_grupo, u.numero
        """)
        df = pd.DataFrame(cursor.fetchall(), 
                         columns=["ID", "Grupo", "Materia", "Número", "Nombre de Unidad", "Actividades"])
        st.dataframe(df, use_container_width=True, hide_index=True)

        # ===================== CREAR NUEVA UNIDAD =====================
    with tab2:
        st.subheader("Crear Nueva Unidad")
        with st.form("nueva_unidad", clear_on_submit=True):
            cursor.execute("""
                SELECT g.id_grupo, g.nombre_grupo, m.nombre 
                FROM grupo g
                JOIN materia m ON g.id_materia = m.id_materia
                ORDER BY g.nombre_grupo
            """)
            grupos = cursor.fetchall()

            grupo_sel = st.selectbox("Grupo", [f"{g[0]} - {g[1]} ({g[2]})" for g in grupos])
            numero = st.number_input("Número de Unidad", min_value=1, max_value=10, value=1, step=1)
            nombre_unidad = st.text_input("Nombre de la Unidad", value=f"Unidad {numero}")

            if st.form_submit_button("Crear Unidad"):
                id_grupo = int(grupo_sel.split(" - ")[0])

                # ===================== VALIDACIÓN: Número duplicado =====================
                cursor.execute("""
                    SELECT COUNT(*) 
                    FROM unidad 
                    WHERE id_grupo = %s AND numero = %s
                """, (id_grupo, numero))
                existe = cursor.fetchone()[0]

                if existe > 0:
                    st.error(f"Ya existe una Unidad {numero} en este grupo. Elige otro número.")
                elif not nombre_unidad.strip():
                    st.warning("Debes ingresar un nombre para la unidad")
                else:
                    try:
                        cursor.execute("""
                            INSERT INTO unidad (id_grupo, numero, nombre)
                            VALUES (%s, %s, %s)
                        """, (id_grupo, numero, nombre_unidad.strip()))
                        conn.commit()
                        st.success(f"Unidad {numero} creada correctamente")
                        time.sleep(1.5)
                        st.rerun()
                    except Exception as e:
                        conn.rollback()
                        st.error(f"Error al crear unidad: {e}")
    # ===================== EDITAR / ELIMINAR =====================
    with tab3:
        st.subheader("Editar o Eliminar Unidad")
        cursor.execute("""
            SELECT u.id_unidad, g.nombre_grupo, u.numero, u.nombre, COUNT(c.id_config_evaluacion) as actividades
            FROM unidad u
            JOIN grupo g ON u.id_grupo = g.id_grupo
            LEFT JOIN config_evaluacion c ON c.id_unidad = u.id_unidad
            GROUP BY u.id_unidad, g.nombre_grupo, u.numero, u.nombre
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
                nuevo_numero = st.number_input("Número de Unidad", min_value=1, max_value=10, value=datos[0])
                nuevo_nombre = st.text_input("Nombre de la Unidad", value=datos[1] or "")

                col1, col2 = st.columns(2)
                with col1:
                    if st.form_submit_button("Guardar cambios"):
                        try:
                            cursor.execute("""
                                UPDATE unidad 
                                SET numero = %s, nombre = %s
                                WHERE id_unidad = %s
                            """, (nuevo_numero, nuevo_nombre.strip() or None, id_unidad))
                            conn.commit()
                            st.success("Unidad actualizada correctamente")
                            time.sleep(1.5)
                            st.rerun()
                        except Exception as e:
                            conn.rollback()
                            st.error(f"Error al actualizar: {e}")

                with col2:
                    if st.form_submit_button("Eliminar Unidad", type="secondary"):
                        cursor.execute("SELECT COUNT(*) FROM config_evaluacion WHERE id_unidad = %s", (id_unidad,))
                        actividades = cursor.fetchone()[0]
                        if actividades > 0:
                            st.error(f"No se puede eliminar. Esta unidad tiene {actividades} actividad(es) configurada(s).")
                        else:
                            if st.checkbox("¿Estás seguro de eliminar esta unidad?"):
                                try:
                                    cursor.execute("DELETE FROM unidad WHERE id_unidad = %s", (id_unidad,))
                                    conn.commit()
                                    st.success("Unidad eliminada correctamente")
                                    time.sleep(1.5)
                                    st.rerun()
                                except Exception as e:
                                    conn.rollback()
                                    st.error("Error al eliminar")
# ===================== ACTIVIDADES Y CALIFICACIONES =====================
elif pagina == "Actividades y Calificaciones":
    st.title("Actividades y Calificaciones")

    # ===================== LISTA DE GRUPOS =====================
    if st.session_state.get("grupo_seleccionado") is None:
            st.subheader("Mis Grupos")

            busqueda = st.text_input("Buscar grupo", placeholder="Escribe nombre del grupo...").strip().lower()

            if st.session_state.rol_actual == "Alumno":
                # Alumno solo ve sus grupos inscritos
                cursor.execute("""
                    SELECT g.id_grupo, g.nombre_grupo, g.periodo 
                    FROM grupo g
                    JOIN inscripcion i ON i.id_grupo = g.id_grupo
                    WHERE i.id_alumno = %s
                    ORDER BY g.periodo DESC, g.nombre_grupo
                """, (st.session_state.usuario['id'],))
            else:
                # Maestro y Admin ven todos (o los suyos)
                if st.session_state.rol_actual == "Maestro":
                    cursor.execute("""
                        SELECT id_grupo, nombre_grupo, periodo 
                        FROM grupo 
                        WHERE id_maestro = %s 
                        ORDER BY periodo DESC, nombre_grupo
                    """, (st.session_state.maestro_id,))
                else:
                    cursor.execute("""
                        SELECT id_grupo, nombre_grupo, periodo 
                        FROM grupo 
                        ORDER BY periodo DESC, nombre_grupo
                    """)

            grupos = cursor.fetchall()

            if busqueda:
                grupos = [g for g in grupos if busqueda in g[1].lower()]

            if not grupos:
                st.info("No se encontraron grupos.")
            else:
                cols = st.columns(3)
                for idx, (id_grupo, nombre_grupo, periodo) in enumerate(grupos):
                    with cols[idx % 3]:
                        with st.container(border=True):
                            st.markdown(f"**{nombre_grupo}**")
                            st.caption(periodo)
                            if st.button("→ Ver Grupo", key=f"ver_grupo_{id_grupo}", use_container_width=True):
                                st.session_state.grupo_seleccionado = id_grupo
                                st.session_state.unidad_seleccionada = None
                                st.session_state.actividad_seleccionada = None
                                st.rerun()

    # ===================== VISTA INTERNA DEL GRUPO =====================
    elif st.session_state.get("unidad_seleccionada") is None:
        id_grupo = st.session_state.grupo_seleccionado
        cursor.execute("SELECT nombre_grupo, periodo FROM grupo WHERE id_grupo = %s", (id_grupo,))
        grupo_info = cursor.fetchone()

        if st.button("← Volver a Grupos"):
            st.session_state.grupo_seleccionado = None
            st.rerun()

        st.subheader(f"{grupo_info[0]} — {grupo_info[1]}")
        st.divider()
        st.subheader("Unidades")

        cursor.execute("""
            SELECT id_unidad, numero, nombre 
            FROM unidad 
            WHERE id_grupo = %s 
            ORDER BY numero
        """, (id_grupo,))
        unidades = cursor.fetchall()

        cols = st.columns(3)
        for idx, (id_unidad, numero, nombre) in enumerate(unidades):
            with cols[idx % 3]:
                with st.container(border=True):
                    st.markdown(f"**Unidad {numero}**")
                    st.caption(nombre or "Sin nombre")
                    if st.button("→ Ver Unidad", key=f"ver_unidad_{id_unidad}", use_container_width=True):
                        st.session_state.unidad_seleccionada = id_unidad
                        st.rerun()

    # ===================== VISTA INTERNA DE LA UNIDAD =====================
    elif st.session_state.get("actividad_seleccionada") is None:
        id_unidad = st.session_state.unidad_seleccionada

        # Información de la unidad
        cursor.execute("""
            SELECT u.numero, u.nombre, g.nombre_grupo, g.periodo
            FROM unidad u
            JOIN grupo g ON u.id_grupo = g.id_grupo
            WHERE u.id_unidad = %s
        """, (id_unidad,))
        unidad_info = cursor.fetchone()

        col_back, col_title = st.columns([0.8, 5])
        with col_back:
            if st.button("←"):
                st.session_state.unidad_seleccionada = None
                st.rerun()

        with col_title:
            st.subheader(f"Unidad {unidad_info[0]} - {unidad_info[1] or 'Sin nombre'}")
            st.caption(f"{unidad_info[2]} — {unidad_info[3]}")

        st.divider()

        # ===================== BOTÓN SUBIR NUEVA ACTIVIDAD (Solo Maestro/Admin) =====================
        if st.session_state.rol_actual in ["Admin", "Maestro"]:
            if st.button("Subir Nueva Actividad", type="primary", use_container_width=True):
                st.session_state.modo_nueva_actividad = True
                st.rerun()

        st.subheader("Actividades")

        cursor.execute("""
            SELECT c.id_config_evaluacion, a.nombre, crit.nombre as criterio, 
                   c.fecha_final
            FROM config_evaluacion c
            JOIN actividad a ON c.id_actividad = a.id_actividad
            LEFT JOIN criterio crit ON c.id_criterio = crit.id_criterio
            WHERE c.id_unidad = %s
            ORDER BY a.nombre
        """, (id_unidad,))
        actividades = cursor.fetchall()

        if not actividades:
            st.info("Aún no hay actividades configuradas en esta unidad.")
        else:
            cols = st.columns(2)
            for idx, (id_config, nombre_act, criterio, fecha_final) in enumerate(actividades):
                with cols[idx % 2]:
                    with st.container(border=True):
                        st.markdown(f"**{nombre_act}**")
                        st.caption(f"Criterio: {criterio or 'Sin criterio'}")
                        
                        if fecha_final:
                            st.caption(f"Fecha Final: {fecha_final.strftime('%d/%m/%Y %H:%M')}")
                        else:
                            st.caption("Fecha Final: Sin límite")

                        # Botones solo para Maestro/Admin
                        if st.session_state.rol_actual in ["Admin", "Maestro"]:
                            col_edit, col_arrow = st.columns([1, 1])
                            with col_edit:
                                if st.button("Editar", key=f"edit_act_{id_config}", use_container_width=True):
                                    st.session_state.edit_id = id_config
                                    st.session_state.edit_nombre = nombre_act
                                    st.rerun()
                            with col_arrow:
                                if st.button("→", key=f"ver_act_{id_config}", use_container_width=True):
                                    st.session_state.actividad_seleccionada = id_config
                                    st.rerun()
                        else:
                            # Para Alumno solo muestra flecha
                            if st.button("→ Ver Actividad", key=f"ver_act_{id_config}", use_container_width=True):
                                st.session_state.actividad_seleccionada = id_config
                                st.rerun()
        # ===================== FORMULARIO DE EDICIÓN =====================
        if 'edit_id' in st.session_state:
            st.divider()
            st.subheader("Editar Actividad")

            with st.form("editar_actividad"):
                nuevo_nombre = st.text_input("Nombre de la actividad", value=st.session_state.edit_nombre)

                # Cargar criterios de la unidad
                cursor.execute("""
                    SELECT c.id_criterio, c.nombre 
                    FROM criterio c
                    JOIN criterio_unidad cu ON cu.id_criterio = c.id_criterio
                    WHERE cu.id_unidad = %s AND cu.ponderacion > 0
                    ORDER BY c.nombre
                """, (id_unidad,))
                crit_list = cursor.fetchall()

                criterio_sel = st.selectbox(
                    "Criterio", 
                    [f"{c[0]} - {c[1]}" for c in crit_list] if crit_list else []
                )

                # Cargar descripción actual
                cursor.execute("SELECT descripcion FROM actividad WHERE id_actividad = (SELECT id_actividad FROM config_evaluacion WHERE id_config_evaluacion = %s)", 
                             (st.session_state.edit_id,))
                desc_actual = cursor.fetchone()
                descripcion = st.text_area("Descripción / Instrucciones", 
                                         value=desc_actual[0] if desc_actual and desc_actual[0] else "")

                nuevo_archivo = st.file_uploader("Subir nuevo archivo (reemplaza el anterior)", 
                                               type=["pdf", "docx", "jpg", "png", "zip"])

                col_f1, col_f2 = st.columns(2)
                with col_f1:
                    fecha_inicio = st.date_input("Fecha de Inicio", value=date.today())
                with col_f2:
                    fecha_final = st.date_input("Fecha Final (Límite)", value=date.today())

                col1, col2 = st.columns(2)
                with col1:
                    if st.form_submit_button("Guardar cambios"):
                        if not criterio_sel:
                            st.error("Debes seleccionar un criterio")
                        else:
                            id_criterio = int(criterio_sel.split(" - ")[0])
                            try:
                                # Actualizar config_evaluacion
                                cursor.execute("""
                                    UPDATE config_evaluacion 
                                    SET id_criterio = %s,
                                        fecha_inicio = %s,
                                        fecha_final = %s
                                    WHERE id_config_evaluacion = %s
                                """, (id_criterio, fecha_inicio, fecha_final, st.session_state.edit_id))

                                # Actualizar actividad (nombre + descripción)
                                cursor.execute("""
                                    UPDATE actividad 
                                    SET nombre = %s,
                                        descripcion = %s
                                    WHERE id_actividad = (
                                        SELECT id_actividad 
                                        FROM config_evaluacion 
                                        WHERE id_config_evaluacion = %s
                                    )
                                """, (nuevo_nombre.strip(), descripcion.strip(), st.session_state.edit_id))

                                conn.commit()
                                st.success("Actividad actualizada correctamente")
                                time.sleep(1.5)
                                del st.session_state.edit_id
                                del st.session_state.edit_nombre
                                st.rerun()
                            except Exception as e:
                                conn.rollback()
                                st.error(f"Error al guardar: {e}")

                with col2:
                    if st.form_submit_button("Cancelar"):
                        del st.session_state.edit_id
                        del st.session_state.edit_nombre
                        st.rerun()
        # ===================== FORMULARIO NUEVA ACTIVIDAD =====================
        if st.session_state.get("modo_nueva_actividad"):
            st.divider()
            st.subheader("Nueva Actividad")
            with st.form("agregar_actividad", clear_on_submit=True):
                col1, col2 = st.columns(2)
                with col1:
                    nombre_actividad = st.text_input("Nombre de la actividad *", "")
                with col2:
                    cursor.execute("""
                        SELECT c.id_criterio, c.nombre 
                        FROM criterio c
                        JOIN criterio_unidad cu ON cu.id_criterio = c.id_criterio
                        WHERE cu.id_unidad = %s AND cu.ponderacion > 0
                        ORDER BY c.nombre
                    """, (id_unidad,))
                    criterios = cursor.fetchall()
                    criterio_sel = st.selectbox("Asignar a criterio *", 
                                              [f"{c[0]} - {c[1]}" for c in criterios] if criterios else [])

                descripcion = st.text_area("Descripción / Instrucciones (opcional)", "")
                archivo = st.file_uploader("Subir archivo", type=["pdf", "docx", "jpg", "png"])

                col_f1, col_f2 = st.columns(2)
                with col_f1:
                    fecha_inicio = st.date_input("Fecha de Inicio", value=date.today())
                with col_f2:
                    fecha_final = st.date_input("Fecha Final", value=date.today())

                col_guardar, col_cancelar = st.columns(2)
                with col_guardar:
                    if st.form_submit_button("Agregar Actividad"):
                        if not nombre_actividad.strip():
                            st.error("Debes escribir el nombre de la actividad")
                        elif not criterio_sel:
                            st.error("Debes seleccionar un criterio")
                        else:
                            id_criterio = int(criterio_sel.split(" - ")[0])
                            try:
                                cursor.execute("""
                                    INSERT INTO actividad (nombre, descripcion) 
                                    VALUES (%s, %s) RETURNING id_actividad
                                """, (nombre_actividad.strip(), descripcion.strip()))
                                id_actividad = cursor.fetchone()[0]

                                cursor.execute("""
                                    INSERT INTO config_evaluacion 
                                    (id_unidad, id_actividad, id_criterio, fecha_inicio, fecha_final)
                                    VALUES (%s, %s, %s, %s, %s)
                                """, (id_unidad, id_actividad, id_criterio, fecha_inicio, fecha_final))
                                conn.commit()
                                st.success("Actividad agregada correctamente")
                                time.sleep(1.5)
                                st.session_state.modo_nueva_actividad = False
                                st.rerun()
                            except Exception as e:
                                conn.rollback()
                                st.error(f"Error: {e}")

                with col_cancelar:
                    if st.form_submit_button("Cancelar"):
                        st.session_state.modo_nueva_actividad = False
                        st.rerun()
    # ===================== VISTA INTERNA DE LA ACTIVIDAD =====================
    else:
        id_config = st.session_state.actividad_seleccionada

        # Información completa de la actividad
        cursor.execute("""
            SELECT a.nombre, 
                   crit.nombre as criterio, 
                   a.descripcion,
                   c.fecha_inicio, 
                   c.fecha_final
            FROM config_evaluacion c
            JOIN actividad a ON c.id_actividad = a.id_actividad
            LEFT JOIN criterio crit ON c.id_criterio = crit.id_criterio
            WHERE c.id_config_evaluacion = %s
        """, (id_config,))
        act_info = cursor.fetchone()

        col_back, col_title = st.columns([0.8, 5])
        with col_back:
            if st.button("←"):
                st.session_state.actividad_seleccionada = None
                st.rerun()

        with col_title:
            st.subheader(act_info[0])
            inicio = act_info[3].strftime('%d/%m/%Y %H:%M') if act_info[3] else 'Sin fecha'
            final = act_info[4].strftime('%d/%m/%Y %H:%M') if act_info[4] else 'Sin límite'
            st.caption(f"Criterio: {act_info[1] or 'Sin criterio'} | Inicio: {inicio} | Final: {final}")

        # Mostrar descripción (visible para todos los roles)
        if act_info[2]:
            st.markdown("**Descripción / Instrucciones:**")
            st.write(act_info[2])
        else:
            st.caption("Sin descripción registrada para esta actividad.")

        st.divider()

        # ===================== VISTA PARA ALUMNO =====================
        if st.session_state.rol_actual == "Alumno":
            st.subheader("Entregar Actividad")

            cursor.execute("""
                SELECT calificacion, observacion, entrega_texto, estado
                FROM resultado 
                WHERE id_config_evaluacion = %s AND id_alumno = %s
            """, (id_config, st.session_state.usuario['id']))
            entrega = cursor.fetchone()

            if entrega and entrega[3] == 'calificado':
                st.success("Esta actividad ya fue calificada.")
                st.metric("Tu Calificación", entrega[0] if entrega[0] is not None else "Sin calificar")
                
                st.write("**Observación del profesor:**")
                st.text_area("", value=entrega[1] or "Sin observación", disabled=True, height=100)
                
                st.write("**Tu entrega anterior:**")
                st.text_area("", value=entrega[2] or "Sin texto entregado", disabled=True, height=120)
            else:
                entrega_texto = st.text_area("Escribe tu entrega aquí (comentario al profesor)", height=150)
                entrega_archivo = st.file_uploader("Subir archivo (opcional)", type=["pdf", "docx", "jpg", "png", "zip"])

                if st.button("Enviar Actividad", type="primary", use_container_width=True):
                    try:
                        cursor.execute("""
                            INSERT INTO resultado 
                            (id_config_evaluacion, id_alumno, entrega_texto, estado)
                            VALUES (%s, %s, %s, 'entregado')
                            ON CONFLICT (id_config_evaluacion, id_alumno) 
                            DO UPDATE SET entrega_texto = %s, estado = 'entregado'
                        """, (id_config, st.session_state.usuario['id'], entrega_texto, entrega_texto))
                        conn.commit()
                        st.success("Actividad enviada correctamente")
                        time.sleep(1.5)
                        st.rerun()
                    except Exception as e:
                        conn.rollback()
                        st.error(f"Error al enviar: {e}")

        # ===================== VISTA PARA MAESTRO / ADMIN =====================
        else:
            # Resumen superior
            cursor.execute("""
                SELECT 
                    COUNT(*) as total,
                    COUNT(CASE WHEN r.estado IN ('entregado', 'calificado') THEN 1 END) as entregados,
                    COUNT(CASE WHEN r.estado = 'pendiente' THEN 1 END) as pendientes
                FROM inscripcion i
                LEFT JOIN resultado r ON r.id_alumno = i.id_alumno 
                    AND r.id_config_evaluacion = %s
                WHERE i.id_grupo = (SELECT id_grupo FROM unidad WHERE id_unidad = %s)
            """, (id_config, st.session_state.unidad_seleccionada))
            resumen = cursor.fetchone()

            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Total Alumnos", resumen[0])
            with col2:
                st.metric("Entregados", resumen[1] or 0)
            with col3:
                st.metric("Pendientes", resumen[2] or 0)

            filtro = st.selectbox("Mostrar", ["Todos", "Entregados", "Pendientes"], index=0)

            st.subheader("Lista de Alumnos")

            cursor.execute("""
                SELECT 
                    a.id_alumno,
                    a.matricula,
                    a.nombre || ' ' || a.apellido_paterno || ' ' || COALESCE(a.apellido_materno, '') as alumno,
                    r.calificacion,
                    r.observacion,
                    r.entrega_texto,
                    r.estado,
                    r.fecha_registro
                FROM inscripcion i
                JOIN alumno a ON i.id_alumno = a.id_alumno
                LEFT JOIN resultado r ON r.id_alumno = a.id_alumno 
                    AND r.id_config_evaluacion = %s
                WHERE i.id_grupo = (SELECT id_grupo FROM unidad WHERE id_unidad = %s)
                ORDER BY a.nombre
            """, (id_config, st.session_state.unidad_seleccionada))
            data = cursor.fetchall()

            df = pd.DataFrame(data, columns=["id_alumno", "Matrícula", "Alumno", "Calificación", "Observación", "Entrega Alumno", "Estado", "Fecha Entrega"])

            if filtro == "Entregados":
                df = df[df["Estado"].isin(['entregado', 'calificado'])]
            elif filtro == "Pendientes":
                df = df[df["Estado"] == 'pendiente']

            # ===================== EXPANDERS POR ALUMNO =====================
            for _, row in df.iterrows():
                with st.expander(f"{row['Alumno']} — {row['Matrícula']}"):
                    col1, col2 = st.columns([1, 2])
                    
                    with col1:
                        cursor.execute("""
                            SELECT COALESCE(cu.ponderacion, 0) 
                            FROM config_evaluacion c
                            LEFT JOIN criterio_unidad cu ON cu.id_criterio = c.id_criterio 
                                AND cu.id_unidad = %s
                            WHERE c.id_config_evaluacion = %s
                        """, (st.session_state.unidad_seleccionada, id_config))
                        ponderacion = cursor.fetchone()[0] or 0.0

                        calif = st.number_input(
                            f"Calificación ({ponderacion}%)",
                            min_value=0.0,
                            max_value=100.0,
                            value=float(row["Calificación"]) if pd.notna(row["Calificación"]) else 0.0,
                            step=0.5,
                            key=f"calif_{row['id_alumno']}"
                        )
                    
                    with col2:
                        obs = st.text_area(
                            "Observación (visible para el alumno)",
                            value=row["Observación"] or "",
                            key=f"obs_{row['id_alumno']}",
                            height=70
                        )

                    st.write("**Entrega del alumno:**")
                    if row["Entrega Alumno"]:
                        st.text_area(
                            "Texto entregado", 
                            value=row["Entrega Alumno"], 
                            disabled=True, 
                            height=100,
                            key=f"ver_texto_{row['id_alumno']}"
                        )
                    else:
                        st.info("El alumno aún no ha entregado nada.")

                    if st.button("Guardar calificación de este alumno", key=f"save_{row['id_alumno']}", use_container_width=True):
                        try:
                            cursor.execute("""
                                INSERT INTO resultado (id_config_evaluacion, id_alumno, calificacion, observacion, estado)
                                VALUES (%s, %s, %s, %s, 'calificado')
                                ON CONFLICT (id_config_evaluacion, id_alumno) 
                                DO UPDATE SET calificacion = %s, observacion = %s, estado = 'calificado'
                            """, (id_config, row['id_alumno'], calif, obs, calif, obs))
                            conn.commit()
                            st.success("Calificación guardada correctamente")
                            time.sleep(1.0)
                            st.rerun()
                        except Exception as e:
                            conn.rollback()
                            st.error(f"Error al guardar: {e}")
# ===================== CALIFICACIONES =====================
elif pagina == "Calificaciones":
    st.title("Calificaciones")
    st.markdown("**Transparencia matemática completa** – Cálculo por criterio y promedio final")

    # Filtrar grupos según rol
    if st.session_state.rol_actual == "Maestro" and 'maestro_id' in st.session_state:
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
        st.warning("No hay grupos disponibles.")
    else:
        grupo_sel = st.selectbox("Grupo", [f"{g[0]} - {g[1]}" for g in grupos])
        id_grupo = int(grupo_sel.split(" - ")[0])

        tab1, tab2 = st.tabs(["Cálculo por Alumno", "Desglose General del Grupo"])

        # ===================== TAB 1: CÁLCULO POR ALUMNO =====================
        with tab1:
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

                st.subheader(f"Cálculos académicos de {alumno_sel.split(' - ')[2]}")

                # Verificar si ya está bloqueado
                cursor.execute("""
                    SELECT EXISTS (
                        SELECT 1 FROM calificacion_final 
                        WHERE id_inscripcion IN (
                            SELECT id_inscripcion FROM inscripcion 
                            WHERE id_alumno = %s AND id_grupo = %s
                        )
                        AND locked = TRUE
                    )
                """, (id_alumno, id_grupo))
                esta_bloqueado = cursor.fetchone()[0]

                calif_unidades = []

                cursor.execute("""
                    SELECT id_unidad, numero, nombre 
                    FROM unidad 
                    WHERE id_grupo = %s 
                    ORDER BY numero
                """, (id_grupo,))
                unidades = cursor.fetchall()

                for id_unidad, numero, nombre_unidad in unidades:
                    with st.expander(f"Unidad {numero} — {nombre_unidad or 'Sin nombre'}", expanded=True):
                        
                        cursor.execute("""
                            SELECT crit.nombre as criterio,
                                   COALESCE(AVG(r.calificacion), 0) as promedio_criterio,
                                   COALESCE(cu.ponderacion, 0) as ponderacion
                            FROM config_evaluacion c
                            JOIN criterio crit ON c.id_criterio = crit.id_criterio
                            LEFT JOIN resultado r ON r.id_config_evaluacion = c.id_config_evaluacion 
                                AND r.id_alumno = %s
                            LEFT JOIN criterio_unidad cu ON cu.id_criterio = c.id_criterio 
                                AND cu.id_unidad = %s
                            WHERE c.id_unidad = %s
                            GROUP BY crit.nombre, cu.ponderacion
                            ORDER BY crit.nombre
                        """, (id_alumno, id_unidad, id_unidad))
                        resultados = cursor.fetchall()

                        total_unidad = 0.0
                        for criterio, prom_crit, peso in resultados:
                            contrib = float(prom_crit) * (float(peso) / 100)
                            total_unidad += contrib
                            st.write(f"**{criterio}** → {prom_crit:.2f} × {peso}% = **{contrib:.2f}**")

                        # Obtener valor guardado
                        cursor.execute("""
                            SELECT calif_final 
                            FROM calificacion_final 
                            WHERE id_inscripcion IN (
                                SELECT id_inscripcion FROM inscripcion 
                                WHERE id_alumno = %s AND id_grupo = %s
                            )
                            AND id_unidad = %s
                        """, (id_alumno, id_grupo, id_unidad))
                        row = cursor.fetchone()
                        valor_guardado = float(row[0]) if row and row[0] is not None else total_unidad

                        if esta_bloqueado:
                            st.success(f"**Calificación Final Unidad:** {valor_guardado:.2f} (Bloqueada)")
                            calif_unidades.append(valor_guardado)
                        else:
                            nueva_calif = st.number_input(
                                "Calificación Final de la Unidad",
                                min_value=0.0,
                                max_value=100.0,
                                value=valor_guardado,
                                step=0.5,
                                key=f"ajuste_{id_alumno}_{id_unidad}"
                            )
                            calif_unidades.append(nueva_calif)

                # ===================== GUARDAR TODO =====================
                if calif_unidades and not esta_bloqueado:
                    st.divider()
                    st.subheader("Calificación Final de la Materia")
                    promedio_final = sum(calif_unidades) / len(calif_unidades)

                    if promedio_final < 70:
                        st.error(f"**Calificación Final de la Materia:** {promedio_final:.2f}")
                    else:
                        st.success(f"**Calificación Final de la Materia:** {promedio_final:.2f}")

                    if st.button("Guardar Todas las Calificaciones", type="primary", use_container_width=True):
                        try:
                            for id_unidad, calif in zip([u[0] for u in unidades], calif_unidades):
                                cursor.execute("""
                                    INSERT INTO calificacion_final 
                                    (id_inscripcion, id_unidad, calif_calculada, calif_final, locked, es_modificada)
                                    SELECT i.id_inscripcion, %s, %s, %s, TRUE, TRUE
                                    FROM inscripcion i 
                                    WHERE i.id_alumno = %s AND i.id_grupo = %s
                                    ON CONFLICT (id_inscripcion, id_unidad)
                                    DO UPDATE SET 
                                        calif_calculada = %s,
                                        calif_final = %s,
                                        locked = TRUE,
                                        es_modificada = TRUE,
                                        fecha_modificacion = CURRENT_TIMESTAMP
                                """, (id_unidad, calif, calif, id_alumno, id_grupo, calif, calif))

                            # Calificación Final de la Materia
                            cursor.execute("""
                                INSERT INTO calificacion_final 
                                (id_inscripcion, id_unidad, calif_calculada, calif_final, locked, es_modificada)
                                SELECT i.id_inscripcion, NULL, %s, %s, TRUE, TRUE
                                FROM inscripcion i 
                                WHERE i.id_alumno = %s AND i.id_grupo = %s
                                ON CONFLICT (id_inscripcion, id_unidad)
                                DO UPDATE SET 
                                    calif_calculada = %s,
                                    calif_final = %s,
                                    locked = TRUE,
                                    es_modificada = TRUE,
                                    fecha_modificacion = CURRENT_TIMESTAMP
                            """, (promedio_final, promedio_final, id_alumno, id_grupo, promedio_final, promedio_final))

                            conn.commit()
                            st.success("Todas las calificaciones guardadas y bloqueadas correctamente")
                            time.sleep(1.5)
                            st.rerun()
                        except Exception as e:
                            conn.rollback()
                            st.error(f"Error al guardar: {e}")
        # ===================== TAB 2: DESGLOSE GENERAL DEL GRUPO =====================
        with tab2:
            st.subheader("Desglose General del Grupo")

            cursor.execute("""
                SELECT 
                    a.id_alumno,
                    a.matricula,
                    a.nombre || ' ' || a.apellido_paterno || ' ' || COALESCE(a.apellido_materno, '') as alumno,
                    COALESCE(cf1.calif_final, 0) as "Unidad 1",
                    COALESCE(cf2.calif_final, 0) as "Unidad 2",
                    COALESCE(cf3.calif_final, 0) as "Unidad 3",
                    COALESCE(cf_final.calif_final, 0) as "Calificación Final"
                FROM inscripcion i
                JOIN alumno a ON i.id_alumno = a.id_alumno
                LEFT JOIN calificacion_final cf1 ON cf1.id_inscripcion = i.id_inscripcion 
                    AND cf1.id_unidad = (SELECT id_unidad FROM unidad WHERE id_grupo = i.id_grupo AND numero = 1 LIMIT 1)
                LEFT JOIN calificacion_final cf2 ON cf2.id_inscripcion = i.id_inscripcion 
                    AND cf2.id_unidad = (SELECT id_unidad FROM unidad WHERE id_grupo = i.id_grupo AND numero = 2 LIMIT 1)
                LEFT JOIN calificacion_final cf3 ON cf3.id_inscripcion = i.id_inscripcion 
                    AND cf3.id_unidad = (SELECT id_unidad FROM unidad WHERE id_grupo = i.id_grupo AND numero = 3 LIMIT 1)
                LEFT JOIN calificacion_final cf_final ON cf_final.id_inscripcion = i.id_inscripcion 
                    AND cf_final.id_unidad IS NULL
                WHERE i.id_grupo = %s
                ORDER BY a.nombre
            """, (id_grupo,))
            data = cursor.fetchall()

            if not data:
                st.info("No hay calificaciones registradas aún.")
            else:
                df = pd.DataFrame(data, columns=[
                    "id_alumno", "Matrícula", "Alumno", 
                    "Unidad 1", "Unidad 2", "Unidad 3", 
                    "Calificación Final"
                ])

                st.dataframe(
                    df.drop(columns=["id_alumno"]),
                    use_container_width=True,
                    hide_index=True
                )

                # Estadísticas
                st.divider()
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Total Alumnos", len(df))
                with col2:
                    aprobados = (df["Calificación Final"] >= 70).sum() if not df.empty else 0
                    st.metric("Aprobados", aprobados)
                with col3:
                    prom = df["Calificación Final"].mean() if not df.empty else 0
                    st.metric("Promedio del Grupo", f"{prom:.2f}" if prom > 0 else "N/A")
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
# ===================== CRITERIOS DE EVALUACIÓN =====================
elif pagina == "Criterios de Evaluación":
    st.title("Criterios de Evaluación")
    st.markdown("**Gestiona los criterios y asigna pesos por unidad**")

    if st.session_state.rol_actual != "Admin":
        st.error("Solo el Administrador puede gestionar los criterios.")
    else:
        tab1, tab2, tab3 = st.tabs(["Ver Criterios", "Nuevo Criterio", "Asignar Pesos por Unidad"])

        # ===================== VER CRITERIOS =====================
        with tab1:
            st.subheader("Criterios existentes")
            cursor.execute("""
                SELECT id_criterio, nombre, descripcion 
                FROM criterio 
                ORDER BY nombre
            """)
            criterios = cursor.fetchall()

            if criterios:
                df = pd.DataFrame(criterios, columns=["ID", "Criterio", "Descripción"])
                st.dataframe(df, use_container_width=True, hide_index=True)
            else:
                st.info("Aún no hay criterios registrados.")

        # ===================== NUEVO CRITERIO =====================
        with tab2:
            st.subheader("Crear nuevo criterio")
            with st.form("nuevo_criterio", clear_on_submit=True):
                nombre = st.text_input("Nombre del criterio *", placeholder="Ej: Examen, Tareas, Participación")
                desc = st.text_area("Descripción (opcional)")

                if st.form_submit_button("Guardar Criterio"):
                    if not nombre.strip():
                        st.warning("El nombre del criterio es obligatorio")
                    else:
                        try:
                            cursor.execute("""
                                INSERT INTO criterio (nombre, descripcion)
                                VALUES (%s, %s)
                                ON CONFLICT (nombre) DO NOTHING
                            """, (nombre.strip().title(), desc.strip()))
                            conn.commit()
                            st.success("Criterio guardado correctamente")
                            time.sleep(1.5)
                            st.rerun()
                        except Exception as e:
                            conn.rollback()
                            st.error(f"Error al guardar: {e}")

        # ===================== ASIGNAR PESOS POR UNIDAD =====================
        with tab3:
            st.subheader("Asignar pesos por unidad")

            # Selector de Grupo
            cursor.execute("SELECT id_grupo, nombre_grupo FROM grupo ORDER BY nombre_grupo")
            grupos = cursor.fetchall()
            if not grupos:
                st.warning("No hay grupos creados aún.")
            else:
                grupo_sel = st.selectbox("Grupo", [f"{g[0]} - {g[1]}" for g in grupos])
                id_grupo = int(grupo_sel.split(" - ")[0])

                # Selector de Unidad
                cursor.execute("""
                    SELECT id_unidad, numero, nombre 
                    FROM unidad 
                    WHERE id_grupo = %s 
                    ORDER BY numero
                """, (id_grupo,))
                unidades = cursor.fetchall()

                if not unidades:
                    st.warning("Este grupo aún no tiene unidades.")
                else:
                    unidad_sel = st.selectbox(
                        "Unidad", 
                        [f"{u[0]} - Unidad {u[1]} ({u[2] or 'Sin nombre'})" for u in unidades]
                    )
                    id_unidad = int(unidad_sel.split(" - ")[0])

                    # Cargar criterios y pesos actuales
                    cursor.execute("""
                        SELECT c.id_criterio, c.nombre, COALESCE(cu.ponderacion, 0) as ponderacion
                        FROM criterio c
                        LEFT JOIN criterio_unidad cu ON cu.id_criterio = c.id_criterio 
                            AND cu.id_unidad = %s
                        ORDER BY c.nombre
                    """, (id_unidad,))
                    data = cursor.fetchall()

                    st.subheader("Pesos por criterio")

                    nuevos_pesos = {}
                    total = 0.0

                    for id_crit, nombre_crit, ponderacion in data:
                        col1, col2 = st.columns([3, 2])
                        with col1:
                            st.write(f"**{nombre_crit}**")
                        with col2:
                            peso = st.number_input(
                                "Peso (%)",
                                min_value=0.0,
                                max_value=100.0,
                                value=float(ponderacion),
                                step=0.5,
                                key=f"peso_{id_unidad}_{id_crit}"
                            )
                            nuevos_pesos[id_crit] = peso
                            total += peso

                    st.caption(f"**Suma actual de pesos: {total:.1f}%**")

                    if st.button("Guardar pesos de esta unidad", type="primary"):
                        if abs(total - 100) > 0.01:
                            st.error("La suma de los pesos debe ser exactamente 100%")
                        else:
                            try:
                                for id_crit, peso in nuevos_pesos.items():
                                    cursor.execute("""
                                        INSERT INTO criterio_unidad (id_unidad, id_criterio, ponderacion)
                                        VALUES (%s, %s, %s)
                                        ON CONFLICT (id_unidad, id_criterio)
                                        DO UPDATE SET ponderacion = %s
                                    """, (id_unidad, id_crit, peso, peso))
                                conn.commit()
                                st.success("Pesos guardados correctamente")
                                time.sleep(1.5)
                                st.rerun()
                            except Exception as e:
                                conn.rollback()
                                st.error(f"Error al guardar pesos: {e}")
# ===================== PERFIL =====================
elif st.session_state.pagina == "Perfil":
    st.title("Mi Perfil")

    # Determinar tabla y datos según rol
    if st.session_state.usuario['rol'] == "Maestro":
        cursor.execute("""
            SELECT nombre, apellido_paterno, apellido_materno, fecha_nacimiento,
                   telefono, email, especialidad, clave
            FROM maestro 
            WHERE id_maestro = %s
        """, (st.session_state.usuario['id'],))
        datos = cursor.fetchone()
        es_maestro = True
    else:  # Alumno
        cursor.execute("""
            SELECT nombre, apellido_paterno, apellido_materno, fecha_nacimiento,
                   email, matricula, nip, telefono
            FROM alumno 
            WHERE id_alumno = %s
        """, (st.session_state.usuario['id'],))
        datos = cursor.fetchone()
        es_maestro = False

    if not datos:
        st.error("No se encontraron tus datos.")
    else:
        nombre_completo = f"{datos[0]} {datos[1]} {datos[2] or ''}".strip()

        # ===================== VISTA PRINCIPAL =====================
        col_foto, col_info = st.columns([1, 3])
        
        with col_foto:
            avatar_url = f"https://ui-avatars.com/api/?name={nombre_completo.replace(' ', '+')}&background=2C3E50&color=fff&size=180&bold=true"
            st.image(avatar_url, width=180)

        with col_info:
            st.subheader(nombre_completo)
            
            if es_maestro:
                st.markdown(f"**ID:** `PROF-{str(st.session_state.usuario['id']).zfill(4)}`")
                st.markdown(f"**Clave:** `{datos[7]}`")
            else:
                st.markdown(f"**ID:** `ALUM-{str(st.session_state.usuario['id']).zfill(4)}`")
                st.markdown(f"**Matrícula:** `{datos[5]}`")
                st.markdown(f"**NIP:** `{datos[6]}`")

        # Botón de edición
        if st.button("Editar información", type="secondary"):
            st.session_state.editar_perfil = True
            st.rerun()

        # ===================== TABS =====================
        if es_maestro:
            tab_info, tab_grupos, tab_horario = st.tabs(["Información", "Mis Grupos", "Horario"])
        else:
            tab_info, tab_academica = st.tabs(["Información", "Información Académica"])

        with tab_info:
            st.subheader("Información Actual")
            col1, col2 = st.columns(2)
            with col1:
                st.write("**Fecha de Nacimiento:**", datos[3].strftime("%d/%m/%Y") if datos[3] else "No registrado")
                st.write("**Email:**", datos[5] if es_maestro else datos[4])
            with col2:
                if es_maestro:
                    st.write("**Teléfono:**", datos[4] or "No registrado")
                    st.write("**Especialidad:**", datos[6] or "No registrada")
                else:
                    st.write("**Teléfono:**", datos[7] or "No registrado")

        # ===================== FORMULARIO DE EDICIÓN =====================
        if st.session_state.get("editar_perfil", False):
            st.divider()
            st.subheader("Editar Perfil")

            with st.form("form_editar_perfil"):
                col1, col2 = st.columns(2)
                
                with col1:
                    nuevo_nombre = st.text_input("Nombre(s)", value=datos[0])
                    nuevo_ap_paterno = st.text_input("Apellido Paterno", value=datos[1])
                    nuevo_ap_materno = st.text_input("Apellido Materno", value=datos[2] or "")
                    nueva_fecha = st.date_input("Fecha de Nacimiento", value=datos[3])

                with col2:
                    nuevo_email = st.text_input("Email", value=datos[5] if es_maestro else datos[4])
                    nuevo_telefono = st.text_input("Teléfono", 
                                                 value=datos[4] if es_maestro else (datos[7] or ""))

                # ===================== CAMBIO DE NIP =====================
                st.divider()
                st.subheader("Cambiar NIP / Contraseña")
                cambiar_nip = st.checkbox("Quiero cambiar mi NIP / Contraseña", value=False)
                
                nip_final = None
                if cambiar_nip:
                    nuevo_nip = st.text_input("Nuevo NIP / Contraseña", type="password", key="nuevo_nip")
                    confirmar_nip = st.text_input("Confirmar Nuevo NIP / Contraseña", type="password", key="confirm_nip")
                    
                    if nuevo_nip and confirmar_nip:
                        if nuevo_nip == confirmar_nip:
                            nip_final = nuevo_nip
                        else:
                            st.error("Los NIP no coinciden")

                col_guardar, col_cancelar = st.columns(2)
                
                with col_guardar:
                    if st.form_submit_button("Guardar Cambios"):
                        try:
                            if es_maestro:
                                cursor.execute("""
                                    UPDATE maestro 
                                    SET nombre = %s, apellido_paterno = %s, apellido_materno = %s,
                                        fecha_nacimiento = %s, email = %s, telefono = %s
                                    WHERE id_maestro = %s
                                """, (nuevo_nombre.title(), nuevo_ap_paterno.title(), 
                                      nuevo_ap_materno.title() if nuevo_ap_materno else None,
                                      nueva_fecha, nuevo_email, nuevo_telefono, 
                                      st.session_state.usuario['id']))
                            else:
                                cursor.execute("""
                                    UPDATE alumno 
                                    SET nombre = %s, apellido_paterno = %s, apellido_materno = %s,
                                        fecha_nacimiento = %s, email = %s, telefono = %s
                                    WHERE id_alumno = %s
                                """, (nuevo_nombre.title(), nuevo_ap_paterno.title(), 
                                      nuevo_ap_materno.title() if nuevo_ap_materno else None,
                                      nueva_fecha, nuevo_email, nuevo_telefono, 
                                      st.session_state.usuario['id']))

                            # Actualizar NIP si se cambió
                            if nip_final:
                                if es_maestro:
                                    cursor.execute("UPDATE maestro SET nip = %s WHERE id_maestro = %s", 
                                                 (nip_final, st.session_state.usuario['id']))
                                else:
                                    cursor.execute("UPDATE alumno SET nip = %s WHERE id_alumno = %s", 
                                                 (nip_final, st.session_state.usuario['id']))

                            conn.commit()
                            st.success("Perfil actualizado correctamente")
                            time.sleep(1.5)
                            st.session_state.editar_perfil = False
                            st.rerun()

                        except Exception as e:
                            conn.rollback()
                            st.error(f"Error al guardar: {e}")

                with col_cancelar:
                    if st.form_submit_button("Cancelar"):
                        st.session_state.editar_perfil = False
                        st.rerun()
# ===================== MIS CALIFICACIONES (Solo Alumnos) =====================
elif pagina == "Mis Calificaciones":
    if st.session_state.rol_actual != "Alumno":
        st.error("Esta sección es solo para Alumnos.")
    else:
        st.title("Mis Calificaciones")
        st.markdown("**Todas tus calificaciones por materia y periodo**")

        # Filtro de Periodo
        cursor.execute("""
            SELECT DISTINCT g.periodo 
            FROM inscripcion i
            JOIN grupo g ON g.id_grupo = i.id_grupo
            WHERE i.id_alumno = %s
            ORDER BY g.periodo DESC
        """, (st.session_state.usuario['id'],))
        periodos = [row[0] for row in cursor.fetchall()]

        if not periodos:
            st.info("Aún no tienes calificaciones.")
        else:
            periodo_sel = st.selectbox("Selecciona Periodo", periodos, index=0)

            # Obtener grupos del periodo seleccionado
            cursor.execute("""
                SELECT g.id_grupo, g.nombre_grupo, m.nombre as materia
                FROM inscripcion i
                JOIN grupo g ON g.id_grupo = i.id_grupo
                JOIN materia m ON m.id_materia = g.id_materia
                WHERE i.id_alumno = %s AND g.periodo = %s
                ORDER BY m.nombre
            """, (st.session_state.usuario['id'], periodo_sel))
            grupos = cursor.fetchall()

            if not grupos:
                st.info("No hay materias en este periodo.")
            else:
                for id_grupo, nombre_grupo, materia in grupos:
                    with st.expander(f"{materia} — {nombre_grupo}", expanded=True):
                        
                        cursor.execute("""
                            SELECT u.numero,
                                   COALESCE(cf.calif_final, 
                                            (SELECT ROUND(AVG(r.calificacion)::numeric, 2)
                                             FROM resultado r
                                             JOIN config_evaluacion c ON c.id_config_evaluacion = r.id_config_evaluacion
                                             WHERE c.id_unidad = u.id_unidad 
                                               AND r.id_alumno = %s)) as calif_unidad
                            FROM unidad u
                            LEFT JOIN calificacion_final cf ON cf.id_inscripcion IN (
                                SELECT id_inscripcion FROM inscripcion 
                                WHERE id_alumno = %s AND id_grupo = %s
                            ) AND cf.id_unidad = u.id_unidad
                            WHERE u.id_grupo = %s
                            ORDER BY u.numero
                        """, (st.session_state.usuario['id'], 
                              st.session_state.usuario['id'], id_grupo, id_grupo))
                        unidades_data = cursor.fetchall()

                        cols = st.columns(len(unidades_data) + 1)
                        
                        for idx, (numero, calif) in enumerate(unidades_data):
                            with cols[idx]:
                                valor = float(calif) if calif is not None else None
                                if valor is None:
                                    st.metric(f"Unidad {numero}", "—")
                                elif valor < 70:
                                    st.metric(f"Unidad {numero}", f"{valor:.2f}")
                                else:
                                    st.metric(f"Unidad {numero}", f"{valor:.2f}")

                        # Calificación Final de la Materia
                        cursor.execute("""
                            SELECT calif_final 
                            FROM calificacion_final 
                            WHERE id_inscripcion IN (
                                SELECT id_inscripcion FROM inscripcion 
                                WHERE id_alumno = %s AND id_grupo = %s
                            )
                            AND id_unidad IS NULL
                        """, (st.session_state.usuario['id'], id_grupo))
                        final_row = cursor.fetchone()
                        final_calif = float(final_row[0]) if final_row and final_row[0] is not None else None

                        with cols[-1]:
                            if final_calif is None:
                                st.metric("**Final**", "—")
                            elif final_calif < 70:
                                st.metric("**Final**", f"{final_calif:.2f}")
                            else:
                                st.metric("**Final**", f"{final_calif:.2f}")
