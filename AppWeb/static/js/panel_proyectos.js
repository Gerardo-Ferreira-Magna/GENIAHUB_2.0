/* ============================================================
   TOAST
============================================================ */


function showToast(message, tipo="success") {
    const toastHTML = `
        <div class="toast align-items-center text-bg-${tipo} border-0 show" role="alert">
          <div class="d-flex">
            <div class="toast-body">${message}</div>
            <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast"></button>
          </div>
        </div>`;

    const container = document.querySelector(".toast-container");
    container.insertAdjacentHTML("beforeend", toastHTML);

    setTimeout(() => {
        const toast = container.querySelector(".toast");
        if (toast) toast.remove();
    }, 3500);
}

/* ============================================================
   RECARGAR TABLA + TARJETAS
============================================================ */
function reloadTable() {
    fetch(window.location.href)
        .then(res => res.text())
        .then(html => {
            const parser = new DOMParser();
            const doc = parser.parseFromString(html, "text/html");

            /* === Recargar TABLA === */
            const newTbody = doc.querySelector("#projectsTable tbody");
            const oldTbody = document.querySelector("#projectsTable tbody");
            oldTbody.innerHTML = newTbody.innerHTML;

            /* === Recargar TARJETAS === */
            const newCards = doc.querySelector(".resumen-cards");
            const oldCards = document.querySelector(".resumen-cards");

            if (newCards && oldCards) {
                oldCards.innerHTML = newCards.innerHTML;
            }

            assignRowEvents();
            paginate();
        });
}

/* ============================================================
   ASIGNAR EVENTOS A LOS BOTONES
============================================================ */
function assignRowEvents() {

    const modalDetalle = new bootstrap.Modal(document.getElementById("modalDetalle"));
    const modalEditar  = new bootstrap.Modal(document.getElementById("modalEditar"));
    const modalEliminar = new bootstrap.Modal(document.getElementById("modalEliminar"));

    /* -------- VER DETALLE -------- */
    document.querySelectorAll(".btn-ver").forEach(btn => {
        btn.onclick = () => {
            document.getElementById("detalleTitulo").textContent = btn.dataset.titulo;
            document.getElementById("detalleAutor").textContent = btn.dataset.autor;
            document.getElementById("detalleEstado").textContent = btn.dataset.estado;
            document.getElementById("detalleResumen").textContent = btn.dataset.resumen;
            document.getElementById("detalleDescripcion").textContent = btn.dataset.descripcion;
            modalDetalle.show();
        };
    });

    /* -------- EDITAR -------- */
    document.querySelectorAll(".btn-editar").forEach(btn => {
        btn.onclick = () => {
            document.getElementById("editId").value = btn.dataset.id;
            document.getElementById("editTitulo").value = btn.dataset.titulo;
            document.getElementById("editEstado").value = btn.dataset.estado;
            document.getElementById("editResumen").value = btn.dataset.resumen;
            document.getElementById("editDescripcion").value = btn.dataset.descripcion;
            modalEditar.show();
        };
    });

    document.getElementById("formEditar").onsubmit = function(e) {
        e.preventDefault();
        
        fetch(window.URL_EDITAR, {
            method: "POST",
            headers: { "X-CSRFToken": window.CSRF_TOKEN },
            body: new FormData(this)
        })
        .then(res => res.json())
        .then(data => {
            if (data.ok) {
                showToast(data.message, "success");
                modalEditar.hide();
                reloadTable();
            } else {
                showToast(data.error, "danger");
            }
        });
    };

    /* -------- ELIMINAR -------- */
    document.querySelectorAll(".btn-eliminar").forEach(btn => {
        btn.onclick = () => {
            document.getElementById("deleteId").value = btn.dataset.id;
            document.getElementById("eliminarTitulo").textContent = btn.dataset.titulo;
            modalEliminar.show();
        };
    });

    document.getElementById("formEliminar").onsubmit = function (e) {
        e.preventDefault();

        fetch(window.URL_ELIMINAR, {
            method: "POST",
            headers: { "X-CSRFToken": window.CSRF_TOKEN },
            body: new FormData(this)
        })
        .then(res => res.json())
        .then(data => {
            if (data.ok) {
                showToast(data.message, "danger");
                modalEliminar.hide();
                reloadTable();
            } else {
                showToast(data.error, "danger");
            }
        });
    };

}

/* ============================================================
   PAGINACIÓN
============================================================ */
function paginate() {
    const rows = document.querySelectorAll("tr.fila-proyecto");
    const rowsPerPage = 10;
    const pagination = document.getElementById("pagination");

    let currentPage = 1;

    function displayPage() {
        const start = (currentPage - 1) * rowsPerPage;
        const end = start + rowsPerPage;

        rows.forEach((row, i) => {
            row.style.display = (i >= start && i < end) ? "" : "none";
        });
    }

    function renderPagination() {
        const totalPages = Math.ceil(rows.length / rowsPerPage);
        pagination.innerHTML = "";

        if (totalPages <= 1) return;

        for (let i = 1; i <= totalPages; i++) {
            const li = document.createElement("li");
            li.className = `page-item ${i === currentPage ? "active" : ""}`;
            li.innerHTML = `<a class='page-link' href='#'>${i}</a>`;

            li.onclick = (e) => {
                e.preventDefault();
                currentPage = i;
                displayPage();
                renderPagination();
            };

            pagination.appendChild(li);
        }
    }

    displayPage();
    renderPagination();
}

/* ============================================================
   BUSCADOR
============================================================ */
function setupSearch() {
    const searchInput = document.getElementById("searchInput");

    searchInput.addEventListener("keyup", () => {
        const search = searchInput.value.toLowerCase();
        const rows = document.querySelectorAll("tr.fila-proyecto");

        rows.forEach(row => {
            row.style.display = row.textContent.toLowerCase().includes(search) ? "" : "none";
        });
    });
}

/* ============================================================
   READY
============================================================ */
document.addEventListener("DOMContentLoaded", () => {
    assignRowEvents();
    paginate();
    setupSearch();
});

function applyFilters() {
    const estado = document.getElementById("filtroEstado").value.toLowerCase();
    const anio = document.getElementById("filtroAnio").value;
    const docente = document.getElementById("filtroDocente") ? document.getElementById("filtroDocente").value : "";
    const texto = document.getElementById("filtroTexto").value.toLowerCase();

    document.querySelectorAll("tr.fila-proyecto").forEach(row => {
        const rowText = row.textContent.toLowerCase();
        const rowEstado = row.querySelector("td:nth-child(4)").textContent.toLowerCase();
        const rowAnio = row.querySelector("td:nth-child(6)").textContent.slice(-4);
        const rowDocente = row.querySelector("td:nth-child(3)").dataset.userid;

        let visible = true;

        if (estado && !rowEstado.includes(estado)) visible = false;
        if (anio && rowAnio != anio) visible = false;
        if (docente && rowDocente != docente) visible = false;
        if (texto && !rowText.includes(texto)) visible = false;

        row.style.display = visible ? "" : "none";
    });
}

document.getElementById("filtroEstado").onchange = applyFilters;
document.getElementById("filtroAnio").onchange = applyFilters;
if (document.getElementById("filtroDocente")) {
    document.getElementById("filtroDocente").onchange = applyFilters;
}
document.getElementById("filtroTexto").onkeyup = applyFilters;



