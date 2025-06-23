let proyectoActivo = null;

document.addEventListener("DOMContentLoaded", function() {
  // Cargar mensajes del proyecto activo si existe
  const idActivo = sessionStorage.getItem("proyectoActivo");
  if (idActivo) {
    proyectoActivo = idActivo;
    cargarMensajes(proyectoActivo);
  }

  // Mostrar el botón al pasar el mouse
  document.querySelectorAll('.contenedor-proyecto').forEach(proyecto => {
    proyecto.addEventListener('mouseenter', () => {
        proyecto.querySelectorAll('.boton-editar, .boton-eliminar').forEach(btn => {
            btn.classList.remove('d-none');
        });
    });

    proyecto.addEventListener('mouseleave', () => {
        proyecto.querySelectorAll('.boton-editar, .boton-eliminar').forEach(btn => {
            btn.classList.add('d-none');
        });
    });

    // Añadir evento de clic para seleccionar proyecto
    proyecto.addEventListener('click', function(e) {
      if (!e.target.closest('.boton-editar') && !e.target.closest('.boton-eliminar')) {
        let contenedorProyectos=document.getElementById("contenedor-proyectos");
        contenedorProyectos.querySelectorAll("#contenedor-proyectos .active").forEach(el=>{el.classList.remove("active")});
        const id = this.dataset.id;
        proyectoActivo = id;
        sessionStorage.setItem("proyectoActivo", id);
        const contenedor = document.querySelector(`.contenedor-proyecto[data-id="${proyectoActivo}"]`);
        if (contenedor) {
          contenedor.classList.add("active");
          const enlace = contenedor.querySelector("a");
          if (enlace) {
            enlace.classList.add("active");
          }
        }

        const reportePath = this.getAttribute("data-reporte");
        const btnDescargarReporte = document.getElementById("btnDescargarReporte");

        if (reportePath && reportePath !== "None" && reportePath !== "") {
          const nombreArchivo = reportePath.split('/').pop();
          btnDescargarReporte.href = `/descargar-reporte/${nombreArchivo}`;
          btnDescargarReporte.classList.remove("d-none");
        } else {
          btnDescargarReporte.classList.add("d-none");
          btnDescargarReporte.href = "";
        }

        cargarMensajes(id);
      }
    });
  });

  // Guardar ID al hacer clic en el botón de editar
  document.querySelectorAll(".boton-editar").forEach(boton => {
    boton.addEventListener("click", function () {
      const contenedor = this.closest(".contenedor-proyecto");
      if (contenedor) {
        const id = contenedor.dataset.id;
        sessionStorage.setItem("proyectoActivo", id);
      }
    });
  });

  // Aplicar clase "active" al volver a /proyectos
  if (idActivo) {
    const contenedor = document.querySelector(`.contenedor-proyecto[data-id="${idActivo}"]`);
    if (contenedor) {
      contenedor.classList.add("active");
      const enlace = contenedor.querySelector("a");
      if (enlace) {
        enlace.classList.add("active");
      }
    }
  }

  document.getElementById("sbomFile").addEventListener("change", subirSBOM);

  function subirSBOM() {
    const proyectoActivo = sessionStorage.getItem("proyectoActivo");

    if (!proyectoActivo) {
      alert("Selecciona un proyecto antes de subir SBOM.");
      return;
    }

    const fileInput = document.getElementById("sbomFile");
    const file = fileInput.files[0];

    if (!file) {
      alert("Selecciona un archivo SBOM.");
      return;
    }

    const formData = new FormData();
    formData.append("proyecto_id", proyectoActivo);
    formData.append("sbom", file);

    fetch("http://localhost:5010/subir-sbom", {
      method: "POST",
      credentials: "include",
      body: formData
    })
    .then(res => {
      if (!res.ok) throw new Error("Error al subir el archivo");
      return res.json();
    })
    .then(data => {
      alert("Archivo subido correctamente: " + data.nombre);
    })
    .catch(err => {
      alert("Error al subir: " + err.message);
    });
  }
});

