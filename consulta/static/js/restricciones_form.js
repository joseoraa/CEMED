// static/js/restricciones_form.js

document.addEventListener('DOMContentLoaded', function () {

    const campos = {
      
        'id_cedula': 'solo-numeros',
        'id_telefono': 'solo-numeros',
        'id_codigo_exa': 'solo-numeros',


        'apellido_paciente': 'solo-letras',
        'nombre_paciente': 'solo-letras',
        'id_nombre': 'solo-letras',
        'id_apellido': 'solo-letras',
        'id_nom_exa': 'solo-letras',
        'id_nombre_ins': 'solo-letras',
        'id_presentacion_ins': 'solo-letras',
        'id_proveedor_ins': 'solo-letras',
        'id_descripcion_ins':'solo-letras',

        
    };

    Object.keys(campos).forEach(id => {
        const input = document.getElementById(id);
        if (input) {
            input.classList.add(campos[id]);
        }
    });

    document.querySelectorAll('.solo-numeros').forEach(input => {
        input.addEventListener('keypress', function(e) {
            if (!/[0-9]/.test(e.key) && 
                !['Backspace', 'Delete', 'ArrowLeft', 'ArrowRight', 'Tab'].includes(e.key)) {
                e.preventDefault();
            }
        });

        input.addEventListener('paste', function(e) {
            const text = (e.clipboardData || window.clipboardData).getData('text');
            if (!/^\d+$/.test(text)) e.preventDefault();
        });
    });
    
    document.querySelectorAll('.solo-letras').forEach(input => {
        input.addEventListener('keypress', function(e) {
            if (!/[A-Za-záéíóúÁÉÍÓÚñÑ\s]/.test(e.key) && 
                !['Backspace', 'Delete', 'ArrowLeft', 'ArrowRight', 'Tab'].includes(e.key)) {
                e.preventDefault();
            }
        });

        input.addEventListener('paste', function(e) {
            const text = (e.clipboardData || window.clipboardData).getData('text');
            if (!/^[A-Za-záéíóúÁÉÍÓÚñÑ\s]+$/.test(text)) e.preventDefault();
        });
    });

});



document.addEventListener("submit", function(e){
    if(e.target.id === "formHistoria"){
        e.preventDefault();

        let formData = new FormData(e.target);

        fetch(window.location.href, {
            method: "POST",
            body: formData
        })
        .then(res => res.json())
        .then(data => {
            if(data.success){
                document.getElementById("modalBody").innerHTML = data.html;
            }
        });
    }
});