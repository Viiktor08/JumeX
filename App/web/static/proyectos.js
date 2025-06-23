let proyectoActivo = null;

document.addEventListener("DOMContentLoaded", function() {
  // Cargar mensajes del proyecto activo si existe
  const idActivo = sessionStorage.getItem("proyectoActivo");

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
});