function cargarMensajes(proyectoId) {
  const chatBody = document.getElementById("chatBody");
  chatBody.innerHTML = ''; // Limpiar mensajes actuales

  fetch(`http://localhost:5011/chat?proyecto_id=${proyectoId}`, {
    method: 'GET',
    credentials: 'include'
  })
  .then(response => response.json())
  .then(mensajes => {
    mensajes.forEach(mensaje => {
      const div = document.createElement("div");
      div.className = `chat-message ${mensaje.es_bot ? 'bot' : 'user'} d-flex`;
      
      if (mensaje.es_bot) {
        div.innerHTML = `
          <div class="col-1 px-0">
            <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" fill="currentColor" class="bi bi-robot" viewBox="0 0 16 16">
              <path d="M6 12.5a.5.5 0 0 1 .5-.5h3a.5.5 0 0 1 0 1h-3a.5.5 0 0 1-.5-.5M3 8.062C3 6.76 4.235 5.765 5.53 5.886a26.6 26.6 0 0 0 4.94 0C11.765 5.765 13 6.76 13 8.062v1.157a.93.93 0 0 1-.765.935c-.845.147-2.34.346-4.235.346s-3.39-.2-4.235-.346A.93.93 0 0 1 3 9.219zm4.542-.827a.25.25 0 0 0-.217.068l-.92.9a25 25 0 0 1-1.871-.183.25.25 0 0 0-.068.495c.55.076 1.232.149 2.02.193a.25.25 0 0 0 .189-.071l.754-.736.847 1.71a.25.25 0 0 0 .404.062l.932-.97a25 25 0 0 0 1.922-.188.25.25 0 0 0-.068-.495c-.538.074-1.207.145-1.98.189a.25.25 0 0 0-.166.076l-.754.785-.842-1.7a.25.25 0 0 0-.182-.135"/>
              <path d="M8.5 1.866a1 1 0 1 0-1 0V3h-2A4.5 4.5 0 0 0 1 7.5V8a1 1 0 0 0-1 1v2a1 1 0 0 0 1 1v1a2 2 0 0 0 2 2h10a2 2 0 0 0 2-2v-1a1 1 0 0 0 1-1V9a1 1 0 0 0-1-1v-.5A4.5 4.5 0 0 0 10.5 3h-2zM14 7.5V13a1 1 0 0 1-1 1H3a1 1 0 0 1-1-1V7.5A3.5 3.5 0 0 1 5.5 4h5A3.5 3.5 0 0 1 14 7.5"/>
            </svg>
          </div>
          <div class="alert alert-secondary col-10" style="width: 90%;">
            <p class="fs-5">${mensaje.contenido}</p>
          </div>`;
      } else {
        div.innerHTML = `
          <div class="alert alert-primary col-10" style="width: 90%;">
            <p class="fs-5">${mensaje.contenido}</p>
          </div>
          <div class="col-1 px-0 text-end">
            <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" fill="currentColor" class="bi bi-person-fill" viewBox="0 0 16 16">
              <path d="M3 14s-1 0-1-1 1-4 6-4 6 3 6 4-1 1-1 1zm5-6a3 3 0 1 0 0-6 3 3 0 0 0 0 6"/>
            </svg>
          </div>`;
      }
      chatBody.appendChild(div);
    });
    chat_box.scrollTop = chat_box.scrollHeight;
  })
  .catch(error => {
    console.error("Error al cargar mensajes:", error);
  });
}

