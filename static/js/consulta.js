// Paso 1: Buscar CDCs desde la base de datos por fecha
function buscarCdcsPorFecha() {
    const desde = document.getElementById("desde").value;
    const hasta = document.getElementById("hasta").value;
    const textarea = document.getElementById("cdcInput");
    const resultado = document.getElementById("resultado");
  
    if (!desde || !hasta) {
      resultado.textContent = "Por favor selecciona el rango de fechas.";
      return;
    }
  
    resultado.textContent = "Buscando CDCs en la base de datos...";
  
    fetch("/buscar_cdcs", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ desde, hasta })
    })
      .then(res => res.json())
      .then(data => {
        if (data.cdcs) {
          textarea.value = data.cdcs.join("\n");
          resultado.textContent = `✅ Se encontraron ${data.cdcs.length} CDC(s). Ahora puedes consultar.`;
        } else if (data.error) {
          resultado.textContent = "⚠️ Error: " + data.error;
        }
      })
      .catch(err => {
        resultado.textContent = "⚠️ Error: " + err;
      });
  }
  
  // Paso 2: Enviar los CDCs a la API para consultar
  function consultarCDC() {
    const textarea = document.getElementById("cdcInput");
    const resultado = document.getElementById("resultado");
  
    const cdcList = textarea.value
      .split('\n')
      .map(cdc => cdc.trim())
      .filter(cdc => cdc.length > 0);
  
    if (cdcList.length === 0) {
      resultado.textContent = "⚠️ Por favor ingresa al menos un CDC.";
      return;
    }
  
    resultado.textContent = "⏳ Consultando en la API...";
  
    fetch("/consultar", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ cdcList })
    })
      .then(res => res.json())
      .then(data => {
        document.getElementById("resultado").value = JSON.stringify(data, null, 2);
      })
      .catch(error => {
        document.getElementById("resultado").value = "❌ Error al consultar: " + error;
      });
  }

  function abrirInforme() {
    fetch("/informe")
      .then(res => res.json())
      .then(data => {
        if (data.error) {
          alert(data.error);
        } else {
          let tabla = "Fecha\tFactura\tRespuesta\tCDC\n";
          data.forEach(row => {
            tabla += `${row.Fecha}\t${row.Factura}\t${row.Resp}\t${row.CDC}\n`;
          });
          alert(tabla); // puedes cambiar por mostrarlo en un <div> bonito también
        }
      });
  }
  