function sendMessage() {
  if (!proyectoActivo) {
    alert("Por favor, selecciona un proyecto primero");
    return;
  }

  let input = document.getElementById("userInput");
  let message = input.value.trim();
  if (message === "") return;

  let chatBody = document.getElementById("chatBody");

  // mensaje del usuario
  let userMsg = document.createElement("div");
  userMsg.className = "chat-message user d-flex";
  userMsg.innerHTML = `<div class="alert alert-primary col-10" style="width: 90%;"><p class="fs-5">${message}</p></div><div class="col-1 px-0 text-end"><svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" fill="currentColor" class="bi bi-person-fill" viewBox="0 0 16 16"><path d="M3 14s-1 0-1-1 1-4 6-4 6 3 6 4-1 1-1 1zm5-6a3 3 0 1 0 0-6 3 3 0 0 0 0 6"/></svg></div>`;
  chatBody.appendChild(userMsg);
  chat_box.scrollTop = chat_box.scrollHeight;

  input.value = "";

  // petición a servidor
  fetch(`http://localhost:5011/chat`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    credentials: 'include',
    body: JSON.stringify({
      proyecto_id: proyectoActivo,
      message: message
    })
  })
  .then(response => {
    if (!response.ok) {
      throw new Error(`Error HTTP: ${response.status} ${response.statusText}`);
    }
    return response.json();
  })
  .then(data => {
    let responseText = data.response;

    // mensaje del chatbot
    let botMsg = document.createElement("div");
    botMsg.className = "chat-message bot d-flex";
    botMsg.innerHTML = `<div class="col-1 px-0"><svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" fill="currentColor" class="bi bi-robot" viewBox="0 0 16 16"><path d="M6 12.5a.5.5 0 0 1 .5-.5h3a.5.5 0 0 1 0 1h-3a.5.5 0 0 1-.5-.5M3 8.062C3 6.76 4.235 5.765 5.53 5.886a26.6 26.6 0 0 0 4.94 0C11.765 5.765 13 6.76 13 8.062v1.157a.93.93 0 0 1-.765.935c-.845.147-2.34.346-4.235.346s-3.39-.2-4.235-.346A.93.93 0 0 1 3 9.219zm4.542-.827a.25.25 0 0 0-.217.068l-.92.9a25 25 0 0 1-1.871-.183.25.25 0 0 0-.068.495c.55.076 1.232.149 2.02.193a.25.25 0 0 0 .189-.071l.754-.736.847 1.71a.25.25 0 0 0 .404.062l.932-.97a25 25 0 0 0 1.922-.188.25.25 0 0 0-.068-.495c-.538.074-1.207.145-1.98.189a.25.25 0 0 0-.166.076l-.754.785-.842-1.7a.25.25 0 0 0-.182-.135"/><path d="M8.5 1.866a1 1 0 1 0-1 0V3h-2A4.5 4.5 0 0 0 1 7.5V8a1 1 0 0 0-1 1v2a1 1 0 0 0 1 1v1a2 2 0 0 0 2 2h10a2 2 0 0 0 2-2v-1a1 1 0 0 0 1-1V9a1 1 0 0 0-1-1v-.5A4.5 4.5 0 0 0 10.5 3h-2zM14 7.5V13a1 1 0 0 1-1 1H3a1 1 0 0 1-1-1V7.5A3.5 3.5 0 0 1 5.5 4h5A3.5 3.5 0 0 1 14 7.5"/></svg></div><div class="alert alert-secondary col-10" style="width: 90%;"><p class="fs-5">${responseText}</p></div>`;
    chatBody.appendChild(botMsg);
    chat_box.scrollTop = chat_box.scrollHeight;
  })
  .catch(error => {
    console.error("Error en la petición:", error);
    let botMsg = document.createElement("div");
    botMsg.className = "chat-message bot d-flex";
    botMsg.innerHTML = `<div class="col-1 px-0"><svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" fill="currentColor" class="bi bi-robot" viewBox="0 0 16 16"><path d="M6 12.5a.5.5 0 0 1 .5-.5h3a.5.5 0 0 1 0 1h-3a.5.5 0 0 1-.5-.5M3 8.062C3 6.76 4.235 5.765 5.53 5.886a26.6 26.6 0 0 0 4.94 0C11.765 5.765 13 6.76 13 8.062v1.157a.93.93 0 0 1-.765.935c-.845.147-2.34.346-4.235.346s-3.39-.2-4.235-.346A.93.93 0 0 1 3 9.219zm4.542-.827a.25.25 0 0 0-.217.068l-.92.9a25 25 0 0 1-1.871-.183.25.25 0 0 0-.068.495c.55.076 1.232.149 2.02.193a.25.25 0 0 0 .189-.071l.754-.736.847 1.71a.25.25 0 0 0 .404.062l.932-.97a25 25 0 0 0 1.922-.188.25.25 0 0 0-.068-.495c-.538.074-1.207.145-1.98.189a.25.25 0 0 0-.166.076l-.754.785-.842-1.7a.25.25 0 0 0-.182-.135"/><path d="M8.5 1.866a1 1 0 1 0-1 0V3h-2A4.5 4.5 0 0 0 1 7.5V8a1 1 0 0 0-1 1v2a1 1 0 0 0 1 1v1a2 2 0 0 0 2 2h10a2 2 0 0 0 2-2v-1a1 1 0 0 0 1-1V9a1 1 0 0 0-1-1v-.5A4.5 4.5 0 0 0 10.5 3h-2zM14 7.5V13a1 1 0 0 1-1 1H3a1 1 0 0 1-1-1V7.5A3.5 3.5 0 0 1 5.5 4h5A3.5 3.5 0 0 1 14 7.5"/></svg></div><div class="alert alert-secondary col-10" style="width: 90%;"><p class="fs-5">Error de conexión: ${error.message}</div>`;
    chatBody.appendChild(botMsg);
    chat_box.scrollTop = chat_box.scrollHeight;
  });
}

let input = document.getElementById("userInput");
input.addEventListener("keydown", function(event) {
  if (event.key === "Enter" && !event.shiftKey) {
    event.preventDefault();
    sendMessage();
  }
});

document.getElementById("btnAnalizarSBOM").addEventListener("click", () => {
  const proyectoActivo = sessionStorage.getItem("proyectoActivo");
  if (!proyectoActivo) {
    alert("Selecciona un proyecto primero");
    return;
  }

  const chatBody = document.getElementById("chatBody");

  // Mostrar mensaje de análisis y barra de progreso
  const divAnalisis = document.createElement("div");
  divAnalisis.className = "chat-message bot d-flex";
  divAnalisis.innerHTML = `
    <div class="col-1 px-0">
      <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" fill="currentColor" class="bi bi-robot" viewBox="0 0 16 16">
        <path d="M6 12.5a.5.5 0 0 1 .5-.5h3a.5.5 0 0 1 0 1h-3a.5.5 0 0 1-.5-.5M3 8.062C3 6.76 4.235 5.765 5.53 5.886a26.6 26.6 0 0 0 4.94 0C11.765 5.765 13 6.76 13 8.062v1.157a.93.93 0 0 1-.765.935c-.845.147-2.34.346-4.235.346s-3.39-.2-4.235-.346A.93.93 0 0 1 3 9.219zm4.542-.827a.25.25 0 0 0-.217.068l-.92.9a25 25 0 0 1-1.871-.183.25.25 0 0 0-.068.495c.55.076 1.232.149 2.02.193a.25.25 0 0 0 .189-.071l.754-.736.847 1.71a.25.25 0 0 0 .404.062l.932-.97a25 25 0 0 0 1.922-.188.25.25 0 0 0-.068-.495c-.538.074-1.207.145-1.98.189a.25.25 0 0 0-.166.076l-.754.785-.842-1.7a.25.25 0 0 0-.182-.135"/>
        <path d="M8.5 1.866a1 1 0 1 0-1 0V3h-2A4.5 4.5 0 0 0 1 7.5V8a1 1 0 0 0-1 1v2a1 1 0 0 0 1 1v1a2 2 0 0 0 2 2h10a2 2 0 0 0 2-2v-1a1 1 0 0 0 1-1V9a1 1 0 0 0-1-1v-.5A4.5 4.5 0 0 0 10.5 3h-2zM14 7.5V13a1 1 0 0 1-1 1H3a1 1 0 0 1-1-1V7.5A3.5 3.5 0 0 1 5.5 4h5A3.5 3.5 0 0 1 14 7.5"/>
      </svg>
    </div>
    <div class="alert alert-secondary col-10">
      <p class="fs-5 mb-2">Analizando SBOM... por favor, espera.</p>
      <div class="progress">
        <div class="progress-bar progress-bar-striped progress-bar-animated bg-info" role="progressbar" style="width: 100%"></div>
      </div>
    </div>`;
  chatBody.appendChild(divAnalisis);
  chat_box.scrollTop = chat_box.scrollHeight;

  const formData = new FormData();
  formData.append("proyecto_id", proyectoActivo);

  fetch("/analizar-sbom", {
    method: "POST",
    body: formData,
  })
  .then(res => {
    if (!res.ok) {
      return res.json().then(data => { throw new Error(data.error || "Error desconocido") });
    }
    return res.json();
  })
  .then(data => {
    // Eliminar barra de progreso
    divAnalisis.remove();

    data.mensajes.forEach(cve => {
      const div = document.createElement("div");
      div.className = "chat-message bot d-flex";
      let solucionabilidad = "";
      if (cve.solucionable && cve.detalles_solucion) {
        const versiones = cve.detalles_solucion.versiones_seguras.map(v => `<li>${v}</li>`).join("");
        const referencias = cve.detalles_solucion.referencias_utiles.map(url => `<li><a href="${url}" target="_blank">${url}</a></li>`).join("");
        solucionabilidad = `
          <p><strong>Solución disponible:</strong></p>
          ${versiones ? `<p>Versiones seguras:</p><ul>${versiones}</ul>` : ""}
          ${referencias ? `<p>Referencias útiles:</p><ul>${referencias}</ul>` : ""}
        `;
      } else {
        solucionabilidad = `<p><strong>Solución NO disponible</strong></p>`;
      }

      div.innerHTML = `
        <div class="alert alert-secondary col-10">
          <p><strong>Componente:${cve.componente}</strong></p>
          <p><strong>${cve.id}</strong></p>
          <p><strong>Descripción: </strong>${cve.descripcion}</p>
          <p><strong>Puntuación: </strong>${cve.puntuacion}</p>
          ${solucionabilidad}
        </div>
      `;
      chatBody.appendChild(div);
    });

    if (data.criterios) {
      const div = document.createElement("div");
      div.className = "chat-message bot d-flex";
      div.innerHTML = `
        <div class="alert alert-info col-10">
          <p><strong>Resultado de criterios:</strong></p>
          <p>${data.criterios.mensaje}</p>
        </div>
      `;
      chatBody.appendChild(div);
    }

    // Mensaje final con botón de descarga
    if (data.descarga) {
      const div = document.createElement("div");
      div.className = "chat-message bot d-flex";
      div.innerHTML = `
        <div class="alert alert-success col-10">
          <p><strong>¡Análisis finalizado!</strong></p>
          <p>Puedes descargar el informe completo aquí:</p>
          <a href="${data.descarga}" class="btn btn-success" download>Descargar reporte</a>
        </div>
      `;
      chatBody.appendChild(div);
    }
    chat_box.scrollTop = chat_box.scrollHeight;
  }).catch(err => {
    divAnalisis.remove();
    alert(err.message);
  });
});
